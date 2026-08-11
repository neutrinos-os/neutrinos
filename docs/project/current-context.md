---
status: informative
last_updated: 2026-08-11
source_snapshot_revision: cc87b1d
current_gate: G1
target_gate: G2
active_plan: none (PLN-0001 complete 2026-08-11; no accepted successor)
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
on a hosted runner at `d0a2cc5`. Repeatability was then measured at `6ec625a`:
two independent green runs, `31420905770` and `31421167463`, both first-attempt
with no intervening fix, closing PR-0028 C-001.

PLN-0001-01 and PLN-0001-02 are complete. The slice declares its inputs in
bounded TOML validated by JSON Schema, and composes a bootable Fedora 44
deployment set unprivileged on `desktop-jason` with no host mutation, from a
single frozen repository enforced by mkosi's `LocalMirror`. The UKI, kernel,
initrd, package manifest, and the complete 7780-file tree are bit-identical
across builds. The disk image is not, and the cause is identified: the btrfs
chunk tree UUID is generated randomly and `mkfs.btrfs` offers no way to fix it,
so disk-image reproducibility is unreachable with a btrfs root regardless of
configuration. It is a goal, not a G1 requirement. An EROFS root would likely
be reproducible; that is a recorded hypothesis and not a reason to select
EROFS. See the [input declaration](slice-input-declaration.md) and
[composition record](slice-composition-record.md).

PLN-0001-03 is complete and **the artifact boots**: 26 targets reached, zero
failed units, virtual TPM found. It stopped at the interactive
`systemd-firstboot` prompt and never reached `multi-user.target`, so three
composition gaps were attributed back to PLN-0001-02 -- no first-boot
configuration, no kernel command line so no serial console, and no credential
or autologin. Booted under TCG: `/dev/kvm` is absent and loading `kvm-amd`
would mutate the build host. See the [boot record](slice-boot-record.md).

PLN-0001-04 is complete. The three gaps were **authorized by the owner and
fixed** in the composition fixture on 2026-08-10; the amendment changed
configuration only, leaving the package manifest and kernel digests and the
104-package closure unchanged. The machine now reaches `multi-user.target` with
no failed units, and **every identity it can report matches composition** --
kernel, systemd, distribution, command line, timezone, locale, hostname,
credentials -- with the UKI on its own ESP bit-identical to the composed
output. Three findings: the image carries **no package database**, so package
closure is not self-verifiable and rests on the builder's manifest alone; the
root filesystem is mounted `rw`, so **SYS-049 is not demonstrated** and the
plan's earlier read-only-root claim was never true -- owner-deferred to G2 on
2026-08-10, because the authenticated half needs a Verity substrate `S-004` has
not selected, a signature this slice has no authority to make, and a second
deployment to substitute; and systemd cannot use the
vTPM, because the tss2 runtime libraries are missing from the closure (systemd
itself is built `+TPM2`). A correction to PLN-0001-02's method is
recorded: `CleanPackageMetadata=auto` skips `directory` output, so the two
directory builds compared a tree that is not the shipped tree. See the
[identity report](slice-identity-report.md). mkosi and
Fedora remain candidate fixtures; one boot under emulation is not
qualification.

PLN-0001-05 is complete. Three slice tests are registered in the existing
runner: `T2-SLICE-001` validates the declared input set against its own schema
and reproduces the nine constructed rejections, closing the gap PLN-0001-01
recorded; `T3-SLICE-001` inspects the composed artifact and asserts the UKI on
the ESP is byte-identical to the composed UKI, which until now was a hand-made
claim; `T4-SLICE-001` boots the literal artifact under `snapshot=on` to a login
prompt whose hostname the harness supplied, with no failed units and the
artifact byte-identical afterwards, in 72 seconds under TCG. The runner gained
capability gating and `blocked` results, which it had no way to express. Two
consequences: `jsonschema` is now the repository's only runtime dependency, and
**`check:complete` fails with `blocked=1` unless `NEUTRINOS_SLICE_ARTIFACT_DIR`
names a composed artifact**, because composition needs the network and
canonical validation is offline. `check:fast` needs no artifact.

PLN-0001-06 is complete and produced the slice's first negative result. Seven
faults were injected, each into its own copy of `src/slice`; six failed closed
and named their responsible input, with the diagnostics recorded verbatim in the
[failure evidence](slice-failure-evidence.md). **The seventh did not fail.**
Replacing `LocalMirror=` with `Mirror=` in the composition fixture admitted
Fedora's `updates` repository -- which the declaration deliberately excludes as
inexact -- and built a complete artifact with 45 of its 104 packages from it.
`T3-SLICE-001` passed on that artifact. Two causes: no check asserts the
`LocalMirror=` construction is still present, and the retained manifest carries
no per-package repository attribution, so no check could verify sourcing even if
one wanted to. **SYS-059 is downgraded from demonstrated to partial and SYS-018
from demonstrated to partial; both were accepted at `Partial` by Jason
Tarasovic on 2026-08-11.** A second finding: the two mixed-branch faults fail closed on
Fedora's per-release GPG keys, not on anything in `src/slice` comparing an input
against its declaration -- an inherited guarantee, not an enforced one, and one
that does not survive a change of distribution. Two mitigations were proposed in
the evidence record and both were implemented on 2026-08-11; neither restores
SYS-059, because what the requirement asks for is per-package repository
attribution in the retained composition record and mkosi's manifest cannot
carry it.

