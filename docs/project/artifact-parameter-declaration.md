---
status: draft
last_updated: 2026-08-12
governing_plan: PLN-0002
---

# Declared parameter set for the two artifact arms

This is PLN-0002-05's deliverable. The plan's standard is stated in the task
itself -- *declare before building; an undeclared parameter invalidates the
comparison* -- and it is the reason this document exists at all: every value
below is one that would otherwise be inherited silently from a tool default and
then read back out of a measurement as though it had been chosen.

**Nothing here is accepted by its author.** Every value below was ruled by
Jason Tarasovic on 2026-08-12 -- four rulings that bound the drafting, recorded
in the next section, and four taken on the draft itself: the compression
algorithm and level, `systemd.image_policy=`, and how the trimmed module list is
confirmed. Where a recommendation was declined or narrowed, that is recorded
rather than edited away.

**One part is declared but not yet measured**: the trimmed `KernelModules=`
list, whose confirmation is a boot of both arms before PLN-0002-06.

**Deadline: before PLN-0002-06.** Every parameter below is inside the signed
UKI or inside the artifact it authenticates. A change after 06 means tasks 07
through 10 measured a different artifact and are void.

## What was already ruled

Four rulings on 2026-08-12 by Jason Tarasovic constrain this declaration and are
treated here as settled inputs, not as open options.

- **The initrd is a `mkosi.images/initrd/` subimage** with `Include=mkosi-initrd`,
  replacing the additive `$ARTIFACTDIR/io.mkosi.initrd` cpio.
- **`KernelModules=` is a trimmed list, identical across both arms.** The
  subimage route makes a per-arm list expressible; the ruling declines to use
  it. That is a stronger position than it looks and the reason is recorded
  under "The initrd" below.
- **mkfs parameters that bear on C-007's criteria are pinned**; the rest are
  inherited and named as inherited.
- **The EROFS arm is declared compressed** -- the arm as it would ship, rather
  than an uncompressed image chosen for parity with a format that cannot
  compress.

A fifth, from the same day, is carried by
[amendment 4](../plans/0002-usr-artifact-format-spike.md): **one certificate
subject for the verity signer** across every build root.

## The builder is not the shipped systemd

Stated first because it conditions everything below. The tools tree resolves
**systemd 259.5-1.fc44**, and the image ships **systemd 261.999+1208**. So
`systemd-repart` -- which formats both arms, builds both verity trees, and
decides every default this document either pins or inherits -- is 259.5, one
major version behind the systemd the artifact runs.

That is a real asymmetry and it was undeclared until now. It is not obviously
wrong: the builder's job is to produce bytes, and pinning it independently of
the shipped systemd is arguably correct. But it means "the default" in every
row below is 259.5's default, and a tools-tree rebuild that moved to 261 could
move the artifact without any file in this repository changing.

**Recommendation: declare the builder version as a parameter of the comparison**
and pin it, which the tools tree already does by recipe. The alternative --
aligning the builder with the shipped systemd -- is defensible and is *not*
recommended here, because it would couple the build to the overlay that exists
only because Fedora 44 ships systemd 259.x, and that overlay is a fixture.

`Compression=` and `CompressionLevel=` are documented "Added in version 257",
so both are available in the pinned builder. Confirmed against the installed
`repart.d` documentation.

## What systemd-repart actually passes

Measured from systemd's `src/shared/mkfs-util.c` at `v259`, not assumed. This
matters because three of the parameters the plan asks task 05 to declare turn
out to be fixed by the builder rather than free.

**erofs:**

```
mkfs.erofs -U <uuid> [--quiet] [-z <algorithm>[,level=<n>]] <node> <root>
```

Nothing else. No cluster size, no block size, no feature flags. `-z` appears
**only** if the partition sets `Compression=`.

**ext4:**

```
mke2fs -L <label> -U <uuid> -I 256 -m 0 -E nodiscard,lazy_itable_init=1 \
       -b 4096 -T default [-d <root>] [-q] [-O verity] <node>
```

So inode size (256), reserved-block percentage (0), and block size (4096) are
**already fixed by the builder** and are not ours to choose without overriding.
Inode ratio is not passed at all: it comes from `mke2fs.conf`'s `default` type
in e2fsprogs 1.47.3.

Both accept appended options through `SYSTEMD_REPART_MKFS_OPTIONS_<fstype>`,
which is the mechanism available if a pin below needs to override a builder
default.

## The EROFS arm

