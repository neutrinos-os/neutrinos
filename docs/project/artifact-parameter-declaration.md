---
status: accepted
last_updated: 2026-08-12
accepted_by: Jason Tarasovic
accepted_date: 2026-08-12
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

**Accepted 2026-08-12 by Jason Tarasovic.** Two parts were declared and not yet
satisfied at acceptance, and acceptance was of that state rather than of a clean
one. Both have since been satisfied; the original text is kept and marked rather
than edited away, so the record shows what was accepted rather than only what is
now true.

- ~~The trimmed `KernelModules=` list is declared and **not yet measured**.~~
  **Satisfied 2026-08-12.** Both arms now boot to readiness with the trimmed
  list, no unit failures, artifact unchanged by the boot. The ext4 arm existed
  for the first time on that date; see "The initrd" below for the measurement
  and the arm-switch mechanism that produced it. This closes the last
  outstanding parameter before PLN-0002-06.
- The single verity signer subject of amendment 4 is **satisfied for the slice
  build root, 2026-08-12**, and deliberately not for the spike's. Both scripts
  now name `CN=NeutrinOS verity, synthetic` and guard on the subject of any
  certificate already present, because both guarded generation on the
  certificate *existing* -- so changing the string alone was a silent no-op on
  every build root that already had keys, and the parameter would have read as
  satisfied while every artifact kept the old signer. The slice regenerated and
  rebuilt; `/usr/lib/verity.d` in the artifact carries the declared subject and
  the full profile passes at 13. The spike's keys are untouched: its retained
  artifact is RES-0013's evidence and re-signing would change the thing the
  evidence is about, so a spike rebuild now stops until an operator adopts the
  subject deliberately.

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
default. **Confirmed by use, 2026-08-12**, not only by reading: two parameters
below travel this way, and the options are appended *after* repart's own, so an
override here wins over a builder default rather than colliding with it.

**Do not take the variable's name from mkosi.** mkosi at the pinned commit
spells its own ext4 workaround `SYSTEMD_REPART_MKFS_EXT4_OPTIONS`, which systemd
does not recognise; that workaround is therefore dead code at this pin. systemd
builds the name as `SYSTEMD_` + component + `_MKFS_OPTIONS_` + fstype, so the
form above is correct. Both spellings were tested against systemd-repart and
only this one has any effect. Nothing here depends on mkosi's version, but
anyone reading mkosi's source for the name will get it wrong.

mkosi's dead workaround is `-O ^orphan_file`, and its guard also evaluates false
for a Fedora image built with a Fedora tools tree, so nothing is being masked by
the wrong name. Confirmed on the built ext4 arm: `orphan_file` is present.

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
| Feature set | **builder default, less the journal** | Explicit feature tuning | Corrected 2026-08-12; see below. Tuning beyond the journal would make the arm something other than what a Fedora-composed ext4 image is |
| Journal | **removed**, `-O ^has_journal` | The builder default, a 16M journal | Ruled 2026-08-12. The partition is mounted read-only under dm-verity and can never write, so the journal is 16M of a measured size criterion buying nothing. Same principle that declared the EROFS arm compressed: measure the arm as it would ship. Measured: the feature bit is absent and there is no journal inode -- removed outright, not left disabled -- and the arm boots to readiness without it |
| Compression | **none, and not available** | — | ext4 does not compress. Recorded because it is the asymmetry the EROFS compression ruling has to be read against |

**`-O verity` was declared and was never true.** This table said the feature set
was "builder default plus `-O verity`", on the reasoning that repart adds it
when the partition is a verity data partition. The built filesystem has no
`verity` feature at all. The two things are unrelated: ext4's `verity` feature
is fs-verity, which authenticates individual files through the filesystem, while
this partition is authenticated by **dm-verity**, a block-level hash tree living
in its own partition and named on the kernel command line. repart therefore has
no reason to pass `-O verity` and does not.

Nothing was harmed -- the artifact was always dm-verity-sealed, which is what
C-013 relies on -- but the declared value did not describe the artifact, and it
was written from reasoning rather than from a measurement. It was caught the
first time anyone dumped the superblock of a built ext4 arm, which is an
argument for building both arms before freezing rather than after.

