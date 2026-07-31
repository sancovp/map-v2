% Minimal non-DD witness for the independent MAP domain protocol.

:- dynamic map_subject/2.
:- dynamic map_kappa_domain/2.
:- dynamic map_kappa_invariant/2.
:- dynamic claim_fact/2.

map_domain_target_kind(claim).
map_domain_target_subject(claim, Subject) :-
    map_subject(claim, Subject).

toy_kappa_complete(Subject) :-
    map_kappa_domain(Subject, toy_claims),
    map_kappa_invariant(Subject, grounded_claim),
    \+ (
        map_kappa_invariant(Subject, Other),
        Other \= grounded_claim
    ).

map_domain_target_status(Subject, claim, compiled) :-
    toy_kappa_complete(Subject),
    claim_fact(Subject, grounded_claim),
    !.
map_domain_target_status(Subject, claim, partial) :-
    map_subject(claim, Subject).

map_domain_target_obligation(_Subject, claim, kappa_domain(toy_claims)).
map_domain_target_obligation(_Subject, claim, kappa_invariant(grounded_claim)).
map_domain_target_obligation(_Subject, claim, grounded_claim).

map_domain_target_obligation_status(
    Subject,
    claim,
    kappa_domain(toy_claims),
    compiled
) :-
    map_kappa_domain(Subject, toy_claims),
    !.
map_domain_target_obligation_status(
    Subject,
    claim,
    kappa_domain(toy_claims),
    partial
) :-
    \+ map_kappa_domain(Subject, toy_claims).
map_domain_target_obligation_status(
    Subject,
    claim,
    kappa_invariant(grounded_claim),
    compiled
) :-
    map_kappa_invariant(Subject, grounded_claim),
    !.
map_domain_target_obligation_status(
    Subject,
    claim,
    kappa_invariant(grounded_claim),
    partial
) :-
    \+ map_kappa_invariant(Subject, grounded_claim).
map_domain_target_obligation_status(Subject, claim, grounded_claim, compiled) :-
    claim_fact(Subject, grounded_claim),
    !.
map_domain_target_obligation_status(Subject, claim, grounded_claim, partial) :-
    \+ claim_fact(Subject, grounded_claim).

map_domain_target_extension_term(
    report,
    Subject,
    claim,
    toy_next_obligation(Subject, add_grounded_claim)
) :-
    \+ claim_fact(Subject, grounded_claim).
map_domain_target_extension_term(
    frontier,
    Subject,
    claim,
    toy_next_obligation(Subject, add_grounded_claim)
) :-
    \+ claim_fact(Subject, grounded_claim).
map_domain_target_extension_term(
    admissible,
    Subject,
    claim,
    toy_next_obligation(Subject, add_grounded_claim)
) :-
    \+ claim_fact(Subject, grounded_claim).
map_domain_target_extension_term(
    outputs,
    Subject,
    claim,
    toy_proof(Subject, grounded_claim)
) :-
    map_domain_target_status(Subject, claim, compiled).
map_domain_target_extension_term(blocked, _Subject, claim, _Term) :-
    fail.