| Parameter | Declared value | Alternative not chosen | Reason |
| --- | --- | --- | --- |
| Compression algorithm | **`lz4hc`** | `lz4`, `zstd`, `lzma`, `deflate` | `lz4hc` compresses harder than `lz4` at the same decompression cost, and decompression is what the boot path pays on every read. `zstd` and `lzma` compress better and cost more per read, which would move four measured criteria at once and in opposite directions |
| Compression level | **12**, the top of the algorithm's range | Any level the algorithm accepts, or the tool default | Build time is measured separately as its own criterion, so paying it here appears in the results rather than disappearing into them. It also gives the format its best showing on the size criteria, which is the right direction for an arm declared as it would ship |
| Cluster size | **inherited** | `-C <n>` via the override env var | `mkfs.erofs` derives the physical cluster size from the block size when `-C` is absent, and repart does not pass it. Pinning it would be pinning a value with no measurement behind it |
| Block size | **inherited** (page size, 4096 on x86-64) | Explicit `-b` | Not passed by repart, and a non-page-size block size changes mount behavior in ways this plan has no reason to explore |
| UUID | **derived from `Seed=`** | Random | Already true and already load-bearing for reproducibility; stated so it is not read as incidental |

**The uncompressed default is the finding that produced this section.** Before
this declaration, `mkosi.repart/10-usr.conf` set no `Compression=`, so the EROFS
arm was being compared against ext4 with the format's principal advantage
switched off, on two criteria that measure exactly that advantage. Nothing had
declared it, and no measurement would have revealed it, because an uncompressed
EROFS image is not an error -- it is simply a different artifact than the one
anyone would deploy.

**Stated so the result is not overread:** with compression on, part of any
EROFS image-size and transfer-size win is compression rather than on-disk
format. PLN-0002-13's recommendation must say so.

## The ext4 arm

| Parameter | Declared value | Alternative not chosen | Reason |
| --- | --- | --- | --- |
| Block size | **4096**, fixed by the builder | Override to 1024 or 2048 | Matches the page size; smaller blocks cost throughput and gain nothing on an image of this size |
| Inode size | **256**, fixed by the builder | 128 | Builder default; 128 forecloses extended attributes and is a regression for no measured gain |
| Reserved blocks | **0%**, fixed by the builder | The mke2fs 5% default | Correct here and worth stating: reserved blocks exist for a writable root's fragmentation headroom, and this filesystem is read-only and verity-sealed. This is a case where the builder's default is better than the tool's |
| Inode ratio | **inherited** from `mke2fs.conf` `default` in e2fsprogs 1.47.3 | Explicit `-i` | Named as inherited per the ruling. It bears on image size, but only through inode-table sizing on a fixed file count, and the file count is a property of the closure rather than of the arm |
| Feature set | **builder default plus `-O verity`** | Explicit feature tuning | `verity` is added by repart when the partition is a verity data partition. Tuning the rest would make the arm something other than what a Fedora-composed ext4 image is |
| Compression | **none, and not available** | — | ext4 does not compress. Recorded because it is the asymmetry the EROFS compression ruling has to be read against |

## Verity

| Parameter | Declared value | Reason |
| --- | --- | --- |
| Hash algorithm | **inherited** (repart default) | Not a free parameter of the format comparison; identical across both arms, so it cannot influence the result |
| Hash block size | **inherited** (repart default) | Same |
| Salt | **derived from `Seed=`** | Reproducibility. A random salt would make every build produce a different root hash and would defeat PLN-0001-07's reconstruction check |
| Signature partition | **present from PLN-0002-06** | Absent today by design; `mkosi.repart` records why. Task 06 adds it with its signing material |
| Signer subject | **one subject, all build roots** | Amendment 4. The subject is what is enrolled in `db` and what sits in `/usr/lib/verity.d` |

**The lazy-verification limit is declared, not assumed away.** dm-verity
verifies per block on read, so neither arm's successful boot is a statement
about its artifact. This is a property of the mechanism and identical across
arms; it is stated here because tasks 08 and 09 must not read a clean boot as
evidence of integrity.

## The kernel command line

Inside the signed UKI, therefore part of the artifact. Current value is
`root=tmpfs rw` and nothing else.