PLN-0001-07 is complete and confirmed the identity claims while finding the
offline claim weaker than recorded. The artifact, both output directories, and
all six VM state directories were destroyed and the artifact rebuilt inside a
network namespace with loopback and nothing else, serving the declared
repository from a retained local copy. Every stable identity came back
byte-for-byte, the UKI read out of the reconstructed image's ESP matches the
standalone UKI, and trees extracted from two disk images compare **13240
entries with zero differences** -- which closes PLN-0001-04's correction that
the earlier comparison measured the composition process rather than the shipped
tree. `check:complete` `passing=10 failing=0` against the reconstructed
artifact, booting in 15.8 seconds. **Two findings.** Nothing in the fixture
retains the declared repository's metadata, so the first offline attempt could
not resolve at all and the retention had to be assembled by hand; **SYS-041 is
downgraded from demonstrated to partial in the plan trace and awaits owner
acceptance**, and only its acquisition half was exercised in any case. Second,
58 of the 179 RPMs in the shared package cache are not in the declared
repository -- `fc43` packages and `updates` builds left behind by PLN-0001-06's
injected faults -- so a cache shared across fault injection is not a retention
store. Nothing consumed them here. See the
[reconstruction record](slice-reconstruction-record.md).

Both findings, and the two F-RES-01 mitigations PLN-0001-06 had proposed, were
closed on 2026-08-11 at owner request. `compose.sh` now retains the declared
repository's metadata and the packages it resolved as a build step, into
`inputs/repository` under the build root, and **fails closed** on any package
that repository does not publish -- so retention is a check as well as a copy,
and the shared cache it used to draw from is out of the path. An offline
rebuild from that retention reproduced all four stable digests with one flag,
`--local-mirror=file://...`, and no assembled harness. Two tests were
registered: `T2-SLICE-002` asserts the composition mechanism still enforces the
declaration -- `LocalMirror=`, no `Mirror=` or `Repositories=`, matching branch,
and agreement of the values `compose.sh` duplicates -- and `T3-SLICE-002`
attributes every NEVRA in the shipped closure to the declared repository's own
published index, anchored to the declared `metadata_digest`. Both were verified
failure-sensitive, `T3-SLICE-002` against the exact `updates` package F-RES-01
admitted. `T4-SLICE-001` now records `accelerator_used`, read from the running
VM through QMP `query-kvm`, so a silent fallback to emulation is visible in the
evidence. `check:fast` is 8/0 and `check:complete` 12/0.

**None of this amends a requirement status.** SYS-018, SYS-059, and SYS-041
were **accepted at `Partial` by Jason Tarasovic on 2026-08-11**: the guards are
new, the measurements that produced the downgrades stand. SYS-018 cannot be
closed in a VM-only slice at all -- it needs a second role or machine -- and
SYS-059's gap is a limit of mkosi's manifest rather than of this configuration,
which makes it the first hard evidence bearing on mechanism selection and gives
it to `P-001`, `L-001`, and `L-004`. All three carry into G2 as inherited
obligations. The amendment to an approved gate's evidence basis is recorded as
post-acceptance evidence in [PR-0029](reviews/0029-g1-gate-approval.md); whether
G1's approval should be revisited against the corrected trace is left open
there. PLN-0001-08 is complete, and with it **all eight tasks of PLN-0001**. The
evidence bundle is retained outside the repository at
`~/.cache/neutrinos/slice/evidence/pln-0001-08/` -- 6310 KiB, 64 files, one
SHA-256 per file, scanned clean by canonical validation's own unsafe-output
patterns -- carrying the declaration, the mechanism, the resolved manifest, the
retention record, every output digest, three gzipped tree manifests, and both
profile runs in full. It carries no image: those are reconstructible from
declared inputs, and the commands that rebuild them are recorded instead. The
requirement trace is updated from planned to observed results. **Closing
measurement**: the shipped tree extracted from three separately produced disk
images -- the 2026-08-10 offline reconstruction, the 2026-08-11 networked
build, and the 2026-08-11 offline rebuild from retention -- is byte-identical
at 13240 entries with the same UKI on both ESPs. See the
[evidence bundle record](slice-evidence-bundle.md).

