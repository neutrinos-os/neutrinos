---
status: accepted
last_updated: 2026-08-15
governing_plan: PLN-0002
task: PLN-0002-09
accepted_by: Jason Tarasovic
accepted: 2026-08-15
---

# Corruption behaviour for the two `/usr` artifact formats

PLN-0002-09. **Single-bit corruption injected into an authenticated region of
each artifact, with the detection point, the diagnostic, and the blast radius
recorded per format.** Four injections: two arms, two target files each.

This is the seventh of C-007's eight criteria and **the first one that
separates the arms on the mechanism rather than on a number**. Boot behaviour,
memory and determinism came back tied ([boot records](artifact-boot-records.md),
[measurements](artifact-format-measurements.md)); this one does not.

**This record recommends nothing.** PLN-0002-13 answers C-007.

Figures are in `$NEUTRINOS_SLICE_BUILD_ROOT/evidence/pln0002-09/corruption.json`
with the console of every run retained beside it under `serial/`, written by
`src/slice/measure-corruption.py`.

## What was injected, and where

One bit, flipped in the **`/usr` data partition** -- the region the root hash
covers. Not the hash tree, not the `usr-verity-sig` partition, not the ESP. The
signed UKI still carries the root hash of the *original* bytes, which is exactly
the condition dm-verity exists to detect.

| | EROFS | ext4 |
| --- | --- | --- |
| `System.map` | byte 554117120, `0x14` -> `0x15`, verity data block 3954 | byte 578426880, `0x66` -> `0x67`, block 9889 |
| `vmlinuz` | byte 565770240, `0x3e` -> `0x3f`, verity data block 6799 | byte 680441856, `0x17` -> `0x16`, block 34795 |

Each injection went into a **copy**. The six accepted artifacts are unmodified
and their digests were checked before and after every run.

**Two targets per arm, because blast radius is data-dependent.** A flipped bit
costs ext4 one block whatever the file holds. It costs EROFS one *physical
cluster*, which covers as much logical data as that cluster's contents happened
to compress into -- so a record built on one file would report a property of
that file as a property of the format. `System.map` compresses to 25.43% and
`vmlinuz`, being already-compressed data, to 98.77%. Both are byte-identical
across the arms, in the same directory, and **neither is read during boot**: the
kernel that boots is the copy inside the UKI, not this one. The read is the
probe, not a side effect.

Both arms use 4096-byte blocks by PLN-0002-05 declaration -- ext4 block size,
dm-verity hash block size, and the page size `mkfs.erofs` derives from -- so one
bit lands in exactly one verity data block on either arm. That is what makes the
two radii comparable at all.

## Three detection points, and only one of them is the boot

**Offline `veritysetup verify`: rejects all four.** Identical on both arms by
construction, because verity hashes every data block whatever filesystem sits
above it. Measured rather than assumed.

**Boot: all four succeed.** `running`, no failed units, `/usr` mounted
read-only from `/dev/mapper/usr`, unrelated files reading normally. This is
this plan's first standing finding -- lazy per-block dm-verity -- reproduced on
the accepted artifacts and on both arms. It is not an eighth fail-open
instance; it is the first one, measured where it matters most.

**The read: detected, immediately, with a diagnostic that names the block.**

```
device-mapper: verity: 253:2: data block 9889 is corrupted
audit: type=1339 audit(...): module=verity op=verify-data dev=253:2 sector=9889 res=0
```

The block index dm-verity names is **the block this harness flipped**, on all
four injections, in both the console and the audit record. That is what ties the
guest's complaint to the specific byte, and it is why the console of every run is
retained. The diagnostic is identical in form on both arms: the discriminating
information is at the verity layer, and the filesystem above it contributes
nothing to it.

## Blast radius

**Measured twice per injection, because the default measurement is not a format
property.** A 4 KiB read still triggers readahead, and a readahead request
spanning the bad block fails as a unit; the first run of this task recorded
EROFS losing 45 KiB against ext4's 16 KiB, which is neither arm's real cost.
`blockdev --setra 0` on the dm device removes that term from both arms equally.

