"""Domain-neutral PSC construction fixture for MAP relational proof tests."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_stack_core import RenderablePiece


Atom = Annotated[str, Field(pattern=r"^[a-z][a-zA-Z0-9_]*$")]


class WitnessHow(RenderablePiece):
    kind: Literal["human_witness"]
    source: Atom

    def render(self) -> str:
        return f"witness:{self.source}"


class ChainStep(RenderablePiece):
    kind: Literal["step"]
    id: Atom
    source: Atom
    target: Atom
    how: WitnessHow

    def render(self) -> str:
        return f"{self.id}:{self.source}->{self.target}[{self.how.render()}]"


class ChainConstruction(RenderablePiece):
    kind: Literal["typed_chain"]
    subject: Atom
    start: Atom
    goal: Atom
    steps: list[ChainStep] = Field(min_length=1)

    @field_validator("steps")
    @classmethod
    def unique_step_ids(cls, steps: list[ChainStep]) -> list[ChainStep]:
        ids = [step.id for step in steps]
        if len(ids) != len(set(ids)):
            raise ValueError("step ids must be unique")
        return steps

    @model_validator(mode="after")
    def no_self_edges(self) -> "ChainConstruction":
        if any(step.source == step.target for step in self.steps):
            raise ValueError("chain steps cannot be self edges")
        return self

    def render(self) -> str:
        rendered = "\n".join(step.render() for step in self.steps)
        return f"chain:{self.subject}:{self.start}->{self.goal}\n{rendered}"


class TypedChainAdapter:
    target = "typed_chain"
    schema_id = "map.fixture.typed_chain.v1"
    lowering_id = "map.fixture.typed_chain.lowering.v1"
    model_type = ChainConstruction
    candidate_predicates = frozenset(
        {"candidate_goal", "candidate_step", "source_witness"}
    )

    def lower(self, construction: RenderablePiece) -> list[str]:
        if not isinstance(construction, ChainConstruction):
            raise TypeError("TypedChainAdapter requires ChainConstruction")
        facts = [
            "candidate_goal("
            f"{construction.subject},{construction.start},{construction.goal}"
            ")."
        ]
        for step in construction.steps:
            facts.extend(
                (
                    "candidate_step("
                    f"{construction.subject},{step.id},{step.source},{step.target}"
                    ").",
                    "source_witness("
                    f"{construction.subject},{step.id},{step.how.source}"
                    ").",
                )
            )
        return facts


class ChangedTypedChainAdapter(TypedChainAdapter):
    lowering_id = "map.fixture.typed_chain.lowering.v2"


class ForgedDerivedAdapter(TypedChainAdapter):
    candidate_predicates = frozenset({"derived_reachable"})

    def lower(self, construction: RenderablePiece) -> list[str]:
        return ["derived_reachable(chain_probe,alpha,omega)."]


class VariableCandidateAdapter(TypedChainAdapter):
    def lower(self, construction: RenderablePiece) -> list[str]:
        return ["candidate_goal(chain_probe,Start,omega)."]


class ConjoinedCandidateAdapter(TypedChainAdapter):
    def lower(self, construction: RenderablePiece) -> list[str]:
        return [
            "candidate_goal(chain_probe,alpha,omega),"
            "derived_reachable(chain_probe,alpha,omega)."
        ]
