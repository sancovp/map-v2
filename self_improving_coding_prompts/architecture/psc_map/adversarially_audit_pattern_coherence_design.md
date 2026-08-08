# Adversarially Audit the Pattern Coherence Design

PromptType: AdversarialPrompt

SituationClass: Soundness and architecture-boundary review.

ConcreteContext: `docs/pattern-coherence-compiler.md` proposes a CodeNose -> LFPOOP -> PSC -> MAP pipeline whose first proof target is categorical-ring coherence.

AgentOrientation: Attempt to falsify the design. Assume an LLM, stale cache, partial observer, ambiguous binding, or convenient package shortcut will exploit every unspecified boundary.

HardQuestions:

- Can a candidate adapter smuggle source evidence into its own proof?
- Can incomplete AST coverage prove absence of reflective or aliased access?
- Can a proof about a pattern be confused with an occurrence of that pattern?
- Can a post-edit certificate survive changed observer code, configuration, bindings, or negative dependencies?
- Can contradiction disappear into generic unresolved residue?
- Does any dependency direction force MAP core to know code-domain concepts?

MeasurableOutcome: Every discovered attack either has an explicit rejection/residue path in the design or becomes a named design defect with a concrete repair.

ReplayInstructions:

1. Trace every fact from author to Prolog predicate and certificate.
2. Try to forge source facts from the construction side.
3. Challenge every negative constraint with partial coverage, reflection, aliases, and dynamic evaluation.
4. Challenge role binding with zero, one, and multiple compatible artifacts.
5. Mutate source, pattern, observer, configuration, evidence, and baseline independently and verify invalidation.
6. Force both logical contradiction and mere missing evidence and verify they remain distinct.
7. Inspect dependency arrows for reverse imports or hidden coupling.
8. Compare the acceptance tests with the failure modes and add any missing fixture.

ShapeInvariant: A clean result is valid only when the proof engine received independently grounded, coverage-qualified evidence and emitted a reproducible certificate.

AllowedVariation: Test framework, fixture language, and certificate encoding may vary.

ForbiddenDrift: Do not accept prose assurances, happy-path-only tests, whole-workspace hashes as a substitute for dependency tracking, or LLM confidence as evidence.

VerificationGate: The audit passes only if forged evidence, incomplete coverage, ambiguous roles, stale evidence, logical contradiction, and behavior regression cannot produce ONT.

PersistenceTarget: Amend `docs/pattern-coherence-compiler.md`; promote recurring review checks into tests and a `sic-*` skill.

PromotionSignal: Promote after the same adversarial suite catches or prevents defects in two separate pattern implementations.
