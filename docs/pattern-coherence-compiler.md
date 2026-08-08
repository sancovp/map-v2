# Pattern Coherence Compiler

## Status

This document designs a consuming MAP domain. It does not make architectural
pattern semantics part of the MAP core.

The system combines four already separate tools:

```text
CodeNose  -> fast edit hooks, observations, and user-facing residue
LFPOOP    -> code reification, checked candidate envelopes, shadow laws,
             learned wiring, deltas, and append-only provenance
PSC       -> typed, recursively reifiable pattern language
MAP       -> closed-world relational proof, SOUP/ONT, and certificates
```

The working name in this document is *pattern coherence*. Naming is not part
of the contract.

## The problem

An LLM can understand an architecture globally and still make a locally
reasonable edit that destroys it. Unit tests may remain green while a stable
extension boundary, representation morphism, role separation, or composition
law silently decoheres.

The target behavior is:

```text
source snapshot S0
  -> recognize pattern occurrence P
  -> prove P under exact witnesses
  -> certificate C0

proposed edit D
  -> source snapshot S1
  -> recompute impacted observations and occurrences
  -> prove preservation against C0
  -> ONT, or exact SOUP/contradiction residue
```

The first useful sentence is:

> Extending a recognized LFPOOP ring must not introduce an undeclared
> capability or break the previously proven composition boundary.

## Non-goals

Version one does not:

- understand every semantic property of Python;
- infer arbitrary design-pattern names without an explicit pattern theory;
- treat a CodeNose smell or statistical cluster as proof;
- claim full program equivalence from a finite test suite;
- let the LLM author its own evidence or proof result;
- serialize arbitrary Prolog or Python callbacks inside a pattern definition;
- merge CodeNose, LFPOOP, PSC, and MAP into one package;
- require CodeOntologyPython.

## Existing assets

The design starts from behavior that already exists.

### CodeNose

The `ceo` branch update in `sancovp/sanctuary-revolution-alpha` adds:

- project-authored onion layers in `.codenose/onion.json`;
- structural recognition of LFPOOP `@ring` declarations;
- `ring_leak` for direct `self.X` access outside `adds + requires`;
- `unlifted_reusable_class` as a pattern-discovery hint;
- a post-edit enforcement surface that can present exact findings.

These are sensors. They produce observations and candidate violations, not
pattern truth.

### LFPOOP

LFPOOP already supplies most of the evidence discipline:

- `blocks.py`: statement-grain code-as-data with reads, writes, kinds, source,
  and functionalized regeneration;
- `alphabets.py`: classification of free names into operational roles;
- `rollup.py`: candidate structural grouping learned from static wiring and
  runtime coactivation;
- `envelope.py`: LLM code enters as a claim; derivable declarations are
  checked against AST evidence in both directions;
- `deltas.py`: typed edit algebra, named conflicts, and evidence
  non-transferability on fork;
- `predict.py`: capability and binding residues remain distinct;
- `compiler.py` and `onionize.py`: quarantine and behavioral shadow gates;
- `codething.py`: content identity, provenance, and an external witness seat;
- `owl.py`, `prolog.py`, `domain.py`, and `chains.py`: ontology projection,
  closure, and explicit compiler/metacompiler levels.

LFPOOP does not yet provide a generic pattern/role/occurrence proof language.

### PSC

PSC already provides versioned, schema-hashed recursive `RenderablePiece`
trees, an explicit type registry, validated reconstruction, and non-mutating
`fork()` and nested `edit()` operations.

### MAP

MAP already provides candidate-only Prolog lowering, relational closure,
per-obligation reports, exact residue, SOUP/ONT transitions, certificate
staleness, and an independent domain boundary.

## Authority separation

The system has three authorities. They must not collapse.

