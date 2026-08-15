---
status: accepted
last_updated: 2026-08-15
governing_plan: PLN-0002
task: PLN-0002-07
accepted_by: Jason Tarasovic
accepted: 2026-08-15
---

# Offline measurements of the two `/usr` artifact formats

PLN-0002-07. Five of C-007's eight criteria, measured over the six artifacts
PLN-0002-06 built and accepted: **image size, build wall time, build
determinism, update transfer size, and inspectability**. Boot behaviour and
memory are task 08; corruption behaviour is tasks 09 and 10.

**This record recommends nothing.** C-007 is answered by PLN-0002-13, and no
single criterion decides it -- the plan's own non-goal. Of the five measured
here, image size favours EROFS; build wall time and inspectability favour ext4;
build determinism is a tie; update transfer size is split against itself,
whole-image favouring ext4 and block-differential favouring EROFS. That spread
is the result, not a problem with it.

The figures are in
`$NEUTRINOS_SLICE_BUILD_ROOT/evidence/pln0002-07/static.json` and
`build.json`, written by `src/slice/measure-artifact-set.py` and
`src/slice/measure-build-time.py`. Every figure is read from a built artifact,
never from the configuration that produced it.

## What was measured against

The six accepted artifacts, unchanged. The two primaries carry the comparison;
the four variants contribute the update-transfer deltas and their own build
times.

**The rebuilds this task ran overwrote the accepted set in place.** Owner
ruling 2026-08-15: all six were copied aside before the timed builds and the
copies discarded only after every rebuild reproduced its retained digest. They
all did, so the accepted set is the accepted set.

## Image size

**Filesystem bytes in use, with partition size reported separately.** Both arms
hold `Minimize=guess` because `Minimize=best` is unavailable on ext4, so a
partition figure measures systemd-repart's estimator on one arm and the
filesystem on the other. The measurement shows exactly that.

| | EROFS | ext4 | ratio |
| --- | --- | --- | --- |
| **`/usr` filesystem bytes in use** | **171.0 MiB** | **282.4 MiB** | **1.65x** |
| `/usr` filesystem image size | 171.0 MiB | 440.1 MiB | 2.57x |
| `/usr` free space inside the filesystem | 0 | 157.7 MiB | -- |
| `/usr` partition size | 171.0 MiB | 440.1 MiB | 2.57x |
| space in the partition outside the filesystem | 0 | 0 | -- |
| verity hash tree bytes in use | 1.4 MiB | 3.5 MiB | 2.5x |
| verity partition size | 64.0 MiB | 64.0 MiB | 1.0x |
| UKI | 58.1 MiB | 58.1 MiB | 1.0x |
| whole `.raw` | 748.0 MiB | 1017.1 MiB | 1.36x |

Three things this table is here to prevent.

**The estimator's margin is inside the ext4 filesystem, not outside it.**
systemd-repart sizes the partition to its estimate and the filesystem is made
to fill it, so nothing is left over in the partition -- both arms measure zero
there. The 157.7 MiB shows up as ext4 free blocks. A partition-size comparison
therefore does not merely include the margin, it is indistinguishable from a
filesystem comparison, which is why the plan required bytes in use.

**Reporting partition size would have overstated EROFS's advantage by 56%**:
2.57x against the 1.65x that is actually there.

**Part of the 1.65x is compression, not format.** The EROFS arm is `lz4hc`
level 12 by the PLN-0002-05 declaration; ext4 cannot compress and has no
matching setting. PLN-0002-13 must not read this row as a format result alone.

The verity partitions are identical 64 MiB on both arms and 95% empty on both.
That is a layout finding rather than a comparison one -- it cancels between the
arms -- but it is 62.6 MiB per artifact and the disposable layout of
PLN-0002-04 is where it belongs.

## Update transfer size

Two definitions, because they disagree, and the disagreement is the finding.

### Whole-artifact update

What an A/B slot scheme ships: the `/usr` partition, compressed.

