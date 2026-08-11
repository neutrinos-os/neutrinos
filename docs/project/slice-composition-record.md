---
status: active
last_updated: 2026-08-10
governing_plan: PLN-0001
---

# Reference-VM slice composition record

PLN-0001-02. This records what the composition fixture produced, what its
identity is, and how to reconstruct it. The artifacts themselves are not in the
repository: the hygiene contract's binary and size bounds bind here, and a
1.3 GiB disk image is retained outside the checkout under the build root.

Composition ran unprivileged on `desktop-jason`. It installed nothing on the
host, required no root, and wrote only under the build root
(`${XDG_CACHE_HOME:-$HOME/.cache}/neutrinos/slice`). That was a constraint, not
a convenience: PLN-0001 permits no mutation of this host, so a composition path
that needed a host package would have been a stop condition.

## Fixture

| Part | Location |
| --- | --- |
| Declaration | `src/slice/input-set.toml`, schema `input-set-v2.schema.json` |
| Composition configuration | `src/slice/composition/mkosi.conf` |
| Entry point | `src/slice/compose.sh` |
| Build root | `${XDG_CACHE_HOME:-$HOME/.cache}/neutrinos/slice`, overridable with `NEUTRINOS_SLICE_BUILD_ROOT` |

Reconstruct with `./src/slice/compose.sh --force build`. The script clones mkosi
at the pinned commit, builds the tools tree from the pinned base image plus the
declared packages from the frozen repository, and runs the composition. It
resolves no floating reference.

## Output identity

Digests of the retained build, SHA-256:

| Artifact | Digest | Stable across builds |
| --- | --- | --- |
| `neutrinos-slice.efi` (UKI) | `575c847dd491a081ff364b0139fe3e81b4e00add7f08f12fb6b4c2582a8cd0fd` | yes |
| `neutrinos-slice.vmlinuz` | `4b37e4e542a62c580c751787848be6c99e6f908f6712c8c6da85516b8d541de2` | yes |
| `neutrinos-slice.initrd` | `e7061e2539c9bab9b2c3a94f7f4bf75d4da6103cba6d490730896d43382c8b71` | yes |
| `neutrinos-slice.manifest` | `cb438999575af8889ba4bc23534e7b4a6e683d115e81d10f1b77120ef63bbaa2` | yes |
| `neutrinos-slice.raw` (disk) | no stable digest; differs every build | **no** |

The UKI, kernel, and initrd digests are unchanged by the `RemoveFiles=`
normalization, which is expected: the removed paths are not inputs to the
kernel image. The disk image has no digest to record because it does not have a
stable one; see the reproducibility section below.

## Resolved package closure

104 RPMs, all from the single declared frozen repository. Anchor versions:

- `kernel-core` 6.19.10-300.fc44
- `systemd` 259.5-1.fc44
- `dbus-broker` 37-8.fc44
- `systemd-boot-unsigned` — the declaration requests `systemd-boot`, which
  Fedora satisfies through this package. The record names what was installed,
  not what was asked for.

The complete resolved set with exact versions is retained as
`neutrinos-slice.manifest` in the build root. `ManifestFormat=json` is set in
the composition configuration so the record is produced by every build rather
than by a flag someone remembers to pass.

## Reproducibility, measured

The UKI, kernel, initrd, and package manifest are bit-identical across builds.
The disk image is not, and the reasons are now identified rather than unknown.

### The file tree is reproducible

Two `Format=directory` builds were compared by per-file SHA-256 over all 7780
files. File metadata -- type, mode, and symlink targets -- was identical for
every entry. Four files differed:

| Path | Nature |
| --- | --- |
| `var/cache/ldconfig/aux-cache` | Linker cache, regenerated at runtime |
| `usr/lib/sysimage/rpm/rpmdb.sqlite-shm` | SQLite shared-memory sidecar |
| `usr/lib/sysimage/rpm/rpmdb.sqlite-wal` | SQLite write-ahead log, empty |
| `usr/lib/sysimage/libdnf5/transaction_history.sqlite-{shm,wal}` | As above |

The package databases themselves (`rpmdb.sqlite`,
`transaction_history.sqlite`) are byte-identical; only the journal sidecars
vary, because the databases were not closed cleanly. Checkpointing the dnf
history WAL reports zero live frames and leaves the database unchanged, so the
sidecars hold no committed data and `RemoveFiles=` discards nothing. With them
removed, the tree is reproducible.

Four files (`etc/shadow`, `etc/shadow-`, `etc/gshadow`, `etc/gshadow-`) are
mode 0000 and were skipped by the first comparison. They were hashed inside the
user namespace and are identical. A comparison that silently omits the files
most likely to carry a random salt is not a comparison.

### The disk image is not reproducible, for two identified reasons

With the tree reproducible, two `Format=disk` builds still differ in 101679
bytes out of 1.39 GB. Both causes lie below the file tree:

