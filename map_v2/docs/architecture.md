# MAP v2 Architecture

MAP v2 is a small, independent system for letting an LLM construct persistent
Prolog-backed concept lattices. It uses a pattern demonstrated by GAS but does
not execute or import GAS.

## Dependency Boundary

```text
application -> domain -> map_v2 -> SWI-Prolog
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

The domain manifest is explicit so loading a theory is never an ambient or
hard-coded side effect.