| Parameter | Declared value | Alternative not chosen | Reason |
| --- | --- | --- | --- |
| `root=tmpfs` | **keep** | `systemd.volatile=yes` | mkosi's spelling against systemd's own. They are not assumed identical: `systemd.volatile=` has a documented three-mode contract and no mode physically removes anything, while `root=tmpfs` is what the initrd acts on to create a root for `/usr` to mount into. `root=tmpfs` is what PLN-0002-01 and PLN-0002-04 booted, so keeping it holds a measured configuration; switching would re-open early boot immediately before the artifacts are frozen |
| `rw` | **keep** | `ro` | The tmpfs root is writable; `/usr` is read-only by its own mount. `ro` here would describe the wrong thing |
| `usrhash=` | **injected by mkosi, declared** | Suppress and set manually | Already the mechanism that makes the `/usr` mount verity-authenticated rather than merely successful. Declared so the root-hash-to-UKI binding PLN-0002-11 registers a check for is a stated property, not an observed one |
| `systemd.image_policy=` | **`usr=signed`** | Absent, as today, or `usr=verity` | The substantive gap. NeutrinOS currently asserts `/usr` integrity **by having mounted it**, which PLN-0002-01 showed to be unsafe when a corrupt artifact booted normally. This is the mechanism that makes task 09's and task 10's negative evidence fail closed for a stated reason instead of incidentally, and it is the same class of control that closed the confext signature question. `usr=verity` was rejected on that measurement rather than by analogy: verity alone did not discriminate on the signer, because the image carries a signature partition either way. **It must be measured before 06**, for the same reason -- the confext work found that the broad `=signed` spelling refuses everything including the correct artifact, so the designator being right is a result and not a reading of the manual |
| `systemd.image_filter=` | **absent** *(recommended, needs ruling)* | Set by label | Becomes load-bearing at task 06, which builds a second same-format artifact per arm as task 10's substitution source. Recommended absent **now** and revisited at 06, because setting it before the second artifact exists would be declaring against a shape nobody has built |
| `systemd.confext=` | **absent** | Set explicitly | Whether the merge happens is currently decided by unit presence. Relevant to the finding-1 fixture and to whatever 03b decides; setting it now would harden a fixture into an assertion |

## The initrd

**Route: a `mkosi.images/initrd/` subimage** with `Include=mkosi-initrd`,
ruled 2026-08-12. Subimages inherit `Distribution=`, `Release=`,
`LocalMirror=`, `ToolsTree=` and `PackageDirectories=` as universal settings, so
nothing needs restating. Two costs are accepted with it: `Initrds=` has no
output-directory specifier, so the path is passed from `compose.sh`, and setting
it makes `want_default_initrd()` return False -- NeutrinOS stops adding to
mkosi's initrd and starts owning it.

That last is the point rather than a side effect. "The default initrd plus these
two files" is a smaller declaration only while the default is not itself a
declared parameter, and amendment 3 made it one.

### Contents

| Item | Declared value | Reason |
| --- | --- | --- |
| Base | `mkosi-initrd` at pinned mkosi `84af2089` | It *is* mkosi's default initrd -- `finalize_default_initrd()` parses `resources/mkosi-initrd` in place -- so this is the same initrd, invoked explicitly |
| Packages | `systemd`, `udev`, `bash`, `less`, `gzip` | Upstream's set, unchanged. Trimming it is a build-time saving against an emergency-login capability the plan may need when a boot fails |
| `RemoveFiles=` | upstream's set, unchanged | Catalogs, hwdb, kernel images, `/var/cache`, `/var/log` |
| NeutrinOS units | 2 files, below | PLN-0002-03a's replay unit and its drop-in, inside the UKI's signature and therefore release content |
| `SOURCE_DATE_EPOCH` | **0** | Already set; the initrd's identity is what PLN-0001-07 verifies a reconstruction against |
| Ownership and mtime | pinned in the cpio | Same reason |

The two NeutrinOS units, by path and SHA-256 prefix:

| Path | Digest |
| --- | --- |
| `usr/lib/systemd/system/neutrinos-etc-factory.service` | `904efcfd8dd99bca…` |
| `usr/lib/systemd/system/systemd-confext-sysroot.service.d/10-neutrinos-etc-factory.conf` | `1c36ce085aaf857a…` |

### `KernelModules=`

Upstream's list is **98 modules** and is a general-purpose list for arbitrary
hardware: it carries `btrfs`, `squashfs` and `xfs` into an artifact that mounts
none of them, and it carries **both `erofs` and `ext4`**, which is PR-0030
C-003's named outcome -- "both drivers ship in both arms and neither artifact is
the one that would ship" -- measured rather than predicted.

**Ruled: a trimmed list, identical across both arms.** The subimage route makes
a per-arm list expressible and the ruling declines to use it. The reason is that
it makes the initrd a **held constant**: if the two arms' initrds differ, then
initrd size, boot time and memory differ partly because of the initrd, and the
comparison stops isolating the filesystem. Shipping the other arm's driver is
the price of that, and it is a small and stated one.

**The two filesystem drivers are not symmetric, and "both in both" hides that.**
Measured on the built confext, not assumed: `neutrinos-network.raw` is a
3-partition DDI whose root partition is **erofs**, and the merge runs *in the
initrd* through `systemd-confext-sysroot.service`. So:

