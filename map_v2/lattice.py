from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Callable, Protocol

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
    [dict[str, Any], dict[str, Any], dict[str, list[str]]], dict[str, Any]
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
        guide_builder: GuideBuilder | None = None,
        certificate_builder: CertificateBuilder | None = None,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.state_path = self.state_dir / "state.json"
        self.workspace_path = self.state_dir / "workspace.pl"
        self.compiler = compiler
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
        if phase == "soup":
            advance_griess(node["griess"], "derive", "retry from MAP residue")
        elif phase == "ont" and (workspace_stale or kappa_stale or domain_stale):
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
            }
        )
        node["facts"] = facts
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
