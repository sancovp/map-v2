# Build the PSC-to-MAP typed construction boundary

PromptType: WorkPrompt

SituationClass: Replace an over-trusting authored-fact seam with a typed candidate-construction seam while preserving the existing proof lifecycle.

ConcreteContext: Standalone MAP v2 currently accepts arbitrary authored Prolog facts through `fill`, while `pydantic-stack-core` already supplies agent-discoverable, recursively composable Pydantic models. The user corrected the architecture: PSC should own construction and local validation; MAP should own relational derivation, recursion, negation, closure, residue, and certificate lifecycle. A generic `MetaStack` also loses subclass fields during `model_dump`, so the integration must use explicit domain construction models rather than pretending generic polymorphic round-tripping works.

AgentOrientation: Preserve MAP's domain neutrality and Griess lifecycle. Treat a PSC payload as a candidate program, not proof. Make the lowering boundary explicit, canonical, inspectable, and incapable of directly emitting reserved derived predicates. Prove the distinction with a non-DD fixture whose relational conclusion requires recursive Prolog derivation across multiple typed candidate steps.

HardQuestions: Can a naked conclusion reach ONT? Can a construction lower a derived or runtime predicate? Does certificate identity bind the schema, canonical payload, rendered construction, lowering implementation, and generated candidate facts? Can a valid typed payload still remain SOUP when relational closure is missing? Does recursive closure prove something that no local Pydantic validator supplied? Does changing the construction invalidate an earlier certificate? Can the persisted payload round-trip without losing subtype fields?

MeasurableOutcome: MAP exposes a generic typed-construction fill/revise path backed by Pydantic Stack Core; validated constructions persist canonically; lowerers emit candidate facts only; reserved namespaces are rejected; compiler packets and certificates bind construction identity; a domain-neutral chain fixture reaches ONT only through recursive derivation; malformed, naked, forged, partial, stale, and round-trip cases are tested.

ReplayInstructions: Add the PSC dependency; define a generic construction adapter contract and canonical identity helpers; extend lattice state with construction metadata and typed fill/revise operations; bind construction identity into packet scope, proof context, and certificates; build a Pydantic fixture model with discriminated HOW steps; lower it into candidate-only facts; add a Prolog domain that recursively derives reachability/warrant; add focused tests; run the standalone suite; inspect the wheel surface; update architecture and rules so raw authored facts are explicitly legacy/weak while typed construction is the proof-oriented seam.

ShapeInvariant: PSC validates one constructed value; MAP derives relations across validated values. Candidate predicates are authorable only through the lowerer; derived predicates are never authorable. ONT means closure relative to the frozen construction schema, lowering implementation, domain theory, kappa, and generated facts—not external truth.

AllowedVariation: Class names, fixture vocabulary, certificate field names, and exact module layout may change if the authority boundary, canonical identity, domain neutrality, and recursive proof witness remain explicit and tested.

ForbiddenDrift: Hard-code DD vocabulary into MAP; accept a prose `how`; let Pydantic validators perform the recursive theorem; serialize subclass fields through generic `MetaStack` and silently lose them; allow lowerers to emit `map_`, `derived_`, or domain proof predicates; call hashes semantic proof; mark a naked assertion ONT; replace exact residue with a score.

VerificationGate: Focused typed-construction tests and the full `test_map_v2*.py` suite pass; `git diff --check` passes; a wheel builds with the new module and Prolog runtime; an installed-wheel smoke creates, validates, lowers, recursively compiles, exports, and verifies one construction certificate outside the checkout.

PersistenceTarget: `map_v2` construction module, lattice/certificate state, domain-neutral fixtures and tests, architecture/rule docs, and a paired adversarial prompt.

PromotionSignal: Promote this workflow into a reusable MAP typed-domain skill after a second independent consumer uses the same adapter without changing MAP core semantics.
