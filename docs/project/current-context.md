---
status: informative
last_updated: 2026-08-10
source_snapshot_revision: a00b4a6
current_gate: G1
target_gate: G2
active_plan: PLN-0001
---

# Current project context

> Maintained, non-normative, self-contained cold-context artifact. For a
> read-only status/orientation/report task, rely on this file and do not open
> any path it cites. Exception: open one authority explicitly named by the
> user. Before edits, acceptance, or a high-risk claim, verify only the
> governing source. A conflicting source wins; correct this summary.

## Current position

NeutrinOS has an accepted architecture-policy baseline and **G1 is satisfied**:
approved by Jason Tarasovic on 2026-08-10 following PR-0029, which also
satisfies PRE-018 and completes PLN-0000
(`docs/plans/0000-pre-implementation-readiness.md`, status `complete`).

NeutrinOS source implementation is now **authorized, and only** for the
disposable VM/lab scope of accepted PLN-0001
(`docs/plans/0001-reference-vm-slice.md`), which is the **active plan** and the
sole active implementation slice. Both conditions of PLN-0000's mutation
boundary — G1 plus an accepted follow-on plan — now hold. Physical-host
mutation, production authority, and any mechanism ADR remain unauthorized, and
no candidate fixture became a decision.

Readiness history: EX-0016 passed at `c96fdbb`; PRE-012 and PRE-013 are
satisfied for the owner-approved Codex/Claude set. PRE-017 is satisfied
following PR-0028: the tracked baseline, licence, and secret scanning are
committed, the remote was force-pushed over an unrelated 2022 history and moved
to a ruleset requiring the `canonical profiles` check, and both profiles passed
on a hosted runner at `d0a2cc5`. That is a single green run; repeatability is
untested. The four canonical tasks, Linux-x64 tool locks, failed invocations,
output-safety quarantine, named T0 checks, secret scanning, and registered
hostile, empty-cache, and clean-clone probes are implemented. Copilot remains
unverified and must not be relied on for autonomous repository work.

PR-0029 C-005 is the standing risk for the duration of G1: mkosi, the Fedora
snapshot, EROFS/Btrfs, `systemd-sysinstall`, and the general distribution
kernel will now be used repeatedly and successfully, and repeated success is
how a candidate becomes a decision without an ADR. The test is whether the
required challengers — bootc, a literal Arch snapshot — are ever actually run.

`docs/project/work-register.md` is the aggregate view. Question state lives in
`docs/project/decision-backlog.md`. Neither is architecture authority. Do not
open either for a cold status report.

## Accepted decisions relevant now

- The project name is **NeutrinOS** in prose, **`neutrinos`** in machine-facing
  identifiers, and **`neutrinos-os`** for the GitHub organization
  (`docs/project/naming.md`).
- The repository is licensed **Apache-2.0** and is **public**, resolving
  `P-007` (`docs/project/scope.md`). Public visibility limits nothing in scope:
  "not a public distribution" governs support and compatibility promises, not
  source visibility.
- NeutrinOS is systemd-first; an overlapping non-systemd mechanism carries a
  documented burden of proof (`docs/adrs/0001-systemd-first.md`, ADR-0001).
- Routine, exceptional, machine, and data authorities remain separate, with an
  independently usable recovery path
  (`docs/adrs/0002-separate-authority-and-recovery.md`, ADR-0002).
- Fleet intent uses bounded TOML records and exact native configuration, JSON
  Schema validation, and canonical JSON evidence
  (`docs/adrs/0003-bounded-fleet-intent-representation.md`, ADR-0003).
- Accepted system policy covers deployment lifecycle, configuration, storage
  boundaries, package inputs, supply-chain evidence, rollout, installation,
  credentials, Unix identity, and software-placement boundaries
  (`docs/requirements/system.md`). Exact mechanisms remain open where no ADR
  accepts them.
- Test policy uses the T0-through-T7 taxonomy, cross-cutting `T5@Tn` failure
  notation, exact requirements-to-test traces, and explicit claim boundaries
  (`docs/project/test-strategy.md`).
- Validation policy uses the canonical `mise run check:fast`, `check:complete`,
  `check:list`, and `check:run` tasks, with a locked Python 3.14/uv engine by
  default. Applicable-suite, offline/unprivileged/secret-free, result, timeout,
  cleanup, and CI rules are accepted (`docs/project/validation-contract.md`).
  The Linux-x64 task/runner/T0 slice, external XDG test cache, and registered
  environment, cache-boundary, network, timeout, interruption, output, and
  process-cleanup probes are implemented.
  Canary scanning and quarantine are accepted and implemented, as is the
  retained empty-cache acquisition-boundary probe. Bootstrap is an unfiltered
  acquisition phase bounded by pinned hash-checked locks, not by endpoint
  restriction, which the locked platform cannot enforce. Clean-clone profiles
  pass, and the pinned least-privilege CI job runs both profiles on a hosted
  runner. `T5-VAL-002` and `T5-VAL-003` now build `PATH` as a directory of
  symlinks to exactly the executables they declare, closing PR-0028 C-002 for
  both known instances: a system directory admits everything beside the tool
  that justified it, so an undeclared dependency resolves and the probe passes
  for a reason it never stated. Repository mise use does not select
  host-role software placement.
