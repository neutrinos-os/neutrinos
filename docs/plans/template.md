---
id: PLN-NNNN
title: Short outcome-oriented title
status: proposed
owner: Unassigned
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
gate: Gx
depends_on: []
---

# Short outcome-oriented title

## Outcome

State the concrete result and the claim it will support.

## Non-goals

- Name nearby work that this plan will not absorb.

## Mutation and authority boundary

State which repository paths, build/test environments, machines, storage,
networks, identities, credentials, and external services this plan may read or
change. Explicitly prohibit production or physical-host effects that are not
authorized.

## Inputs and dependencies

| Input or dependency | Identity/status | Blocking behavior |
| --- | --- | --- |
| DES/ADR/SYS/EX or artifact | Accepted, candidate, or exact identity | Fail, stop for review, or named fallback |

## Decision and requirement trace

| ID | Applicability | Planned evidence |
| --- | --- | --- |
| SYS-NNN | Demonstrated, partial, not applicable, or deferred to Gx/EX-NNNN | Test, inspection, or retained record |

Candidate mechanisms used by the plan remain candidates unless a separate ADR
accepts them.

## Work

At most one task should normally be `active`.

| Task | Status | Depends on | Output/evidence | Next action |
| --- | --- | --- | --- | --- |
| PLN-NNNN-01 | pending | — | Named artifact or record | One concrete action |

## Failure, interruption, and cleanup

Describe stop conditions, partial-output handling, safe retry, cleanup,
retention, capacity limits, and any state that cannot be automatically removed.

## Risks and unknowns

| Risk or unknown | Effect | Disposition |
| --- | --- | --- |
| R-NNN or a bounded question | Claim or schedule affected | Block, test, accept, or defer to named gate |

## Exit criteria

1. Every task is satisfied, cancelled with rationale, or moved to a linked plan.
2. Every claimed requirement has retained evidence.
3. Native diagnostics and failure evidence are retained.
4. The work register and affected source records are updated.
5. Remaining unknowns are linked and assigned to a later gate or plan.

## Decision

Open for owner review. State exactly what accepting or activating this plan
would authorize and what it would not.
