---
id: PR-0029
subject: G1 gate approval and PRE-018
reviewer: Claude implementation pass
date: 2026-08-10
last_updated: 2026-08-11
status: accepted
---

# G1 gate approval review

## Decision scope

This review examines whether PLN-0000's G1 exit evidence is actually met and
what approving G1 does and does not authorize. It covers PRE-018, the five exit
conditions, and the open items the gate would carry forward.

It accepts no mechanism, no fixture, and no ADR, and it does not authorize any
mutation outside PLN-0000's permitted set.

## Summary judgment

The five G1 exit conditions are met on their own terms. PRE-001 through PRE-017
are satisfied with linked evidence, PLN-0001 is accepted, the work register
names it the sole active implementation slice, and both mutation boundaries are
written down.

The honest qualification is that this is a readiness gate, not a capability
gate. Nothing about G1 has been demonstrated by building anything. What has been
demonstrated is that the project can state what it is about to do, execute its
own checks, and refuse to let a fixture become a decision. Those are the right
preconditions, and they are not the same as evidence that the first slice will
work.

## Challenges

### C-001: PRE-018 is satisfied by the act of approving it

- Severity: medium
- Claim: PRE-018 reads "G1 approval is recorded explicitly," and its evidence is
  the recording of the approval. The criterion cannot fail. A checklist item
  that is satisfied by writing it down adds no constraint.
- Response: correct as a logical matter, and it is deliberate. PRE-018 exists to
  prevent the failure mode where the other seventeen criteria are quietly
  treated as sufficient and implementation begins without anyone deciding. Its
  content is not a test; it is a required, attributable, dated act by the sole
  acceptance authority. The constraint it supplies is that its absence blocks,
  not that its presence proves.
- Disposition: accepted as an authority record rather than an evidence
  criterion.
- Residual risk: none beyond the ordinary risk of a wrong decision, which no
  checklist removes.

### C-002: The gate rests on CI evidence that is one green run

- Severity: medium
- Claim: PRE-017 was satisfied on run `31418770417` at `d0a2cc5`, after four
  consecutive failures, all of which were defects in this repository. PR-0028
  C-001 records that repeatability is untested. G1 now depends on that evidence.
- Response: accurate and unchanged. The two commits carrying the PRE-017
  acceptance and the PATH hardening are committed locally and unpushed, so the
  first push after this gate is still the first repeatability test.
- Disposition: accepted; the weakness is recorded rather than resolved.
- Residual risk: a failure on that push is a defect in G1's evidence, not a
  regression. It would not invalidate the gate's authority record, but it would
  reopen PRE-017.

### C-003: Every criterion was satisfied within a single day

- Severity: low
- Claim: PRE-001 through PRE-017 were all accepted on 2026-08-10. No criterion
  has been exercised across time, across a machine other than one workstation
  and one hosted runner, or by any contributor other than the owner and its
  agents.
- Response: accurate. The readiness set was built and accepted in one pass by
  construction, because it is scaffolding rather than product. Its weakest
  criteria are those asserting properties of a collaboration that has not yet
  happened: PRE-012 and PRE-013 hold only for the owner-approved Codex/Claude
  set, and Copilot remains explicitly unverified.
- Disposition: accepted with the boundary stated.
- Residual risk: criteria describing multi-agent or multi-contributor behavior
  are untested predictions. Treat their first real use as evidence collection.

### C-004: G1 opens implementation while several review items remain open

- Severity: medium
- Claim: the carried-open set is not empty. PR-0026 C-003 (mise dispatch in a
  clean clone, pending an owner decision on `ALLOWED_RUNNER_ENVIRONMENT`),
  PR-0026 C-005 (`blocked` has counters but no producer), PR-0028 C-002's
  residual class (executables resolved from `PATH` rather than declared
  inputs), PR-0028 C-003 (public CI log disclosure bounded by scanner rules),
  PR-0028 C-006 (cold-cache path unexercised), and PR-0027 C-002 and C-006 all
  remain open. Approving G1 releases implementation work on top of them.
