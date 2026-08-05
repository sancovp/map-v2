% Domain-neutral witness that MAP derives recursive relations PSC did not assert.

:- dynamic map_subject/2.
:- dynamic map_kappa_domain/2.
:- dynamic map_kappa_invariant/2.
:- dynamic candidate_goal/3.
:- dynamic candidate_step/4.
:- dynamic source_witness/3.

:- table derived_reachable/3.

map_domain_target_kind(typed_chain).
map_domain_target_subject(typed_chain, Subject) :-
    map_subject(typed_chain, Subject).

typed_chain_kappa_complete(Subject) :-
    map_kappa_domain(Subject, typed_relations),
    map_kappa_invariant(Subject, relational_closure),
    \+ (
        map_kappa_invariant(Subject, Other),
        Other \= relational_closure
    ).

derived_edge(Subject, From, To) :-
    candidate_step(Subject, Step, From, To),
    source_witness(Subject, Step, _Source).

derived_reachable(Subject, From, To) :-
    derived_edge(Subject, From, To).
derived_reachable(Subject, From, To) :-
    derived_edge(Subject, From, Through),
    derived_reachable(Subject, Through, To).

warranted_goal(Subject, Start, Goal) :-
    candidate_goal(Subject, Start, Goal),
    derived_reachable(Subject, Start, Goal).

map_domain_target_status(Subject, typed_chain, compiled) :-
    typed_chain_kappa_complete(Subject),
    warranted_goal(Subject, _Start, _Goal),
    !.
map_domain_target_status(Subject, typed_chain, partial) :-
    map_subject(typed_chain, Subject).

map_domain_target_obligation(
    _Subject,
    typed_chain,
    kappa_domain(typed_relations)
).
map_domain_target_obligation(
    _Subject,
    typed_chain,
    kappa_invariant(relational_closure)
).
map_domain_target_obligation(Subject, typed_chain, reachable_goal(Start, Goal)) :-
    candidate_goal(Subject, Start, Goal).

map_domain_target_obligation_status(
    Subject,
    typed_chain,
    kappa_domain(typed_relations),
    compiled
) :-
    map_kappa_domain(Subject, typed_relations),
    !.
map_domain_target_obligation_status(
    Subject,
    typed_chain,
    kappa_domain(typed_relations),
    partial
) :-
    \+ map_kappa_domain(Subject, typed_relations).
map_domain_target_obligation_status(
    Subject,
    typed_chain,
    kappa_invariant(relational_closure),
    compiled
) :-
    map_kappa_invariant(Subject, relational_closure),
    !.
map_domain_target_obligation_status(
    Subject,
    typed_chain,
    kappa_invariant(relational_closure),
    partial
) :-
    \+ map_kappa_invariant(Subject, relational_closure).
map_domain_target_obligation_status(
    Subject,
    typed_chain,
    reachable_goal(Start, Goal),
    compiled
) :-
    warranted_goal(Subject, Start, Goal),
    !.
map_domain_target_obligation_status(
    Subject,
    typed_chain,
    reachable_goal(Start, Goal),
    partial
) :-
    candidate_goal(Subject, Start, Goal),
    \+ warranted_goal(Subject, Start, Goal).

map_domain_target_extension_term(
    report,
    Subject,
    typed_chain,
    typed_chain_derived_reachable(Subject, From, To)
) :-
    derived_reachable(Subject, From, To).
map_domain_target_extension_term(
    frontier,
    Subject,
    typed_chain,
    typed_chain_missing_reachable_goal(Subject, Start, Goal)
) :-
    candidate_goal(Subject, Start, Goal),
    \+ warranted_goal(Subject, Start, Goal).
map_domain_target_extension_term(
    admissible,
    Subject,
    typed_chain,
    typed_chain_connect_goal(Subject, Start, Goal)
) :-
    candidate_goal(Subject, Start, Goal),
    \+ warranted_goal(Subject, Start, Goal).
map_domain_target_extension_term(
    outputs,
    Subject,
    typed_chain,
    typed_chain_proof(Subject, Start, Goal, relational_closure)
) :-
    map_domain_target_status(Subject, typed_chain, compiled),
    warranted_goal(Subject, Start, Goal).
map_domain_target_extension_term(blocked, _Subject, typed_chain, _Term) :-
    fail.
