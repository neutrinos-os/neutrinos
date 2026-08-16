# Plans

Plans turn accepted requirements and open evidence questions into bounded work.
They are mutable execution records, not architectural authority.

Use a plan when work has a concrete outcome, ordered or dependent activities,
an exit condition, and a meaningful boundary around what it may change. Use the
[decision backlog](../project/decision-backlog.md) for unresolved questions, a
design for an argument, an ADR for a decision, a requirement for normative
behavior, and a research exercise for evidence.

## Status vocabulary

Plans use these statuses:

```text
proposed -> active -> complete
              |          |
              v          v
           blocked    superseded
              |
              v
           cancelled
```

- **proposed**: scoped for review; work is not yet authorized;
- **active**: its bounded work may proceed;
- **blocked**: a named dependency or decision prevents useful progress;
- **complete**: every exit criterion has evidence;
- **superseded**: replaced by a linked plan; and
- **cancelled**: deliberately stopped with rationale and retained results.

Task-level states are `pending`, `active`, `satisfied`, `blocked`, and
`deferred`. A deferred item names the later gate and an accepted rationale; it
is not silently treated as satisfied.

## Required plan fields

Every plan should declare:

- stable ID, title, status, owner, dates, and applicable phase gate;
- outcome, non-goals, mutation boundary, and retained evidence;
- linked decisions, requirements, risks, and research exercises;
- dependencies and explicit blocking versus deferred unknowns;
- ordered work with one accountable next action;
- failure, cleanup, interruption, and recovery behavior; and
- objective exit criteria.

Plans may reference candidate mechanisms for experiments. A candidate does not
become accepted merely because a plan uses it as a fixture.

## Relationship to issues and pull requests

Repository documents remain authoritative for decisions, requirements, gates,
plans, and evidence. GitHub issues or a project board may later mirror plan
tasks for assignment and day-to-day execution, using the plan/task and
DES/ADR/SYS/EX identifiers in their titles or fields.

Closing an issue does not accept a decision or satisfy a gate. The authoritative
repository record and its evidence must be updated in the same change or a
linked follow-up.

## Current plans

- [PLN-0000: pre-implementation readiness](0000-pre-implementation-readiness.md)
- [PLN-0001: reference-VM evidence slice](0001-reference-vm-slice.md)
- [PLN-0002: authenticated `/usr` artifact format comparison](0002-usr-artifact-format-spike.md)
- [PLN-0003: `/usr` read-workload comparison](0003-usr-read-workload-comparison.md)

Start new plans from the [plan template](template.md).
