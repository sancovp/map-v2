"""Public facade for the independent MAP v2 lattice shell."""

from .cli import main
from .construction import (
    ConstructionAdapter,
    LoweredConstruction,
    MapConstructionError,
    adapter_context,
    validate_and_lower,
)
from .domain import MapDomainError, PrologDomain, load_domain_manifest
from .griess import GriessTransitionError
from .lattice import MapV2Error, MapV2Lattice, TargetCompiler
from .runtime import MapRuntimeError, PrologTargetCompiler

__all__ = [
    "GriessTransitionError",
    "ConstructionAdapter",
    "LoweredConstruction",
    "MapConstructionError",
    "MapDomainError",
    "MapRuntimeError",
    "MapV2Error",
    "MapV2Lattice",
    "PrologDomain",
    "PrologTargetCompiler",
    "TargetCompiler",
    "adapter_context",
    "load_domain_manifest",
    "main",
    "validate_and_lower",
]


if __name__ == "__main__":
    raise SystemExit(main())
