# Adversarially verify the PSC to MAP typed-construction boundary

PromptType: AdversarialPrompt

SituationClass: Neurosymbolic boundary falsification after a new typed input seam

ConcreteContext: MAP v2 now accepts application-owned Pydantic Stack Core
`RenderablePiece` models through `map_v2/construction.py`, lowers them to
candidate-only Prolog facts, and binds construction identity into proof
certificates. The recursive witness is the typed-chain fixture.

AgentOrientation: Assume the feature is unsound until repository evidence
shows that neither the LLM nor the lowering adapter can smuggle a proof result,
that PSC subtype payloads survive persistence, and that MAP rather than
Pydantic establishes relational closure.

HardQuestions:

- Can malformed nested evidence reach a Prolog workspace?
- Can a lowerer author a derived predicate, rule, or directive?
- Can a locally valid PSC value receive ONT without satisfying the recursive
  domain obligation?
- Does a changed schema or lowering leave an old certificate exportable?
- Does the installed wheel retain the dependency and CLI entrypoint needed for
  typed construction?
- Did any consumer ontology or GAS/DD dependency leak into MAP core?

MeasurableOutcome: Focused construction tests and the complete MAP v2 suite
pass; a wheel builds; an installed-wheel smoke check imports PSC integration
and exposes `fill-construction`; dependency-boundary searches reveal no GAS or
DD imports; docs state the PSC/MAP split without claiming semantic proof from
Pydantic validation.

ReplayInstructions:

1. Run `python3 -m unittest tests.test_map_v2_construction -v`.
2. Read the recursive fixture and confirm candidate facts contain no derived
   reachability or proof facts.
3. Run the complete `test_map_v2*.py` suite.
4. Build a wheel and inspect its metadata for `pydantic-stack-core`.
5. From outside the source checkout, install the wheel into an isolated target
   and verify `map_v2`, `map_v2.construction`, and CLI help.
6. Search MAP Python source for GAS or Dharma Detectives imports.
7. Inspect git diff and ensure all behavior changes are covered by focused
   assertions and architecture documentation.

ShapeInvariant: PSC admits typed candidate constructions; application lowering
assigns their explicit candidate interpretation; MAP alone derives recursive
domain consequences and issues or refuses an ONT certificate.

AllowedVariation: Consumer models, candidate predicates, domain obligations,
and Prolog derivations may vary while the generic adapter and certificate
boundary remain stable.

ForbiddenDrift: Treating successful Pydantic validation as semantic proof;
allowing adapter-authored derived facts; using generic `MetaStack` serialization
that erases subtype fields; hard-coding the fixture domain in MAP core; or
reporting success from source-tree imports when the built package is broken.

VerificationGate: Every command in ReplayInstructions succeeds and evidence
shows the recursive ONT result depends on Prolog-derived reachability that is
absent from authored workspace facts.

PersistenceTarget: Keep enduring boundary rules in `.agents/rules/start-here.md`
and user-facing architecture in `README.md` plus
`map_v2/docs/architecture.md`.

PromotionSignal: Promote this shape into a `sic-*` skill after a second MAP
consumer uses a distinct PSC model and the same candidate-only/certificate
boundary without MAP-core specialization.
