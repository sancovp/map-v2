"""Domain descriptors for MAP's independent Prolog runtime."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any


DOMAIN_SCHEMA = "map.domain.v1"
ATOM_RE = re.compile(r"^[a-z][a-zA-Z0-9_]*$")


class MapDomainError(ValueError):
    """A MAP domain descriptor is malformed or incomplete."""


def require_atom(value: str, label: str) -> str:
    if not ATOM_RE.fullmatch(value):
        raise MapDomainError(f"{label} must be an unquoted Prolog atom: {value!r}")
    return value


@dataclass(frozen=True)
class PrologDomain:
    """One independently loadable Prolog theory implementing MAP's protocol."""

    id: str
    entrypoint: Path
    targets: tuple[str, ...]
    sources: tuple[Path, ...]

    def __post_init__(self) -> None:
        require_atom(self.id, "domain id")
        if not self.targets:
            raise MapDomainError("domain requires at least one target")
        for target in self.targets:
            require_atom(target, "domain target")
        if not self.entrypoint.is_file():
            raise MapDomainError(f"domain entrypoint does not exist: {self.entrypoint}")
        for source in self.sources:
            if not source.is_file():
                raise MapDomainError(f"domain source does not exist: {source}")

    @property
    def sha256(self) -> str:
        digest = hashlib.sha256()
        for path in self.sources:
            digest.update(path.name.encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
        return digest.hexdigest()

    def context(self) -> dict[str, Any]:
        return {
            "domain_id": self.id,
            "domain_sha256": self.sha256,
            "domain_sources": [str(path) for path in self.sources],
            "targets": list(self.targets),
        }


def load_domain_manifest(path: str | Path) -> PrologDomain:
    """Load a portable MAP domain manifest without importing domain Python."""
    manifest_path = Path(path).expanduser().resolve()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload.get("schema") != DOMAIN_SCHEMA:
        raise MapDomainError("unsupported MAP domain manifest schema")
    root = manifest_path.parent
    entrypoint = root / payload["entrypoint"]
    sources = tuple(root / source for source in payload.get("sources", []))
    if entrypoint not in sources:
        sources = (entrypoint, *sources)
    return PrologDomain(
        id=str(payload["id"]),
        entrypoint=entrypoint.resolve(),
        targets=tuple(str(target) for target in payload["targets"]),
        sources=tuple(source.resolve() for source in sources),
    )
