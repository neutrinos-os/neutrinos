---
status: informative
last_updated: 2026-08-14
source_snapshot_revision: 1563152
current_gate: G1
target_gate: G2
active_plan: PLN-0002 (accepted 2026-08-11; PLN-0000 and PLN-0001 complete)
---

# Current project context

> Maintained, non-normative, self-contained cold-context artifact. For a
> read-only status/orientation/report task, rely on this file and do not open
> any path it cites. Exception: open one authority explicitly named by the
> user. Before edits, acceptance, or a high-risk claim, verify only the
> governing source. A conflicting source wins; correct this summary.

> This file is a summary and never the sole home of a decision, ruling,
> measurement, or next action. Anything recorded only here is a defect: the
> remedy is to write it where it belongs -- plan, design, backlog, record, or
> code -- and leave a pointer here. Two such items are open and named under
> [Awaiting the owner](#awaiting-the-owner).

## Gate and authority

- **G1 is approved** (2026-08-10, PR-0029), satisfying PRE-018 and completing
  PLN-0000 (`docs/plans/0000-pre-implementation-readiness.md`, `complete`).
  It authorizes disposable VM/lab implementation under an accepted follow-on
  plan and nothing else. It is a readiness gate, not a capability gate. Seven
  review challenges are carried open, not closed: PR-0026 C-003 and C-005,
  PR-0027 C-002 and C-006, PR-0028 C-002's residual class, C-003, and C-006.
- **PLN-0001 is complete**, accepted 2026-08-11 against its exit-criteria
  assessment, including the qualification that criterion 5 is met for six of
  seven injected faults. Its records are the input declaration, composition,
  boot, identity, failure-evidence, reconstruction, and evidence-bundle
  documents in this directory.
- **PLN-0002 is accepted** (2026-08-11, PR-0030) and is the **active plan and
  sole active implementation slice** (`docs/plans/0002-usr-artifact-format-spike.md`).
  PLN-0000's mutation boundary holds: G1 plus an accepted follow-on plan.
  Physical-host mutation, production authority, and any mechanism ADR remain
  unauthorized. No candidate fixture has become a decision.
- Requirement statuses inherited from PLN-0001 and carried into G2:
  **SYS-018, SYS-041, SYS-059 accepted at `Partial`** by Jason Tarasovic on
  2026-08-11; SYS-049 partial and not claimed on substitution alone. The
  amendment to G1's evidence basis is recorded as post-acceptance evidence in
  [PR-0029](reviews/0029-g1-gate-approval.md); **whether G1's approval should
  be revisited against the corrected trace is open and is the owner's.**

## Accepted design decisions that bound current work

Each is recorded in its design; the one-line summaries here are pointers, not
authority.

- **DES-0006 C-013** (2026-08-11): the authenticated release artifact is
  **`/usr`**, not a complete root; configuration is delivered exclusively by
  dm-verity-signed confexts; `/etc` holds nothing durable. No requirement was
  amended. Early-boot integrity and per-machine identity sourcing are
  explicitly not settled by it.
- **DES-0006 C-008** (2026-08-11): `/var` belongs to the machine-state volume,
  every remaining volume must justify itself, and the vocabulary is retired --
  `root image`/`root slot` become release artifact image and `/usr` slot, and
  bare **root** is discouraged. Whether the root partition needs to persist at
  all is recorded as open in DES-0006.
- **DES-0006 C-014 and C-015** (2026-08-11): durable ineligibility before a
  slot is overwritten, and a designed terminal state when every eligible
  deployment fails. C-015's loop breaker is a design commitment beyond SYS-038,
  which is read narrowly, and must not be cited as satisfying it.
- **DES-0005 confext lifecycle** (2026-08-11): a deployment variant resolves to
  a **set** of confexts split by disjoint path ownership; base compatibility is
  a guard, not an identity binding; failure policy is declared per confext in
  the fleet inventory; retention is a reference count. Confext build tooling,
  per-machine identity and secrets, and the actual path carve are left open.
- **DES-0006 C-007 is the open question PLN-0002 answers**: EROFS versus ext4
  for the `/usr` artifact, decided by measurement against verification item 2's
  eight criteria.

## PLN-0002 task state

Authority is the plan's task table. Summary as of 2026-08-14:

| Task | State |
| --- | --- |
| 01 early-boot spike | **complete**, stop-gate not triggered ([record](spike-early-boot-record.md)) |
| 02 `/usr`-only composition | **complete**, one defect found and fixed ([record](usr-artifact-composition.md)) |
| 03a confext build and `/etc` carve | **partial** in the plan text; its last owed item, signature enforcement, is closed by measurement ([carve record](etc-path-carve.md) question 7). The plan row is not yet updated |
| 03b confext delivery | pending; **sequenced after 06, before 07** (owner ruling 2026-08-12) |
| 04 disposable layout | **partial**; the confext partition is deliberately not placed, pending 03b |
| 05 parameter declaration | **accepted 2026-08-12** of a stated incomplete state; **fully implemented as of 2026-08-14** ([declaration](artifact-parameter-declaration.md)) |
| 06 four authenticated artifacts | **in progress**. The verity signature partition, a UKI signed by `CN=NeutrinOS image, synthetic`, and `systemd.image_policy=usr=signed` in the UKI have landed. The stated completion criterion -- build all artifacts, retain digests -- is **not met** |
| 07-09, 11-14 | pending |
| 10 negative evidence | **started out of order** on an owner ruling; one cell covered by `T4-CONFEXT-001` (confext substitution, signature dimension only) |

`06a`/`06b`/`06c`/`06d` are **not plan structure**; task 06 is undivided. The
labels were an agent decomposition and are retracted.

## Standing findings that govern current work

- **This plan's mechanisms fail open silently.** Six observed instances: lazy
  dm-verity booted a corrupt `/usr` normally; a refused confext reported
  `Finished` and left the machine unconfigured; an unenrolled confext signer
  merged anyway; the initrd replay's fail-closed guard covers the initrd merge
  only; a regenerated key sat beside an unrebuilt artifact; and an untrusted
  `/usr` verity signer does not stop the boot. **A successful boot is therefore
  not a statement about the artifact**, which is why tasks 09 and 10 carry the
  plan's weight rather than the positive boots.
- **`systemd.image_policy=usr=signed` is a structural predicate, not an
  enforcement mechanism.** It is satisfied by both enrollment arms, evaluated
  after the initrd already mounted `/usr`, and non-fatal. The declaration
  records the correction; it must not be cited as the mechanism that makes
  tasks 09 and 10 fail closed.
- **Upstream's `/usr` signature enforcement point is the TPM unseal, not the
  mount.** `systemd-veritysetup` retries without the signature and reports
  success; the outcome is measured into a PCR instead. Recorded as an open
  sub-question under `S-005` in the [backlog](decision-backlog.md), and out of
  PLN-0002's scope, which excludes TPM policy.
- **Confext signature enforcement is closed and registered.**
  `--image-policy=root=signed` applied as a unit drop-in admits the enrolled
  signer and refuses the valid-but-unenrolled one; `T4-CONFEXT-001` measures
  the 2x2 in a disposable VM with synthetic keys and is verified
  failure-sensitive.
- **Build determinism is closed properly as of 2026-08-14**, after a
  2026-08-12 closure that claimed more than it measured. The confext now
  reuses the composition's seed. **Any determinism evidence for this slice must
  state whether the confext was rebuilt** (`NEUTRINOS_SKIP_CONFEXT` skips it).
- **`Minimize=best` is unavailable on ext4**, so both arms hold
  `Minimize=guess` and **task 07 must measure filesystem bytes in use,
  reporting partition size separately**, or its size figure measures repart's
  estimator on one arm and the filesystem on the other.
- **Two systemd TPM units are masked from the host** in `T4-SLICE-001`
  (`systemd-tpm2-setup-early`, `systemd-pcrproduct`), because the artifact
  ships no `tpm2-pcr-public-key.pem` and supplying one is TPM policy. The mask
  travels in the check's own `masked_units` field. **Task 08's record must read
  "no failed units except the two masked"**, and whether the mask belongs in
  the PLN-0002-05 declaration is an owner question.
- **Retention is what has repeatedly made work possible**: the declared Fedora
  repository returned 403 for a day, and the slice composed offline from
  retained inputs rather than a declared URL being repointed. The repository is
  reachable again at the same revision as the retained copy. The tools closure
  is still declared by recipe rather than retained, recorded as an open
  sub-question under `L-002`.

## Validation state

- `mise run check:fast` runs **8 checks**; `mise run check:complete` runs
  **14** and is green, so `complete` can act as a gate. The counts are
  authoritative from `mise run check:list`.
- `check:complete` needs a composed artifact and the declared fixture
  directories. `mise run --allow-env=` passes those declarations through
  `sandbox.deny_env`; the three required variables are named in
  [validation](validation.md).
- Editing `tools/validation/` requires `check:complete`, not `check:fast`:
  every VM and fixture check is `complete`-only.
- `tools/validation/vm.py` is the single boot path for both Python checks. Its
  guards and the reasons for each are in the module itself.
  `src/spike/pln0002-01/boot.sh` is deliberately not migrated, being the
  recorded apparatus of a completed spike.
- **Open and unresolved: the CI `check:complete` job cannot pass on a hosted
  runner**, which has no composed artifact. Nothing is pushed, so nothing is
  red. **Explicitly punted 2026-08-12 by Jason Tarasovic** on the grounds that
  CI needs a full answer including how qualification runs a VM at all. It
  belongs with `P-008` and must be answered **before** the workflow's
  `complete` job runs anywhere.
- `P-009` (VM harness selection) is open and blocks nothing under G1; see
  [RES-0013](../research/comparisons/vm-test-harness.md). ssh over vsock is
  not done and is a question rather than a task: it would add
  `openssh-server` to the closure, which is the shape of the PLN-0001-04
  amendment that was reverted.
- `P-008` is open: the required `canonical profiles` check cannot report on an
  unpushed commit, and owner bypass is enabled as a deliberate temporary state.
  Work continues locally; local `main` is ahead of the remote. Copilot remains
  unverified and must not be relied on for autonomous repository work.
- `P-010` (record-corpus maintenance) is **deliberately left open until after
  G2**. Its accepted cost is a continuing rate of referential and
  duplicated-state failures, including acceptances that no mechanism guards.

## Awaiting the owner

Both items are owner rulings that this file was, until now, the only record of.
They are written into their authoritative homes; neither is settled.

1. **Six artifacts, not the plan's four.** Owner ruling 2026-08-12, reaffirmed
   2026-08-14: task 10's substitution source must differ from the primary,
   because the build is bit-reproducible and rebuilding the same tree yields an
   identical artifact, which would make the substitution vacuous. Ruled: build
   both a content variant and a seed variant per arm. Drafted as **PLN-0002
   amendment 5**, which changes accepted plan text and is not in force until
   accepted.
2. **The ruled command line is not the implemented one.** Owner ruling
   2026-08-12: adopt the ParticleOS shape -- `root=dissect`, `mount.usr=dissect`,
   a fully-enumerated `systemd.image_policy=`, `systemd.image_filter=`, and no
   `usrhash=`. What is implemented is `usr=signed` alone with `usrhash=`
   retained, and the parameter declaration argues that enumerating the verity
   designators is harmful. That argument is measured and correct on its own
   terms and was written without the ruling in view; the ruling was taken on
   the premise that an enumerated policy would enforce `/usr`'s signature,
   which the 2026-08-14 measurements show it cannot. Recorded as an open item
   in the [declaration](artifact-parameter-declaration.md). Until it is
   settled, the composition is in a state neither the ruling nor the
   declaration fully describes.

Also open and not taken by any agent: whether G1's approval should be revisited
against the corrected requirement trace.

## Next action

The remainder of **PLN-0002-06**: build the artifacts and retain their digests,
then retire the `out`/`out-ext4` output asymmetry. The artifact count depends on
item 1 above.

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
  Canary scanning and quarantine, the retained empty-cache acquisition-boundary
  probe, and the pinned least-privilege CI job running both profiles on a
  hosted runner are implemented. Bootstrap is an unfiltered acquisition phase
  bounded by pinned hash-checked locks, not by endpoint restriction, which the
  locked platform cannot enforce. Repository mise use does not select host-role
  software placement.
- PLN-0000's readiness model and fixture/defer classifications are accepted.
  PRE-001 through PRE-018 are satisfied and the plan is complete.

## Leading but unaccepted fixtures

These may support a bounded experiment. They are not permanent architecture:

- direct systemd/UAPI-oriented image composition, likely using mkosi, with
  bootc retained as the required deployment-substrate challenger;
- a declared Fedora stable package snapshot with a declared systemd overlay,
  with a literal Arch snapshot as the required package-ecosystem challenger;
- EROFS and ext4 as the two compared `/usr` candidates, and Btrfs mutable state
  for later evaluation; the exact storage layout, encryption, and recovery
  mechanism remain open;
- `systemd-sysinstall` as the leading installation mechanism;
- a general distribution kernel with a normal initrd for the first VM fixture;
  and
- an ordinary disposable VM as a test harness, not an accepted microVM product
  model or role.

PR-0029 C-005 is the standing risk for the duration of G1: mkosi, the Fedora
snapshot, EROFS, `systemd-sysinstall`, and the general distribution kernel are
used repeatedly and successfully, and repeated success is how a candidate
becomes a decision without an ADR. The test is whether the required challengers
-- bootc, a literal Arch snapshot -- are ever actually run.

PR-0030 C-006 is the standing risk inside PLN-0002: task 03a drew the first
confext path carve and built the first confext tooling, both marked candidate,
and that protection is procedural rather than structural until DES-0005 takes
the carve back.

W-002 microVM lifecycle, W-004 kernel specialization, and workstation, laptop,
router, server/storage, and guest role contracts remain open or explicitly
deferred to later gates. Do not encode their fixture shapes as permanent
architecture.

## Allowed and prohibited work

Currently allowed:

- NeutrinOS source implementation and reference-VM work within the bounded
  scope of active PLN-0002, under its named tasks, using disposable VM disks,
  firmware variables, virtual TPM state, and test networks;
- synthetic signing, enrollment, identity, and credential fixtures;
- build caches and artifacts in declared development locations;
- documentation, repository guidance, and validation scaffolding;
- read-only repository and host inspection when the specific task authorizes
  it; and
- documentation-only evaluation with synthetic inputs.

Currently prohibited:

- implementation outside PLN-0002's accepted task scope, or any work reaching
  for G2 qualification claims;
- mutation of `desktop-jason`, `router`, `misc`, or another physical host;
- use of production credentials, signing keys, enrollment state, recovery
  material, or machine authority;
- treating a candidate fixture, successful probe, or agent summary as an
  accepted decision; and
- autonomous push, merge, release, or publication.

The exact mutation-changing authority and stop conditions live in
`docs/plans/0000-pre-implementation-readiness.md` (mutation boundary, retained
after completion) and `docs/plans/0002-usr-artifact-format-spike.md` (task
scope and stop conditions). Do not open either for a read-only status report;
the current boundary above is complete for that task.

## Working-tree and validation expectations

Assume a dirty worktree may contain user or another task's work. Before editing,
inspect it, preserve unrelated changes, and name them in the handoff.
Concurrent work requires explicit ownership and isolated worktrees under root
`AGENTS.md`.

Read-only task: do not run validation. Report only this requirement: after
edits, run `mise run check:fast`; a successful terminal result is a pass. Edits
under `tools/validation/` require `mise run check:complete` instead. Bootstrap
and the additional canonical profiles are documented in
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

Keep it a summary. A measurement, ruling, or finding belongs in the plan,
design, backlog, record, or code that owns it; this file carries the pointer and
the current-position consequence. Narrative history of how a result was reached
belongs in the owning record, not here.

Set `source_snapshot_revision` to the source revision against which the summary
was checked. This names its inputs, not this file's containing commit, and may
therefore precede HEAD. EX-0016
(`docs/research/exercises/0016-agent-context-and-instruction-loading.md`) is
complete for the owner-approved Codex/Claude set; rerun it before expanding the
supported autonomous-client set or when instruction discovery materially
changes.
