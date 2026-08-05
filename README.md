# MAP v2

MAP v2 is a small, domain-neutral system for letting an LLM construct
persistent Prolog-backed concept lattices. It uses the general closed-world
proof pattern demonstrated by GAS, but it does not import or execute GAS.

```text
application -> optional PSC construction -> domain manifest + Prolog theory
            -> MAP v2 -> SWI-Prolog
```

MAP owns lattice state, kappa declarations, the Griess phase graph, authored
facts, generic Prolog dispatch, proof residue, certificates, combination, and
SES+1 reification. A consuming domain owns its subjects, targets, obligations,
semantic rules, rejection terms, and proof meaning.

## Typed construction boundary

MAP can accept raw Prolog facts, but applications that need a stronger
neurosymbolic boundary can provide a Pydantic Stack Core (PSC) construction
adapter:

```text
LLM JSON
  -> domain-owned RenderablePiece model (local shape and required HOW fields)
  -> domain-owned lowering (candidate_* and source_* facts only)
  -> MAP domain theory (recursive and relational consequences)
  -> SOUP residue or ONT certificate
```

PSC and MAP prove different things. PSC validates one explicit value: field
types, nested structure, discriminators, and local invariants. It does not
prove graph reachability or domain closure. MAP accepts only candidate/source
facts from the adapter, derives semantic predicates in Prolog, and certifies
the exact construction schema, payload, rendering, lowering, facts, domain,
and proof residue used for the result.

An adapter supplies a `RenderablePiece` subclass, stable schema and lowering
identifiers, an allow-list of candidate predicates, and a deterministic
`lower()` function. The complete recursive-chain witness lives in
`tests/fixtures/typed_chain_adapter.py` and
`tests/fixtures/map_domains/typed_chain/`. It demonstrates logic that is
awkward to express as a single Pydantic object: transitive reachability over an
arbitrary chain of witnessed edges.

Typed constructions deliberately do not use a generic `MetaStack` as their
transport envelope. Each application defines its concrete nested PSC model so
subtype fields survive validation, persistence, and certificate replay.

## Install

Requirements:

- Python 3.11 or newer
- SWI-Prolog available as `swipl`

```bash
python3 -m pip install .
map-v2 --help
```

## Domain contract

A domain provides a `map.domain.v1` JSON manifest whose Prolog entrypoint
implements:

```prolog
map_domain_target_kind(Target).
map_domain_target_subject(Target, Subject).
map_domain_target_status(Subject, Target, Status).
map_domain_target_obligation(Subject, Target, Obligation).
map_domain_target_obligation_status(Subject, Target, Obligation, Status).
map_domain_target_extension_term(Mode, Subject, Target, Term).
```

The toy domain under `tests/fixtures/map_domains/toy/` is the canonical
independence witness.

## CLI

```bash
map-v2 --domain-manifest PATH --state STATE new SUBJECT TARGET
map-v2 --domain-manifest PATH --state STATE kappa NODE DOMAIN NAME=DESCRIPTION
map-v2 --domain-manifest PATH --state STATE compute NODE
map-v2 --domain-manifest PATH --state STATE fill NODE 'FACT.'
map-v2 --domain-manifest PATH --state STATE compile NODE
```

For typed construction, select the application adapter explicitly and pass a
JSON object or `@file` payload:

```bash
map-v2 \
  --domain-manifest PATH \
  --state STATE \
  --construction-adapter your_package.adapters:YourAdapter \
  fill-construction NODE @construction.json
```

The same adapter must remain selected when compiling or exporting the typed
node. A schema or lowering change reopens an existing certificate instead of
silently treating an old proof as current.

See [the architecture guide](map_v2/docs/architecture.md) for the Griess phase
graph and SOUP/ONT semantics.

## Development

```bash
python3 -m unittest discover -s tests -t . -p 'test_map_v2*.py'
```

This repository is currently private and unlicensed. All rights are reserved.
