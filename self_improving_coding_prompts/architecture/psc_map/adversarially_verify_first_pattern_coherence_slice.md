# Adversarially Verify the First Pattern-Coherence Slice

PromptType: AdversarialPrompt

SituationClass: Proof-authority and closed-world soundness audit after implementation.

ConcreteContext: MAP now has separate construction and observation adapters plus a consumer-owned `categorical_ring` fixture.

AgentOrientation: Attempt to manufacture ONT without independent evidence, complete coverage, an unambiguous role map, or a contradiction-free ring alphabet.

HardQuestions:

- Can `source_*` enter through construction, raw fill, or an undeclared predicate?
- Can `candidate_*` enter through the observation adapter?
- Can a contradiction still emit a proof when Prolog is queried with a bound status?
- Can partial coverage satisfy an absence obligation?
- Can multiple role candidates be silently selected?
- Does changing observation code reopen an existing ONT certificate?

MeasurableOutcome: The focused suite contains and passes an executable attack for every listed boundary; the full MAP suite remains green; docs state the actual two-authority contract.

ReplayInstructions:

1. Run authority-forgery tests for both adapters.
2. Attempt the raw-fill bypass on a typed-authority lattice.
3. Prove a clean ring and inspect its certificate and proof context.
4. Add an undeclared direct access and ensure status is contradicted with no proof output.
5. Mark the observer partial and ensure exact incomplete-scope residue.
6. Supply two complete role candidates and ensure exact ambiguous-binding residue.
7. Change observation lowering identity and ensure certificate export is rejected.
8. Run `git diff --check` and the entire focused suite.

ShapeInvariant: ONT is impossible unless candidate intent and independently observed source evidence jointly close every required obligation.

AllowedVariation: Fixture names and evidence atoms may change.

ForbiddenDrift: Do not accept a test that asserts only terminal SOUP; assert exact residue and absence of proof. Do not treat a report header as a proof term.

VerificationGate: All focused tests pass, contradicted and partial cases emit no `pattern_occurrence_proof`, and no adapter or raw-fill route crosses authority.

PersistenceTarget: Regression tests, architecture docs, and future `sic-pattern-coherence-compiler` workflow.

PromotionSignal: Promote when a second code pattern reuses the same attacks without new authority machinery.
