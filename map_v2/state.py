"""Domain-neutral persistence and queue support for the MAP v2 lattice."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from .certificates import build_certificate_envelope
from .griess import kappa_sha256, migrate_legacy_griess, new_griess_state


STATE_VERSION = 3


class MapV2Error(ValueError):
    """A user-correctable MAP v2 command or state error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def require_node_name(value: str) -> str:
    value = value.strip()
    if not value or "\n" in value or "\r" in value:
        raise MapV2Error("node name must be one non-empty line")
    return value


class MapV2StateMixin:
    """State mechanics kept separate from the LLM-facing lattice operations."""

    def _add_children(
        self, state: dict[str, Any], name: str, parts: list[str]
    ) -> list[str]:
        children: list[str] = []
        for raw_part in parts:
            part = require_node_name(raw_part)
            child = part if "." in part else f"{name}.{part}"
            if child in state["nodes"]:
                raise MapV2Error(f"node already exists: {child}")
            state["nodes"][child] = self._new_node(child, parent=name)
            children.append(child)
        return children

    def guide(self) -> dict[str, Any]:
        state = self._load()
        if self.guide_builder is not None:
            return self.guide_builder(
                self.state_dir,
                state,
                self._queue_from_state(state),
            )
        return {
            "schema": "map.cognition_guide.v1",
            "subject": state["subject"],
            "target": state["target"],
            "next": self.next(),
        }

    def export_certificate(self, name: str | None = None) -> dict[str, Any]:
        state = self._load()
        name = name or state.get("selected")
        if not name:
            raise MapV2Error("no node selected")
        node = self._node(state, name)
        certificate = node.get("certificate")
        reason = self._source_rejection(
            node,
            certificate,
            self._workspace_sha256(state),
            self._current_domain_sha256(state),
        )
        if reason:
            raise MapV2Error(f"certificate_export_rejected:{reason}")
        proof_context = node.get("proof_context")
        if not isinstance(proof_context, dict):
            raise MapV2Error("certificate_export_rejected:missing_proof_context")
        builder = self.certificate_builder or build_certificate_envelope
        return builder(
            certificate,
            node["griess"]["kappa"],
            proof_context,
        )

    def _combine_rejections(
        self, state: dict[str, Any], sources: list[str]
    ) -> list[dict[str, str]]:
        workspace_sha256 = self._workspace_sha256(state)
        domain_sha256 = self._current_domain_sha256(state)
        rejected: list[dict[str, str]] = []
        source_kappas: set[str] = set()
        for source in sources:
            node = self._node(state, source)
            certificate = node.get("certificate")
            reason = self._source_rejection(
                node, certificate, workspace_sha256, domain_sha256
            )
            if reason:
                rejected.append({"node": source, "reason": reason})
            elif certificate.get("kappa_sha256"):
                source_kappas.add(certificate["kappa_sha256"])
        if len(source_kappas) > 1:
            rejected.append({"node": "*", "reason": "incompatible_kappa"})
        return rejected

    @staticmethod
    def _source_rejection(
        node: dict[str, Any],
        certificate: dict[str, Any] | None,
        workspace_sha256: str,
        domain_sha256: str | None,
    ) -> str | None:
        if not certificate:
            return "missing_compile_certificate"
        if certificate.get("status") != "compiled":
            return f"target_status_{certificate.get('status', 'unknown')}"
        if certificate.get("workspace_sha256") != workspace_sha256:
            return "stale_workspace_certificate"
        if certificate.get("kappa_sha256") != kappa_sha256(node["griess"]):
            return "stale_kappa_certificate"
        if (
            domain_sha256 is not None
            and certificate.get("domain_sha256") != domain_sha256
        ):
            return "stale_domain_certificate"
        if node["griess"]["phase"] != "ont":
            return "source_not_ont"
        return None

    def _store_combined_pattern(
        self, state: dict[str, Any], name: str, sources: list[str]
    ) -> dict[str, Any]:
        state["nodes"][name] = {
            **self._new_node(name, parent=state["root"]),
            "status": "combined",
            "sources": list(sources),
        }
        node = state["nodes"][name]
        node["griess"] = new_griess_state("pattern")
        node["griess"]["history"].append(
            f"pattern combined from {', '.join(sources)}"
        )
        root = state["nodes"][state["root"]]
        root["children"].append(name)
        if root["status"] == "open":
            root["status"] = "expanded"
        state["selected"] = name
        self._save(state)
        return {
            "combined": name,
            "sources": list(sources),
            "status": "pattern_unproven",
            "griess_phase": "pattern",
            "next": name,
        }

    def _queue_from_state(self, state: dict[str, Any]) -> list[dict[str, str]]:
        workspace_sha256 = self._workspace_sha256(state)
        domain_sha256 = self._current_domain_sha256(state)
        result: list[dict[str, str]] = []
        for name, node in state["nodes"].items():
            reason = self._queue_reason(node, workspace_sha256, domain_sha256)
            if reason:
                result.append({"name": name, "reason": reason})
        return result

    @staticmethod
    def _queue_reason(
        node: dict[str, Any],
        workspace_sha256: str,
        domain_sha256: str | None,
    ) -> str | None:
        phase = node["griess"]["phase"]
        if node["status"] == "expanded" and phase == "derive":
            return None
        if phase == "derive":
            return "declare_kappa" if not node["griess"].get("kappa") else "compute_constraints"
        if phase == "compute":
            return "revise" if node["status"] == "repairing" else "fill"
        phase_reasons = {
            "pattern": "promote_pattern",
            "implement": "reify_pattern",
            "soup": "retry_from_compiler_residue",
            "verify": "retry_verify",
        }
        if phase in phase_reasons:
            return phase_reasons[phase]
        if phase != "ont":
            return "compile" if phase == "build" else None
        certificate = node.get("certificate")
        if not certificate:
            return "compile"
        if certificate.get("workspace_sha256") != workspace_sha256:
            return "reopen_after_workspace_change"
        if certificate.get("kappa_sha256") != kappa_sha256(node["griess"]):
            return "reopen_after_kappa_change"
        if (
            domain_sha256 is not None
            and certificate.get("domain_sha256") != domain_sha256
        ):
            return "reopen_after_domain_change"
        if certificate.get("status") != "compiled":
            return "repair_from_compiler_residue"
        return None

    @staticmethod
    def _packet_scope(
        state: dict[str, Any], name: str, workspace_sha256: str, node: dict[str, Any]
    ) -> dict[str, str | None]:
        return {
            "node": name,
            "subject": state["subject"],
            "target": state["target"],
            "workspace_sha256": workspace_sha256,
            "kappa_sha256": kappa_sha256(node["griess"]),
            "kappa_binding": "domain_obligations",
        }

    def _certificate(
        self,
        state: dict[str, Any],
        node: dict[str, Any],
        status: str,
        workspace_sha256: str,
        packet: dict[str, Any],
    ) -> dict[str, str | None]:
        certificate_scope = self._packet_scope(
            state, node["name"], workspace_sha256, node
        )
        certificate_scope.pop("node")
        certificate = {
            **certificate_scope,
            "status": status,
            "griess_outcome": node["griess"]["phase"],
            "compiled_at": utc_now(),
        }
        for field in (
            "domain_id",
            "domain_version",
            "domain_semantic_sha256",
            "domain_sha256",
        ):
            if packet.get(field) is not None:
                certificate[field] = packet[field]
        for field, value in packet.get("certificate_fields", {}).items():
            if value is not None:
                certificate[field] = value
        return certificate

    def _current_domain_sha256(self, state: dict[str, Any]) -> str | None:
        compiler = self.compiler
        if compiler is None or not hasattr(compiler, "domain_context"):
            return None
        context = compiler.domain_context(state["target"])
        return context.get("domain_sha256")

    @staticmethod
    def _new_node(name: str, parent: str | None) -> dict[str, Any]:
        return {
            "name": name,
            "parent": parent,
            "children": [],
            "sources": [],
            "facts": [],
            "status": "open",
            "certificate": None,
            "proof_context": None,
            "last_packet": None,
            "griess": new_griess_state(),
            "revisions": [],
            "created_at": utc_now(),
        }

    @staticmethod
    def _public_node(node: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in node.items() if key != "created_at"}

    @staticmethod
    def _node(state: dict[str, Any], name: str) -> dict[str, Any]:
        try:
            return state["nodes"][name]
        except KeyError as exc:
            raise MapV2Error(f"unknown node: {name}") from exc

    def _workspace_text(self, state: dict[str, Any]) -> str:
        lines = ["% Generated by MAP v2. Authored facts remain the source of truth."]
        lines.extend(
            [f"map_subject({state['target']},{state['subject']}).", ""]
        )
        for name, node in state["nodes"].items():
            if not node.get("facts"):
                continue
            safe_name = name.replace("\n", " ").replace("\r", " ")
            lines.append(f"% map_v2_node: {safe_name}")
            lines.extend(node["facts"])
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def _workspace_sha256(self, state: dict[str, Any]) -> str:
        return hashlib.sha256(self._workspace_text(state).encode("utf-8")).hexdigest()

    def _load(self) -> dict[str, Any]:
        if not self.state_path.exists():
            raise MapV2Error(f"no lattice at {self.state_dir}; run 'new' first")
        state = json.loads(self.state_path.read_text(encoding="utf-8"))
        if state.get("version") == 1:
            for node in state.get("nodes", {}).values():
                node["griess"] = migrate_legacy_griess(node)
                node.setdefault("revisions", [])
                node.setdefault("proof_context", None)
                node.setdefault("last_packet", None)
            state["version"] = 2
        if state.get("version") == 2:
            state["subject"] = state.pop("story")
            state["version"] = STATE_VERSION
            self._save(state)
        if state.get("version") != STATE_VERSION:
            raise MapV2Error(f"unsupported MAP v2 state version: {state.get('version')}")
        return state

    def _save(self, state: dict[str, Any]) -> None:
        state["updated_at"] = utc_now()
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        self.workspace_path.write_text(self._workspace_text(state), encoding="utf-8")
