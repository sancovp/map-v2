% Independent MAP v2 report kernel.
%
% A domain owns semantics by implementing:
%   map_domain_target_kind/1
%   map_domain_target_subject/2
%   map_domain_target_status/3
%   map_domain_target_obligation/3
%   map_domain_target_obligation_status/4
%   map_domain_target_extension_term/4

:- initialization(main, main).

emit_term(Term) :-
    write_term(Term, [quoted(true), numbervars(true)]),
    write('.'),
    nl.

emit_unique(Template, Goal) :-
    findall(Template, Goal, Terms0),
    list_to_set(Terms0, Terms),
    forall(member(Term, Terms), emit_term(Term)).

emit_extensions(Mode, Subject, Target) :-
    emit_unique(
        Term,
        map_domain_target_extension_term(Mode, Subject, Target, Term)
    ).

emit_base_report(Subject, Target) :-
    emit_term(map_target_report(Subject, Target)),
    map_domain_target_status(Subject, Target, Status),
    emit_term(map_target_status(Subject, Target, Status)),
    emit_unique(
        map_target_obligation(Subject, Target, Obligation, ObligationStatus),
        (
            map_domain_target_obligation(Subject, Target, Obligation),
            map_domain_target_obligation_status(
                Subject,
                Target,
                Obligation,
                ObligationStatus
            )
        )
    ).

emit_mode(report, Subject, Target) :-
    emit_base_report(Subject, Target),
    emit_extensions(report, Subject, Target).
emit_mode(frontier, Subject, Target) :-
    emit_term(map_target_frontier_report(Subject, Target)),
    emit_unique(
        map_target_frontier(Subject, Target, Obligation, Status),
        (
            map_domain_target_obligation(Subject, Target, Obligation),
            map_domain_target_obligation_status(Subject, Target, Obligation, Status),
            Status \= compiled
        )
    ),
    emit_extensions(frontier, Subject, Target).
emit_mode(blocked, Subject, Target) :-
    emit_term(map_target_blocked_report(Subject, Target)),
    emit_unique(
        map_target_blocked(Subject, Target, Obligation, Status),
        (
            map_domain_target_obligation(Subject, Target, Obligation),
            map_domain_target_obligation_status(Subject, Target, Obligation, Status),
            Status = contradicted
        )
    ),
    emit_extensions(blocked, Subject, Target).
emit_mode(admissible, Subject, Target) :-
    emit_term(map_target_admissible_report(Subject, Target)),
    emit_unique(
        map_target_admissible(Subject, Target, Obligation),
        (
            map_domain_target_obligation(Subject, Target, Obligation),
            map_domain_target_obligation_status(Subject, Target, Obligation, partial)
        )
    ),
    emit_extensions(admissible, Subject, Target).
emit_mode(outputs, Subject, Target) :-
    emit_term(map_target_outputs_report(Subject, Target)),
    emit_extensions(outputs, Subject, Target).

main(Argv) :-
    (   Argv = [DomainPath, WorkspacePath, Subject, Target, Mode]
    ->  load_files(DomainPath, [silent(true)]),
        load_files(WorkspacePath, [silent(true)]),
        map_domain_target_kind(Target),
        map_domain_target_subject(Target, Subject),
        emit_mode(Mode, Subject, Target)
    ;   throw(error(domain_error(map_runtime_arguments, Argv), _))
    ).