- **`erofs` is required by both arms** -- by the EROFS arm for its `/usr`, and
  by **both** arms for the confext. The ext4 arm cannot mount its configuration
  without it.
- **`ext4` is required by one arm**, and is genuinely surplus in the other.

The held-constant argument therefore carries `ext4` only. `erofs` needs no such
justification and would be in both lists under any ruling. This is worth stating
because "both drivers in both arms" reads as a symmetry and is not one, and
because a later trim that reasoned from the arm alone would remove `erofs` from
the ext4 initrd and break the confext merge rather than the boot -- the silent
direction.

Two related things confirmed while drawing the list, so neither is carried as an
assumption. Verity signature validation needs **no module**:
`CONFIG_LOAD_UEFI_KEYS=y` and
`CONFIG_DM_VERITY_VERIFY_ROOTHASH_SIG_PLATFORM_KEYRING=y` are built in, verified
offline against `kernel-core 6.19.10-300.fc44`. And `loop` is required for the
DDI attach, which is why it appears under the confext role rather than as
general-purpose slack.

Recommended list, by role:

| Role | Modules |
| --- | --- |
| Virtual hardware | `virtio_pci`, `virtio_blk`, `virtio_console`, `virtio-rng`, `qemu_fw_cfg` |
| Harness readiness | `vsock`, `vmw_vsock_virtio_transport` |
| Authenticated `/usr` | `dm-mod`, `dm-verity`, `crypto/` |
| Filesystems | `erofs` (both arms: `/usr` and the confext), `ext4` (one arm's `/usr`) |
| ESP | `vfat`, `/fs/nls/` |
| Confext merge | `overlay`, `loop` |
| Firmware access | `efivarfs` |

**Ruled 2026-08-12: the list is confirmed by booting both arms before 06 freezes
them.** An over-trimmed initrd fails as an unbootable artifact, which is a
failure `faults.sh` and the early-boot record already know how to diagnose --
but discovered at task 08 it costs the artifacts and everything measured against
them, and discovered here it costs one boot. The alternative of building on
upstream's 98 and trimming afterwards was rejected for the same reason: the trim
would land after 06 and void the measurements. A boot of both arms with this
list is the acceptance evidence, and until it exists this table is the one part
of this declaration that is not yet measured.

Deliberately excluded, and named so the exclusion is a decision: `tpm_tis` and
the TPM path generally. The fixture has no TPM, PLN-0001-04's standing finding
is that the tss2 runtime libraries are absent from the closure while systemd is
built `+TPM2`, and `T4-SLICE-001` currently fails on two systemd 261 TPM units.
Adding the module would not fix that and would obscure it.

## Signing material identity

Per amendment 4. All synthetic, generated into the build root, destroyed with
it.

| Role | Subject | Enrolled in |
| --- | --- | --- |
| Verity signer | one subject, all build roots | disposable VM `db` |
| Image signer | distinct | disposable VM `db` |
| Second verity key, unenrolled | distinct | nothing, deliberately |
| Platform key | distinct | disposable VM `PK`/`KEK` |

The three remain distinct because `T4-CONFEXT-001`'s entire content is which
signer `db` holds; collapsing them would make the measurement unreadable.

## What this declaration does not cover

Named so nothing here is read as wider than it is.

- **Partition sizing.** The ESP's 512M and the verity partition's 64M are slack,
  not measurements, and `mkosi.repart` says so at each. Real sizing follows the
  task 07 measurements rather than preceding them.
- **Confext delivery.** PLN-0002-03b, sequenced after 06.
- **Persistence and machine identity.** `S-004` and `L-003`. The fixture boots
  on a transient identity and measures nothing that depends on continuity.
- **Whether mkosi is the mechanism.** It is a candidate fixture. bootc remains
  the deployment-substrate challenger and nothing in this document selects
  anything.

## Implementation this declaration obliges

Not done, and listed because a declaration whose implementation is missing is a
document rather than a parameter set.

1. `mkosi.images/initrd/` subimage with `Include=mkosi-initrd`, the trimmed
   `KernelModules=`, and the two NeutrinOS units as a plain `mkosi.extra` tree.
2. Retire `mkosi.finalize.d/10-initrd-etc-factory` and the `Initrds=` path
   handling in `compose.sh`. **Its header comment argues against the subimage**
   and is now contradicted by the ruling; it must be removed with the script
   rather than left to be read as current reasoning.
3. `Compression=` and `CompressionLevel=` in
   `mkosi.repart/10-usr.conf`, once the algorithm and level are ruled.
4. `systemd.image_policy=` on the kernel command line, once ruled.
5. A boot of both arms confirming the trimmed module list, before 06 freezes
   the artifacts.
