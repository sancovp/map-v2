# Start Here

MAP v2 owns generic lattice state, Griess transitions, certificates, authored
facts, Prolog dispatch, and domain-manifest loading.

A consuming domain owns all semantic meaning. Preserve these boundaries:

1. Do not import GAS or Dharma Detectives.
2. Do not copy consumer ontology into Python conveniences.
3. Keep domain loading explicit through `map.domain.v1`.
4. Prove generic behavior with the toy Prolog domain.
5. Treat exact compiler residue as data; do not reduce it to a score.
6. Preserve authored facts and immutable proof/certificate history.
7. If a consumer uses PSC, keep its concrete `RenderablePiece` model and
   lowering adapter consumer-owned; MAP owns only the generic adapter contract.
8. PSC validates local construction shape. MAP/Prolog derives and proves
   recursive or relational consequences. Never claim one substitutes for the
   other.
9. Typed lowerers may emit declared `candidate_*` and `source_*` facts only.
   Derived predicates remain exclusively domain-theory output.
10. Bind construction schema, payload, rendering, lowering, and fact identity
    into proof packets and certificates; adapter drift must reopen old proof.
