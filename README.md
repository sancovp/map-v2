# MAP v2

MAP v2 is a small, domain-neutral system for letting an LLM construct
persistent Prolog-backed concept lattices. It uses the general closed-world
proof pattern demonstrated by GAS, but it does not import or execute GAS.

```text
application -> domain manifest + Prolog theory -> MAP v2 -> SWI-Prolog
```

MAP owns lattice state, kappa declarations, the Griess phase graph, authored
facts, generic Prolog dispatch, proof residue, certificates, combination, and
SES+1 reification. A consuming domain owns its subjects, targets, obligations,
semantic rules, rejection terms, and proof meaning.

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

See [the architecture guide](map_v2/docs/architecture.md) for the Griess phase
graph and SOUP/ONT semantics.

## Development

```bash
python3 -m unittest discover -s tests -t . -p 'test_map_v2*.py'
```

This repository is currently private and unlicensed. All rights are reserved.
