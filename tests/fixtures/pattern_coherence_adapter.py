"""Consumer-owned PSC models for the first code-pattern coherence proof."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_stack_core import RenderablePiece


Atom = Annotated[str, Field(pattern=r"^[a-z][a-zA-Z0-9_]*$")]
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
SemVer = Annotated[str, Field(pattern=r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")]


class ExactPatternRef(RenderablePiece):
    pattern_id: Literal["categorical_ring"]
    version: SemVer
    semantic_sha256: Sha256

    def render(self) -> str:
        return f"{self.pattern_id}@{self.version}:{self.semantic_sha256}"


class CategoricalRingProposal(RenderablePiece):
    kind: Literal["categorical_ring_proposal"]
    subject: Atom
    proposal_id: Atom
    pattern: ExactPatternRef
    ring_candidates: list[Atom] = Field(min_length=1)

    @field_validator("ring_candidates")
    @classmethod
    def unique_candidates(cls, candidates: list[str]) -> list[str]:
        if len(candidates) != len(set(candidates)):
            raise ValueError("ring candidates must be unique")
        return candidates

    def render(self) -> str:
        candidates = ",".join(self.ring_candidates)
        return f"{self.proposal_id}:{self.pattern.render()}[{candidates}]"


class CategoricalRingConstructionAdapter:
    target = "pattern_occurrence"
    schema_id = "map.fixture.categorical_ring_proposal.v1"
    lowering_id = "map.fixture.categorical_ring_proposal.lowering.v1"
    model_type = CategoricalRingProposal
    candidate_predicates = frozenset(
        {
            "candidate_pattern_ref",
            "candidate_occurrence_proposal",
            "candidate_role_binding",
        }
    )

    def lower(self, construction: RenderablePiece) -> list[str]:
        if not isinstance(construction, CategoricalRingProposal):
            raise TypeError(
                "CategoricalRingConstructionAdapter requires CategoricalRingProposal"
            )
        pattern = construction.pattern
        facts = [
            "candidate_pattern_ref("
            f"{construction.subject},{pattern.pattern_id},'{pattern.version}',"
            f"'{pattern.semantic_sha256}'"
            ").",
            "candidate_occurrence_proposal("
            f"{construction.subject},{construction.proposal_id},{pattern.pattern_id}"
            ").",
        ]
        facts.extend(
            "candidate_role_binding("
            f"{construction.subject},{construction.proposal_id},ring_class,{entity}"
            ")."
            for entity in construction.ring_candidates
        )
        return facts


class CapabilityAccess(RenderablePiece):
    capability: Atom
    line: int = Field(ge=1)
    evidence_id: Atom

    def render(self) -> str:
        return f"{self.capability}@{self.line}:{self.evidence_id}"


class RingClassObservation(RenderablePiece):
    entity_id: Atom
    declared_capabilities: list[Atom]
    accesses: list[CapabilityAccess]
    direct_access_coverage: Literal["complete", "partial"]
    kind_evidence_id: Atom

    @field_validator("declared_capabilities")
    @classmethod
    def unique_declarations(cls, declarations: list[str]) -> list[str]:
        if len(declarations) != len(set(declarations)):
            raise ValueError("declared capabilities must be unique")
        return declarations

    def render(self) -> str:
        declarations = ",".join(self.declared_capabilities)
        accesses = ",".join(access.render() for access in self.accesses)
        return (
            f"{self.entity_id}[declared={declarations};accesses={accesses};"
            f"coverage={self.direct_access_coverage}]"
        )


class RingObservationSnapshot(RenderablePiece):
    kind: Literal["categorical_ring_observation"]
    subject: Atom
    snapshot_id: Atom
    extractor_id: Atom
    extractor_implementation_sha256: Sha256
    extractor_configuration_sha256: Sha256
    entities: list[RingClassObservation] = Field(min_length=1)

    @field_validator("entities")
    @classmethod
    def unique_entities(
        cls, entities: list[RingClassObservation]
    ) -> list[RingClassObservation]:
        ids = [entity.entity_id for entity in entities]
        if len(ids) != len(set(ids)):
            raise ValueError("observed entity ids must be unique")
        return entities

    def render(self) -> str:
        body = "\n".join(entity.render() for entity in self.entities)
        return f"snapshot:{self.snapshot_id}:{self.extractor_id}\n{body}"


class CategoricalRingObservationAdapter:
    target = "pattern_occurrence"
    schema_id = "map.fixture.categorical_ring_observation.v1"
    lowering_id = "map.fixture.categorical_ring_observation.lowering.v1"
    model_type = RingObservationSnapshot
    observation_predicates = frozenset(
        {
            "source_snapshot",
            "source_entity_kind",
            "source_declared_capability",
            "source_accessed_capability",
            "source_coverage",
        }
    )

    def lower(self, observation: RenderablePiece) -> list[str]:
        if not isinstance(observation, RingObservationSnapshot):
            raise TypeError(
                "CategoricalRingObservationAdapter requires RingObservationSnapshot"
            )
        facts = [
            "source_snapshot("
            f"{observation.subject},{observation.snapshot_id},{observation.extractor_id},"
            f"'{observation.extractor_implementation_sha256}',"
            f"'{observation.extractor_configuration_sha256}'"
            ")."
        ]
        for entity in observation.entities:
            facts.append(
                "source_entity_kind("
                f"{observation.subject},{observation.snapshot_id},{entity.entity_id},"
                f"ring_class,{entity.kind_evidence_id}"
                ")."
            )
            facts.append(
                "source_coverage("
                f"{observation.subject},{observation.snapshot_id},"
                f"direct_self_attribute,{entity.entity_id},"
                f"{entity.direct_access_coverage}"
                ")."
            )
            facts.extend(
                "source_declared_capability("
                f"{observation.subject},{observation.snapshot_id},{entity.entity_id},"
                f"{capability}"
                ")."
                for capability in entity.declared_capabilities
            )
            facts.extend(
                "source_accessed_capability("
                f"{observation.subject},{observation.snapshot_id},{entity.entity_id},"
                f"{access.capability},{access.line},{access.evidence_id}"
                ")."
                for access in entity.accesses
            )
        return facts