- PLN-0000's readiness model and fixture/defer classifications are accepted.
  PRE-001 through PRE-018 are satisfied and the plan is complete.
- **G1 is approved** (2026-08-10, PR-0029). It authorizes disposable VM/lab
  implementation under PLN-0001 and nothing else. PRE-018 records an authority
  act rather than evidence; the gate is a readiness gate, not a capability
  gate. Seven review challenges are carried open, not closed: PR-0026 C-003 and
  C-005, PR-0027 C-002 and C-006, PR-0028 C-002's residual class, C-003, and
  C-006.

## Leading but unaccepted fixtures

These may support a bounded experiment. They are not permanent architecture:

- direct systemd/UAPI-oriented image composition, likely using mkosi, with
  bootc retained as the required deployment-substrate challenger;
- a declared Fedora stable package snapshot, with a literal Arch snapshot as
  the required package-ecosystem challenger;
- an EROFS root and Btrfs mutable state for later evaluation; the exact storage
  layout, encryption, and recovery mechanism remain open;
- `systemd-sysinstall` as the leading installation mechanism;
- a general distribution kernel with a normal initrd for the first VM fixture;
  and
- an ordinary disposable VM as a test harness, not an accepted microVM product
  model or role.

W-002 microVM lifecycle, W-004 kernel specialization, and workstation, laptop,
router, server/storage, and guest role contracts remain open or explicitly
deferred to later gates. Do not encode their fixture shapes as permanent
architecture.

## Allowed and prohibited work

Currently allowed:

- NeutrinOS source implementation and reference-VM work within the bounded
  scope of active PLN-0001, under its named tasks, using disposable VM disks,
  firmware variables, virtual TPM state, and test networks;
- synthetic signing, enrollment, identity, and credential fixtures;
- build caches and artifacts in declared development locations;
- documentation, repository guidance, and validation scaffolding;
- read-only repository and host inspection when the specific task authorizes
  it; and
- documentation-only evaluation with synthetic inputs.

Currently prohibited:

- implementation outside PLN-0001's accepted task scope, or any work reaching
  for G2 qualification claims;
- mutation of `desktop-jason`, `router`, `misc`, or another physical host;
- use of production credentials, signing keys, enrollment state, recovery
  material, or machine authority;
- treating a candidate fixture, successful probe, or agent summary as an
  accepted decision; and
- autonomous push, merge, release, or publication.

The exact mutation-changing authority and stop conditions live in
`docs/plans/0000-pre-implementation-readiness.md` (mutation boundary, retained
after completion) and `docs/plans/0001-reference-vm-slice.md` (task scope and
stop conditions). Do not open either for a
read-only status report; the current boundary above is complete for that task.

## Working-tree and validation expectations

Assume a dirty worktree may contain user or another task's work. Before editing,
inspect it, preserve unrelated changes, and name them in the handoff.
Concurrent work requires explicit ownership and isolated worktrees under root
`AGENTS.md`.

Read-only task: do not run validation. Report only this requirement: after
edits, run `mise run check:fast`; a successful terminal result is a pass.
Bootstrap and the additional canonical profiles are documented in
`docs/project/validation.md`. PRE-015 is satisfied; a passing run is not by
itself G1 or qualification evidence.

## Context path for a fresh task

1. Read root `AGENTS.md`.
2. Read this file.
3. Read-only status/orientation/report: hard stop. Cite paths from this file
   without opening them. Open only one authority explicitly named by the user.
4. Execution/edit: read only the active-plan sections and sources governing the
   exact change or risk.
5. Aggregate analysis: `docs/project/work-register.md` on demand.
6. History/provenance only: `docs/background/design-session-summary.md`, then
   the transcript only if necessary.

## Maintenance and verification

Update this file whenever any of the following changes:

- the active gate or active plan;
- an accepted, rejected, superseded, or reopened decision relevant to current
  work;
- a leading mechanism or experimental fixture relevant to current work;
- the allowed or prohibited mutation boundary;
- the canonical validation commands; or
- the one next action.

Set `source_snapshot_revision` to the source revision against which the summary
was checked. This names its inputs, not this file's containing commit, and may
therefore precede HEAD. EX-0016
(`docs/research/exercises/0016-agent-context-and-instruction-loading.md`) is
complete for the owner-approved Codex/Claude set; rerun it before expanding the
supported autonomous-client set or when instruction discovery materially
changes.