| Authority | May author | May not author |
| --- | --- | --- |
| LLM/user construction | pattern definitions, occurrence proposals, role bindings, intent, evidence links | source observations, satisfied obligations, proven occurrences, verdicts |
| pinned observer | source snapshots, entity kinds, relations, spans, coverage declarations | pattern meaning, role assignments, proof success |
| MAP domain | derived bindings, constraint and obligation verdicts, occurrences, preservation proofs, residue | source text or candidate intent |

The current generic MAP construction adapter permits both `candidate_*` and
`source_*`. Pattern coherence requires a hardened split:

```text
ConstructionAdapter -> candidate_* only
ObservationAdapter  -> source_* only, pinned implementation and config
```

An LLM-controlled lowerer must never be able to emit `source_*`. Otherwise it
can fabricate the witnesses required to prove its own edit.

## Meta-talk levels

Every entity belongs to an explicit talk level.

```text
L0 artifact      source files, diffs, runtime objects, test results
L1 observation   AST/LFPOOP/CodeNose facts about L0
L2 pattern       definitions over L1 relations
L3 recognition   occurrence proposals and role bindings
L4 proof         proofs, rejections, preservation claims about L3
L5 theory        patterns and rules about patterns, observers, and proofs
```

References are either `use` or `quote`:

- `use` consumes a lower-level entity under an explicit interpretation;
- `quote` treats a claim or definition as data without entailing it;
- moving from quote to use requires a domain-owned interpretation rule;
- v1 refuses direct self-reference;
- later fixed-point/self-application modes must be explicit and separately
  warranted.

This prevents four statements from being confused:

```text
the code contains relation R
the observer reports relation R
the proposal claims R witnesses pattern P
the proof establishes that claim under context C
```

## Typed pattern language

The concrete classes are consumer-owned PSC `RenderablePiece` models. The
following is the normative shape, not final Python spelling.

### Exact references

```text
ExactPatternRef
  pattern_id
  version
  semantic_sha256

ExactRecognizerRef
  recognizer_id
  version
  implementation_sha256
  domain_sha256
```

Durable references never float to the latest version.

### Context

```text
PatternContext
  context_id
  talk_level
  parent_context_id?
  snapshot_ids[]
  quoted_context_ids[]
  interpretation_id?
```

Context parentage must be acyclic. Context does not itself declare arbitrary
relations closed; closure comes from pinned observation coverage below.

### Pattern role

```text
PatternRole
  role_id
  label
  allowed_entity_kinds[]
  min_bindings
  max_bindings?
  distinct_from[]
  same_context_required
  description
```

Required and optional roles are cardinalities, not competing booleans.

### Terms and constraints

Terms are typed role references, contextual entity references, or typed
literals. V1 admits four constraint forms:

```text
RelationConstraint
  constraint_id, relation, arguments[], positive|negative

ComparisonConstraint
  constraint_id, left, eq|ne|lt|le|gt|ge, right

CardinalityConstraint
  constraint_id, role_id, relation?, minimum, maximum?

PathConstraint
  constraint_id, relation, source, target, min_hops, max_hops?
```

There is no unrestricted expression string. Recursive paths are evaluated by
the MAP domain's tabled Prolog closure.

### Obligation

```text
PatternObligation
  obligation_id
  label
  constraint_ids[]
  combine: all|any
  force: required|advisory
  depends_on[]
  failure_code
  repair_prompt?
```

Dependencies must be acyclic. `repair_prompt` is presentation guidance and
can never discharge an obligation.

### Definition

```text
PatternDefinition
  pattern_id
  version
  semantic_sha256
  context_id
  label
  intent
  roles[]
  constraints[]
  obligations[]
  supersedes?
  tags[]
```

The semantic hash is recomputed from the canonical roles, constraints,
obligations, context, and supersession reference. Any semantic change creates
a new exact version. Existing occurrences remain pinned to the old definition.

### Occurrence proposal

