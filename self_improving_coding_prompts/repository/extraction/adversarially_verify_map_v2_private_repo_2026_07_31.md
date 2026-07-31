PromptType: AdversarialPrompt

SituationClass: Falsify a claimed standalone package extraction before private publication.

ConcreteContext: `/Users/isaacwr/Documents/New project/map-v2` was extracted from the co-located `map_v2/` package in `gas_bootstrap_depth_system`. The extraction claims to be domain-neutral, installable, independently tested, and ready for private GitHub repository `sancovp/map-v2`.

AgentOrientation: Assume the extraction is ornamental until installed-artifact behavior and dependency boundaries prove otherwise. Prefer a concrete failure over a reassuring summary.

HardQuestions:
- Did a DD consumer test or theory leak into the standalone repository under a generic filename?
- Do any executable imports reach GAS or DD?
- Does the wheel omit the Prolog runtime or depend on the source checkout?
- Can the installed CLI drive the real toy Prolog domain from outside the repository?
- Did extraction dirty or rewrite the original checkout?
- Do repository discovery rules preserve domain neutrality?
- Is GitHub visibility actually private after creation?

MeasurableOutcome:
- Every leaked consumer surface is removed.
- Runtime-import scans are clean.
- Unit, compilation, wheel-content, and installed toy-domain checks pass.
- The original checkout remains clean.
- The standalone Git tree contains only intentional source, tests, fixtures, rules, prompts, and packaging.
- GitHub metadata reports `private`.

ReplayInstructions:
1. Enumerate every tracked candidate and classify it as MAP-owned or consumer-owned.
2. Search executable imports for `ghost_story_bootstrap` and `dharma_detectives`.
3. Run the MAP-owned unittest discovery pattern.
4. Build a wheel without source-tree fallback and inspect its members.
5. Install the wheel into a temporary virtual environment outside the checkout.
6. Execute new, kappa, compute, fill, and compile against the toy domain; require `compiled`, `ont`, and `toy_proof`.
7. Check the source checkout's Git status.
8. Inspect the initial standalone commit and remote metadata after publication.

ShapeInvariant: Passing requires real generic Prolog execution from the installed artifact, not only mocked compiler tests.

AllowedVariation: Temporary paths, hashes, timestamps, wheel build tags, and Git commit identifiers may vary.

ForbiddenDrift: Ignoring import errors, copying DD merely to satisfy a test, counting documented negative dependency laws as runtime coupling, publishing publicly, or claiming remote completion before verifying GitHub metadata.

VerificationGate: All replay checks pass and `gh repo view sancovp/map-v2 --json visibility` returns `PRIVATE`.

PersistenceTarget: Keep this adversarial prompt beside the extraction WorkPrompt as the repository's initial boundary proof.

PromotionSignal: Promote this verification shape only after another standalone extraction needs the same consumer-leak and installed-Prolog checks.
