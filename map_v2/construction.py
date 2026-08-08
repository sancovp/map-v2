"""Typed candidate-construction boundary between Pydantic Stack Core and MAP."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import inspect
import json
from pathlib import Path
import re
from typing import Any, Mapping, Protocol, runtime_checkable

from pydantic import ValidationError
from pydantic_stack_core import RenderablePiece

from .prologish import split_statements


CONSTRUCTION_SCHEMA = "map.typed_construction.v1"
OBSERVATION_SCHEMA = "map.typed_observation.v1"
ATOM_RE = re.compile(r"^[a-z][a-zA-Z0-9_]*$")
FACT_PREDICATE_RE = re.compile(r"^([a-z][a-zA-Z0-9_]*)\s*\(")
CONSTRUCTION_PREDICATE_PREFIX = "candidate_"
OBSERVATION_PREDICATE_PREFIX = "source_"


class MapConstructionError(ValueError):
    """A typed construction or its lowering boundary is invalid."""


@runtime_checkable
class ConstructionAdapter(Protocol):
    """Domain-owned PSC model and canonical candidate-fact lowering."""

    target: str
    schema_id: str
    lowering_id: str
    model_type: type[RenderablePiece]
    candidate_predicates: frozenset[str]

    def lower(self, construction: RenderablePiece) -> list[str]: ...


@runtime_checkable
class ObservationAdapter(Protocol):
    """Trusted domain-owned observation model and source-fact lowering."""

    target: str
    schema_id: str
    lowering_id: str
    model_type: type[RenderablePiece]
    observation_predicates: frozenset[str]

    def lower(self, observation: RenderablePiece) -> list[str]: ...


@dataclass(frozen=True)
class LoweredConstruction:
    """One validated PSC value plus its canonical MAP candidate facts."""

    facts: list[str]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class LoweredObservation:
    """One validated observation snapshot plus canonical MAP source facts."""

    facts: list[str]
    metadata: dict[str, Any]


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _jsonable_errors(errors: list) -> list:
    """Pydantic error dicts may carry raw exception objects in ctx (e.g. the
    ValueError a field_validator raised); coerce non-JSON leaves to str so the
    rejection message survives serialization instead of masking the residue
    with its own TypeError."""

    def scrub(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: scrub(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [scrub(v) for v in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

    return [scrub(e) for e in errors]


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _adapter_source_sha256(adapter: ConstructionAdapter | ObservationAdapter) -> str:
    adapter_type = type(adapter)
    source_path = inspect.getsourcefile(adapter_type)
    if source_path and Path(source_path).is_file():
        return hashlib.sha256(Path(source_path).read_bytes()).hexdigest()
    try:
        source = inspect.getsource(adapter_type)
    except (OSError, TypeError):
        source = f"{adapter_type.__module__}.{adapter_type.__qualname__}"
    return _sha256_text(source)


def adapter_context(adapter: ConstructionAdapter) -> dict[str, Any]:
    """Return the frozen identity of one domain construction adapter."""
    if not isinstance(adapter, ConstructionAdapter):
        raise MapConstructionError("construction adapter does not implement the MAP protocol")
    if not ATOM_RE.fullmatch(adapter.target):
        raise MapConstructionError(
            f"construction adapter target must be an unquoted Prolog atom: {adapter.target!r}"
        )
    if not adapter.schema_id or "\n" in adapter.schema_id:
        raise MapConstructionError("construction schema_id must be one non-empty line")
    if not adapter.lowering_id or "\n" in adapter.lowering_id:
        raise MapConstructionError("construction lowering_id must be one non-empty line")
    if not isinstance(adapter.model_type, type) or not issubclass(
        adapter.model_type, RenderablePiece
    ):
        raise MapConstructionError(
            "construction model_type must be a RenderablePiece subclass"
        )
    predicates = sorted(adapter.candidate_predicates)
    if not predicates:
        raise MapConstructionError("construction adapter requires candidate predicates")
    for predicate in predicates:
        if not ATOM_RE.fullmatch(predicate):
            raise MapConstructionError(
                f"construction predicate must be an unquoted Prolog atom: {predicate!r}"
            )
        if not predicate.startswith(CONSTRUCTION_PREDICATE_PREFIX):
            raise MapConstructionError(
                f"construction predicate {predicate!r} is not candidate-authorable; "
                f"expected prefix {CONSTRUCTION_PREDICATE_PREFIX!r}"
            )
    model_schema = adapter.model_type.model_json_schema()
    schema_sha256 = _sha256_text(_canonical_json(model_schema))
    source_sha256 = _adapter_source_sha256(adapter)
    lowering_payload = {
        "adapter": f"{type(adapter).__module__}.{type(adapter).__qualname__}",
        "lowering_id": adapter.lowering_id,
        "candidate_predicates": predicates,
        "source_sha256": source_sha256,
    }
    return {
        "target": adapter.target,
        "schema_id": adapter.schema_id,
        "schema_sha256": schema_sha256,
        "model_type": f"{adapter.model_type.__module__}.{adapter.model_type.__qualname__}",
        "lowering_id": adapter.lowering_id,
        "lowering_sha256": _sha256_text(_canonical_json(lowering_payload)),
        "candidate_predicates": predicates,
    }


def observation_adapter_context(adapter: ObservationAdapter) -> dict[str, Any]:
    """Return the frozen identity of one trusted observation adapter."""
    if not isinstance(adapter, ObservationAdapter):
        raise MapConstructionError("observation adapter does not implement the MAP protocol")
    if not ATOM_RE.fullmatch(adapter.target):
        raise MapConstructionError(
            f"observation adapter target must be an unquoted Prolog atom: {adapter.target!r}"
        )
    if not adapter.schema_id or "\n" in adapter.schema_id:
        raise MapConstructionError("observation schema_id must be one non-empty line")
    if not adapter.lowering_id or "\n" in adapter.lowering_id:
        raise MapConstructionError("observation lowering_id must be one non-empty line")
    if not isinstance(adapter.model_type, type) or not issubclass(
        adapter.model_type, RenderablePiece
    ):
        raise MapConstructionError(
            "observation model_type must be a RenderablePiece subclass"
        )
    predicates = sorted(adapter.observation_predicates)
    if not predicates:
        raise MapConstructionError("observation adapter requires observation predicates")
    for predicate in predicates:
        if not ATOM_RE.fullmatch(predicate):
            raise MapConstructionError(
                f"observation predicate must be an unquoted Prolog atom: {predicate!r}"
            )
        if not predicate.startswith(OBSERVATION_PREDICATE_PREFIX):
            raise MapConstructionError(
                f"observation predicate {predicate!r} is not source-authorable; "
                f"expected prefix {OBSERVATION_PREDICATE_PREFIX!r}"
            )
    model_schema = adapter.model_type.model_json_schema()
    schema_sha256 = _sha256_text(_canonical_json(model_schema))
    source_sha256 = _adapter_source_sha256(adapter)
    lowering_payload = {
        "adapter": f"{type(adapter).__module__}.{type(adapter).__qualname__}",
        "lowering_id": adapter.lowering_id,
        "observation_predicates": predicates,
        "source_sha256": source_sha256,
    }
    return {
        "target": adapter.target,
        "schema_id": adapter.schema_id,
        "schema_sha256": schema_sha256,
        "model_type": f"{adapter.model_type.__module__}.{adapter.model_type.__qualname__}",
        "lowering_id": adapter.lowering_id,
        "lowering_sha256": _sha256_text(_canonical_json(lowering_payload)),
        "observation_predicates": predicates,
    }


def _normalize_lowered_facts(
    raw_facts: list[str],
    allowed_predicates: frozenset[str],
    *,
    predicate_prefix: str,
    authority: str,
) -> list[str]:
    statements = split_statements("\n".join(raw_facts), source="<map-psc-lowering>")
    if not statements:
        raise MapConstructionError("typed construction lowered to no candidate facts")
    normalized: list[str] = []
    for statement in statements:
        normalized_statement = statement.strip()
        match = FACT_PREDICATE_RE.match(normalized_statement)
        if match is None:
            raise MapConstructionError(
                f"typed construction lowering emitted a malformed fact: {statement!r}"
            )
        predicate = match.group(1)
        if not predicate.startswith(predicate_prefix):
            raise MapConstructionError(
                f"typed {authority} lowering attempted reserved predicate: {predicate}"
            )
        if predicate not in allowed_predicates:
            raise MapConstructionError(
                f"typed construction lowering emitted undeclared predicate: {predicate}"
            )
        _require_ground_fact(normalized_statement, match.end() - 1)
        normalized.append(normalized_statement)
    return normalized


def _require_ground_fact(statement: str, opening_parenthesis: int) -> None:
    """Reject clauses, conjunctions, and variables outside quoted data."""
    depth = 0
    quote: str | None = None
    escaped = False
    index = opening_parenthesis
    while index < len(statement):
        char = statement[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            index += 1
            continue
        if statement.startswith((":-", "?-", "-->"), index):
            raise MapConstructionError(
                "typed construction lowering accepts ground facts, not rules or directives"
            )
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                break
            if depth == 0 and statement[index + 1 :].strip() != ".":
                raise MapConstructionError(
                    "typed construction lowering accepts one predicate fact per statement"
                )
        elif char == "." and depth != 0:
            raise MapConstructionError(
                "typed construction lowering emitted an unexpected term terminator"
            )
        elif char == "_" or char.isupper():
            previous = statement[index - 1] if index else ""
            if not (previous.isalnum() or previous == "_"):
                raise MapConstructionError(
                    "typed construction lowering accepts ground facts, not variables"
                )
        index += 1
    if quote is not None or depth != 0 or not statement.endswith("."):
        raise MapConstructionError(
            "typed construction lowering emitted an unbalanced or unterminated fact"
        )


def validate_and_lower(
    adapter: ConstructionAdapter, payload: Mapping[str, Any]
) -> LoweredConstruction:
    """Validate one PSC payload and lower it into candidate-only Prolog facts."""
    context = adapter_context(adapter)
    try:
        construction = adapter.model_type.model_validate(dict(payload))
    except ValidationError as exc:
        errors = _jsonable_errors(exc.errors(include_url=False))
        raise MapConstructionError(
            "typed_construction_validation_failed:"
            + _canonical_json({"schema_id": context["schema_id"], "errors": errors})
        ) from exc
    canonical_payload = construction.model_dump(
        mode="json", round_trip=True, serialize_as_any=True
    )
    try:
        rendered = construction.render()
    except Exception as exc:  # codenose ignore: domain renderer failure is residue
        raise MapConstructionError(f"typed_construction_render_failed:{exc}") from exc
    if not isinstance(rendered, str):
        raise MapConstructionError("typed construction render() must return str")
    raw_facts = adapter.lower(construction)
    if not isinstance(raw_facts, list) or not all(
        isinstance(fact, str) for fact in raw_facts
    ):
        raise MapConstructionError("construction lower() must return list[str]")
    facts = _normalize_lowered_facts(
        raw_facts,
        adapter.candidate_predicates,
        predicate_prefix=CONSTRUCTION_PREDICATE_PREFIX,
        authority="construction",
    )
    metadata = {
        "schema": CONSTRUCTION_SCHEMA,
        **context,
        "payload": canonical_payload,
        "payload_sha256": _sha256_text(_canonical_json(canonical_payload)),
        "rendered": rendered,
        "render_sha256": _sha256_text(rendered),
        "facts_sha256": _sha256_text(_canonical_json(facts)),
    }
    return LoweredConstruction(facts=facts, metadata=metadata)


def validate_and_lower_observation(
    adapter: ObservationAdapter, payload: Mapping[str, Any]
) -> LoweredObservation:
    """Validate one trusted snapshot and lower it into source-only Prolog facts."""
    context = observation_adapter_context(adapter)
    try:
        observation = adapter.model_type.model_validate(dict(payload))
    except ValidationError as exc:
        errors = _jsonable_errors(exc.errors(include_url=False))
        raise MapConstructionError(
            "typed_observation_validation_failed:"
            + _canonical_json({"schema_id": context["schema_id"], "errors": errors})
        ) from exc
    canonical_payload = observation.model_dump(
        mode="json", round_trip=True, serialize_as_any=True
    )
    try:
        rendered = observation.render()
    except Exception as exc:  # codenose ignore: observer renderer failure is residue
        raise MapConstructionError(f"typed_observation_render_failed:{exc}") from exc
    if not isinstance(rendered, str):
        raise MapConstructionError("typed observation render() must return str")
    raw_facts = adapter.lower(observation)
    if not isinstance(raw_facts, list) or not all(
        isinstance(fact, str) for fact in raw_facts
    ):
        raise MapConstructionError("observation lower() must return list[str]")
    facts = _normalize_lowered_facts(
        raw_facts,
        adapter.observation_predicates,
        predicate_prefix=OBSERVATION_PREDICATE_PREFIX,
        authority="observation",
    )
    metadata = {
        "schema": OBSERVATION_SCHEMA,
        **context,
        "payload": canonical_payload,
        "payload_sha256": _sha256_text(_canonical_json(canonical_payload)),
        "rendered": rendered,
        "render_sha256": _sha256_text(rendered),
        "facts_sha256": _sha256_text(_canonical_json(facts)),
    }
    return LoweredObservation(facts=facts, metadata=metadata)