```text
RoleBinding
  binding_id, role_id, contextual_entity, entity_kind, ordinal

EvidenceLink
  link_id, constraint_id, evidence_ids[]

OccurrenceProposal
  proposal_id
  proposed_occurrence_id
  exact_pattern_ref
  context_id
  bindings[]
  evidence_links[]
  rationale
  proposed_by

RecognitionAttempt
  attempt_id
  proposal_id
  exact_recognizer_ref
  exact_pattern_ref
  context_id
  observation_snapshot_ids[]
  input_sha256
  initiated_by
```

`RecognitionAttempt` deliberately has no status, satisfied-obligation list,
proof, or rejection field. Those are MAP outputs.

### Output-only models

`ProvenPatternOccurrence` and `PatternRejection` may be PSC models for safe
transport and rendering, but candidate adapters must refuse to lower them.

## Observation model and closed-world boundary

### Snapshot manifest

```text
ObservationSnapshot
  snapshot_id
  context_id
  source_tree_sha256
  observed_graph_sha256
  artifacts[] {artifact_id, kind, content_sha256, locator}
  extractor {id, version, implementation_sha256, configuration_sha256}
  coverage[] {family, scope, complete|partial, limitations[]}
```

### Evidence record

```text
EvidenceRecord
  evidence_id
  snapshot_id
  context_id
  subject_id
  subject_kind
  relation
  object_entity | typed_literal
  artifact_id
  source_span?
  evidence_sha256
```

Evidence records only observed relations. They never state that a constraint
or obligation is satisfied.

### Coverage-qualified negation

Absence is meaningful only inside a complete observation family and scope:

```prolog
closed_absent(Snapshot, Family, Scope, Query) :-
    source_coverage(Snapshot, Family, Scope, complete),
    \+ source_observation_matches(Snapshot, Family, Scope, Query).
```

The current CodeNose ring scan can declare completeness for direct attribute
accesses shaped as literal `self.X`. It must declare partial coverage for
reflective access through `getattr`, aliasing, `eval`, or dynamic mutation.

Therefore the valid result is:

```text
no direct_self_attribute ring leak observed under complete direct-access scan
```

not:

```text
this program can never access an undeclared capability
```

Insufficient coverage produces `incomplete_closed_world_scope(...)` residue.
It never silently compiles through negation-as-failure.

## Candidate and source lowering

The LLM/user adapter emits fixed-arity ground facts such as:

```prolog
candidate_pattern(Pattern, Version, SemanticHash, Context).
candidate_role(Pattern, Version, Role, Min, Max).
candidate_role_kind(Pattern, Version, Role, Kind).
candidate_constraint(Pattern, Version, Constraint, Kind).
candidate_constraint_arg(Pattern, Version, Constraint, Pos, Kind, Value).
candidate_obligation(Pattern, Version, Obligation, Combine, Force).
candidate_occurrence_proposal(Proposal, Occurrence, Pattern, Version, Hash, Context).
candidate_binding(Proposal, Binding, Role, EntityContext, Entity, Kind, Ordinal).
candidate_recognition_attempt(Attempt, Proposal, Recognizer, Version, Hash).
```

The pinned observation adapter exclusively emits:

```prolog
source_snapshot(Snapshot, Context, GraphHash, Extractor, ExtractorHash).
source_snapshot_artifact(Snapshot, Artifact, ArtifactHash).
source_coverage(Snapshot, Family, Scope, Completeness).
source_entity_kind(Snapshot, Context, Entity, Kind, Evidence).
source_relation(Snapshot, Context, Evidence, Subject, Relation, Object).
source_literal_relation(Snapshot, Context, Evidence, Subject, Relation, Datatype, Value).
```

Only the MAP pattern domain derives:

```prolog
derived_valid_binding(...).
derived_constraint_verdict(..., satisfied|unresolved|contradicted).
derived_obligation_verdict(..., satisfied|unresolved|contradicted).
derived_pattern_occurrence(...).
derived_preservation_verdict(...).
```

## Recognition proof

### Binding rules