**S-004's scope half is decided.** On 2026-08-11 Jason Tarasovic accepted
DES-0006 C-013: the authenticated release artifact is **`/usr`**, not a
complete root. Configuration is delivered exclusively by dm-verity-signed
confexts under `image_policy_confext_strict` with mutable mode forbidden, and
the real `/etc` holds nothing durable, being regenerated at boot by
`systemd-tmpfiles` and `systemd-sysusers`. **No accepted requirement was
amended**: SYS-049 binds "release root content" without fixing its scope, and
both its evidence column and SYS-090 already treat configuration as a
deployment-set member distinct from root. SYS-123 now governs every confext.
Two things this does not settle: early-boot integrity, since the root
partition is unauthenticated state and anything read before `/usr` is verified
falls outside the boundary, and per-machine identity sourcing, which cannot
live in `/etc` and passes to L-003. The root *format* question (C-007, EROFS
versus ext4) stays open and is now measurable against the right artifact.
A side effect worth noting: the release artifact is no longer a disk image, so
the unreproducible btrfs and FAT bytes PLN-0001 identified move to state, where
reproducibility is not claimed -- a consequence of the decision, never a reason
for it.

**Two DES-0006 challenges are resolved**, both from RES-0014's review of
shipping A/B updaters, accepted by Jason Tarasovic on 2026-08-11 and now in the
design. C-014: the staging sequence
never marks the target slot ineligible before overwriting it, so on a second
update the retained eligible fallback becomes a partial image while still
selectable -- the outcome SYS-050 forbids, reached through ordinary operation.
C-015: the design carries only half of SYS-038, selecting a fallback on
exhaustion but never designing the "or stop with an attributable diagnosis"
half, so deployments that all fail assessment can alternate indefinitely.
Neither needs a requirement change. Two owner rulings on 2026-08-11 shaped
them, and neither accepts the amendments themselves. On C-014, durable
ineligibility targets surviving power loss, an unreadable ESP, **and** hostile
offline modification; surviving the first two is the accepted fallback, and
power loss alone is acceptable only with a recorded reason. On C-015, SYS-038
is read **narrowly** -- its bounded accounting governs each deployment's own
trial boots, not the cross-deployment loop -- so the loop breaker is a design
commitment beyond the requirement floor and must not be cited as satisfying
SYS-038. RES-0014 was extended with the terminal-state evidence behind it:
greenboot, MicroOS health-checker, Android Rescue Party, and ChromeOS converge
on stop selecting, keep running, be loud, and none halts the machine; MicroOS
additionally branches on whether the deployment was ever known-good, since a
previously-good deployment failing indicts the environment rather than the
image. A minimal ESP notification image was raised and rejected: it needs a
credential exactly when sealed state may be unavailable, and notification
belongs to the degraded running system. Both amendments are now in DES-0006:
C-014 as step 3 of "Staging and selection", C-015 as "When every eligible
deployment fails" in the same section, each with a failure-table row. The
spike inherits two cases from them -- the second-update overwrite of a retained
eligible fallback, and every eligible deployment failing assessment -- and owes
evidence on the strongest ineligibility durability level rather than the first
that works. Two questions are deliberately left unresolved: where the
exhaustion counter and known-good record live, given that state is what may be
damaged in the scenarios that trigger them, and what a machine running in an
unassessed condition is permitted to keep doing, router traffic in particular.

**C-008 is resolved and took the glossary with it**, accepted by Jason
Tarasovic on 2026-08-11. `/var` belongs to the machine-state volume, and every
remaining volume must name the custody, unlock, recovery, preservation, or
destruction difference that justifies it or be collapsed. Encryption scope was
never the question: `/usr` is public release content, dm-verity authenticated
and deliberately unencrypted, and `repart` cannot combine `Verity=` and
`Encrypt=` anyway. The actual defect was vocabulary -- C-013 left the word
**root** naming the superseded authenticated root, the new writable partition,
and the dm-verity root hash at once, and the glossary still defined only the
first. `root image` and `root slot` are retired in favor of release artifact
image and `/usr` slot, `root partition` is defined as the unauthenticated
writable filesystem holding the regenerated `/etc`, and bare **root** joins the
discouraged terms. Retained pre-amendment records and quoted upstream text keep
the old words; other designs still using `root image` generically are a
separate unswept surface. One question is recorded rather than absorbed:
whether the root partition needs to persist at all, since a tmpfs would leave
nothing durable outside the ESP and the named state volumes and would enforce
the "nothing durable in `/etc`" rule by construction, against ParticleOS's
persistent encrypted `btrfs` root with `/var` as a subvolume. It changes the
partition count, so it is a decision, not a detail.

