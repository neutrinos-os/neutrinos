---
status: active
last_updated: 2026-08-11
governing_plan: PLN-0001
---

# Reference-VM slice reconstruction record

PLN-0001-07. The artifact and every VM built from it were destroyed, and the
artifact was then rebuilt with the network removed. This records what was
destroyed, what the reconstruction was allowed to reach, what came back
identical, and what the exercise found missing.

The short result: **every stable identity came back byte-for-byte, and the tree
inside the disk image is identical too.** The exercise also found that the
fixture retains no repository metadata, so the offline build was only possible
after a retention step that `compose.sh` does not perform. That is the finding,
and it is larger than the confirmation.

## What was destroyed

Removed before the rebuild, with nothing extracted from them first except the
digests and tree manifest recorded below:

| Path under the build root | What it held |
| --- | --- |
| `out/`, `out-revert/` | The composed artifact, both copies |
| `vm/`, `vm04/`, `vm04b/`, `vm04c/` | VM disks, firmware variable stores, vTPM state |
| `vm-cmdline/`, `vm-smbios/` | The PLN-0001-04 credential-experiment VMs |

Retained deliberately, because they are the declared inputs the reconstruction
is supposed to run from: the mkosi clone at the pinned commit, the tools tree
built from the pinned base image, and the package cache.

## What the reconstruction could reach

The build ran inside a user and network namespace with loopback and nothing
else. The script asserts this before starting: it attempts a connection to
`dl.fedoraproject.org` and refuses to call itself an offline build if that
connection succeeds. A build that quietly reached the network would have been
worse than a failed one.

Inside the namespace, the declared repository was served over loopback from a
retained local copy. So the build resolved against retained bytes, and the only
reachable source was one we put there.

## Result: the identities came back

| Artifact | Digest | Matches the record |
| --- | --- | --- |
| `neutrinos-slice.efi` (UKI) | `575c847dd491a081ff364b0139fe3e81b4e00add7f08f12fb6b4c2582a8cd0fd` | yes |
| `neutrinos-slice.vmlinuz` | `4b37e4e542a62c580c751787848be6c99e6f908f6712c8c6da85516b8d541de2` | yes |
| `neutrinos-slice.initrd` | `e7061e2539c9bab9b2c3a94f7f4bf75d4da6103cba6d490730896d43382c8b71` | yes |
| `neutrinos-slice.manifest` | `cb438999575af8889ba4bc23534e7b4a6e683d115e81d10f1b77120ef63bbaa2` | yes |
| `initrd.cpio.zst` | `b899abfb83d9534e5328bc73fdfdc45bacf9caf79b5ac2d9a9c1f9cfade5615d` | yes |
| `neutrinos-slice.raw` (disk) | `116ce651bef66ebcb768cc789b016762915c78d7590d42c332ca97e28ced6425` | no, and expected not to |

The disk image differs for the two reasons the
[composition record](slice-composition-record.md) identifies -- the btrfs chunk
tree UUID and the FAT volume serial -- neither of which is reachable from the
composition configuration. Its digest is recorded because the boot check binds
to it, not because it is an identity claim.

The UKI **on the ESP inside the reconstructed image** was read out of the FAT
partition and hashes to `575c847d...`, the same value as the standalone UKI. The
bootloader is identical at both of its paths
(`8aa6a191...` for `EFI/systemd/systemd-bootx64.efi` and `EFI/BOOT/BOOTX64.EFI`).

## Result: the shipped tree is identical

PLN-0001-04 recorded a correction: the two-build comparison used
`Format=directory`, whose tree contains package databases the shipped image does
not, so it measured the composition process rather than the artifact. That
correction is now closed by measurement.

The root filesystem was extracted from each disk image and compared: **13240
entries, zero differences** in type, mode, ownership, symlink target, size, and
per-file SHA-256. The extracted trees contain no `/usr/lib/sysimage/rpm`, which
confirms the correction's claim about what the shipped artifact carries.
`etc/machine-id` is the literal string `uninitialized`, so it is deterministic
and needed no exclusion; no machine ID or boot ID had to be filtered out of the
comparison at all.

