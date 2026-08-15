---
status: accepted
last_updated: 2026-08-15
governing_plan: PLN-0002
task: PLN-0002-08
accepted_by: Jason Tarasovic
accepted: 2026-08-15
---

# Boot records for the two `/usr` artifact formats

PLN-0002-08. The first boots of the six artifacts PLN-0002-06 built: `/usr`
read-only and verity-authenticated, `/etc` regenerated, no failed units, and
**boot behaviour and memory with the repetition count and accelerator state
recorded per run**. Three boots per arm, both primaries, measured identically.

Corruption behaviour is tasks 09 and 10; recovery is 12. The offline five are
[PLN-0002-07](artifact-format-measurements.md).

**This record recommends nothing.** On the two criteria it measures, **the arms
are indistinguishable**, and that is the result rather than a failure to find
one.

Figures are in `$NEUTRINOS_SLICE_BUILD_ROOT/evidence/pln0002-08/boot.json`, with
the console of every run retained beside it under `serial/`, written by
`src/slice/measure-boot.py`. Every figure is read from a running guest or its
console, never from the configuration that produced it.

## How the boots were taken

The two primaries, unchanged. The four variants exist only as PLN-0002-10
substitution sources and booting them would answer no C-007 criterion.

Nothing was added to the artifacts. The probe unit, the credentials, and the
two unit masks arrive from the host as SMBIOS Type 11 credentials and stub
command line; the artifact is the boot disk, attached `snapshot=on`, and its
digest is **unchanged after all six boots**.

**Accelerator: KVM, measured on every run** by asking the running VM over QMP,
not by inspecting the host. A run that answered TCG, or could not be asked,
fails the comparison rather than being averaged into it -- PLN-0001 measured the
same boot at 72s under TCG and 18s under KVM, so an arm that quietly emulated
would produce a 4x difference that reads as a format result. All six answered
KVM.

**Firmware: the plain OVMF build, stated rather than defaulted.** Every
assertion here is about mount state, unit health, timing and memory, and none is
a signature claim. Secure Boot would require enrolling keys into a *copy* of
each artifact, which is a different set of bytes than PLN-0002-07 measured.
`T4-CONFEXT-001` is where the signature arm lives.

## Boot behaviour

| | EROFS | ext4 |
| --- | --- | --- |
| kernel | 0.894 - 0.936s | 0.857 - 0.906s |
| **initrd** (held constant) | 2.833 - 2.857s | 2.845 - 2.886s |
| userspace | 2.448 - 2.462s | 2.451 - 2.456s |
| **guest total, median** | **6.226s** | **6.204s** |
| host-observed readiness, median | 11.374s | 12.007s |
| repetitions | 3 | 3 |

**The difference is 22ms on a 6.2s boot, and the run-to-run spread within each
arm is twice that.** There is no boot-time result here to give PLN-0002-13, and
saying so is the finding: EROFS is 1.65x smaller on disk and `lz4hc`-compressed,
and none of that reaches time-to-ready.

Three constants are why the total is reported split rather than whole.

**The initrd is held constant by declaration.** PLN-0002-05 ruled a trimmed
module list *identical across both arms*, precisely so that boot time and memory
do not measure the initrd -- PR-0030 C-003's named risk. The ~2.85s initrd phase
is therefore the same phase twice, and a single 6.2s total would hand
PLN-0002-13 a number with a large shared constant baked into it.

**The pre-kernel phase is a third constant and is unattributed.** Host-observed
readiness exceeds the guest's own total by about five seconds, which is OVMF
plus systemd-boot loading a 58.1 MiB UKI -- identical in size on both arms.
`systemd-analyze` reports no `firmware` or `loader` component, because the
loader exports none, so the guest cannot see its own pre-kernel time. Measuring
it is a layout question and not a format one, the same disposition
PLN-0002-07's empty verity partitions got, and it is left unmeasured
deliberately. The two arms' host-observed medians differ by 0.6s in the
*opposite* direction from their guest totals, which is what a constant plus
noise looks like.

**Only the kernel and userspace phases can carry a format difference**, and
neither does.

## Memory

Sampled inside the guest 20 seconds after boot, on an idle system, from
`/proc/meminfo`. Ranges across three runs.

| | EROFS | ext4 |
| --- | --- | --- |
| MemAvailable | 1716.4 - 1717.3 MiB | 1705.2 - 1721.2 MiB |
| MemFree | 1756.7 - 1757.5 MiB | 1745.4 - 1761.3 MiB |
| Cached | 65.3 - 65.4 MiB | 64.3 - 64.4 MiB |
| Slab | 42.2 - 42.4 MiB | 42.0 - 42.6 MiB |
| AnonPages | 14.6 - 15.5 MiB | 14.6 - 15.4 MiB |
| MemTotal | 1948.6 MiB | 1948.6 MiB |

**EROFS holds about 1 MiB more page cache than ext4, out of 1948.6 MiB.** That
is the only figure whose ranges do not overlap, and it is 0.05% of guest memory.
Every other figure overlaps -- ext4's MemAvailable range is 16 MiB wide across
three runs and contains EROFS's entire range. As with boot time, this is a tie.

