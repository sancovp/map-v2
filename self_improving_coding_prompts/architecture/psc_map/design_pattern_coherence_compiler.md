# Design the Pattern Coherence Compiler

PromptType: WorkPrompt

SituationClass: Cross-system neurosymbolic architecture design.

ConcreteContext: MAP v2 needs a domain-neutral consumer design that can turn CodeNose and LFPOOP code observations into PSC-authored pattern proposals and MAP-verified recognition or rejection without importing code-domain semantics into MAP core.

AgentOrientation: Treat sensors, candidate authors, proof engines, and certificate consumers as distinct authorities. Design from the smallest executable pattern outward.

HardQuestions:

- Who may author a claim, and who may author the evidence used to prove it?
- What observation coverage makes a negative claim closed-world sound?
- How are patterns, occurrences, recognitions, proofs, and theories kept at distinct meta-levels?
- What exact residue is returned when recognition cannot close?
- What must a certificate bind so an edit cannot reuse stale evidence?

MeasurableOutcome: A versioned design document defines the typed schema, authority boundary, observation contract, proof lifecycle, residue vocabulary, preservation proof, incremental invalidation, certificate fields, package ownership, first categorical-ring pattern, acceptance tests, and build order.

ReplayInstructions:

1. Inspect MAP rules and current typed adapter/certificate surfaces.
2. Inspect PSC recursive reification and fork/edit capabilities.
3. Inspect CodeNose detectors and LFPOOP observation, envelope, delta, rollup, and provenance surfaces.
4. Separate candidate facts from independently observed source facts.
5. Define typed models for patterns, roles, constraints, obligations, proposals, attempts, and output-only proof results.
6. Qualify every negative proof by an explicit complete observation family and scope.
7. Define ONT, SOUP, and contradiction outcomes with exact residue.
8. Define a pre/post preservation proof and its invalidation dependencies.
9. Specify one categorical-ring vertical slice and adversarial acceptance fixtures.
10. Record the result in `docs/pattern-coherence-compiler.md`.

ShapeInvariant: The LLM may propose structures and bindings but cannot self-author the observations or proof status that validate its own claim.

AllowedVariation: Package names, concrete serializers, Prolog predicate names, and the first code pattern may change while authority separation and proof obligations remain intact.

ForbiddenDrift: Do not collapse CodeNose, LFPOOP, PSC, and MAP into one package; do not call partial observation absence; do not convert unresolved proof into success; do not put code-domain semantics in MAP core.

VerificationGate: The design must support a good fixture, a direct ring leak, an ambiguous binding, a partial-coverage negative check, and a behavior-regressing edit with distinct expected outcomes.

PersistenceTarget: `docs/pattern-coherence-compiler.md`, followed by a consumer package and reusable implementation skill after the first vertical slice proves stable.

PromotionSignal: Promote this into a `sic-pattern-coherence-compiler` skill after two different patterns use the same authority, observation, recognition, preservation, and certificate machinery.