**Readahead disabled -- what the format itself costs, per flipped bit:**

| | EROFS | ext4 | ratio |
| --- | --- | --- | --- |
| `System.map` (compresses to 25.43%) | **4 blocks, 16 KiB** | **1 block, 4 KiB** | 4x |
| `vmlinuz` (already compressed, 98.77%) | **2 blocks, 8 KiB** | **1 block, 4 KiB** | 2x |

**These reproduce exactly**, on both runs that measured them, and they match
what the extent maps predict -- which is what makes the extent map usable as a
model rather than as a guess. The default-readahead pass, by contrast, gave a
different answer on each of three runs of the same injection, and on one run did
not include the corrupt block at all. Its non-reproducibility is the evidence
that it measures the system and not the format.

**The single injection is a sample; the extent map gives the distribution.**
Across every physical cluster of the two target files:

| | clusters | logical blocks lost per bit: min / mean / max |
| --- | --- | --- |
| EROFS `System.map` | 720 | 2 / 4.93 / **9** |
| EROFS `vmlinuz` | 4456 | 1 / 2.01 / **9** |
| ext4, both | -- | 1 / 1 / 1 |

The two injections landed near the mean of their file. **The worst case
observed is 9 blocks, 36 KiB, 9x ext4**, and it occurs on both target files --
so it is a property of cluster packing, not of compressibility alone.

**EROFS's floor is 2 blocks, not 1, on compressible data.** Physical clusters
are not aligned to logical block boundaries, so a cluster's logical span
normally straddles a block edge at each end. On `vmlinuz` a cluster occasionally
falls entirely inside one block and EROFS matches ext4 exactly, which is the
minimum of 1 above.

## The readahead finding, which is larger than either arm's

Readahead on the dm device is **16384 sectors, 8 MiB**, and a sequential reader
loses the whole failed window rather than the damaged blocks:

| `dd` over | with readahead | with readahead disabled |
| --- | --- | --- |
| `System.map` (11.6 MB) | stops at **4.0 MiB**, both arms | stops at the bad block: 5.894 MB EROFS, 5.800 MB ext4 |
| `vmlinuz` (18.5 MB) | stops at **8.0 MiB**, both arms | stops at the bad block: 9.134 MB EROFS, 9.241 MB ext4 |

**A naive consumer -- `cat`, `cp`, a checksum -- fails at the last 8 MiB-aligned
boundary before the damage and discards up to 1.7 MB of intact data it had
already read.** Identical on both arms, on all four injections. This is a
property of the block layer under dm-verity, it is not a C-007 criterion, and it
dominates the format difference by two orders of magnitude for any reader that
does not seek. It is recorded because a record that reported only the 4 KiB and
16 KiB figures would leave the impression that a corrupt block costs a reader
those amounts, and it does not.

## What this record does not claim

- **No recommendation.** One criterion does not decide C-007, by the plan's own
  non-goal and the owner ruling of 2026-08-11.
- **Nothing about metadata corruption.** Every injection landed in file data.
  A bit in an EROFS inode block or an ext4 group descriptor is a different blast
  radius and this task did not measure it.
- **Nothing about the whole image.** The distribution above is over two files.
  A bound over every cluster in the artifact was not computed.
- **No signature claim.** Plain OVMF, synthetic keys, and the `/usr` signature
  enforcement question still open from PLN-0002-08 and `S-005`.
- **No availability claim.** All four guests stayed `running` with `/usr`
  mounted, but the damaged file was chosen precisely because nothing depends on
  it. What a corrupt block costs when it lands under a running binary is not
  measured here.
- **No detection-latency figure.** Detection is at first read of the block; how
  long a machine runs before that happens is a workload question.
- **Host-observed readiness is not a figure this task reports.** One run
  recorded 147s while its own console shows a normal 21s guest lifetime; that is
  host contention from the parallel image copies.

## Carried risks

- **The synthetic signing material expires 2026-09-11.** Unchanged by this task,
  which built nothing.
- **The ParticleOS command-line ruling of 2026-08-12 is still open**, and
  settling it in its own favour rebuilds the artifact set and voids these
  records with the rest.
