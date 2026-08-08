% Consumer-owned categorical-ring pattern recognition fixture.

:- dynamic map_subject/2.
:- dynamic map_kappa_domain/2.
:- dynamic map_kappa_invariant/2.
:- dynamic candidate_pattern_ref/4.
:- dynamic candidate_occurrence_proposal/3.
:- dynamic candidate_role_binding/4.
:- dynamic source_snapshot/5.
:- dynamic source_entity_kind/5.
:- dynamic source_declared_capability/4.
:- dynamic source_accessed_capability/6.
:- dynamic source_coverage/5.

map_domain_target_kind(pattern_occurrence).
map_domain_target_subject(pattern_occurrence, Subject) :-
    map_subject(pattern_occurrence, Subject).

pattern_kappa_complete(Subject) :-
    map_kappa_domain(Subject, pattern_coherence),
    map_kappa_invariant(Subject, independent_observation),
    map_kappa_invariant(Subject, closed_world_coverage),
    \+ (
        map_kappa_invariant(Subject, Other),
        Other \= independent_observation,
        Other \= closed_world_coverage
    ).

proposal(Subject, Proposal) :-
    candidate_pattern_ref(Subject, categorical_ring, _Version, _SemanticHash),
    candidate_occurrence_proposal(Subject, Proposal, categorical_ring).

role_candidates(Subject, Proposal, Candidates) :-
    findall(
        Entity,
        candidate_role_binding(Subject, Proposal, ring_class, Entity),
        Candidates0
    ),
    sort(Candidates0, Candidates).

unique_ring_binding(Subject, Proposal, Ring) :-
    role_candidates(Subject, Proposal, [Ring]),
    source_snapshot(Subject, Snapshot, _Extractor, _Implementation, _Config),
    source_entity_kind(Subject, Snapshot, Ring, ring_class, _Evidence).

ring_leak(Subject, Proposal, Ring, Capability, Line, Evidence) :-
    unique_ring_binding(Subject, Proposal, Ring),
    source_snapshot(Subject, Snapshot, _Extractor, _Implementation, _Config),
    source_accessed_capability(
        Subject, Snapshot, Ring, Capability, Line, Evidence
    ),
    \+ source_declared_capability(Subject, Snapshot, Ring, Capability).

ring_coverage(Subject, Proposal, Ring, Coverage) :-
    unique_ring_binding(Subject, Proposal, Ring),
    source_snapshot(Subject, Snapshot, _Extractor, _Implementation, _Config),
    source_coverage(
        Subject, Snapshot, direct_self_attribute, Ring, Coverage
    ).

role_binding_status(Subject, Proposal, compiled) :-
    unique_ring_binding(Subject, Proposal, _Ring),
    !.
role_binding_status(Subject, Proposal, contradicted) :-
    role_candidates(Subject, Proposal, []),
    !.
role_binding_status(Subject, Proposal, partial) :-
    role_candidates(Subject, Proposal, Candidates),
    Candidates = [_,_|_].

alphabet_status(Subject, Proposal, contradicted) :-
    ring_leak(Subject, Proposal, _Ring, _Capability, _Line, _Evidence),
    !.
alphabet_status(Subject, Proposal, compiled) :-
    ring_coverage(Subject, Proposal, _Ring, complete),
    \+ ring_leak(Subject, Proposal, _LeakRing, _Capability, _Line, _Evidence),
    !.
alphabet_status(Subject, Proposal, partial) :-
    ring_coverage(Subject, Proposal, _Ring, partial),
    !.
alphabet_status(Subject, Proposal, partial) :-
    \+ unique_ring_binding(Subject, Proposal, _Ring).

map_domain_target_status(Subject, pattern_occurrence, contradicted) :-
    pattern_kappa_complete(Subject),
    proposal(Subject, Proposal),
    (
        role_binding_status(Subject, Proposal, contradicted)
    ;   alphabet_status(Subject, Proposal, contradicted)
    ),
    !.
map_domain_target_status(Subject, pattern_occurrence, compiled) :-
    pattern_kappa_complete(Subject),
    proposal(Subject, Proposal),
    role_binding_status(Subject, Proposal, compiled),
    alphabet_status(Subject, Proposal, compiled),
    !.
map_domain_target_status(Subject, pattern_occurrence, partial) :-
    map_subject(pattern_occurrence, Subject).

map_domain_target_obligation(
    Subject, pattern_occurrence, unique_role_binding(Proposal, ring_class)
) :-
    proposal(Subject, Proposal).
map_domain_target_obligation(
    Subject, pattern_occurrence, ring_alphabet_closed(Proposal)
) :-
    proposal(Subject, Proposal).

map_domain_target_obligation_status(
    Subject,
    pattern_occurrence,
    unique_role_binding(Proposal, ring_class),
    Status
) :-
    proposal(Subject, Proposal),
    role_binding_status(Subject, Proposal, Status).
map_domain_target_obligation_status(
    Subject,
    pattern_occurrence,
    ring_alphabet_closed(Proposal),
    Status
) :-
    proposal(Subject, Proposal),
    alphabet_status(Subject, Proposal, Status).

map_domain_target_extension_term(
    report,
    Subject,
    pattern_occurrence,
    pattern_bound_ring(Subject, Proposal, Ring)
) :-
    unique_ring_binding(Subject, Proposal, Ring).

map_domain_target_extension_term(
    frontier,
    Subject,
    pattern_occurrence,
    pattern_ambiguous_binding(Subject, Proposal, ring_class, Candidates)
) :-
    proposal(Subject, Proposal),
    role_candidates(Subject, Proposal, Candidates),
    Candidates = [_,_|_].
map_domain_target_extension_term(
    frontier,
    Subject,
    pattern_occurrence,
    incomplete_closed_world_scope(
        Subject, ring_alphabet_closed, Ring, direct_self_attribute
    )
) :-
    proposal(Subject, Proposal),
    ring_coverage(Subject, Proposal, Ring, partial),
    \+ ring_leak(Subject, Proposal, Ring, _Capability, _Line, _Evidence).

map_domain_target_extension_term(
    blocked,
    Subject,
    pattern_occurrence,
    pattern_constraint_contradicted(
        Subject,
        Proposal,
        ring_alphabet_closed,
        accessed_capability(Capability),
        missing_declaration(Capability),
        line(Line),
        evidence(Evidence)
    )
) :-
    proposal(Subject, Proposal),
    ring_leak(Subject, Proposal, _Ring, Capability, Line, Evidence).

map_domain_target_extension_term(
    admissible,
    Subject,
    pattern_occurrence,
    inspect_role_candidates(Subject, Proposal, ring_class)
) :-
    proposal(Subject, Proposal),
    role_binding_status(Subject, Proposal, partial).
map_domain_target_extension_term(
    admissible,
    Subject,
    pattern_occurrence,
    complete_observer_coverage(Subject, Ring, direct_self_attribute)
) :-
    proposal(Subject, Proposal),
    ring_coverage(Subject, Proposal, Ring, partial).

map_domain_target_extension_term(
    outputs,
    Subject,
    pattern_occurrence,
    pattern_occurrence_proof(
        Subject, Proposal, categorical_ring, ring_class(Ring), Snapshot
    )
) :-
    map_domain_target_status(Subject, pattern_occurrence, compiled),
    proposal(Subject, Proposal),
    unique_ring_binding(Subject, Proposal, Ring),
    source_snapshot(Subject, Snapshot, _Extractor, _Implementation, _Config).
