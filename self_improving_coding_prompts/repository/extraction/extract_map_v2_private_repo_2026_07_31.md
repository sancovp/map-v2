PromptType: WorkPrompt

SituationClass: Extract a co-located independent package into its own private repository.

ConcreteContext: `map_v2/` currently lives inside `sancovp/gas_bootstrap_depth_system`, while its architecture and imports declare it independent from GAS and Dharma Detectives. Create a standalone repository at `/Users/isaacwr/Documents/New project/map-v2` intended for private GitHub repository `sancovp/map-v2`. Do not remove or rewrite the source copy in this pass.

AgentOrientation: Preserve MAP's domain-neutral proof-shell identity. Treat this as a package extraction, not a GAS refactor and not a DD migration.

HardQuestions:
- Does every runtime import resolve using only the Python standard library and MAP-owned files?
- Are the generic Prolog runtime and toy-domain independence witness packaged?
- Can the CLI install and run outside the original monorepo?
- Are GAS and DD absent from runtime, tests, packaging, and repository rules?
- Is the initial Git history clean, intentional, private-remote-ready, and reproducible?

MeasurableOutcome:
- A standalone Python package named `map-v2` exists with the `map-v2` console script.
- MAP source, Prolog runtime, architecture documentation, MAP-owned test modules, and toy fixture are present.
- Focused tests pass from the standalone repository.
- A built wheel contains the Prolog runtime.
- A fresh Git repository has one intentional initial commit on `main`.
- The private GitHub remote is created and pushed when authentication is available.

ReplayInstructions:
1. Inventory MAP-owned source, tests, fixtures, documentation, and imports in the source repository.
2. Copy only those owned surfaces into the standalone target.
3. Add standalone packaging, root README, root agent rules, ignore rules, and license.
4. Run compile checks, unit tests, package build, wheel-content inspection, and an installed-wheel CLI smoke test.
5. Search the extracted repository for forbidden runtime coupling to `ghost_story_bootstrap` or `dharma_detectives`.
6. Initialize Git, commit the verified extraction, create a private GitHub repository, and push `main`.
7. Leave the original co-located package untouched.

ShapeInvariant: The extracted repository remains a domain-neutral MAP shell whose domains are supplied through explicit manifests and Prolog contracts.

AllowedVariation: Repository description, semantic version, test runner details, and future consumer repositories may change.

ForbiddenDrift: Importing GAS or DD, copying DD theories, claiming historical preservation that was not performed, removing the source package before consumers migrate, publishing publicly, or treating passing fake-compiler tests as sufficient without the toy Prolog witness.

VerificationGate: Standalone unit tests pass; wheel and installed CLI smoke checks pass; forbidden-import search is clean; Git status is clean after commit; GitHub reports private visibility after push.

PersistenceTarget: Root repository rules and this extraction prompt; promote recurring cross-repository extraction discipline into a `sic-*` skill only after another comparable extraction.

PromotionSignal: A second independent package extraction repeats the same boundary, packaging, installed-artifact, and private-publication checks.