## Verity

| Parameter | Declared value | Reason |
| --- | --- | --- |
| Hash algorithm | **inherited** (repart default) | Not a free parameter of the format comparison; identical across both arms, so it cannot influence the result |
| Hash block size | **inherited** (repart default) | Same |
| Salt | **derived from `Seed=`** | Reproducibility. A random salt would make every build produce a different root hash and would defeat PLN-0001-07's reconstruction check |
| Signature partition | **present from PLN-0002-06** | Absent today by design; `mkosi.repart` records why. Task 06 adds it with its signing material |
| Signer subject | **`CN=NeutrinOS verity, synthetic`**, all build roots | Amendment 4. The subject is what is enrolled in `db` and what sits in `/usr/lib/verity.d`. The literal is named here because "one subject" is not a value a build script can check itself against, and both `compose.sh` and `spike.sh` restate it under a guard that fails when a build root's existing certificate disagrees |

**The lazy-verification limit is declared, not assumed away.** dm-verity
verifies per block on read, so neither arm's successful boot is a statement
about its artifact. This is a property of the mechanism and identical across
arms; it is stated here because tasks 08 and 09 must not read a clean boot as
evidence of integrity.

## The ESP, and build determinism

Held identical across arms, so nothing here can influence the comparison. It is
declared anyway, because it is what stood between this build and a
bit-reproducible disk image.

| Parameter | Declared value | Reason |
| --- | --- | --- |
| Filesystem | **vfat**, `mkfs.fat` 4.2 | Required by firmware. Not a choice |
| Size | **512M**, slack | A fixture, like the verity partition's 64M. Real sizing follows the task 07 measurements |
| Volume ID | **`4E455554`** (`NEUT`), declared | Was seed-derived; see below. It stops being derived and starts being declared, which is the trade `--invariant` demands |
| `mkfs.fat` options | **`--invariant -i 4E455554`** | Ruled 2026-08-12 |
| `Minimize=` | **`guess`**, both arms | Ruled 2026-08-12; see below |

**The disk image is bit-identical across rebuilds, including a rebuilt
confext.** Measured 2026-08-14: two full EROFS-arm builds produced the same
SHA-256 and zero differing bytes.

The 2026-08-12 measurement recorded here previously said the same thing and was
narrower than its claim. Its two builds differed by 2 bytes before the ESP
ruling and 0 after, and 2 bytes is only reachable with the confext **not**
rebuilt -- `compose.sh`'s `NEUTRINOS_SKIP_CONFEXT` guard reuses a previously
built one. The confext had no `Seed=`, so systemd-repart randomised its
partition UUIDs, filesystem UUID and verity salt on every build; the salt moves
the root hash, the root hash moves the signature, and the image changed by 607
bytes. `compose.sh` copies it into `/usr/lib/confexts`, so `/usr` changed by
1497 bytes and the artifact with it. A missing seed on a 1 MiB extension was the
larger of the two defects standing between this build and reproducibility, and
this section previously attributed all of it to the FAT volume label.

Fixed by `Seed=` on the confext, owner ruling of 2026-08-14, reusing the
composition's seed. **Any determinism evidence for this slice must state whether
the confext was rebuilt**, or it does not mean what it says.

Those 2 bytes were the creation time and write time of the FAT volume-label
directory entry, stamped by `mkfs.fat` from the wall clock. The mechanism was
established by measurement rather than inferred: with a fixed input tree and a
fixed volume ID, two runs differ by 18 bytes without `SOURCE_DATE_EPOCH`, by 2
with it, and by **the same 2 when no file is copied at all**. So `mcopy` was
never the problem -- mtools 4.0.49 honours `SOURCE_DATE_EPOCH` and mkosi already
exports it -- and `mkfs.fat` is the whole of it.

An earlier account of this in the project record said `SourceDateEpoch=0` "does
not reach `mkfs.fat`". That named the wrong mechanism. It reaches `mcopy` and
works there; `mkfs.fat` 4.2 has no `SOURCE_DATE_EPOCH` support at all, so
nothing could have reached it.

