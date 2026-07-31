"""Public facade for the independent MAP v2 lattice shell."""

from .cli import main
from .domain import MapDomainError, PrologDomain, load_domain_manifest
from .griess import GriessTransitionError
from .lattice import MapV2Error, MapV2Lattice, TargetCompiler
from .runtime import MapRuntimeError, PrologTargetCompiler

__all__ = [
    "GriessTransitionError",
    "MapDomainError",
    "MapRuntimeError",
    "MapV2Error",
    "MapV2Lattice",
    "PrologDomain",
    "PrologTargetCompiler",
    "TargetCompiler",
    "load_domain_manifest",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
