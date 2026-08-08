from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Callable, Mapping, Protocol

from .construction import (
    ConstructionAdapter,
    ObservationAdapter,
    adapter_context,
    observation_adapter_context,
    validate_and_lower,
    validate_and_lower_observation,
)

from .griess import (
    advance_griess,
    declare_kappa as declare_griess_kappa,
    invalidate_to_derive,
    kappa_sha256,
)
from .state import (
    STATE_VERSION,
    MapV2Error,
    MapV2StateMixin,
    require_node_name,
    utc_now,
)
from .prologish import split_statements


DEFAULT_STATE_DIR = Path(".map-v2")
ATOM_RE = re.compile(r"^[a-z][a-zA-Z0-9_]*$")


class TargetCompiler(Protocol):
    def compile(
        self,
        workspace_path: Path,
        subject: str,
        target: str,
        kappa: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...


GuideBuilder = Callable[[Path, dict[str, Any], list[dict[str, str]]], dict[str, Any]]
CertificateBuilder = Callable[
    [dict[str, Any], dict[str, Any], dict[str, Any]], dict[str, Any]
]


PACKET_FIELDS = (
    "status",
    "purpose",
    "griess_phase",
    "frontier",
    "blocked",
    "admissible",
    "outputs",
    "domain_terms",
    "domain_id",
    "domain_sha256",
    "workspace_sha256",
    "kappa_sha256",
    "construction_schema_id",
    "construction_schema_sha256",
    "construction_payload_sha256",
    "construction_render_sha256",
    "construction_lowering_id",
    "construction_lowering_sha256",
    "construction_facts_sha256",
    "observation_schema_id",
    "observation_schema_sha256",
    "observation_payload_sha256",
    "observation_render_sha256",
    "observation_lowering_id",
    "observation_lowering_sha256",
    "observation_facts_sha256",
)


def compact_packet(packet: dict[str, Any]) -> dict[str, Any]:
    fields = (*PACKET_FIELDS, *packet.get("persist_fields", ()))
    return {field: packet[field] for field in fields if field in packet}


def _require_atom(value: str, label: str) -> str:
    if not ATOM_RE.fullmatch(value):
        raise MapV2Error(f"{label} must be an unquoted Prolog atom: {value!r}")
    return value


def _normalize_facts(raw_facts: list[str]) -> list[str]:
    if not raw_facts:
        raise MapV2Error("fill requires at least one authored Prolog fact")
    statements = split_statements("\n".join(raw_facts), source="<map-v2-fill>")
    if not statements:
        raise MapV2Error("fill did not contain any complete Prolog facts")
    for statement in statements:
        if ":-" in statement or "?-" in statement:
            raise MapV2Error("MAP v2 fill accepts authored facts, not directives or rules")
    return [statement.strip() for statement in statements]


class MapV2Lattice(MapV2StateMixin):
    """Persistent LLM-operated lattice compiled by a selected MAP domain."""

    def __init__(
        self,
        state_dir: str | Path = DEFAULT_STATE_DIR,
        *,
        compiler: TargetCompiler | None = None,
        construction_adapter: ConstructionAdapter | None = None,
        observation_adapter: ObservationAdapter | None = None,
        guide_builder: GuideBuilder | None = None,
        certificate_builder: CertificateBuilder | None = None,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.state_path = self.state_dir / "state.json"
        self.workspace_path = self.state_dir / "workspace.pl"
        self.compiler = compiler
        self.construction_adapter = construction_adapter
        self.observation_adapter = observation_adapter
        self.guide_builder = guide_builder
        self.certificate_builder = certificate_builder

    def create(self, subject: str, target: str, root: str | None = None) -> dict[str, Any]:
        subject = _require_atom(subject, "subject")
        target = _require_atom(target.lower(), "target")
        compiler_targets = tuple(getattr(self.compiler, "targets", ()))
        if compiler_targets and target not in compiler_targets:
            raise MapV2Error(
                f"target must be provided by the selected domain: {', '.join(compiler_targets)}"
            )
        root = require_node_name(root or subject)
        if self.state_path.exists() or self.workspace_path.exists():
            raise MapV2Error(f"lattice already exists at {self.state_dir}")
        now = utc_now()
        state = {
            "version": STATE_VERSION,
            "subject": subject,
            "target": target,
            "domain_id": getattr(getattr(self.compiler, "domain", None), "id", None),
            "root": root,
            "selected": root,
            "created_at": now,
            "updated_at": now,
            "nodes": {root: self._new_node(root, parent=None)},
        }
        self._save(state)
        return self.summary(state)

    def expand(self, name: str, parts: list[str]) -> dict[str, Any]:
        state = self._load()
        node = self._node(state, name)
        if node["status"] != "open":
            raise MapV2Error(f"only open nodes can expand; {name!r} is {node['status']}")
        if not parts:
            raise MapV2Error("expand requires at least one child")
        children = self._add_children(state, name, parts)
        node["children"] = children
        node["status"] = "expanded"
        state["selected"] = children[0]
        self._save(state)
        return {"expanded": name, "children": children, "next": children[0]}

    def declare_kappa(
        self, name: str, domain: str, invariants: dict[str, str]
    ) -> dict[str, Any]:
        state = self._load()
        node = self._node(state, name)
        previous_digest = kappa_sha256(node["griess"])
        _require_atom(domain, "kappa domain")
        for invariant_name in invariants:
            _require_atom(invariant_name, "kappa invariant")
        declare_griess_kappa(node["griess"], domain, invariants)
        current_digest = kappa_sha256(node["griess"])
        if previous_digest != current_digest:
            node["certificate"] = None
            node["proof_context"] = None
        state["selected"] = name
        self._save(state)
        return {
            "node": name,
            "phase": node["griess"]["phase"],
            "kappa": node["griess"]["kappa"],
            "kappa_sha256": current_digest,
            "next": "compute",
        }

    def compute(
        self,
        name: str | None = None,
        compiler: TargetCompiler | None = None,
    ) -> dict[str, Any]:
        state = self._load()
        name = name or state.get("selected")
        if not name:
            raise MapV2Error("no node selected")
        node = self._node(state, name)
        if node["status"] not in {"open", "repairing"}:
            raise MapV2Error(
                f"compute requires an open or repairing node; {name!r} is {node['status']}"
            )
        if node["griess"]["phase"] != "derive":
            raise MapV2Error(
                f"compute requires Griess derive; {name!r} is {node['griess']['phase']}"
            )
        selected_compiler = self._resolve_compiler(compiler)
        packet = selected_compiler.compile(
            self.workspace_path,
            state["subject"],
            state["target"],
            kappa=node["griess"]["kappa"],
        )
        advance_griess(node["griess"], "compute", "MAP domain obligations inspected")
        packet.update(self._packet_scope(state, name, self._workspace_sha256(state), node))
        packet["purpose"] = "compute_constraints"
        packet["griess_phase"] = "compute"
        node["last_packet"] = compact_packet(packet)
        state["selected"] = name
        self._save(state)
        return packet

    def fill(self, name: str, raw_facts: list[str]) -> dict[str, Any]:
        if self.construction_adapter is not None or self.observation_adapter is not None:
            raise MapV2Error(
                "raw fill is disabled when typed authority adapters are selected"
            )
        state = self._load()
        node = self._node(state, name)
        if node["status"] != "open":
            raise MapV2Error(f"only open nodes can be filled; {name!r} is {node['status']}")
        if node["griess"]["phase"] != "compute":
            raise MapV2Error(
                f"fill requires Griess compute; {name!r} is {node['griess']['phase']}"
            )
        facts = _normalize_facts(raw_facts)
        node["facts"] = facts
        node["construction"] = None
        node["status"] = "filled"
        node["certificate"] = None
        node["proof_context"] = None
        advance_griess(node["griess"], "build", "authored facts filled")
        state["selected"] = name
        self._save(state)
        return {
            "filled": name,
            "fact_count": len(facts),
            "griess_phase": "build",
            "next": self.next_name(state),
        }

    def fill_construction(
        self,
        name: str,
        payload: Mapping[str, Any],
        adapter: ConstructionAdapter | None = None,
    ) -> dict[str, Any]:
        """Validate a PSC value and fill a node with candidate-only facts."""
        state = self._load()
        node = self._node(state, name)
        if node["status"] != "open":
            raise MapV2Error(
                f"only open nodes can be filled; {name!r} is {node['status']}"
            )
        if node["griess"]["phase"] != "compute":
            raise MapV2Error(
                f"fill_construction requires Griess compute; {name!r} is "
                f"{node['griess']['phase']}"
            )
        selected_adapter = self._resolve_construction_adapter(adapter)
        if selected_adapter.target != state["target"]:
            raise MapV2Error(
                "construction adapter target mismatch: "
                f"expected {state['target']}, got {selected_adapter.target}"
            )
        lowered = validate_and_lower(selected_adapter, payload)
        node["facts"] = lowered.facts
        node["construction"] = lowered.metadata
        node["status"] = "filled"
        node["certificate"] = None
        node["proof_context"] = None
        advance_griess(
            node["griess"], "build", "typed PSC construction lowered to candidate facts"
        )
        state["selected"] = name
        self._save(state)
        return {
            "filled": name,
            "fact_count": len(lowered.facts),
            "construction": self._construction_summary(lowered.metadata),
            "griess_phase": "build",
            "next": self.next_name(state),
        }

    def attach_observation(
        self,
        name: str,
        payload: Mapping[str, Any],
        adapter: ObservationAdapter | None = None,
    ) -> dict[str, Any]:
        """Attach independently validated source evidence to a filled node."""
        state = self._load()
        node = self._node(state, name)
        if node["status"] != "filled" or node["griess"]["phase"] != "build":
            raise MapV2Error(
                f"attach_observation requires a filled BUILD node; {name!r} is "
                f"{node['status']}/{node['griess']['phase']}"
            )
        if node.get("observation") is not None:
            raise MapV2Error(f"node already has an observation snapshot: {name!r}")
        selected_adapter = self._resolve_observation_adapter(adapter)
        if selected_adapter.target != state["target"]:
            raise MapV2Error(
                "observation adapter target mismatch: "
                f"expected {state['target']}, got {selected_adapter.target}"
            )
        lowered = validate_and_lower_observation(selected_adapter, payload)
        node["facts"].extend(lowered.facts)
        node["observation"] = lowered.metadata
        node["certificate"] = None
        node["proof_context"] = None
        state["selected"] = name
        self._save(state)
        return {
            "observed": name,
            "fact_count": len(lowered.facts),
            "observation": self._artifact_summary(lowered.metadata),
            "griess_phase": "build",
            "next": "compile",
        }

    def retry(self, name: str) -> dict[str, Any]:
        state = self._load()
        node = self._node(state, name)
        phase = node["griess"]["phase"]
        certificate = node.get("certificate") or {}
        workspace_stale = certificate.get("workspace_sha256") != self._workspace_sha256(state)
        kappa_stale = certificate.get("kappa_sha256") != kappa_sha256(node["griess"])
        domain_sha256 = self._current_domain_sha256(state)
        domain_stale = (
            domain_sha256 is not None
            and certificate.get("domain_sha256") != domain_sha256
        )
        construction_stale = self._construction_rejection(node) is not None
        observation_stale = self._observation_rejection(node) is not None
        if phase == "soup":
            advance_griess(node["griess"], "derive", "retry from MAP residue")
        elif phase == "ont" and (
            workspace_stale
            or kappa_stale
            or domain_stale
            or construction_stale
            or observation_stale
        ):
            invalidate_to_derive(node["griess"], "proof context changed")
        else:
            raise MapV2Error(
                f"retry requires Griess soup or stale ont; {name!r} is {phase}"
            )
        node["status"] = "repairing"
        node["certificate"] = None
        node["proof_context"] = None
        state["selected"] = name
        self._save(state)
        return {"retrying": name, "griess_phase": "derive", "next": "compute"}

    def revise(self, name: str, raw_facts: list[str]) -> dict[str, Any]:
        if self.construction_adapter is not None or self.observation_adapter is not None:
            raise MapV2Error(
                "raw revise is disabled when typed authority adapters are selected"
            )
        state = self._load()
        node = self._node(state, name)
        if node["status"] != "repairing":
            raise MapV2Error(f"only repairing nodes can be revised; {name!r} is {node['status']}")
        if node["griess"]["phase"] != "compute":
            raise MapV2Error(
                f"revise requires Griess compute; {name!r} is {node['griess']['phase']}"
            )
        facts = _normalize_facts(raw_facts)
        node.setdefault("revisions", []).append(
            {
                "revised_at": utc_now(),
                "facts": list(node.get("facts", [])),
                "construction": node.get("construction"),
                "observation": node.get("observation"),
            }
        )
        node["facts"] = facts
        node["construction"] = None
        node["observation"] = None
        node["status"] = "filled"
        node["certificate"] = None
        node["proof_context"] = None
        advance_griess(node["griess"], "build", "authored facts revised")
        state["selected"] = name
        self._save(state)
        return {
            "revised": name,
            "fact_count": len(facts),
            "revision_count": len(node["revisions"]),
            "griess_phase": "build",
            "next": "compile",
        }

    def revise_construction(
        self,
        name: str,
        payload: Mapping[str, Any],
        adapter: ConstructionAdapter | None = None,
    ) -> dict[str, Any]:
        """Replace a repairing node with a newly validated PSC construction."""
        state = self._load()
        node = self._node(state, name)
        if node["status"] != "repairing":
            raise MapV2Error(
                f"only repairing nodes can be revised; {name!r} is {node['status']}"
            )
        if node["griess"]["phase"] != "compute":
            raise MapV2Error(
                f"revise_construction requires Griess compute; {name!r} is "
                f"{node['griess']['phase']}"
            )
        selected_adapter = self._resolve_construction_adapter(adapter)
        if selected_adapter.target != state["target"]:
            raise MapV2Error(
                "construction adapter target mismatch: "
                f"expected {state['target']}, got {selected_adapter.target}"
            )
        lowered = validate_and_lower(selected_adapter, payload)
        node.setdefault("revisions", []).append(
            {
                "revised_at": utc_now(),
                "facts": list(node.get("facts", [])),
                "construction": node.get("construction"),
                "observation": node.get("observation"),
            }
        )
        node["facts"] = lowered.facts
        node["construction"] = lowered.metadata
        node["observation"] = None
        node["status"] = "filled"
        node["certificate"] = None
        node["proof_context"] = None
        advance_griess(
            node["griess"], "build", "typed PSC construction revised"
        )
        state["selected"] = name
        self._save(state)
        return {
            "revised": name,
            "fact_count": len(lowered.facts),
            "revision_count": len(node["revisions"]),
            "construction": self._construction_summary(lowered.metadata),
            "griess_phase": "build",
            "next": "compile",
        }

    def select(self, name: str) -> dict[str, Any]:
        state = self._load()
        self._node(state, name)
        state["selected"] = name
        self._save(state)
        return {"selected": name}

    def compile(
        self,
        name: str | None = None,
        compiler: TargetCompiler | None = None,
    ) -> dict[str, Any]:
        state = self._load()
        name = name or state.get("selected")
        if not name:
            raise MapV2Error("no node selected")
        node = self._node(state, name)
        if node["status"] != "filled":
            raise MapV2Error(f"node must be filled before compile; {name!r} is {node['status']}")
        if not node["griess"].get("kappa"):
            raise MapV2Error(f"cannot compile {name!r} without declared kappa")
        phase = node["griess"]["phase"]
        if phase not in {"build", "verify"}:
            raise MapV2Error(
                f"compile requires Griess build or verify; {name!r} is {phase}"
            )
        construction_rejection = self._construction_rejection(node)
        if construction_rejection:
            raise MapV2Error(
                f"compile rejected typed construction: {construction_rejection}"
            )
        observation_rejection = self._observation_rejection(node)
        if observation_rejection:
            raise MapV2Error(
                f"compile rejected typed observation: {observation_rejection}"
            )
        if phase == "build":
            advance_griess(node["griess"], "verify", "MAP verification started")
            self._save(state)
        workspace_sha256 = self._workspace_sha256(state)
        selected_compiler = self._resolve_compiler(compiler)
        packet = selected_compiler.compile(
            self.workspace_path,
            state["subject"],
            state["target"],
            kappa=node["griess"]["kappa"],
        )
        outcome = "ont" if packet["status"] == "compiled" else "soup"
        advance_griess(
            node["griess"], outcome, f"MAP target status {packet['status']}"
        )
        packet.update(self._packet_scope(state, name, workspace_sha256, node))
        packet["workspace"] = str(self.workspace_path)
        packet["griess_phase"] = outcome
        node["last_packet"] = compact_packet(packet)
        proof_context = {
            "domain_terms": list(packet.get("domain_terms", [])),
            "proof_terms": list(packet.get("outputs", [])),
        }
        if node.get("construction") is not None:
            proof_context["construction"] = node["construction"]
        if node.get("observation") is not None:
            proof_context["observation"] = node["observation"]
        proof_context.update(packet.get("proof_context", {}))
        node["proof_context"] = proof_context
        node["certificate"] = self._certificate(
            state, node, packet["status"], workspace_sha256, packet
        )
        self._save(state)
        return packet

    def combine(self, name: str, sources: list[str]) -> dict[str, Any]:
        state = self._load()
        name = require_node_name(name)
        if name in state["nodes"]:
            raise MapV2Error(f"node already exists: {name}")
        if len(sources) < 2:
            raise MapV2Error("combine requires at least two source nodes")
        rejected = self._combine_rejections(state, sources)
        if rejected:
            payload = {"combine_rejected": name, "reasons": rejected}
            raise MapV2Error(json.dumps(payload, sort_keys=True))
        return self._store_combined_pattern(state, name, sources)

    def promote(self, name: str) -> dict[str, Any]:
        state = self._load()
        node = self._node(state, name)
        if node["status"] != "combined":
            raise MapV2Error(f"only combined patterns can promote; {name!r} is {node['status']}")
        advance_griess(node["griess"], "implement", "pattern made meta-compilable")
        state["selected"] = name
        self._save(state)
        return {"promoted": name, "griess_phase": "implement", "next": "reify"}

    def reify(self, name: str) -> dict[str, Any]:
        state = self._load()
        node = self._node(state, name)
        if node["status"] != "combined":
            raise MapV2Error(f"only combined patterns can reify; {name!r} is {node['status']}")
        advance_griess(node["griess"], "derive", "SES+1 construction candidate")
        node["status"] = "open"
        node["sources"] = list(node.get("sources", []))
        node["certificate"] = None
        node["proof_context"] = None
        state["selected"] = name
        self._save(state)
        return {
            "reified": name,
            "griess_phase": "derive",
            "ses_depth": node["griess"]["ses_depth"],
            "next": "declare_kappa",
        }

    def queue(self) -> list[dict[str, str]]:
        return self._queue_from_state(self._load())

    def next(self) -> dict[str, Any]:
        state = self._load()
        queue = self._queue_from_state(state)
        if not queue:
            return {"next": None, "reason": "queue_empty"}
        name = queue[0]["name"]
        node = self._node(state, name)
        siblings = []
        if node.get("parent"):
            siblings = state["nodes"][node["parent"]].get("children", [])
        return {
            **queue[0],
            "parent": node.get("parent"),
            "siblings": siblings,
            "node": self._public_node(node),
        }

    def show(self, name: str | None = None) -> dict[str, Any]:
        state = self._load()
        if name:
            return self._public_node(self._node(state, name))
        return self.summary(state)

    def tree(self) -> dict[str, Any]:
        state = self._load()

        def build(name: str) -> dict[str, Any]:
            node = state["nodes"][name]
            return {
                "name": name,
                "status": node["status"],
                "griess_phase": node["griess"]["phase"],
                "children": [build(child) for child in node.get("children", [])],
            }

        return build(state["root"])

    def summary(self, state: dict[str, Any] | None = None) -> dict[str, Any]:
        state = state or self._load()
        return {
            "version": state["version"],
            "subject": state["subject"],
            "target": state["target"],
            "domain_id": state.get("domain_id"),
            "root": state["root"],
            "selected": state.get("selected"),
            "node_count": len(state["nodes"]),
            "queue": self._queue_from_state(state),
            "workspace": str(self.workspace_path),
        }

    def next_name(self, state: dict[str, Any] | None = None) -> str | None:
        queue = self._queue_from_state(state or self._load())
        return queue[0]["name"] if queue else None

    def _resolve_compiler(
        self, compiler: TargetCompiler | None
    ) -> TargetCompiler:
        selected = compiler or self.compiler
        if selected is None:
            raise MapV2Error(
                "MAP compute/compile requires a selected domain compiler"
            )
        return selected

    def _resolve_construction_adapter(
        self, adapter: ConstructionAdapter | None
    ) -> ConstructionAdapter:
        selected = adapter or self.construction_adapter
        if selected is None:
            raise MapV2Error(
                "typed construction fill requires a selected construction adapter"
            )
        return selected

    def _resolve_observation_adapter(
        self, adapter: ObservationAdapter | None
    ) -> ObservationAdapter:
        selected = adapter or self.observation_adapter
        if selected is None:
            raise MapV2Error(
                "typed observation attachment requires a selected observation adapter"
            )
        return selected

    @staticmethod
    def _construction_summary(metadata: dict[str, Any]) -> dict[str, Any]:
        return MapV2Lattice._artifact_summary(metadata)

    @staticmethod
    def _artifact_summary(metadata: dict[str, Any]) -> dict[str, Any]:
        return {
            key: metadata[key]
            for key in (
                "schema_id",
                "schema_sha256",
                "payload_sha256",
                "render_sha256",
                "lowering_id",
                "lowering_sha256",
                "facts_sha256",
            )
        }

    def _construction_rejection(self, node: dict[str, Any]) -> str | None:
        construction = node.get("construction")
        if construction is None:
            return None
        if self.construction_adapter is None:
            return "missing_current_construction_adapter"
        current = adapter_context(self.construction_adapter)
        if current["target"] != construction.get("target"):
            return "stale_construction_target"
        if current["schema_id"] != construction.get("schema_id"):
            return "stale_construction_schema_id"
        if current["schema_sha256"] != construction.get("schema_sha256"):
            return "stale_construction_schema"
        if current["lowering_id"] != construction.get("lowering_id"):
            return "stale_construction_lowering_id"
        if current["lowering_sha256"] != construction.get("lowering_sha256"):
            return "stale_construction_lowering"
        return None

    def _observation_rejection(self, node: dict[str, Any]) -> str | None:
        observation = node.get("observation")
        if observation is None:
            return None
        if self.observation_adapter is None:
            return "missing_current_observation_adapter"
        current = observation_adapter_context(self.observation_adapter)
        if current["target"] != observation.get("target"):
            return "stale_observation_target"
        if current["schema_id"] != observation.get("schema_id"):
            return "stale_observation_schema_id"
        if current["schema_sha256"] != observation.get("schema_sha256"):
            return "stale_observation_schema"
        if current["lowering_id"] != observation.get("lowering_id"):
            return "stale_observation_lowering_id"
        if current["lowering_sha256"] != observation.get("lowering_sha256"):
            return "stale_observation_lowering"
        return None