- Response: none of these is a gating defect for a disposable VM-only slice.
  Each concerns the validation harness's own fidelity or a bounded disclosure
  surface, not the mutation boundary and not any production authority. PR-0028
  C-002's class was narrowed structurally at `a00b4a6`: both known instances now
  build `PATH` from declared executables, so a new undeclared dependency fails
  on the workstation rather than surfacing later on a runner.
- Disposition: accepted as carried, not as closed.
- Residual risk: open harness defects degrade the trustworthiness of evidence
  collected under PLN-0001. They do not extend what PLN-0001 may mutate.

### C-005: Gate approval increases pressure to promote fixtures

- Severity: high
- Claim: until now no fixture could harden into a decision because nothing could
  be built. After G1, mkosi, a Fedora stable snapshot, EROFS/Btrfs,
  `systemd-sysinstall`, and a general distribution kernel will be used
  repeatedly and successfully. Repeated success is the exact mechanism by which
  a candidate becomes a de facto decision without an ADR.
- Response: this is the principal standing risk of the gate, and it is
  structural rather than avoidable. PLN-0001 R-003 names it and requires every
  record to restate candidate status. The required challengers — bootc for the
  substrate, a literal Arch snapshot for the package ecosystem — exist precisely
  so that the leading fixture must beat something rather than merely work.
- Disposition: accepted as the gate's dominant residual risk.
- Residual risk: high and continuous. The test is not whether the fixtures work;
  it is whether the challengers are ever actually run. If G2 arrives with no
  comparison executed, the mechanisms were selected by repetition.

## Probe observations

- PLN-0000 exit condition 1: PRE-001 through PRE-017 satisfied with linked
  evidence; PRE-018 is this record.
- Condition 2: PLN-0001 accepted 2026-08-10 following PR-0027; status `active`.
- Condition 3: the work register's reference-VM row names PLN-0001 the sole
  active implementation slice.
- Condition 4: PLN-0000 states the permitted and not-permitted sets; PLN-0001
  restates the VM-only boundary.
- Condition 5: recorded in PLN-0000's decision section and below.
- Local `main` is at `a00b4a6`, two commits ahead of the remote.

## Required confirmations

- G1 authorizes disposable VM/lab implementation under PLN-0001 only. It does
  not authorize physical-host mutation, production authority, or any ADR.
- PRE-018 records an authority act; it proves nothing on its own.
- The CI evidence underlying PRE-017 is a single green run.
- Seven review challenges remain open and are carried, not closed.
- No fixture named in PLN-0001 becomes a decision by being used.

## Owner decision

Accepted by Jason Tarasovic on 2026-08-10. G1 is satisfied and PRE-018 is
recorded. PLN-0000 is complete; PLN-0001 becomes the active plan. All seven
carried challenges remain open, with C-005 the standing risk to monitor for the
duration of G1.

## Post-acceptance evidence

Recorded 2026-08-11. Three requirement rows in PLN-0001's trace were
`Demonstrated` when this gate was approved and are now `Partial`, accepted as
such by Jason Tarasovic on 2026-08-11:

- **SYS-018** — failure attribution never identifies configuration scope, for
  the structural reason that the slice has one machine, one role, and no
  precedence conflict. Measured by PLN-0001-06.
- **SYS-059** — the undeclared-repository half was refuted by measurement, not
  merely unproven: a complete artifact was built from a repository the
  declaration excludes and passed every check the slice then had. Measured by
  PLN-0001-06. Two guards were added on 2026-08-11 and neither restores the
  requirement, because what it asks for is per-package repository attribution
  in the retained composition record, which mkosi's manifest cannot carry.
- **SYS-041** — only the acquisition half is exercised; the lifecycle control
  path has no path to test in this slice. Measured by PLN-0001-07.

This amends the evidence basis of an approved gate rather than the decision.
The gate's criteria are unchanged and none of the three was a G1 criterion; the
downgrades are carried into G2 as inherited obligations, and each names why it
cannot be closed in a VM-only slice. Whether that is sufficient, or whether G1's
approval should be revisited against the corrected trace, is an owner question
left open here rather than settled by the drafter.

C-005 is worth re-reading in this light. SYS-059's downgrade is the first hard
evidence bearing on mechanism selection -- it is a limit of mkosi's manifest,
not of this configuration -- and it belongs to `P-001`, `L-001`, and `L-004`
rather than to this gate.
