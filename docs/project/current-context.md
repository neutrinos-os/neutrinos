---
status: informative
last_updated: 2026-08-15
source_snapshot_revision: 6a75f20
current_gate: G1
target_gate: G2
active_plan: none (PLN-0000, PLN-0001, PLN-0002 complete; no implementation slice is authorized)
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
> code -- and leave a pointer here. One such item remains open and is named
> under [Awaiting the owner](#awaiting-the-owner).

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
- **PLN-0002 is complete**, accepted 2026-08-15 by Jason Tarasovic against its
  exit-criteria assessment, with two qualifications carried in that assessment:
  03a and 04 stay permanently partial, their remainders moved to `S-004`, and no
  registered check re-measures a figure the plan produced.
  (`docs/plans/0002-usr-artifact-format-spike.md`, `complete`.)
- **There is no active plan, and therefore no implementation authority.**
  PLN-0000's mutation boundary requires G1 *plus an accepted follow-on plan*, so
  NeutrinOS source and reference-VM work is unauthorized until another plan is
  accepted. Documentation, ADR, design, backlog and validation work is
  unaffected. Physical-host mutation, production authority, and any mechanism
  ADR remain unauthorized as before, and **no candidate fixture has become a
  decision**.
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

Authority is the plan's task table. Summary as of 2026-08-15:

| Task | State |
| --- | --- |
| 01 early-boot spike | **complete**, stop-gate not triggered ([record](spike-early-boot-record.md)) |
| 02 `/usr`-only composition | **complete**, one defect found and fixed ([record](usr-artifact-composition.md)) |
| 03a confext build and `/etc` carve | **partial permanently, nothing owed**: signature enforcement, its last owed item, is closed by measurement ([carve record](etc-path-carve.md) question 7); the general case left the plan with 03b on 2026-08-15. The carve, the tooling and the `/usr/lib/confexts` delivery path stay **candidate fixtures** handed back to DES-0005 |
| 03b confext delivery | **moved out of PLN-0002 by owner ruling 2026-08-15** (plan amendment 6). Where a separately delivered confext lives and when it is merged is now an open sub-question under `S-004` in the [backlog](decision-backlog.md), owned by DES-0005. Nothing in the plan depended on it and no measurement waited on it |
| 04 disposable layout | **partial permanently**; the unplaced confext partition moved out with 03b on 2026-08-15 and is part of the `S-004` sub-question. The four partitions it did place are fixtures, and one is measured wasteful: the Verity partition is 64 MiB fixed and **95% empty** on both arms |
| 05 parameter declaration | **accepted 2026-08-12** of a stated incomplete state; implemented in the composition and **audited against the built artifacts 2026-08-14**, which took three corrections; both of its open parameters were ruled the same day ([declaration](artifact-parameter-declaration.md)) |
| 06 six authenticated artifacts | **complete**, accepted 2026-08-14: six artifacts from one tree state, digests retained, command line uniform across the set, determinism re-measured with the confext rebuilt ([artifact set](usr-artifact-set.md)). The verity signature partition, a UKI signed by `CN=NeutrinOS image, synthetic`, and `systemd.image_policy=usr=signed` in the UKI landed earlier the same day |
| 07 offline measurements | **complete and accepted 2026-08-15**: five of C-007's eight criteria measured over the six artifacts ([measurements](artifact-format-measurements.md)). No recommendation; the five do not agree |
| 08 boot records | **complete and accepted 2026-08-15**: three boots per arm, both primaries. Boot behaviour and memory are a **tie** ([boot records](artifact-boot-records.md)) |
| 09 corruption behaviour | **complete and accepted 2026-08-15**: four injections, two targets per arm. The **first criterion to separate the arms** ([corruption records](artifact-corruption-records.md)) |
| 11 slice tests | **complete, accepted 2026-08-15**: the five hold on both arms; two checks added and one widened, each verified failure-sensitive, plus `T4-SLICE-003`/`T4-SLICE-004` registered **deferred** for task 10's signature fail-open ([check updates](slice-check-updates.md)). Both questions it raised are ruled 2026-08-15 -- registration belongs to the task that first needs the assertion enforced, and the fail-open owes a deferred registration rather than a check asserting the observed behaviour |
| 12 recovery disposition | **complete and accepted 2026-08-15**: format layer measured over eight injection sites -- a tie on file data, **ext4 ahead on metadata diagnosis**; system layer deferred to items 3 and 5; `crypttab` unsatisfiable because none exists in the artifact ([disposition](artifact-recovery-disposition.md)) |
| 13 C-007 recommendation | **complete and accepted 2026-08-15**, recommendation and weighing rule both: **EROFS, conditional on the update mechanism not being whole-image-only**, on image size as the one deciding criterion ([recommendation](artifact-format-recommendation.md)). **This does not accept EROFS** -- an ADR does that, and C-007 stays open |
| 14 evidence bundle and DES-0006 disposition | **complete and accepted 2026-08-15** ([bundle](artifact-evidence-bundle.md)): 9343 KiB across 130 files retained outside the repository, scan clean, both profile runs retained in full; the plan's requirement trace updated from planned evidence to observed results; DES-0006 disposition and the exit-criteria assessment accepted with it, including the qualifications on criteria 1 and 5. **It accepts no format**: C-007 stays open for an ADR |
| 10 negative evidence | **complete and accepted 2026-08-15**: seven cells per arm, 32 boots, both firmware states ([substitution records](artifact-substitution-records.md)). Image substitution fails **closed**; signature substitution fails **open**, enrolled or not. Identical on both arms |

`06a`/`06b`/`06c`/`06d` are **not plan structure**; task 06 is undivided. The
labels were an agent decomposition and are retracted.

## Standing findings that govern current work

- **This plan's mechanisms fail open silently.** Seven observed instances: lazy
  dm-verity booted a corrupt `/usr` normally; a refused confext reported
  `Finished` and left the machine unconfigured; an unenrolled confext signer
  merged anyway; the initrd replay's fail-closed guard covers the initrd merge
  only; a regenerated key sat beside an unrebuilt artifact; and an untrusted
  `/usr` verity signer does not stop the boot; and `fsck.erofs
  --extract=X --path=<file>` reports success and writes nothing, the first
  instance that is a measurement hazard rather than a boot one -- and **that
  last one is corrected in place as of 2026-08-15, not withdrawn**: PLN-0002-12
  re-measured the probe and the tool writes the content to the destination path
  itself, so that instance is a harness artifact; but the same tool fails open
  for real one field over, printing `<E> erofs: failed to verify superblock
  checksum` and **exiting 0**. Seven stands, with the seventh's evidence
  replaced. The correction is drafted, not taken, because the records carrying
  it are accepted; see the
  [disposition](artifact-recovery-disposition.md). **A successful
  boot is therefore
  not a statement about the artifact**, which is why tasks 09 and 10 carry the
  plan's weight rather than the positive boots. **Task 09 reproduced instance
  one on the accepted artifacts and on both arms**: four corrupted copies each
  booted to `running` with no failed units, and detection came at first read of
  the damaged block. That is a reproduction, not an eighth instance. **Task 10 carried the
  remaining weight and split it in two**: the *image* fails closed on every
  substitution measured, and the *signature* fails open on every one -- an
  eighth instance, and the first where the mechanism is configured, runs, and
  still gates nothing. A valid signature by the enrolled signer over a root hash
  the image does not carry boots to `running` with zero failed units. **The
  pattern is not confined to the artifact's mechanisms**: PLN-0002-11's
  injections caught two fail-opens in its own first drafts -- a signature check
  blind to the certificate embedded in the CMS blob, and an arm-symmetry check
  that would have permitted a compressing ext4 arm. Both were closed before the
  checks were registered, and neither is an instance of the count above; see the
  [check updates](slice-check-updates.md). The eighth instance is now carried by
  `T4-SLICE-003` and `T4-SLICE-004`, registered **deferred** against SYS-049's
  open sub-question under `S-005`, so it survives PLN-0002 closing.
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
  reuses the composition's seed. Re-measured during PLN-0002-06: the EROFS
  primary was rebuilt rather than carried forward and reproduced its prior
  digest exactly, **with the confext rebuilt**. **Any determinism evidence for
  this slice must state whether the confext was rebuilt**
  (`NEUTRINOS_SKIP_CONFEXT` skips it); `retain-artifact-digests.py` records it
  as a field. **Re-measured again in task 07: all six artifacts reproduced on
  all three rebuilds, 18 of 18, confext rebuilt on every run.** Determinism is
  a tie between the arms and separates nothing -- as are **boot time and
  memory**, measured in task 08: 22ms apart on a 6.2s boot and 1 MiB apart in
  page cache, both inside the run-to-run spread. Three of the eight criteria
  separate the arms not at all.
- **Corruption behaviour is the first criterion to separate the arms on a
  mechanism rather than a number**, measured in task 09. With readahead
  disabled, one flipped bit costs ext4 exactly one 4 KiB block and EROFS its
  physical cluster's logical span -- 4 blocks on data compressing to 25.43%,
  2 on already-compressed data, worst case 9 across the two target files'
  5,176 clusters. Two measurement findings outrank that ratio and both are in
  the [corruption records](artifact-corruption-records.md): a 4 KiB read still
  triggers readahead, so the first pass measured a non-reproducible 45 KiB
  against 16 KiB; and readahead on the dm device is 8 MiB, so a sequential
  reader fails at the last aligned boundary *before* the damage and discards
  up to 1.7 MB of intact data, identically on both arms. **Any later blast-radius
  claim must state whether readahead was disabled**, the same requirement the
  `Minimize` finding below imposes on any size claim.
- **`Minimize=best` is unavailable on ext4**, so both arms hold
  `Minimize=guess` and a partition-size figure measures repart's estimator on
  one arm and the filesystem on the other. Task 07 measured bytes in use
  accordingly, and the difference was not cosmetic: **partition size would have
  overstated EROFS's advantage by 56%** (2.57x against the real 1.65x). The
  estimator's margin lands inside the ext4 filesystem as free blocks, not in
  the partition outside it. Any later size claim carries the same requirement.
- **Two systemd TPM units are masked from the host** in `T4-SLICE-001`
  (`systemd-tpm2-setup-early`, `systemd-pcrproduct`), because the artifact
  ships no `tpm2-pcr-public-key.pem` and supplying one is TPM policy. The mask
  travels in the check's own `masked_units` field. **Task 08 ran under exactly
  that condition** and its record says so: no failed units on either arm, with
  the two masks named in the retained result. Whether the mask belongs in the
  PLN-0002-05 declaration is still an owner question. The **two primaries have
  now been booted** three times each, and task 09 booted four corrupted copies
  of them under the same masks with the same result; the four variants have not.
- **A declared parameter can be wrong rather than merely missing.** The
  2026-08-14 audit of PLN-0002-05 read the built artifacts instead of the
  configuration. Most of the declaration held: the ext4 superblock, the ESP
  volume ID, the four signing subjects and the initrd unit digests all verify.
  Three claims did not -- a superseded mkosi pin, an `orphan_file` feature that
  the journal removal precludes, and the initrd module list, which **ships 130
  modules against 21 declared** while eight of its entries select kernel
  builtins and three prefix-match whole subsystems. All are corrected in the
  [declaration](artifact-parameter-declaration.md). The pattern is this plan's
  usual one in a new place: a configuration that looks authoritative, produces
  no error, and does not describe the artifact.
- **Retention is what has repeatedly made work possible**: the declared Fedora
  repository returned 403 for a day, and the slice composed offline from
  retained inputs rather than a declared URL being repointed. The repository is
  reachable again at the same revision as the retained copy. The tools closure
  is still declared by recipe rather than retained, recorded as an open
  sub-question under `L-002`.

## Validation state

- `mise run check:fast` runs **8 checks**; `mise run check:complete` runs
  **16** as of PLN-0002-11, which registered `T3-SLICE-004` and `T4-SLICE-002`.
  Both profiles were re-run for PLN-0002-14 on 2026-08-15 against the EROFS
  primary of the PLN-0002-06 set -- `fast` 8 of 8, `complete` 16 of 16 with 2
  deferred -- and **both runs are retained in full in the PLN-0002-14 bundle**,
  so `complete` can still act as a gate and the run behind that claim survives
  the temporary directory it was written to. The counts are authoritative from
  `mise run check:list`.
- **18 tests are registered and 16 run.** `T4-SLICE-003` and `T4-SLICE-004` are
  registered `deferred` and are never selected, so they neither pass nor fail;
  `complete` reports them as `deferred=2` with their justification in the
  manifest's `omissions`. See [validation](validation.md#deferred-checks).
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
- **CI is red on `main` and stays red.** `check:complete` needs a composed
  artifact that a hosted runner does not have. This is expected until there is
  something to continuously integrate; it is not tracked, re-measured, or
  reported. `P-008` owns it.
- `P-009` (VM harness selection) is open and blocks nothing under G1; see
  [RES-0013](../research/comparisons/vm-test-harness.md). ssh over vsock is
  not done and is a question rather than a task: it would add
  `openssh-server` to the closure, which is the shape of the PLN-0001-04
  amendment that was reverted.
- `P-008` is open: owner bypass is enabled as a deliberate temporary state, so
  pushes to `main` land with the remote recording `Bypassed rule violations`.
  Copilot remains unverified and must not be relied on for autonomous
  repository work.
- `P-010` (record-corpus maintenance) is **deliberately left open until after
  G2**. Its accepted cost is a continuing rate of referential and
  duplicated-state failures, including acceptances that no mechanism guards.

## Awaiting the owner

**PLN-0002-14 was accepted 2026-08-15** -- bundle, requirement trace, DES-0006
disposition and exit-criteria assessment -- and **03b was moved out of the plan**
by the same ruling, so neither is open. What is left of the plan is whether it
is complete as a whole; see [Next action](#next-action). The two items below are
separate from that and predate it.

**Two items are open.** PLN-0002-13's recommendation and its weighing rule were
**accepted 2026-08-15** and are not among them; that acceptance did not accept
EROFS, and C-007 stays open for an ADR.

PLN-0002-12 was accepted 2026-08-15 -- the deferral of
the system layer is now an accepted amendment to verification item 2, and the
`crypttab` disposition stands -- but **one item was deliberately excluded from
that acceptance and is still the owner's**:

- **A correction to two accepted records.** `fsck.erofs --extract=X
  --path=<file>` writes to `X` itself and does not fail open; PLN-0002-07's
  seventh instance is a harness artifact, and its inspectability finding
  overstates the EROFS cost by describing a fallback that is not needed. The
  tools-reach half of that finding is unaffected, and the same tool does fail
  open one field over -- a corrupt superblock is detected, both CRCs printed,
  and the exit status is 0. See the
  [disposition](artifact-recovery-disposition.md). Correcting an accepted record
  is not a task's to take.

The second is the command-line item below. PLN-0002-07, PLN-0002-08, PLN-0002-09 and PLN-0002-10
were all accepted 2026-08-15, which completes every measurement task in the
plan; three further items were ruled on 2026-08-14 and are recorded
where they belong -- the six-artifact count as PLN-0002 amendment 5, and
`systemd.image_filter=` and the initrd module list in the
[declaration](artifact-parameter-declaration.md). They are not repeated here.

**The ruled command line is not the implemented one.** Owner ruling 2026-08-12:
adopt the ParticleOS shape -- `root=dissect`, `mount.usr=dissect`, a
fully-enumerated `systemd.image_policy=`, `systemd.image_filter=`, and no
`usrhash=`. What is implemented is `usr=signed` alone with `usrhash=` retained,
and the parameter declaration argues that enumerating the verity designators is
harmful. That argument is measured and correct on its own terms and was written
without the ruling in view; the ruling was taken on the premise that an
enumerated policy would enforce `/usr`'s signature, which the 2026-08-14
measurements show it cannot. Recorded as an open item in the
[declaration](artifact-parameter-declaration.md). **The six artifacts of
PLN-0002-06 carry the implemented value**, so settling this in the ruling's
favour would rebuild them and void anything measured against them first.

Also open and not taken by any agent: whether G1's approval should be revisited
against the corrected requirement trace.

## Next action

**Decide what the next plan is, or take C-007 to an ADR.** PLN-0002 is
**complete, accepted 2026-08-15**, and with it the last implementation
authority: there is no active plan, so no NeutrinOS source or reference-VM work
is authorized until another is accepted. Nothing is mid-flight -- every task row
is complete, accepted, or moved out, both canonical profiles are green, and the
evidence is retained.

The two natural candidates, neither selected:

- **An ADR on C-007**, which is what the recommendation exists for. It still
  needs four things and one of them is a measurement: verification item 9's
  workload read comparison, the one result that could reverse EROFS.
- **A plan for DES-0006 verification items 3, 4 and 5** -- A/B slots, staging,
  finalization, power loss, recovery -- which is where every uncovered C-001
  cell and the deferred system layer of the recovery criterion went.

Two qualifications ride with the plan's acceptance and are recorded in its
assessment rather than here: **03a and 04 stay partial permanently**, their
remainders having left with 03b; and **no check re-measures a figure**, so image
size, boot time and blast radius are retained measurements rather than enforced
invariants.

**The requirement trace now records one measured falsification.** SYS-049's
substitution clause holds for the image and the Verity tree -- eight cells, all
failing closed -- and **does not hold for the signature**, six cells, all
failing open. That is a gap in the requirement's satisfaction, carried in the
registry by two deferred checks, and not a missing measurement.

**PLN-0002-13 is complete and accepted 2026-08-15**, recommendation and weighing
rule both ([recommendation](artifact-format-recommendation.md)): **EROFS,
conditional on the update mechanism not being whole-image-only**. Deciding
criterion: **image size, 1.65x and 111.4 MiB per slot**, paid per machine for the
life of the deployment. Supporting: differential update transfer, 3.2x. The
condition is criterion 6's other half -- a whole-image updater ships **8% fewer
ext4 bytes on every update** -- so the recommendation is a trade of update
bandwidth for storage, and a fleet bound by bandwidth rather than storage decides
C-007 the other way on the same evidence. ext4 won four criteria and all are
low-weight under the accepted rule: three describe what an operator learns
*after* dm-verity has already refused the read. The raw tally is one criterion to
EROFS, four to ext4, three ties and one split; **the rule is what turns that into
the answer**, which is why it was accepted as a separate object.

**The acceptance does not accept EROFS**, and 14's DES-0006 disposition must not
record it as if it did. C-007 stays open until an ADR records a format; EROFS and
ext4 both remain candidate fixtures, and PR-0029 C-005's standing risk is
unchanged. What such an ADR would still need is listed in the recommendation:
the workload comparison, a selected updater, the command-line ruling, and a C-002
capacity budget.

**The strongest argument against the recommendation is an absence**, and the
acceptance does not discharge it. No workload was applied;
memory is a tie measured on an idle guest, and a wide read across `/usr` is
exactly where EROFS's decompression cost would land. That belongs to DES-0006
verification item 9 and should be measured before an ADR accepts EROFS. The
"selected by having been tried first" risk (PR-0029 C-005, PR-0030 C-006) is
answered on the record rather than noted: ext4 won or tied seven of nine rows,
including two results that contradict the naive prior -- the compressed format
ships more bytes on a whole-image update, and the uncompressed one builds
faster.

The two findings that outlive this plan are unchanged by 13, which counts
neither as C-007 evidence: the [substitution
records](artifact-substitution-records.md)' fail-open -- signature substitution
boots to `running` on every cell, enrolment changing which code path runs and no
outcome -- and the [check updates](slice-check-updates.md)' two deferred
registrations, which are what keeps that fail-open in the registry once PLN-0002
closes. Both are identical on the two arms.

**PLN-0002-03b has left the plan** (owner ruling 2026-08-15, amendment 6):
confext delivery is an open sub-question under `S-004`, owned by DES-0005, and
no task in PLN-0002 depended on it.

The synthetic signing material expires **2026-09-11**, after which these
artifacts are measured against expired enrollment material.

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

- documentation, repository guidance, ADR and design work, and validation
  scaffolding;
- read-only repository and host inspection when the specific task authorizes
  it;
- re-running the existing canonical validation profiles against retained
  artifacts, which is maintenance of what exists rather than new implementation;
  and
- documentation-only evaluation with synthetic inputs.

**No NeutrinOS source implementation or reference-VM work is currently
authorized.** PLN-0002 completed on 2026-08-15 and PLN-0000's boundary requires
G1 *plus an accepted follow-on plan*. Composition, VM boots, measurement runs,
and new fixtures need a new accepted plan first; the disposable-VM, synthetic-
material and declared-cache allowances above return with it.

Currently prohibited:

- NeutrinOS source implementation and reference-VM work of any kind, there
  being no active plan to bound it, and any work reaching for G2 qualification
  claims;
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
