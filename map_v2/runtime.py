"""Independent SWI-Prolog compiler adapter for MAP domain packages."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

from .domain import PrologDomain, require_atom


REPORT_MODES = ("report", "frontier", "blocked", "admissible", "outputs")


def term_lines(report: str, prefixes: tuple[str, ...] | None = None) -> list[str]:
    lines = [line.strip() for line in report.splitlines() if line.strip()]
    if prefixes is None:
        return lines
    starts = tuple(f"{prefix}(" for prefix in prefixes)
    return [line for line in lines if line.startswith(starts)]


def status_from_report(report: str, subject: str, target: str) -> str:
    prefix = f"map_target_status({subject},{target},"
    for term in term_lines(report):
        if term.startswith(prefix) and term.endswith(")."):
            return term[len(prefix) : -2]
    return "unknown"


class MapRuntimeError(RuntimeError):
    """The selected MAP domain could not be evaluated."""


class PrologTargetCompiler:
    """Compile one subject against an independent MAP Prolog domain."""

    def __init__(
        self,
        domain: PrologDomain,
        *,
        swipl: str | None = None,
        timeout_s: float = 120.0,
    ) -> None:
        self.domain = domain
        self.swipl = swipl or shutil.which("swipl") or "swipl"
        self.timeout_s = timeout_s
        self.runtime_path = Path(__file__).resolve().parent / "prolog" / "runtime.pl"

    @property
    def targets(self) -> tuple[str, ...]:
        return self.domain.targets

    def domain_context(self, target: str) -> dict[str, Any]:
        if target not in self.targets:
            return {}
        return self.domain.context()

    def compile(
        self,
        workspace_path: Path,
        subject: str,
        target: str,
        kappa: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        subject = require_atom(subject, "MAP subject")
        target = require_atom(target, "MAP target")
        if target not in self.targets:
            raise MapRuntimeError(
                f"target {target!r} is not provided by domain {self.domain.id!r}"
            )
        proof_workspace, kappa_terms = self._proof_workspace(
            workspace_path, subject, kappa
        )
        try:
            reports = {
                mode: self._run(proof_workspace, subject, target, mode)
                for mode in REPORT_MODES
            }
        finally:
            if proof_workspace != workspace_path:
                proof_workspace.unlink(missing_ok=True)
        context = self.domain.context()
        compile_terms = term_lines(reports["report"])
        domain_terms = [
            term for term in compile_terms if not term.startswith("map_target_")
        ]
        return {
            "status": status_from_report(reports["report"], subject, target),
            "frontier": term_lines(reports["frontier"]),
            "blocked": term_lines(reports["blocked"]),
            "admissible": term_lines(reports["admissible"]),
            "outputs": term_lines(reports["outputs"]),
            "domain_terms": domain_terms,
            "domain_id": context["domain_id"],
            "domain_sha256": context["domain_sha256"],
            "kappa_terms": kappa_terms,
            "reports": reports,
        }

    def _run(
        self, workspace_path: Path, subject: str, target: str, mode: str
    ) -> str:
        command = [
            self.swipl,
            "-q",
            "-s",
            str(self.runtime_path),
            "--",
            str(self.domain.entrypoint),
            str(workspace_path),
            subject,
            target,
            mode,
        ]
        try:
            result = subprocess.run(
                command,
                text=True,
                capture_output=True,
                timeout=self.timeout_s,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise MapRuntimeError(f"MAP Prolog runtime failed: {exc}") from exc
        if result.returncode != 0:
            residue = result.stderr.strip() or result.stdout.strip()
            raise MapRuntimeError(f"MAP Prolog domain failed: {residue}")
        return result.stdout

    @staticmethod
    def _proof_workspace(
        workspace_path: Path,
        subject: str,
        kappa: dict[str, Any] | None,
    ) -> tuple[Path, list[str]]:
        if not kappa:
            raise MapRuntimeError("MAP compile requires declared kappa")
        domain = require_atom(str(kappa.get("domain", "")), "kappa domain")
        invariants = kappa.get("invariants")
        if not isinstance(invariants, dict) or not invariants:
            raise MapRuntimeError("MAP kappa requires invariant names")
        terms = [f"map_kappa_domain({subject},{domain})."]
        for name in sorted(invariants):
            invariant = require_atom(str(name), "kappa invariant")
            terms.append(f"map_kappa_invariant({subject},{invariant}).")
        source = workspace_path.read_text(encoding="utf-8").rstrip()
        rendered = source + "\n\n% MAP kappa proof overlay.\n" + "\n".join(terms) + "\n"
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".pl",
            prefix="map_v2_proof_",
            delete=False,
        ) as handle:
            handle.write(rendered)
            return Path(handle.name), terms