1. **The btrfs chunk tree UUID.** `mkfs.btrfs` generates it randomly, and it is
   embedded in the 80-byte header of every metadata node and leaf, so each
   header and its checksum differs. Measured directly: the filesystem UUID is
   now identical across builds (`Seed=` works), while the chunk tree UUID
   differs. `mkfs.btrfs` exposes `-U` for the filesystem UUID and
   `--device-uuid` for the device UUID, and **no option for the chunk tree
   UUID**. This is not a configuration gap on our side; upstream btrfs
   discussion of reproducible builds names the same three obstacles --
   UUIDs other than the volume UUID, timestamps, and non-deterministic extent
   and inode allocation -- and singles out the chunk UUID because it appears in
   every node and leaf.
2. **The FAT volume serial number of the ESP**, nine bytes immediately before
   the `ESP` volume label. `mkfs.vfat` supports `-i` to set it, so this one is
   fixable in principle, but it is not reachable through mkosi configuration
   here.

### Status of the goal

Full disk-image reproducibility is a worthwhile goal and not a requirement at
this stage. It is currently **unreachable with a btrfs root and this
toolchain**, and no amount of configuration in `mkosi.conf` will change that.

EROFS supports both a fixed UUID and `--mkfs-time`, and is deterministic by
design. It is already a named candidate for the slice root. That makes
"an EROFS root would probably be bit-reproducible" a plausible hypothesis and
explicitly **not a reason to select EROFS**: the storage mechanism is open
under S-004, and choosing a filesystem because it made a build comparison
convenient is precisely the failure [PR-0029](reviews/0029-g1-gate-approval.md)
C-005 warns about. The hypothesis is recorded for whoever takes that decision
on its own merits.

Until then, SYS-016's two-build comparison holds at the UKI, kernel, initrd,
manifest, and file-tree layers, and fails at the disk layer. PLN-0001-07's
offline reconstruction must compare those layers, not the `.raw` digest.

### Correction: the compared tree is not the shipped tree

Recorded 2026-08-10 from PLN-0001-04, which found the running machine has no
package database at all. The cause is mkosi's `CleanPackageMetadata=auto`
default, which removes package databases when the package manager is not
installed in the image -- **but skips the removal entirely for `directory` and
`tar` output** (`mkosi/installer/__init__.py:209`).

The two-build comparison above used `Format=directory`. Those trees therefore
contain `/usr/lib/sysimage/rpm` and `/usr/lib/sysimage/libdnf5`, which the
shipped `Format=disk` artifact does not. Two consequences:

1. The `RemoveFiles=` entries for the sqlite sidecars never affect the disk
   image. They are retained because they keep the directory comparison -- the
   actual measurement method -- meaningful.
2. The reproducibility result is sound but narrower than it reads. It
   establishes that the composition process is deterministic. It is not a direct
   measurement of the tree inside the artifact. A tighter method extracts the
   trees from two disk images and compares those.

Neither changes a G1 claim. See the [identity report](slice-identity-report.md).

## What this does not establish

- **Nothing boots yet.** The artifact has not been executed. Booting is
  PLN-0001-03, and a disk image that builds is not a disk image that starts.
  (Superseded by measurement: it boots, and it reaches `multi-user.target`
  after the PLN-0001-04 amendment. See the [boot record](slice-boot-record.md)
  and [identity report](slice-identity-report.md). The digests in this record
  predate that amendment; the manifest and kernel digests survived it unchanged,
  the UKI and initrd digests did not. **The amendment was reverted on
  2026-08-10 and all four digests above are current again**, reproduced exactly
  by a rebuild from the reverted fixture -- which is the evidence that the
  amendment was the only difference and that nothing else drifted underneath
  it.)
- **No mechanism is selected.** mkosi and Fedora 44 remain candidate fixtures.
  bootc and a literal Arch snapshot remain the required challengers, and this
  build working is not evidence for mkosi over bootc because bootc was not
  tried. See [PR-0029](reviews/0029-g1-gate-approval.md) C-005.
- **The declaration is enforced at one point only.** `LocalMirror=` makes the
  single frozen repository the only one that exists during the build, which is
  why `updates` cannot leak in. That is a property of this configuration, not a
  guarantee of the fixture: a future change to `Mirror=` would silently restore
  mkosi's default repository set, including `updates`.
- **`--nogpgcheck` is used when building the tools tree.** The tools packages
  are fetched from the frozen repository over TLS but their signatures are not
  verified, because the keys arrive in the same transaction that installs them.
  The image build itself does verify signatures. This is a real gap in the
  tools-tree path and is not closed by the digest pin on the base image.
- **No registered check guards any of this**, including agreement between
  `compose.sh` and `input-set.toml`, which repeat the same values. Slice tests
  register under PLN-0001-05.