**PLN-0001 is complete**, accepted by Jason Tarasovic on 2026-08-11 against
the exit-criteria assessment drafted in the plan, including its qualification
that criterion 5 is met for six of seven injected faults. One owner decision
stays open and is not taken by the drafter: whether G1's approval should be
revisited against the corrected trace.

A hygiene breach was found and closed alongside it.
`tools/validation/__pycache__/check.cpython-314.pyc` had been tracked since
`f54c217`, committed in the forty-minute window before `.gitignore` existed,
and survived twenty-six commits and the G1 review because the contract's
"no tracked binary artifact" bound was policy a reviewer applies and no
reviewer applied it. The file is untracked and `T0-HYG-001` now enforces both
artifact bounds against the index in both profiles, closing PR-0026 C-002.
**It is deliberately left in history**: `f54c217` is an ancestor of both
published refs, and rewriting would invalidate seven cited commit identities
including `6ec625a`, the commit G1 was approved at, and `874e9c7`, the source
revision `src/slice/input-set.toml` declares. `check:fast` is now 7/0.

**Open and unresolved: this makes the CI `check:complete` job fail.** The
workflow runs both profiles, and a hosted runner has no composed artifact, so
the three-way choice is CI composing the slice itself, CI running `fast` only
with `complete` becoming a local qualification profile, or accepting a red
`complete` in CI. Nothing has been pushed, so nothing is currently broken. The
choice is the owner's and belongs with `P-008`.

`P-009` is newly open and blocks nothing under G1: QEMU became the VM harness in
PLN-0001-03 without a comparison, so [RES-0013](../research/comparisons/vm-test-harness.md)
records one. QEMU alone offers a writable firmware varstore and a TCG fallback;
cloud-hypervisor and `test.thing` offer neither, and `test.thing` is
GPL-3.0-or-later, so its code cannot be copied into this Apache-2.0 repository.
Four of its techniques should still be adopted independently -- guest-driven
readiness over a notify vsock, SMBIOS Type 11 credentials, ssh over vsock with
ephemeral keys, and `snapshot=on` disposability. Three are now adopted; ssh
over vsock is the one held back, and for a reason recorded below. Two were measured working
under TCG against the literal pre-amendment artifact: `snapshot=on` leaves it
byte-identical, and SMBIOS credentials plus
`io.systemd.stub.kernel-cmdline-extra` take it from a blocking prompt to a
login prompt without changing a byte. **All three PLN-0001-04 composition
amendments are therefore unnecessary for reachability**. **Owner decision
2026-08-10: revert them, but not until KVM works**, so the revert and the move
to vsock ssh happen in one motion; where first-boot configuration belongs on a
physical host, which has no harness, remains an open `C-002`/`L-003` question.

**SVM was enabled in firmware setup on 2026-08-10 and the revert was executed.**
KVM is live -- `svm` present, `kvm_amd` loaded, QMP `query-kvm` reporting
`enabled` on the harness's own flag set -- and `T4-SLICE-001` runs at 18 seconds
against 72 under TCG with identical evidence fields. The six settings were
removed from the composition fixture and the rebuild reproduced the
pre-amendment UKI, initrd, kernel, and manifest digests **exactly**, which is
what establishes the amendment was the only difference. `check:complete` is
`passing=10 failing=0` against the reverted artifact.

**Notify-vsock readiness landed the same day.** `T4-SLICE-001` now waits for
`READY=1` from pid 1 over a vsock rather than for a `login:` string in the
serial log -- 13.2 seconds against 15.4, and a stronger claim, since a prompt
is a getty starting while `READY=1` is the boot transaction completing. The
hostname is read from `X_SYSTEMD_HOSTNAME`. It adds nothing to the image: the
guest side is stock systemd reading the `vmm.notify_socket` credential. Hosts
without `/dev/vhost-vsock` fall back to the serial marker and say so in
`readiness_source`.

Two things remain open and should not be read as closed. **ssh over vsock is
not done and is now a question rather than a task**: it needs `openssh-server`
in the image, which changes the closure and every pinned digest, and it is the
same shape as the amendment just reverted -- the artifact carrying something it
does not need so a test can drive it. Nothing currently depends on it. And the
retained `T4-SLICE-001` result still records `accelerator_requested` but not
which accelerator was obtained, so a silent fallback to TCG would report
passing; the vsock fallback deliberately does not have that defect.
`W-002` no longer blocks `P-009` on hardware grounds.

`P-008` is open and blocks nothing under G1: the required `canonical profiles`
check cannot report on an unpushed commit, so direct pushes to `main` are
rejected and `main` is pull-request-only in effect, and the only enabled merge
method replaces owner-signed commits with one signed by GitHub's `web-flow`
key. Work continues locally by owner decision; local `main` is ahead of the
remote and pull request 7 is open and green but unmerged. The four canonical tasks, Linux-x64 tool locks, failed invocations,
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
