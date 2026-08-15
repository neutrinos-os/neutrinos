---
status: accepted
last_updated: 2026-08-15
governing_plan: PLN-0002
task: PLN-0002-13
accepted_by: Jason Tarasovic
accepted: 2026-08-15
---

# C-007 recommendation: the `/usr` artifact format

PLN-0002-13. **DES-0006 C-007 asks whether EROFS materially outperforms or
simplifies ext4+dm-verity for actual NeutrinOS `/usr` images. This is the
recommendation, its evidence, the weighing rule that produced it, and its
threats.**

**Drafted for owner decision under PLN-0002 exit criterion 6, which requires the
drafter not to accept it. Accepted 2026-08-15 by Jason Tarasovic**, both the
recommendation and the [weighing rule](#the-weighing-rule) that produced it,
which were offered for separate acceptance and were both taken.

**The acceptance does not accept EROFS.** A format is accepted by an ADR; what
is accepted here is that this is the recommendation C-007 gets, on this
evidence, under this rule. C-007 stays open, and [what an ADR would still
need](#what-an-adr-would-still-need) is unchanged by the acceptance -- in
particular threat 1, the unmeasured workload, which the acceptance does not
discharge.

**Recommendation: EROFS, conditionally.** The condition is the update mechanism,
which is not selected and which reverses one criterion depending on its shape.
Full statement in [The recommendation](#the-recommendation).

Nothing new is measured here. Every figure is carried from the six accepted
records named in the tally, all of which were accepted 2026-08-15 or earlier.

## The tally

Verification item 2's eight criteria, plus the recovery disposition it names
alongside them.

| # | Criterion | Result | Magnitude | Weight |
| --- | --- | --- | --- | --- |
| 1 | Image size | **EROFS** | 171.0 vs 282.4 MiB in use, **1.65x**, 111.4 MiB per slot | **high** |
| 2 | Build wall time | ext4 | 46.65s vs 52.87s median, 6.2s, 13% | low |
| 3 | Build determinism | **tie** | 18 of 18 reproduced, both arms | none |
| 4 | Boot behaviour | **tie** | 22ms on a 6.2s boot, inside the spread | none |
| 5 | Memory | **tie** | ~1 MiB page cache of 1948.6 MiB, idle | none |
| 6 | Update transfer size | **split** | whole-image ext4 by 8%; differential EROFS by **3.2x** | **conditional** |
| 7 | Inspectability | ext4 | tooling reach, not image property | low |
| 8 | Corruption behaviour | ext4 | 1 block vs 2-9 blocks per flipped bit | low |
| — | Recovery behaviour | ext4, narrowly | metadata diagnosis; ties on the other three sub-questions | low |

Sources, in order: [measurements](artifact-format-measurements.md) for 1, 2, 3,
6 and 7; [boot records](artifact-boot-records.md) for 4 and 5; [corruption
records](artifact-corruption-records.md) for 8; [recovery
disposition](artifact-recovery-disposition.md) for recovery; [substitution
records](artifact-substitution-records.md), which measured nothing that
separates the arms and is treated as such below.

**Counting the rows gives ext4 four criteria to EROFS's one.** That count is not
the answer and no criterion decides C-007 alone -- the plan's own non-goal and
the owner ruling of 2026-08-11. The weighing rule below is what turns nine rows
into a recommendation, and it is stated before the recommendation so it can be
rejected independently of it.

## The weighing rule

Proposed by this record and **accepted 2026-08-15 by Jason Tarasovic**, as a
rule for weighing C-007's criteria and not beyond it. It was offered for
acceptance, rejection, or replacement separately from the recommendation,
because under a different rule the tally above supports a different answer; the
acceptance is of this rule and therefore of that answer.

1. **A criterion measured at or near the noise floor decides nothing, whatever
   its sign.** Boot behaviour, memory and determinism came back inside their own
   run-to-run spread. Build time is 6.2s on a developer workstation, paid by no
   machine in the fleet.
2. **A criterion whose consequence is already neutralized by an accepted
   mechanism carries little weight.** Under dm-verity no damaged block is ever
   served on either arm, and the answer to a damaged `/usr` is redeployment, not
   repair -- the recovery disposition measures that an authenticated artifact has
   no in-place repair path at all. Blast radius, metadata diagnosability, and
   repairability all describe what an operator learns *after* the mechanism has
   already refused the read.
3. **A criterion whose magnitude is large and whose cost recurs per machine or
   per update carries the most weight.** Image size is paid on every machine, in
   every slot, for the life of the deployment. Transfer size is paid on every
   machine on every update.
4. **A split criterion is conditional on an unmade decision and is recorded as a
   condition, not resolved by picking the half that suits.**

Rules 1 and 2 remove five of the nine rows. Rule 3 leaves image size and update
transfer. Rule 4 makes the second of those a condition rather than a result.

## The recommendation

**Recommend EROFS as the `/usr` artifact format, conditional on the update
mechanism not being whole-image-only.**

**What decided it.** One criterion survives the weighing rule unconditionally:
**image size, 1.65x and 111.4 MiB per slot**, paid per machine, per slot, for the
life of the deployment. Under an A/B layout that is 222.8 MiB of every machine's
storage. It is the largest unconditional magnitude in the comparison by an order
of magnitude over anything ext4 won.

**What supports it.** The **differential half of update transfer**, which is
also large -- 3.2x fewer bytes for a realistic content change, and 4 KiB against
16.3 MiB for an identity-only rebuild -- and points the same way. It is support
rather than a decider because it is conditional.

**What was weighed and did not decide it.** Build time, inspectability,
corruption blast radius and metadata diagnosability, all to ext4, none of them
large and three of them describing consequences that arrive after dm-verity has
refused the read. They are not dismissed; they are the reason this
recommendation is stated as a weighing rather than a result.

**What was inconclusive.** Determinism, boot behaviour and memory are ties in
fact -- three criteria that separate the formats not at all, plus substitution
behaviour, which is not a C-007 criterion and was identical on both arms down to
the wording of the diagnostics. Update transfer is inconclusive in a different
sense: it is split against itself and its resolution belongs to a decision no
plan has made.

**The condition, stated so it can be checked later.** If the selected updater
ships whole `/usr` partitions -- the shape `systemd-sysupdate` has today -- ext4
ships **8% fewer bytes on every update, forever**: 128.2 MiB against 140.0 MiB
at zstd level 19. That is a recurring per-machine per-update cost under rule 3,
on the same footing as image size, and it is the one place ext4's advantage is
operational rather than diagnostic. It does not overturn the recommendation --
111.4 MiB of standing storage against 11.8 MiB per update transfer is not close
per event, and a machine updates far less often than it stores -- but the owner
should know that **the honest form of this recommendation is a trade of update
bandwidth for storage**, and that a fleet whose binding constraint turns out to
be bandwidth rather than storage would decide C-007 the other way on the same
evidence.

**What this recommendation does not say.** It does not say EROFS is faster, uses
less memory, boots better, is more reliable under corruption, or is easier to
diagnose. Four of those are measured ties and the other two measured against it.
It says EROFS is materially **smaller**, which is what C-007 asked first, and
that nothing measured against it is large enough to outweigh that under the
stated rule.

## Was it selected by having been tried first?

DES-0006 verification item 2 exists because of exactly this failure mode:
"absent that, EROFS would be selected by having been tried first". PR-0029 C-005
carries it as a standing risk and PR-0030 C-006 repeats it inside this plan.
Recommending EROFS is the outcome that risk predicts, so the defence has to be
on the record.

**The comparison discriminated.** ext4 was built as a full arm, booted, and
measured on all eight criteria, and it **won or tied seven of the nine rows**.
An arm that existed only to lose does not do that. The two results that most
plainly contradict the naive prior are ext4's: the compressed format ships
*more* bytes on a whole-image update, and the format with no compression is the
one that builds faster.

**Two of this plan's measurements were corrected against the prior rather than
toward it.** Reporting partition size would have handed EROFS a 2.57x advantage;
measuring bytes in use cut it to 1.65x. The first corruption pass credited ext4
with a 3x blast-radius advantage that turned out to be readahead; disabling it
moved the figure to a smaller one, against EROFS in the same direction but by a
reproducible amount rather than a system artifact.

**What the defence does not cover.** No workload was run. See the first threat
below; it is the one place where "tried first" could still be operating, because
the criterion that would most plausibly favour ext4 was not measured at all.

## Threats to this finding

1. **No workload was applied, and that is where EROFS would be expected to
   lose.** Memory is a tie measured on an idle guest 20 seconds after boot, which
   has read only what booting read. EROFS pays its compression cost on *read*, in
   decompression time and in cache holding decompressed pages. A workload that
   reads widely across `/usr` is the unmeasured case, it is the case a
   workstation role actually is, and DES-0006 verification item 9 already owns a
   representative workload comparison. **This is the strongest argument against
   the recommendation and it is an absence of evidence rather than evidence.**
   It should be measured before an ADR accepts EROFS, not after.
2. **Part of the deciding number is compression, not format.** The EROFS arm is
   `lz4hc` level 12 by declaration and ext4 cannot compress at all. The
   attribution is therefore impure -- but the *choice* is not, because
   compression is available on one format and unavailable on the other, and the
   compressed EROFS artifact is the actual candidate. The confound limits what
   may be said about the formats in the abstract; it does not limit the
   comparison of the two artifacts NeutrinOS would ship. **Any restatement of
   1.65x must carry this sentence.**
3. **The ruled command line is not the implemented one.** The 2026-08-12 owner
   ruling adopts the ParticleOS shape; the six artifacts carry `usr=signed` with
   `usrhash=` retained. Settling that ruling in its own favour rebuilds the set
   and **voids every figure in the tally**, this recommendation with them. It is
   open and it is the owner's.
4. **One correction to an accepted record is pending and it favours EROFS.**
   PLN-0002-07's inspectability finding describes `fsck.erofs --extract` as
   failing open; the recovery disposition measures that it does not, and that the
   finding therefore overstates the EROFS cost. **The recommendation is
   unaffected either way** -- inspectability is a low-weight ext4 row under rule
   2 whether the finding stands whole or half -- and it is named here so that
   taking the correction is not mistaken for moving the recommendation.
   Correcting an accepted record is not a task's to take.
5. **The initrd asymmetry risk is closed, not open.** PR-0030 C-003 warned that
   boot and memory would partly measure the initrd rather than the format.
   PLN-0002-05 declared one module list identical across both arms and both
   arms carry both filesystem drivers, so the ~2.85s initrd phase is the same
   phase twice and is reported split out. The ties at rows 4 and 5 are not an
   artifact of a shared initrd; they survive it being held constant.
6. **Scope.** One package closure, one release, a disposable VM with synthetic
   signing material, plain OVMF for most measurements, no physical role, and no
   A/B slots. C-002 capacity is unsettled, so the 111.4 MiB advantage cannot yet
   be cashed against any requirement -- it is a magnitude without a budget to
   spend it in.
7. **The recovery criterion is answered at the format layer only.** Its system
   layer is deferred to verification items 3 and 5 by accepted amendment. If
   that layer later separates the arms it would be new evidence against this
   recommendation, and nothing here forecloses it.
8. **The synthetic signing material expires 2026-09-11.** After that these
   artifacts are measured against expired enrollment material and any
   re-measurement re-issues it.

## What is not evidence for either format

Recorded because each was measured in this plan, is important, and would be
misread as a C-007 input.

- **The signature fail-open.** A valid signature by the enrolled signer over a
  root hash the image does not carry boots to `running` with zero failed units,
  enrolled or not, on both arms. It is the plan's eighth fail-open instance and
  the first where the mechanism is configured, runs, and gates nothing. It is
  **identical on both arms**, so it decides no part of C-007. It is carried past
  this plan by `T4-SLICE-003` and `T4-SLICE-004`, registered deferred against
  SYS-049's open sub-question under `S-005`.
- **The readahead finding.** A sequential reader loses up to 1.7 MB of intact
  data at the last 8 MiB-aligned boundary before the damage, identically on both
  arms. It dominates the format blast-radius difference by two orders of
  magnitude and belongs to the block layer, not to either format. **Any later
  blast-radius claim must state whether readahead was disabled.**
- **The empty verity partitions.** 64 MiB allocated and 95% empty on both arms,
  62.6 MiB wasted per artifact. It cancels between the arms and is a layout
  finding for PLN-0002-04, not a format one -- and it is over half the size
  advantage this recommendation rests on, which is worth noticing before the
  advantage is spent.
- **`e2fsck -fy` voiding an artifact's verity.** Measured on a *pristine* image:
  it reports no errors, writes anyway, and the artifact then fails
  `veritysetup verify`. It is a genuine ext4 footgun and it is deliberately not
  counted in the tally, because it is a property of running a repairer on an
  authenticated artifact and the correct operational answer -- do not repair,
  redeploy -- applies to both arms.

## What an ADR would still need

Not this task's to produce; listed so PLN-0002-14's disposition can carry them.

1. The workload read comparison of threat 1, which is DES-0006 verification
   item 9's and is the one measurement that could reverse this.
2. A selected update mechanism, which resolves the condition in the
   recommendation and settles criterion 6 one way or the other.
3. The ParticleOS command-line ruling, on which the validity of the whole tally
   rests.
4. A capacity budget from C-002, without which the deciding magnitude has no
   requirement to be measured against.

## What this record does not claim

- **It does not accept EROFS.** The 2026-08-15 acceptance covers this
  recommendation and its weighing rule. **C-007 stays open until an ADR records
  a format**, and EROFS remains a candidate fixture until then -- which is the
  distinction PR-0029 C-005 exists to protect.
- **No measurement of its own.** Every figure is carried from an accepted
  record and cited to it.
- **No claim about the package ecosystem, partition layout, state filesystem,
  updater, or encryption.** PLN-0002's non-goals are unchanged by a
  recommendation drawn from it.
- **No G2 or qualification claim.**