The role solver enumerates and deduplicates substitutions.

- A required role absent under complete coverage is contradicted.
- A required role absent under partial coverage is unresolved.
- More than `max_bindings` is contradicted.
- Multiple complete mappings without an explicit canonicalization rule are
  unresolved as `ambiguous_binding`.
- Entity kind must come from source evidence, not the proposal.
- Distinct roles cannot bind the same entity.

### Obligation verdicts

Every required obligation has one verdict:

```text
satisfied     enough warranted evidence closes it
unresolved    evidence, binding, or coverage remains open
contradicted  complete evidence supplies a counterwitness
```

Occurrence precedence is:

```text
any required contradiction -> CONTRADICTED
else any required unresolved -> SOUP
else all required satisfied -> ONT
```

MAP may continue to use SOUP as the terminal Griess phase for both unresolved
and contradicted attempts, but public proof residue must preserve the
tri-state verdict. Contradiction must never be flattened into generic partial.

### Exact residue

The initial machine terms are:

```text
missing_binding
ambiguous_binding
missing_relation
forbidden_relation(counterwitness)
cardinality_violation
unsupported_observation
incomplete_closed_world_scope
baseline_role_lost
representation_drift
behavior_regression
stale_evidence
```

Each term names the attempt, obligation or constraint, affected roles and
bindings, evidence IDs/hashes, source spans where available, and observed
counterterms. The system says `changed_support`, not `caused_by`, unless a
separate causal witness exists.

## Preservation across an edit

A preservation claim is distinct from recognizing a fresh occurrence.

Inputs:

```text
baseline ONT certificate C0
baseline snapshot S0
new snapshot S1
normalized source/observation delta D
exact pattern and recognizer versions
```

The domain first recognizes the occurrence in S1, then checks pattern-owned
cross-snapshot obligations:

- stable role identity where the role is declared stable;
- preservation of required relations;
- absence of newly forbidden relations under sufficient coverage;
- old-variant monotonicity for declared extension boundaries;
- representation/round-trip laws;
- behavioral shadow probes required by the pattern.

Changing the pattern version is a migration, not proof that the edit preserved
the old pattern.

## Incremental invalidation

V1 may safely recompile a bounded source scope. Later incremental proof must
index both:

- positive dependencies: facts and witnesses actually used;
- negative antidependencies: complete-family absence queries that would be
  invalidated by a newly added matching fact.

An occurrence is impacted by changed or removed positive support, a new fact
matching an antidependency, changed selector candidates, or drift in extractor,
pattern, recognizer, probe, domain, or lowering identity.

An unaffected occurrence receives a new carry-forward certificate linking the
old certificate to a disjoint-impact proof. An old-snapshot certificate is
never simply relabeled current.

## Certificate contract

An ONT certificate binds at least:

- source tree and artifact hashes;
- observation graph and coverage manifest hashes;
- extractor/detector implementation and configuration hashes;
- PSC schema, payload, rendering, and lowering hashes;
- exact pattern semantic hash and recognizer hash;
- MAP domain, kappa, runtime, and Prolog identities;
- normalized unique role map;
- every required obligation and witness hash;
- behavioral probe identities and results when required;
- baseline certificate, delta, and impact hashes for preservation proofs.

SOUP and contradicted attempts persist equally replayable verdict artifacts,
but only ONT exports an admissibility certificate.

## First pattern: categorical ring

### Roles

```text
ring_class             exactly one
added_capability       zero or more
required_capability    zero or more
accessed_capability    zero or more
supporting_ring        zero or more
```

### Required obligations

1. Every direct accessed capability is declared in `adds` or `requires`.
2. Every required capability is supplied by a base or inner ring.
3. The ring order satisfies requirements from the inside out.
4. An extension introduces no undeclared direct access.
5. Existing compositions retain their declared capabilities.

### Advisory discovery rule

