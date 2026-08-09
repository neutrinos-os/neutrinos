# Architecture decision records

ADRs record decisions, not explorations. A design may result in several ADRs;
small decisions may need only an ADR if the alternatives and consequences fit
comfortably in the template.

Statuses are `proposed`, `accepted`, `rejected`, `deprecated`, and
`superseded`. Accepted ADRs remain historical records. Corrections may be
annotated, but changing a decision requires a new ADR with explicit
`supersedes` and `superseded_by` links.

## Index

| ADR | Status | Decision |
| --- | --- | --- |
| [ADR-0001](0001-systemd-first.md) | Accepted | Prefer systemd ecosystem mechanisms; require strong justification for overlapping alternatives. |
| [ADR-0002](0002-separate-authority-and-recovery.md) | Accepted | Separate routine, exceptional, machine, and data authorities while keeping recovery independently usable. |

Strong preferences from the design-session transcript remain stated directions
in the decision backlog until they are deliberately ratified.