Method, and its limits. The root partition is copied out of the GPT by byte
range and handed to `btrfs restore`, which reads a filesystem image as a file.
No loop device, no mount, and no root on the build host: the restore runs inside
a user namespace where the caller is mapped to uid 0, so recorded ownership is
reproduced and the manifest sees the image's uids rather than the caller's. Two
limits are worth stating rather than hiding:

- Timestamps are excluded from the comparison. `SourceDateEpoch=` fixes them for
  build outputs, but restore-time directory mtimes are an artifact of the
  extraction.
- `user.*` xattrs were compared and are identical (only the tree root carries
  any, the three `user.validatefs.*` entries). **`security.*` xattrs are not
  attested by this method**: none appeared, and this exercise cannot distinguish
  "the image has no file capabilities" from "the restore dropped them". If file
  capabilities become part of a claim, this method needs replacing.

## Result: the reconstructed artifact boots

`check:complete` against the reconstructed artifact: `passing=10 failing=0
blocked=0`. `T4-SLICE-001` booted it in 15.8 seconds, reaching `READY=1` over
the notify vsock at 13.754 seconds with no failed units, the harness hostname
reported back over the notify stream, and the artifact byte-identical
afterwards. So the destroyed VM was rebuilt from the reconstructed artifact, not
merely rebuilt.

## Finding: the fixture retains no repository metadata

The first offline attempt failed, and it failed in the most useful way.

`mkosi --cache-only=always` with the retained package cache could not resolve
the transaction: `No match for argument: basesystem`. The cache holds packages
and no repository metadata, so with the network removed there is nothing to
resolve against. Nothing in `compose.sh`, `mkosi.conf`, or `input-set.toml`
retains the metadata of the repository the declaration names.

This is a real gap in the offline claim, not an inconvenience of the harness.
The declared repository is a URL. The bytes behind that URL are retained only by
accident, as a side effect of a package cache written by whichever build ran
last.

Closing it required a retention step performed **for this exercise, not by the
fixture**: the declared repository's `repodata/` was fetched once with the
network available, and the retained RPMs were hardlinked into the paths that
metadata names. The metadata is upstream's, unmodified, so resolution against
the local copy is resolution against the declared repository, restricted to the
packages actually retained. Anything the build needed but did not have would
have failed rather than reached elsewhere -- which is the property that makes
the identical result meaningful.

## Finding: the shared package cache is contaminated

Of 179 RPMs in the retained cache, **58 are not in the declared repository's
metadata at all**. They are the residue of PLN-0001-06's injected faults: `fc43`
packages from the mixed-branch transactions, and newer `fc44` builds
(`coreutils-9.10-5`, `audit-libs-4.2.1-1`, and others) that can only have come
from the `updates` repository admitted by the `Mirror=` fault.

Nothing consumed them here -- the mirror is laid out from upstream metadata, so
a package the declaration does not contain has no path to be resolved through,
and the identical digests confirm none was. But the cache that a naive
`--cache-only` build would have installed from contains packages from an
undeclared repository and from two other Fedora branches. **A package cache
shared across fault-injection builds is not a retention store**, and the
distinction matters exactly when the declaration is what is being tested. This
compounds the [failure evidence](slice-failure-evidence.md) finding behind the
SYS-059 downgrade: there, an undeclared repository could be admitted without
detection; here, its output persists on disk afterwards.

## What this does not establish

- **Reconstruction is not reproducibility of the disk image.** The `.raw`
  differs, for known reasons, and this exercise did not attempt to change that.
- **The retention that made it work is not part of the fixture.** The
  reconstruction ran offline; the *ability* to run offline was assembled by
  hand. Until `compose.sh` retains the declared repository subset, "we can
  rebuild this with the network removed" is true of this build root on this host
  and is not a property of the slice. **Recommended, not accepted: SYS-041's
  trace row should be downgraded from `Demonstrated` to `Partial`.**
- **SYS-041 is broader than what was measured.** The requirement covers the
  lifecycle control path -- health recording, blessing, fallback, deliberate
  rollback -- with named services unavailable. The slice has no blessing and no
  fallback path, so only the acquisition half was exercised: composition and
  boot need no publication service, discovery service, package repository, or
  WAN. The other half remains untestable here for the reasons SYS-012's partial
  status already records.
- **No mechanism is selected.** mkosi and Fedora 44 remain candidate fixtures.
  Reconstructing successfully is not evidence for mkosi over bootc, which was
  not tried.
