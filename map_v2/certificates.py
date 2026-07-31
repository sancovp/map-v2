"""Domain-neutral portable MAP node certificates."""

from __future__ import annotations

import hashlib
import json
from typing import Any


CERTIFICATE_SCHEMA = "map.node_certificate.v1"


def artifact_sha256(payload: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "envelope_sha256"}
    canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_certificate_envelope(
    certificate: dict[str, Any],
    kappa: dict[str, Any],
    proof_context: dict[str, list[str]],
) -> dict[str, Any]:
    payload = {
        "schema": CERTIFICATE_SCHEMA,
        "subject": certificate.get("subject"),
        "target": certificate.get("target"),
        "certificate": certificate,
        "kappa": kappa,
        "proof_context": proof_context,
    }
    payload["envelope_sha256"] = artifact_sha256(payload)
    return payload