A class reused as a base by multiple classes but not declared as a ring emits
an `unlifted_reusable_class` proposal. It is not automatically a violation;
the LLM/user may accept it as a new pattern candidate or dismiss it.

### Example contradiction

```prolog
pattern_constraint_contradicted(
    attempt_17,
    ring_alphabet_closed,
    accessed_capability(database),
    missing_declaration(database),
    evidence_93
).
```

## Package ownership

The packages remain independent:

```text
codenose
  observes edits and presents findings

lfpoop
  supplies reusable Python observers, candidate-envelope discipline,
  deltas, shadow probes, and provenance records

pydantic-stack-core
  supplies generic typed reification only

map-v2
  supplies generic lattice/proof runtime plus the generic authority split

pattern-coherence consumer
  owns PatternDefinition PSC models, lowering adapters, observation manifest,
  Prolog domain, recognizer rules, and ring fixture
```

The consumer should begin as an experimental sibling package. MAP must not
import CodeNose or LFPOOP. CodeNose may invoke the consumer from its hook.

## Smallest executable vertical slice

Input fixture:

```python
from lfpoop.onion import ring

@ring(adds=("audit",), requires=("provenance",))
class AuditRing:
    def audit(self):
        return self.provenance()
```

The slice must:

1. Produce a content-addressed source snapshot.
2. Emit pinned observer facts for the ring, declaration alphabet, and direct
   `self.provenance` access with complete direct-access coverage.
3. Validate and lower a typed `categorical_ring` definition and occurrence
   proposal through PSC.
4. Derive the unique role binding and close every required v1 obligation.
5. Export an ONT certificate with source, observer, pattern, role-map, domain,
   and witness hashes.
6. Edit the method to access `self.database` without declaring it.
7. Reobserve and prove the old occurrence contradicted with an exact source
   span and `missing_declaration(database)` counterwitness.
8. Add `database` to `requires`, reobserve, and return ONT only if a supporting
   inner/base capability is witnessed; otherwise remain SOUP with
   `missing_support(database)`.
9. Demonstrate that `getattr(self, name)` does not falsely compile as clean;
   it yields coverage residue.
10. Surface the final structured result through CodeNose's existing edit hook.

## Acceptance tests

The vertical slice is complete only when tests prove:

- an LLM construction cannot emit `source_*`;
- an observation adapter cannot emit `candidate_*`;
- a lowerer cannot emit derived predicates, variables, rules, or conjunctions;
- observer implementation/config drift stales the certificate;
- pattern, recognizer, domain, or PSC schema drift stales the certificate;
- the good ring is ONT;
- the undeclared direct access is contradicted with exact residue;
- unsupported required capability is SOUP, not falsely ONT;
- reflective access produces incomplete-coverage residue;
- contradictory and unresolved verdicts remain distinguishable;
- fork/edit preserves structure but strips non-transferable proof evidence;
- replay from the stored payloads and manifests reproduces the same verdict;
- CodeNose formatting does not alter proof semantics.

## Build order

1. Create the consumer package with PSC models and a static ring pattern.
2. Add MAP's `ConstructionAdapter`/`ObservationAdapter` authority split and
   adversarial tests.
3. Wrap the existing CodeNose/LFPOOP direct-ring scanner as a pinned observer
   that emits snapshots, facts, spans, and explicit coverage.
4. Implement the ring Prolog domain and exact residue.
5. Bind observation and per-obligation witness hashes into certificates.
6. Implement baseline/post preservation claims.
7. Connect CodeNose's post-edit hook to the consumer CLI.
8. Add LFPOOP shadow probes as optional behavioral obligations.
9. Add learned rollup/family-resemblance output only as occurrence proposals.
10. Generalize from `categorical_ring` to additional user-authored patterns.

The first five steps establish the trustworthy neurosymbolic kernel. Hook
ergonomics, incremental recomputation, learned pattern discovery, OWL export,
and metapattern self-application come afterward.
