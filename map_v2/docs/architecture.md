# MAP v2 Architecture

MAP v2 is a small, independent system for letting an LLM construct persistent
Prolog-backed concept lattices. It uses a pattern demonstrated by GAS but does
not execute or import GAS.

## Dependency Boundary

```text
candidate author -> optional ConstructionAdapter --\
                                                 +-> domain -> map_v2 -> SWI-Prolog
trusted observer -> optional ObservationAdapter --/
```

MAP owns:

- lattice nodes, selection, expansion, and authored facts;
- kappa declarations;
- the Griess phase graph;
- workspace, kappa, and domain-scoped certificates;
- a generic SWI-Prolog reporting kernel;
- SOUP residue, retry, revision, combination, and SES+1 reification.

A domain owns:

- available targets and subjects;
- obligations and their statuses;
- semantic compilation and rejection;
- domain-specific report and proof terms;
- theory identity and versioning.

## PSC and MAP proof boundary

The optional construction adapter is application-owned. It gives MAP:

- a concrete `pydantic_stack_core.RenderablePiece` model;
- stable schema and lowering identifiers;
- an allow-list containing only `candidate_*` predicates;
- a deterministic lowering from the validated value to ground candidate facts.

An independently selected observation adapter gives MAP:

- a concrete snapshot/evidence `RenderablePiece` model;
- pinned schema and lowering identities;
- an allow-list containing only `source_*` predicates;
- deterministic lowering from observed evidence to ground source facts.

The construction adapter cannot emit source evidence, and the observation
adapter cannot emit candidates. Neither can emit derived predicates. This
prevents an LLM-authored proposal from manufacturing the evidence that proves
itself while keeping both inputs typed and replayable.

The separation is intentional:

| Layer | Establishes | Does not establish |
| --- | --- | --- |
| PSC | One value has the declared nested shape and local invariants | Recursive consequences, graph closure, or domain truth |
| Construction adapter | The proposal has one canonical candidate-fact interpretation | Source evidence, derived predicates, or proof success |
| Observation adapter | The snapshot has one canonical source-fact interpretation | Candidate intent, derived predicates, or proof success |
| MAP + Prolog domain | Relational consequences close the declared obligations | That malformed source data should have been accepted |

The lowerer cannot author derived predicates, rules, or directives. Only the
domain theory can derive proof terms. MAP persists hashes and identities for
each concrete model schema, canonical payload, rendered value, lowering source,
and lowered fact set. Those fields enter the proof packet and certificate, so
drift in either authority makes prior ONT state stale.

This is a weak-to-strong neurosymbolic path rather than a claim that natural
language proves itself. An LLM first proposes an explicit construction with
required HOW-shaped evidence. PSC rejects malformed constructions. MAP then
tests whether the admitted candidates entail the target under a closed-world
domain theory, returning exact SOUP residue when they do not.

## SOUP and ONT

The portable phase graph is:

```text
DERIVE -> COMPUTE -> BUILD -> VERIFY -> ONT | SOUP
ONT instances -> PATTERN -> IMPLEMENT -> DERIVE at SES+1
SOUP -> DERIVE after explicit retry
```

SOUP and ONT come from MAP's specialization of Crystal Ball's Griess
constructor algebra. They are not GAS statuses. `compiled` is the current
domain compiler's success result; MAP maps that VERIFY result to ONT and maps
every noncompiled result to SOUP while preserving residue.

SOMA also uses the word `SOUP` in its own `SOUP -> CODE` admission model. That
is a separate type/admission distinction. MAP's paired outcome here is
`SOUP | ONT`; shared vocabulary does not make either one a GAS state.

## Prolog Domain Contract

A `map.domain.v1` manifest names an entrypoint, source bundle, and targets. Its
Prolog entrypoint implements:

```prolog
map_domain_target_kind(Target).
map_domain_target_subject(Target, Subject).
map_domain_target_status(Subject, Target, Status).
map_domain_target_obligation(Subject, Target, Obligation).
map_domain_target_obligation_status(Subject, Target, Obligation, Status).
map_domain_target_extension_term(Mode, Subject, Target, Term).
```

MAP supplies `map_subject/2`, `map_kappa_domain/2`, and
`map_kappa_invariant/2` through the managed workspace and temporary proof
overlay. Domain code supplies all meaning.

The toy domain in `tests/fixtures/map_domains/toy/` is the minimal independence
witness. Dharma Detectives is a larger consumer of exactly the same contract.

## CLI

```bash
map-v2 --domain-manifest PATH --state STATE new SUBJECT TARGET
map-v2 --domain-manifest PATH --state STATE kappa NODE DOMAIN NAME=DESCRIPTION
map-v2 --domain-manifest PATH --state STATE compute NODE
map-v2 --domain-manifest PATH --state STATE fill NODE 'FACT.'
map-v2 --domain-manifest PATH --state STATE compile NODE
```

Typed applications additionally select their adapter explicitly:

```bash
map-v2 --domain-manifest PATH --state STATE \
  --construction-adapter package.module:Adapter \
  fill-construction NODE @payload.json
```

Observed applications attach independently validated evidence before compile:

```bash
map-v2 --domain-manifest PATH --state STATE \
  --construction-adapter package.module:ConstructionAdapter \
  --observation-adapter package.module:ObservationAdapter \
  attach-observation NODE @snapshot.json
```

The domain manifest is explicit so loading a theory is never an ambient or
hard-coded side effect.
