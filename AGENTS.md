# MAP v2 Agent Rules

Read `.agents/rules/start-here.md` before changing this repository.

MAP v2 is an independent, domain-neutral cognition and Prolog proof shell.

Dependency law:

```text
map_v2 -> SWI-Prolog
map_v2 -/-> ghost_story_bootstrap
map_v2 -/-> dharma_detectives
```

Keep the Griess phase graph explicit:

```text
DERIVE -> COMPUTE -> BUILD -> VERIFY -> ONT | SOUP
```

SOUP and ONT are MAP outcomes inherited from the Crystal Ball/Griess
constructor pattern. They are not GAS statuses. A domain compiler alone
decides whether VERIFY reaches ONT or SOUP.

Every domain must implement the generic Prolog target contract exercised by
`map_v2/prolog/runtime.pl`. Never hard-code a consuming domain's ontology,
targets, or proof terms into MAP.

Run the focused standalone suite after behavior changes:

```bash
python3 -m unittest discover -s tests -t . -p 'test_map_v2*.py'
```

For release checks, also build a wheel, verify that it contains
`map_v2/prolog/runtime.pl`, and smoke-test the installed `map-v2` command
outside the checkout.
