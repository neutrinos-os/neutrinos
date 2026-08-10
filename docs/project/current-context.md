---
status: informative
last_updated: 2026-08-10
source_snapshot_revision: 0c7dc38
current_gate: G0-complete
target_gate: G1
active_plan: PLN-0000
---

# Current project context

> Maintained, non-normative, self-contained cold-context artifact. For a
> read-only status/orientation/report task, rely on this file and do not open
> any path it cites. Exception: open one authority explicitly named by the
> user. Before edits, acceptance, or a high-risk claim, verify only the
> governing source. A conflicting source wins; correct this summary.

## Current position

NeutrinOS has an accepted architecture-policy baseline and is preparing the G1
gate for one disposable VM-only evidence prototype. G1 is **not satisfied** and
NeutrinOS source implementation is **not authorized**.

PLN-0000 (`docs/plans/0000-pre-implementation-readiness.md`) is active only for
repository readiness, documentation, validation, and collaboration
scaffolding. EX-0016 passed at `c96fdbb`; PRE-012 and PRE-013 are satisfied for
the owner-approved Codex/Claude set. PRE-014 is satisfied and PRE-015 is active.
Its one next action is to implement the accepted `./check` interface and named
T0 registrations, then run its hostile probes and clean local profiles before
the initial CI check. Copilot remains unverified and must not be relied on for
autonomous repository work.

`docs/project/work-register.md` is the aggregate view. Question state lives in
`docs/project/decision-backlog.md`. Neither is architecture authority. Do not
open either for a cold status report.

## Accepted decisions relevant now

- The project name is **NeutrinOS** in prose, **`neutrinos`** in machine-facing
  identifiers, and **`neutrinos-os`** for the GitHub organization
  (`docs/project/naming.md`).
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
- Validation policy uses the stable `./check fast|complete|list|run` interface,
  applicable-suite semantics, offline/unprivileged/secret-free defaults, and
  explicit result, timeout, cleanup, and CI rules
  (`docs/project/validation-contract.md`). Its implementation is incomplete.
- PLN-0000's readiness model and fixture/defer classifications are accepted.
  PRE-001, PRE-002, and PRE-010 through PRE-014 are satisfied; PRE-018 and G1
  are not.

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

- documentation, repository guidance, validation scaffolding, and other
  readiness changes within active PLN-0000;
- read-only repository and host inspection when the specific task authorizes
  it; and
- documentation-only evaluation with synthetic inputs.

Currently prohibited:

- NeutrinOS source implementation or a reference-VM build under G1;
- mutation of `desktop-jason`, `router`, `misc`, or another physical host;
- use of production credentials, signing keys, enrollment state, recovery
  material, or machine authority;
- treating a candidate fixture, successful probe, or agent summary as an
  accepted decision; and
- autonomous push, merge, release, or publication.

The exact mutation-changing authority and stop conditions live in
`docs/plans/0000-pre-implementation-readiness.md`. Do not open it for a
read-only status report; the current boundary above is complete for that task.

## Working-tree and validation expectations

Assume a dirty worktree may contain user or another task's work. Before editing,
inspect it, preserve unrelated changes, and name them in the handoff.
Concurrent work requires explicit ownership and isolated worktrees under root
`AGENTS.md`.

Read-only task: do not run validation. Report only this requirement: after
documentation edits, run `git diff --check` and the internal Markdown-link
check; no output is a pass. Exact temporary commands:
`docs/project/validation.md`. They do not satisfy PRE-015.

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