**4.2 is upstream's newest release, not a Fedora lag.** Tagged 2021-01-31, with
no release since; the `SOURCE_DATE_EPOCH` support exists on dosfstools master
and is unreleased. So `--invariant` is the lever that exists, and a future
dosfstools would solve this properly and give the seed-derived volume ID back.

**`-i` is paired with `--invariant` deliberately**, following the recipe at
[reproducible-builds.org](https://reproducible-builds.org/docs/system-images/).
`--invariant` alone also replaces repart's seed-derived volume ID with
dosfstools' hardcoded `1234abcd`. repart appends these options after its own
`-i`, so the explicit one wins and the ID becomes a value this document names.
Verified end to end through repart: unset gives 2 differing bytes and a
seed-derived ID; `--invariant` gives 0 and `1234abcd`; `--invariant -i 4E455554`
gives 0 and `4e455554`.

The recipe's other steps -- `faketime` around `mmd`/`mcopy`, and `LC_ALL=C sort`
for directory order -- are **not needed here**, because mtools already honours
`SOURCE_DATE_EPOCH`. That is why this build was 2 bytes away rather than dozens.

This is unsolved upstream in every comparable project: [mkosi#1212](https://github.com/systemd/mkosi/issues/1212)
proposed exactly this for the ESP and was never implemented, and `invariant`
appears nowhere in the pinned mkosi tree. [nixpkgs#286969](https://github.com/NixOS/nixpkgs/issues/286969)
and [archiso#105](https://gitlab.archlinux.org/archlinux/archiso/-/issues/105)
are the same defect.

**`Minimize=guess`, both arms. Ruled 2026-08-12, and it is a ruling against a
tempting alternative.** The ext4 arm's `/usr` partition is 439.8 MiB with
157.6 MiB free, because `guess` sizes it; EROFS packs, so it has no equivalent
slack. `Minimize=best` looks like the fix and **is not available**: `repart.d(5)`
supports `best` only for read-only filesystems and btrfs, so it would apply to
the EROFS arm alone and would *introduce* an asymmetry rather than remove one.
Holding `guess` on both keeps the setting a constant, as the initrd is.

**The consequence lands on PLN-0002-07, which must measure filesystem bytes in
use, not partition size**, and report partition size separately. A size figure
taken off the partition table measures repart's estimator on one arm and the
filesystem on the other. Measured on the built arms: EROFS 170.9 MiB, ext4
282.2 MiB in use against a 439.8 MiB partition.

## The kernel command line

Inside the signed UKI, therefore part of the artifact. Current value is
`root=tmpfs rw` and nothing else.

| Parameter | Declared value | Alternative not chosen | Reason |
| --- | --- | --- | --- |
| `root=tmpfs` | **keep** | `systemd.volatile=yes` | mkosi's spelling against systemd's own. They are not assumed identical: `systemd.volatile=` has a documented three-mode contract and no mode physically removes anything, while `root=tmpfs` is what the initrd acts on to create a root for `/usr` to mount into. `root=tmpfs` is what PLN-0002-01 and PLN-0002-04 booted, so keeping it holds a measured configuration; switching would re-open early boot immediately before the artifacts are frozen |
| `rw` | **keep** | `ro` | The tmpfs root is writable; `/usr` is read-only by its own mount. `ro` here would describe the wrong thing |
| `usrhash=` | **injected by mkosi, declared** | Suppress and set manually | Already the mechanism that makes the `/usr` mount verity-authenticated rather than merely successful. Declared so the root-hash-to-UKI binding PLN-0002-11 registers a check for is a stated property, not an observed one |
| `systemd.image_policy=` | **`usr=signed`** | Absent, as today, or `usr=verity` | Ruled 2026-08-12; landed in the UKI 2026-08-14 and measured there across both enrollment arms. **What it does is narrower than this row originally claimed, and the correction is recorded because the original claim was load-bearing.** It was described as the mechanism that makes task 09's and task 10's negative evidence fail closed. It does not. `usr=signed` is a *structural* predicate: `dissect-image.c` sets the SIGNED flag when the signature partition is **found**, with no verification and no keyring, so both the enrolled and unenrolled arms satisfy it. It is evaluated by `systemd-gpt-auto-generator` at ~5.25s in the real root, after the initrd mounted `/usr` at ~2.4s, and a generator's non-zero exit is non-fatal -- a mismatch logs and boots. `usr=verity` remains rejected on the original measurement. Naming `usr-verity=`/`usr-verity-sig=` is rejected as actively harmful: `signed` is a flag of the data partition, sets no flags on a verity partition, and no flags implies `open`, which permits absent. The value stands as declared; what changes is that it must not be cited as the integrity mechanism |
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
| `SOURCE_DATE_EPOCH` | **0**, inherited | Universal setting: mkosi rejects it in a subimage outright, so the composition's value is the initrd's. Load-bearing here even though it cannot be declared here, because the initrd's identity is what PLN-0001-07 verifies a reconstruction against |
| cpio compression | **zstd, level 3**, inherited | mkosi's default, found by reading the resolved configuration rather than assumed. Identical across arms, so it cannot influence the comparison -- but it is inside the UKI and it moves initrd size, so it is declared rather than left as a default nobody named |
| Ownership and mtime | pinned in the cpio | Same reason |

The two NeutrinOS units, by path and SHA-256 prefix:

| Path | Digest |
| --- | --- |
| `usr/lib/systemd/system/neutrinos-etc-factory.service` | `904efcfd8dd99bca…` |
| `usr/lib/systemd/system/systemd-confext-sysroot.service.d/10-neutrinos-etc-factory.conf` | `1c36ce085aaf857a…` |

### The module list binds on the composition, not on the initrd

Stated before the list itself, because the first implementation put it in the
wrong place and the build succeeded anyway.

`KernelModulesInitrd=yes` on the main image makes mkosi build a **second** cpio
from the main image's kernel modules and concatenate it onto the initrd. That
second cpio is selected by `KernelModulesInitrdInclude=` on the **composition**.
The initrd subimage's own `KernelModules=` selects from the initrd image's
kernel -- and that image has no kernel package, so it selects from nothing.

Measured, after the first attempt: the initrd subimage contained **zero kernel
modules**, while the composed initrd was 113.5M against the subimage's 35.9M.
The missing 77.6M was every module the kernel ships, arriving through the
setting nobody had named.

Two consequences beyond the correction. **Upstream's 98-module list never
governed the artifact either** -- it has the same shape, `KernelModules=` on an
initrd image -- so PR-0030 C-003's "both drivers ship in both arms" was true and
understated: every driver shipped in both arms. And this is the same failure
shape this plan keeps meeting, a configuration that looks authoritative,
produces no error, and does nothing. Left uncorrected, this declaration would
have recorded a 21-module initrd while the artifact shipped thousands, and tasks
07 and 08 would have measured against a list that was never applied.

The subimage keeps an empty `KernelModules=` reset, so upstream's list does not
sit there looking authoritative.

### `KernelModulesInitrdInclude=`

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

**Confirmed on both arms, 2026-08-12.** Each composed artifact boots to
readiness with the trimmed list: `/usr` mounts verity-authenticated, the boot
reaches the harness's vsock readiness signal, no unit fails, and the artifact is
unchanged by the boot. This is the acceptance evidence the ruling below asks
for, and it is complete.

The ext4 arm existed for the first time on that date, and it was built for this
confirmation rather than as part of PLN-0002-06. The plan's own standard is what
made that the right order: the list is inside the signed UKI, so confirming it
after 06 freezes the artifacts would cost the artifacts and everything measured
against them. Building an unsigned second arm to answer the question costs one
boot. **No signing material was involved and none of 06's work was done here.**

The arm is selected by `NEUTRINOS_SLICE_ARM`, not by editing a file. The shared
`composition/mkosi.repart/` holds every partition identical across arms -- the
ESP and the verity hash -- and `mkosi.repart.erofs/` and `mkosi.repart.ext4/`
each hold the one `10-usr.conf` that differs. Only the arm directory is passed;
mkosi picks the shared one up by path suffix and the command-line value appends
to it, verified against `mkosi summary` rather than assumed. Neither arm
directory can mask the other, because the shared directory has no file of that
name. An arm switch that lived in an edited working tree would mean no artifact
could be traced back to a declared value.

Verified as genuinely the other filesystem rather than a mislabelled rebuild:
superblock magic `0xef53` and volume label `neutrinos-usr` at the ext4 arm's
`/usr` partition offset, against `0x0ab0` at the same offset in the EROFS arm.

Output paths are asymmetric on purpose and temporarily: the EROFS arm keeps
`out`, which every registered check reads and every recorded artifact digest
refers to, and the ext4 arm gets `out-ext4`. PLN-0002-06 builds all four
artifacts as peers and is where the naming should become symmetric.

What it cost, measured on the same rebuild:

| | before | after |
| --- | --- | --- |
| Modules segment of the initrd | 77.6M | **6.0M** |
| Composed initrd | 113.5M | **40.3M** |
| UKI | 132.1M | **58.1M** |
| `neutrinos-usr` (also `lz4hc,12`) | 246.7M | **170.9M** |

Not zero and not everything, which is what says the include list matched a real
subset rather than failing open in either direction.

**Timing is deliberately not claimed.** Build time and boot behavior are two of
C-007's eight criteria and both need a matched pair -- same tree, one variable
moved -- which does not exist until 06 builds all four artifacts. One boot
measured 146.4s to readiness; there is no comparable prior number, because the
previous artifact was overwritten by the rebuild and the 18s in the
[boot record](slice-boot-record.md) is a different check's whole runtime, in a
record that says its numbers are not a timing baseline. Owner ruling
2026-08-12: measure it at PLN-0002-07 rather than now.

**Ruled 2026-08-12: the list is confirmed by booting both arms before 06 freezes
them.** An over-trimmed initrd fails as an unbootable artifact, which is a
failure `faults.sh` and the early-boot record already know how to diagnose --
but discovered at task 08 it costs the artifacts and everything measured against
them, and discovered here it costs one boot. The alternative of building on
upstream's 98 and trimming afterwards was rejected for the same reason: the trim
would land after 06 and void the measurements. A boot of both arms with this
list is the acceptance evidence. **That evidence now exists**, recorded above;
this table is no longer the outstanding part of this declaration.

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
| Verity signer | `CN=NeutrinOS verity, synthetic`, all build roots | disposable VM `db` |
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

Listed because a declaration whose implementation is missing is a document
rather than a parameter set. Status as of 2026-08-12.

1. **Done.** `mkosi.images/initrd/` subimage with `Include=mkosi-initrd`, the
   trimmed module list, and the two NeutrinOS units as a plain `mkosi.extra`
   tree.
2. **Done.** Retire `mkosi.finalize.d/10-initrd-etc-factory` and the `Initrds=`
   path handling in `compose.sh`. **Its header comment argued against the
   subimage** and was contradicted by the ruling; it was removed with the script
   rather than left to be read as current reasoning.
3. **Done.** `Compression=` and `CompressionLevel=` in the EROFS arm's
   `10-usr.conf`.
4. **Done, 2026-08-14.** `systemd.image_policy=usr=signed`, embedded in the UKI
   rather than appended, so the loader cannot drop it. See the row above for
   what it does and does not assert.
   The one parameter still owed, and it cannot be satisfied before PLN-0002-06:
   there is no signature partition for a policy to require, so setting it now
   would declare against an artifact shape nobody has built. It **must be
   measured**, not read off the manual -- the confext work found the broad
   `=signed` spelling refuses everything including the correct artifact.
5. **Done.** A boot of both arms confirming the trimmed module list, before 06
   freezes the artifacts. This is what required the arm switch, and the ext4 arm
   was built unsigned for it.
6. **Done.** `Environment=` in `composition/mkosi.conf` carrying
   `SYSTEMD_REPART_MKFS_OPTIONS_VFAT` and `SYSTEMD_REPART_MKFS_OPTIONS_EXT4`.
   Both parameters exist only in the environment repart is run with, so neither
   is expressible in a `repart.d` file.

**One parameter is owed and it belongs to task 06.** Everything else this
declaration obliges is implemented and measured. That is the state in which the
artifacts are ready to be frozen.