| | EROFS | ext4 |
| --- | --- | --- |
| uncompressed | 171.0 MiB | 440.1 MiB |
| zstd level 3 | 146.6 MiB | 138.6 MiB |
| **zstd level 19** | **140.0 MiB** | **128.2 MiB** |

**ext4 ships fewer bytes than EROFS on this criterion, at both levels.** The
EROFS image is already `lz4hc`-compressed and recompresses poorly, while ext4's
uncompressed content compresses well and its 157.7 MiB of free space compresses
to almost nothing. The arm that is 1.65x larger on disk is 8% *smaller* on the
wire.

This is the clearest case in the whole comparison of a criterion that would
have been answered backwards by inference. Nothing about "EROFS is the
compressed format" predicts it.

### Differential update

What a block-differential updater ships. Counted as differing 4 KiB blocks --
the filesystem block size and the dm-verity data block size on both arms --
between an artifact and its variant.

| perturbation | EROFS | ext4 |
| --- | --- | --- |
| one added file (content variant) | 11084 blocks, **43.3 MiB** (25.3%) | 35104 blocks, **137.1 MiB** (31.2%) |
| identity only, same tree (seed variant) | 1 block, **4 KiB** (0.002%) | 4182 blocks, **16.3 MiB** (3.7%) |

**EROFS ships 3.2x fewer bytes for one added file.** Read carefully: both arms
were given the identical perturbation, and on both a large fraction of the
image moved. Inserting a file shifts the layout of everything allocated after
it, so this measures the format's amplification of a realistic change and not a
minimal edit. It is a fair comparison and a pessimistic one for both arms.

**The seed row is where the two formats differ in kind.** Changing only the
identity -- same tree, different `Seed=` -- moves one EROFS block and 16.3 MiB
of ext4. ext4 carries `metadata_csum_seed`, so a filesystem UUID change
rewrites every group's checksums; EROFS rewrites its superblock. Neither number
is the whole transfer, because the root hash and therefore the entire verity
tree change on both arms (1.4 MiB and 3.5 MiB, from the table above).

No differential updater is selected, and this plan selects none. The figures
say what one would be able to achieve, which is what C-007 asks.

## Inspectability

Both arms are inspectable offline, unprivileged, with no loop device and no
mount. The difference measured is **what has to be present to do it**.

| | EROFS | ext4 |
| --- | --- | --- |
| listing tool | `dump.erofs --ls` | `debugfs -R 'ls -l /'` |
| present on the build host | **no** | yes |
| present in the declared tools tree | yes | yes |
| root directory listed | yes, 16 entries | yes, 14 entries |
| single-file extraction | **fails open** | yes, 629 bytes |
| directory extraction | yes, 4 entries | yes, 4 entries |
| required root | no | no |

Two findings.

**e2fsprogs is on the build host and erofs-utils is not.** That is a property of
tooling reach, not of the image: an operator debugging an ext4 artifact uses
what their distribution already ships, while EROFS reaches them only through
the declared tools tree, which is a build input rather than an environment.
The tools tree is retained, so nothing is unavailable -- it is a step, not a
wall.

**`fsck.erofs --extract=X --path=<file>` fails open.** At the pinned
erofs-utils version it prints `Extracted filesystem successfully`, exits 0, and
writes nothing. Only a directory path extracts anything. This is the plan's
recurring pattern in a seventh place, and it is a measurement hazard rather
than a boot hazard: a probe that trusted the exit status would have scored the
arm as inspectable on the strength of a tool that did nothing. The measurement
script records the exit status and the extracted byte count separately for
exactly this reason.

## Build wall time

Owner ruling 2026-08-15: **three timed rebuilds per artifact, all six**. 18
timed builds, each a full `compose.sh --force build` with the confext rebuilt.
**Accelerator: not applicable** -- nothing here boots a VM, so there is no
KVM-versus-TCG difference of the kind that moved PLN-0001's boot figure. The
build is host CPU work on 16 threads of a Ryzen 7 3700X, kernel 7.1.6-arch1-1.
Packages resolve from the retained repository in the build root; no run touches
the network.

