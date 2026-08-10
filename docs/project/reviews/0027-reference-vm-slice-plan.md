---
id: PR-0027
subject: Reference-VM evidence slice plan
reviewer: Claude implementation pass
date: 2026-08-10
status: accepted
---

# Reference-VM evidence slice plan review

## Decision scope

This review examines [PLN-0001](../../plans/0001-reference-vm-slice.md): its
outcome, boundary, requirement trace, task decomposition, and stop conditions.

Accepting it supplies the accepted follow-on plan PLN-0000 requires, bounded
to this slice. It does not authorize NeutrinOS source implementation: PLN-0000
permits that only after G1 and only under such a plan, and this acceptance
satisfies the second condition alone. It accepts no mechanism, package
ecosystem, storage layout, or role definition, and does not satisfy PRE-018
or G1.

## Summary judgment

The plan states one narrow claim, keeps the fixture set candidate, and defers
the requirement families a booting VM would otherwise be tempted to claim.

Its weakest points are not in what it plans but in what it cannot yet size: no
task has been executed, so every duration, artifact size, and tool behavior in
it is an expectation. That is inherent to a first implementation plan and is
the reason the stop conditions matter more than the task list.

## Challenges

### C-001: This plan is accepted on an untested plan

- Severity: high
- Claim: PLN-0000 spent eighteen criteria establishing that nothing is
  authorized without evidence, and this plan is authorized with none. No task
  has run; the composition tool has never been invoked in this repository.
- Response: correct, and unavoidable. A plan that precedes first
  implementation cannot itself carry implementation evidence, or no first
  implementation is ever possible. The mitigation is bounded authority rather
  than proven authority, and the gate remains a second condition: the slice is VM-only, disposable, synthetic-credential
  only, and carries seven named stop conditions inherited from PLN-0000 plus
  seven risks of its own. A stop result is defined as evidence, not failure.
- Disposition: accepted as the intended function of the G1 gate.
- Residual risk: the task decomposition is an estimate. If `PLN-0001-02` finds
  that composition cannot express the deployment-set boundary, the plan's
  middle collapses and returns to design review. That is R-001, and it is the
  single most likely way this plan ends early.

### C-002: The requirement trace claims classification it has not tested

- Severity: high
- Claim: twelve requirements are marked demonstrated before any evidence
  exists. Marking a requirement demonstrated in a proposed plan is precisely
  the promotion of intent into claim that the repository forbids.
- Response: the column is `Planned evidence`, not evidence, and the plan states
  that a requirement moving from deferred to demonstrated requires updating the
  trace rather than an implementation quietly claiming it. Exit criterion 2
  requires every demonstrated or partial row to have retained evidence before
  the plan completes.
- Disposition: accepted as planned applicability, not as a claim.
- Residual risk: nothing mechanically distinguishes a planned row from an
  evidenced one. A reader of the table mid-plan can mistake intent for result.
  A status column per row would close this and is not present.

### C-003: Family-level deferral can hide an individual requirement

- Severity: medium
- Claim: rows such as "SYS-060 through SYS-064, SYS-068 through SYS-074" defer
  twelve requirements in one line. A requirement the slice does touch could sit
  inside a deferred family and never be examined.
- Response: PLN-0000 explicitly directed classification rather than copying all
  132 forward, and family grouping is how that direction was followed. The
  demonstrated and partial rows are individual; only deferrals are grouped.
- Disposition: accepted, with the boundary noted.
- Residual risk: a grouped deferral is coarser than the work it describes.
  `PLN-0001-08` updates the trace with observed results and is the point at
  which a mis-grouped requirement should surface.

### C-004: A new `src/` tree is authorized without a layout

- Severity: medium
- Claim: the boundary permits changes under "a new `src/` tree" that no
  accepted record describes. The hygiene contract's top-level table is closed
  and does not contain `src/`.
- Response: real gap. The table requires a named owner and lifecycle for any
  new top-level entry, and `PLN-0001-01` is the first task that would create
  one.
- Disposition: accepted with a required action: the first task that creates a
  top-level tree amends the hygiene table in the same commit.
- Residual risk: if that amendment is skipped, the contract silently describes
  a repository that no longer exists, which is PR-0026 C-001 recurring.

### C-005: Synthetic credentials in retained evidence

- Severity: medium
- Claim: the slice generates synthetic signing, enrollment, and credential
  fixtures and retains logs. Synthetic credentials in a retained log look
  exactly like real ones to a scanner and to a reader.
- Response: the plan routes retained evidence through the same output-safety
  path canonical validation uses, and states that synthetic credentials are
  still credentials in a log. `T0-SEC-001` covers the repository; evidence
  bundles live outside it and are covered by the runner's scanning and
  quarantine.
- Disposition: accepted.
- Residual risk: an evidence bundle retained outside both paths is unscanned.

### C-006: Nothing enforces VM-only

- Severity: high
- Claim: the prohibition on physical-host effects is documentation. An
  implementation error, not malice, is the realistic path to touching
  `desktop-jason`.
- Response: accurate and not resolved. The repository has no mechanism that
  prevents a task from writing outside its VM; the boundary is enforced by
  review and by the runner refusing to run as root.
- Disposition: accepted as a documented boundary without enforcement.
- Residual risk: the highest-consequence boundary in the plan is the least
  mechanically defended. A task that needs elevated privilege should be treated
  as a stop condition rather than a permission request.

## Probe observations

- PLN-0001 satisfies PRE-003 through PRE-009 by construction: each criterion
  names the follow-on plan as its evidence, and each has a corresponding
  section. This is coherence, not verification.
- G1 remains unsatisfied after this acceptance. PRE-017 has no CI run, and
  PRE-018 is unrecorded.
- The plan does not restate PLN-0000's mutation boundary as new authority; it
  inherits and narrows it, which keeps one authority rather than two.

## Required confirmations

- Accepting this supplies the follow-on plan only. Implementation additionally
  requires G1, which is unsatisfied.
- No mechanism, ecosystem, storage layout, or role is accepted by it.
- Demonstrated rows are planned applicability until `PLN-0001-08` records
  observed results.
- The first task creating a top-level tree amends the hygiene table with it.

## Owner decision

Accepted by Jason Tarasovic on 2026-08-10. PLN-0001 becomes active and
PRE-003 through PRE-009 are satisfied. C-004's required action is binding on
`PLN-0001-01`. C-002 and C-006 remain open and carry through execution.
