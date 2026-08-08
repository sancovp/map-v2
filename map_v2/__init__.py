"""Public facade for the independent MAP v2 lattice shell."""

from .cli import main
from .construction import (
    ConstructionAdapter,
    LoweredConstruction,
    LoweredObservation,
    MapConstructionError,
    ObservationAdapter,
    adapter_context,
    observation_adapter_context,
    validate_and_lower,
    validate_and_lower_observation,
)
from .domain import MapDomainError, PrologDomain, load_domain_manifest
from .griess import GriessTransitionError
from .lattice import MapV2Error, MapV2Lattice, TargetCompiler
from .runtime import MapRuntimeError, PrologTargetCompiler

__all__ = [
    "GriessTransitionError",
    "ConstructionAdapter",
    "LoweredConstruction",
    "LoweredObservation",
    "MapConstructionError",
    "MapDomainError",
    "MapRuntimeError",
    "MapV2Error",
    "MapV2Lattice",
    "ObservationAdapter",
    "PrologDomain",
    "PrologTargetCompiler",
    "TargetCompiler",
    "adapter_context",
    "observation_adapter_context",
    "load_domain_manifest",
    "main",
    "validate_and_lower",
    "validate_and_lower_observation",
]


if __name__ == "__main__":
    raise SystemExit(main())