| artifact | median | min | max | spread |
| --- | --- | --- | --- | --- |
| out-erofs | **52.87s** | 52.64 | 53.40 | 0.76 |
| out-erofs-content | 52.82s | 52.41 | 67.96 | 15.55 |
| out-erofs-seed | 52.64s | 52.27 | 52.72 | 0.45 |
| out-ext4 | **46.65s** | 46.40 | 61.51 | 15.11 |
| out-ext4-content | 46.61s | 46.55 | 46.81 | 0.26 |
| out-ext4-seed | 46.51s | 46.24 | 46.60 | 0.36 |

**EROFS builds ~6.2s slower than ext4, about 13%**, and the three artifacts
within each arm agree to under a second of each other. Read the medians, not
the maxima: three of the eighteen runs came in ~15s long, each of them the
first rep of its group, and no run in any group was slow twice. That is host
scheduling noise on a shared machine, which is what taking three repetitions
was for.

### What the wrapper costs

`compose.sh` is not only the artifact build -- it rebuilds two confexts,
retains the repository, and writes the enrollment fixture, identically on both
arms. Three more runs per primary with `NEUTRINOS_SKIP_CONFEXT=1` price that
shared part.

| primary | full median | confext skipped | wrapper share |
| --- | --- | --- | --- |
| out-erofs | 52.87s | 50.65s | 2.2s |
| out-ext4 | 46.65s | 45.12s | 1.5s |

So the arm-to-arm difference is **in the artifact build, not the wrapper**:
5.5s of the 6.2s survives with the confext skipped. `lz4hc` level 12 is the
plausible cause and this task does not establish it -- no run varied the
compression setting, and tuning it is a plan non-goal.

**No determinism claim is taken from the confext-skipped pass.** It reuses a
previously built extension, which would make any reproduction it showed
narrower than it sounds.

## Build determinism

**All six artifacts reproduced on all three rebuilds. 18 of 18.** Compared
against the digests PLN-0002-06 retained, every file in each output directory
and not only `neutrinos-slice.raw` -- the UKI carries the command line and the
root hash, so a UKI that stopped reproducing would be invisible to an
image-only check.

| artifact | reproduced | files compared |
| --- | --- | --- |
| all six, 3 rebuilds each | **yes** | every retained file per directory |

Two things this does and does not say.

**The confext was rebuilt on every run that carries this claim.** That is the
scope of the claim and the reason the overhead pass is fenced off from it.

**Determinism does not separate the arms.** Both are reproducible, so this
criterion is a tie and contributes nothing to C-007 beyond ruling out a failure
mode. It is worth having measured precisely because a non-reproducing arm would
have been disqualifying.

The accepted set was copied aside before these rebuilds and the copies
discarded only after all 18 reproduced, per the owner ruling. The signatures
were reproduced, not reissued; the synthetic material's 2026-09-11 expiry is
unchanged.

## What this record does not claim

- **No recommendation.** PLN-0002-13 answers C-007, against these figures plus
  tasks 08, 09 and 10, which do not exist yet.
- **No boot, memory, corruption or recovery figure.** Those are tasks 08, 09,
  10 and 12. Task 08 has since booted the two primaries three times each
  ([boot records](artifact-boot-records.md)); the four variants remain
  unbooted.
- **Nothing about compression tuning.** `lz4hc` level 12 is a declared
  parameter of this comparison, not a tuned one, and this plan's non-goals
  exclude performance tuning of either format.
- **Nothing about a differential update mechanism.** The block deltas measure
  what the formats permit, not a selected updater.

## Carried risks

- **The synthetic signing material expires 2026-09-11.** Unchanged by this
  task; the rebuilds reproduced the existing signatures rather than reissuing
  them.
- **The ParticleOS command-line ruling of 2026-08-12 is still open**, and these
  measurements are taken against artifacts carrying the implemented command
  line rather than the ruled one. Settling it in the ruling's favour rebuilds
  the set and voids every figure here.
