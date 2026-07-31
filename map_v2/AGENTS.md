# MAP v2 Rules

MAP v2 is an independent, domain-neutral cognition and Prolog proof shell. It
implements a reusable pattern demonstrated by GAS; it does not run GAS.

Dependency law:

```text
map_v2 -> SWI-Prolog
map_v2 -/-> ghost_story_bootstrap
map_v2 -/-> dharma_detectives
```

Keep the Griess phase graph explicit:
`DERIVE -> COMPUTE -> BUILD -> VERIFY -> ONT/SOUP`. SOUP and ONT are MAP
states inherited from the Crystal Ball/Griess constructor pattern, not GAS
states. A domain compiler alone decides whether VERIFY reaches ONT or SOUP.

Every domain must implement the `map_domain_target_*` Prolog contract exercised
by `prolog/runtime.pl`. Prove domain neutrality with the toy fixture before
adding conveniences for a concrete domain. Never hard-code DD realms, story
targets, or domain-specific certificate semantics into MAP.
