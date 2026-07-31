"""MAP's portable specialization of Crystal Ball's Griess phase algebra.

SOUP and ONT are MAP construction outcomes: VERIFY enters ONT only when the
selected domain compiler closes its declared kappa, otherwise it enters SOUP
with repair residue. They are not GAS states. Crystal Ball-specific geometry,
amplitudes, fuzzy grounding, scry, and SOMA validation remain outside MAP.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


GRIESS_PHASES = (
    "derive",
    "compute",
    "build",
    "verify",
    "ont",
    "soup",
    "pattern",
    "implement",
)

TRANSITIONS: dict[str, tuple[str, ...]] = {
    "derive": ("compute",),
    "compute": ("build",),
    "build": ("verify",),
    "verify": ("ont", "soup"),
    "ont": ("pattern",),
    "soup": ("derive",),
    "pattern": ("implement",),
    "implement": ("derive",),
}


class GriessTransitionError(ValueError):
    """A caller attempted an unlawful constructor transition."""


def new_griess_state(phase: str = "derive") -> dict[str, Any]:
    if phase not in GRIESS_PHASES:
        raise GriessTransitionError(f"unknown Griess phase: {phase}")
    return {
        "phase": phase,
        "kappa": None,
        "ses_depth": 0,
        "history": [f"registered at {phase}"],
    }


def declare_kappa(
    state: dict[str, Any], domain: str, invariants: dict[str, str]
) -> dict[str, Any]:
    domain = _one_line(domain, "kappa domain")
    if not invariants:
        raise GriessTransitionError("kappa requires at least one invariant")
    normalized: dict[str, str] = {}
    for name, description in invariants.items():
        normalized[_one_line(name, "invariant name")] = _one_line(
            description, "invariant description"
        )

    phase = state.get("phase")
    if phase != "derive" and state.get("kappa") is not None:
        raise GriessTransitionError(
            f"kappa can only change at derive; current phase is {phase}"
        )
    state["kappa"] = {"domain": domain, "invariants": normalized}
    state.setdefault("history", []).append(
        f"kappa declared: {domain} with {len(normalized)} invariants"
    )
    return state


def advance_griess(
    state: dict[str, Any], to_phase: str, reason: str = ""
) -> dict[str, Any]:
    current = state.get("phase")
    if current not in TRANSITIONS:
        raise GriessTransitionError(f"unknown current Griess phase: {current}")
    if to_phase not in TRANSITIONS[current]:
        valid = ", ".join(TRANSITIONS[current])
        raise GriessTransitionError(
            f"invalid Griess transition: {current} -> {to_phase}; valid: [{valid}]"
        )
    if current == "derive" and not state.get("kappa"):
        raise GriessTransitionError(
            "cannot leave derive without declaring kappa"
        )
    state["phase"] = to_phase
    if current == "implement" and to_phase == "derive":
        state["ses_depth"] = int(state.get("ses_depth", 0)) + 1
    entry = f"{current} -> {to_phase}"
    if reason:
        entry += f" ({reason})"
    state.setdefault("history", []).append(entry)
    return state


def kappa_sha256(state: dict[str, Any]) -> str | None:
    kappa = state.get("kappa")
    if not kappa:
        return None
    canonical = json.dumps(kappa, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def invalidate_to_derive(state: dict[str, Any], reason: str) -> dict[str, Any]:
    """Invalidate prior proof context without pretending it is a forward phase move."""
    current = state.get("phase")
    state["phase"] = "derive"
    state.setdefault("history", []).append(
        f"{current} invalidated -> derive ({_one_line(reason, 'invalidation reason')})"
    )
    return state


def migrate_legacy_griess(node: dict[str, Any]) -> dict[str, Any]:
    """Infer the least-surprising constructor phase for a v1 MAP node."""
    status = node.get("status")
    certificate = node.get("certificate") or {}
    if status == "combined":
        phase = "pattern"
    elif certificate.get("status") == "compiled":
        phase = "ont"
    elif certificate:
        phase = "soup"
    elif status == "filled":
        phase = "build"
    else:
        phase = "derive"
    state = new_griess_state(phase)
    state["history"].append("migrated from MAP v2 state version 1")
    return state


def _one_line(value: str, label: str) -> str:
    value = value.strip()
    if not value or "\n" in value or "\r" in value:
        raise GriessTransitionError(f"{label} must be one non-empty line")
    return value