**What this does not measure is the interesting case.** An idle system 20s in
has touched only what booting touched, and EROFS's compression cost is paid on
*read*, in decompression and in the cache holding decompressed pages. A workload
that reads widely across `/usr` is where the arms would be expected to diverge,
and this task applies none. The tie is real and its scope is narrow.

## What the boots assert

Identical on both arms, on all three runs each.

| | EROFS | ext4 |
| --- | --- | --- |
| `/usr` source | `/dev/mapper/usr` | `/dev/mapper/usr` |
| `/usr` filesystem | erofs | ext4 |
| mount options | `ro,relatime,user_xattr,acl,cache_strategy=readaround` | `ro,relatime` |
| **read-write remount** | **refused** | **refused** |
| verity device UUID | matches the artifact's hash partition | matches |
| `usrhash` on the running command line | matches the signed UKI | matches |
| dm device read-only flag | 1 | 1 |
| `/etc` | overlay, 71 entries | overlay, 71 entries |
| `/etc/passwd`, `/etc/os-release`, `/etc/machine-id` | present | present |
| root filesystem | tmpfs | tmpfs |
| system state | `running` | `running` |
| failed units | none | none |
| artifact digest after boot | unchanged | unchanged |

**Read-only is measured, not read off a flag.** `ro` in the mount options is
what the mount was asked for; a remount that is *refused* is the property
itself. This project has been caught by that distinction before --
`systemd.image_policy=` is satisfied by both enrollment arms and enforces
neither -- so the stronger measurement is the one taken.

**Two bindings, worth different amounts.** The dm device UUID carries the verity
**superblock** UUID, which PLN-0002-05 declares and which is therefore
*identical on both arms*; it proves the guest mounted a verity device this plan
built and nothing narrower. The root hash is per-artifact, and matching the
guest's `usrhash` against the one read out of that arm's signed UKI is what ties
the running kernel to the artifact under test. Conflating the two was this
harness's first wrong assertion and it failed all six runs before being fixed.

**"No failed units" is conditional on two masks.** `systemd-tpm2-setup-early`
and `systemd-pcrproduct` are masked from the host command line, because the
artifact ships no `tpm2-pcr-public-key.pem` and supplying one is TPM policy,
explicitly out of PLN-0002's scope. The masks are named individually rather than
by pattern, so a third unit cannot fail behind them, and they travel in the
retained record.

## The confext signature fails open, on both arms, six times per boot

Measured here rather than inferred, and the reason the console of every run is
retained:

```
device-mapper: table: 252:1: verity: Root hash verification failed (-ENOKEY)
device-mapper: table: 252:2: verity: Root hash verification failed (-ENOKEY)
```

Six occurrences on 252:1 during `systemd-confext-sysroot.service` in the initrd,
six on 252:2 during `systemd-confext.service` in the host, on every one of the
six boots, followed each time by `erofs (device dm-1|dm-2): mounted` and a unit
that reports `Finished`. This is PLN-0002-03a's recorded finding -- dm-verity
resolves the signing key through the kernel keyring, a synthetic key is in none,
and systemd falls back to unsigned verity and merges -- reproduced on the
accepted artifacts. Nothing new, and now measured on both arms.

**It is the confext, not `/usr`.** 252:0 is `/usr`, and it produces no such line:
`systemd-veritysetup@usr.service` finishes clean. Attributing these lines to the
`/usr` artifact would have been easy and wrong.

**What `/usr` does instead is an open question this task does not answer.**
PLN-0002-06 built a detached `usr-verity-sig` partition, and the console shows
no signature attempt for `/usr` at all -- neither a refusal nor a confirmation.
Absence of a diagnostic is not evidence that the signature was checked. Where
the enforcement point actually is belongs to tasks 09 and 10 and to the `S-005`
sub-question already recorded in the backlog.

## What this record does not claim

- **No recommendation.** PLN-0002-13 answers C-007, and two of the eight
  criteria coming back tied is an input to that, not a tiebreak.
- **No signature claim.** Plain firmware, synthetic keys, and the fail-open
  above. A successful boot is not a statement about the artifact: dm-verity
  verifies lazily, per block, so these boots prove the blocks they touched.
- **No memory figure under load.** Idle, 20s in, on a system that has read only
  what booting read.
- **No pre-kernel timing.** Stated as a constant, unmeasured on purpose.
- **Nothing about corruption, substitution, or recovery.** Tasks 09, 10 and 12.

## Carried risks

- **The synthetic signing material expires 2026-09-11.** Unchanged by this task,
  which built nothing.
- **The ParticleOS command-line ruling of 2026-08-12 is still open.** These
  boots are of artifacts carrying the implemented command line rather than the
  ruled one, and the guest's `usrhash` assertion is against the implemented UKI.
  Settling the ruling in its own favour rebuilds the set and voids these
  records with the rest.
