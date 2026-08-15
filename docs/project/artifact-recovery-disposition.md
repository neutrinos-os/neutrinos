---
status: accepted
last_updated: 2026-08-15
governing_plan: PLN-0002
task: PLN-0002-12
accepted_by: Jason Tarasovic
accepted: 2026-08-15
---

# Recovery-behaviour disposition for the two `/usr` artifact formats

PLN-0002-12. **DES-0006 verification item 2 names recovery behaviour as the
eighth of C-007's criteria, and names `fstab` and `crypttab` in its early-boot
clause. This is the disposition of both.** **Accepted 2026-08-15 by Jason
Tarasovic**, including the deferral, which is therefore an accepted amendment to
verification item 2 rather than a proposal.

**The correction this record owes PLN-0002-07 is not covered by that
acceptance** and stays open; it is the last section below.

**This record recommends nothing about C-007.** PLN-0002-13 answers it.

Two things are settled by evidence and the third is the owner's ruling on them.

- **Settled by measurement**: what each format's own tooling can do with a
  damaged authenticated `/usr`. Neither arm's checker sees damaged **file
  data**; ext4's sees damaged **metadata** and EROFS's mostly does not; one arm
  has a repairer and running it destroys the artifact's authentication even when
  it finds nothing wrong; and both arms hand back a full-length file that is
  silently wrong. The criterion **ties on data and separates on metadata**, in
  ext4's favour and for diagnosis rather than for availability.
- **Settled by inventory**: what the artifact consumes before `/usr` is
  verified. There is no `fstab`, no `crypttab` and no `veritytab` anywhere in
  the initrd, while the machinery that would read them ships in both.
- **Accepted 2026-08-15**: that item 2's recovery criterion is answered at the
  format layer and **deferred at the system layer** to verification items 3 and
  5, which need A/B slots and are this plan's stated non-goal.

Figures are in `$NEUTRINOS_SLICE_BUILD_ROOT/evidence/pln0002-12/recovery.json`,
written by `src/slice/measure-recovery.py`. Nothing here boots; every cell is
offline, against the six artifacts PLN-0002-06 froze.

## What "recovery behaviour" can mean, and which layer this plan owns

Item 2 lists recovery behaviour beside image size and boot time, as a property
of a **format**. Verification items 3 and 5 name recovery again, as a property
of a **system**: slots, staging, blessing, ineligibility, and a terminal state
when every eligible deployment fails. The two are not the same criterion and
only one of them is answerable here.

| Layer | Question | Owned by |
| --- | --- | --- |
| Format tooling | Given a damaged authenticated `/usr`, what do the format's checker, repairer, and extractor do? | **This task. Measured below.** |
| Early boot | What is consumed before `/usr` is verified, and what would a `crypttab` even touch? | **This task. Inventoried below.** |
| System | Recovery boot after every eligible deployment fails; the terminal state; mutable state locked | Items 3 and 5, C-014 and C-015. **Deferred, accepted 2026-08-15** |

The system layer cannot be reached from inside PLN-0002 without building what
the plan excludes. A recovery boot presupposes an eligible deployment to fall
back to, which is A/B slots (item 3); the terminal-state claim is C-015's, whose
loop breaker DES-0006 records as a design commitment beyond SYS-038. This plan's
non-goals name both. Measuring it here would be the plan reaching past its own
boundary, and the disposition is a deferral for that reason rather than for
cost.

## The format layer, measured

One bit, flipped in a copy of the `/usr` data partition. **Eight cells: two
arms, four injection sites each** — two in file data, which is task 09's
injection chosen the same way in the same two files so the boot-side and
tooling-side records describe one event, and two in metadata, which is where a
checker has a mechanism to work with at all. Offline `veritysetup verify`
rejected all eight damaged images and accepted both pristine ones, which is the
control this record's other claims rest on.

### File data: neither checker sees it, and only one cell really asked

| Arm | Target | Metadata check | Content check |
| --- | --- | --- | --- |
| EROFS | `System.map` (compressed, 25.43%) | `fsck.erofs`: exit 0, silent | `fsck.erofs --extract`: exit 0, silent |
| EROFS | `vmlinuz` (98.77%, cluster stored raw) | exit 0, silent | exit 0, silent |
| ext4 | both | `e2fsck -fn`: exit 0, `11947/28224 files … 72289/112653 blocks` | **none exists** |

**Neither format's checker detects a flipped bit in file data — but three of
these four cells could not have detected it whatever the tool did**, and the
claim is worth only what the fourth is worth.

- **Both ext4 cells are structurally vacuous.** ext4 checksums metadata and
  never file data, and e2fsprogs ships no command that reads file content back.
  There is no mechanism to fail.
- **The EROFS `vmlinuz` cell is vacuous too.** At 98.77% the cluster is stored
  raw, so the flipped bit propagates one for one with no decompressor in the
  path — which is exactly what the salvage table below measures, 1 byte wrong.
- **The EROFS `System.map` cell is the real test**, and EROFS is the format that
  offers the test: `--extract` with no destination is documented as "check if
  all files are well encoded". The bit landed in a compressed cluster, the
  decompressor consumed the corrupt stream, **produced 27 wrong bytes, and
  reported nothing.** LZ4 carries no checksum of its own, so a decoder that does
  not happen to hit a malformed token returns success.

So for file data the only thing that detected the damage offline is dm-verity,
on both arms, as in the guest. The narrow, defensible statement is: **no
filesystem-level detection of data corruption exists on either arm, and on
EROFS the one mechanism that could have provided it did not fire.**

### Metadata: this is where the arms separate

Two more injections per arm, into a field a format covers with its own checksum:
the superblock, and the inode of `System.map`.

| Arm | Site | Field | Checker | Exit | What it said |
| --- | --- | --- | --- | --- | --- |
| ext4 | superblock | `s_blocks_count_lo` | `e2fsck -fn` | **4** | `Group 2 inode bitmap does not match checksum`, `WARNING: Filesystem still has errors` |
| ext4 | inode | `i_size_lo` | `e2fsck -fn` | **4** | `Inode 1775 passes checks, but checksum does not match inode` |
| EROFS | superblock | `blocks` | `fsck.erofs` | **0** | `<E> erofs: invalid checksum 0x5ad20e14, 0xd06ed389 expected`, `failed to verify superblock checksum` |
| EROFS | inode | `i_size` | `fsck.erofs`, `--extract` | 0 | **nothing** |

Three findings, and the first one is the answer to "could it have detected it".

**ext4 detects both, precisely, with a non-zero exit.** The declared feature set
carries `metadata_csum` — confirmed in the on-disk superblock, `crc32c`, seed
`0x79724991` — so every metadata structure is checksummed and e2fsck names the
inode by number.

**EROFS detects the superblock and exits 0 anyway.** It prints the expected and
actual CRC on stderr and returns success. A caller that checks the exit
status — a script, a `mise` check, a pipeline — records this artifact as clean.
The first draft of this harness did precisely that and scored the cell as
undetected, which is how the behaviour was found. **This is a genuine fail-open
in the same tool where PLN-0002-07 recorded one that is not** (see the
correction below), and it is a measurement hazard rather than a boot hazard.

**EROFS cannot detect the inode corruption at all.** EROFS checksums its
superblock and nothing else: no per-inode, per-directory or per-block checksum
exists in the format. A wrong `i_size` in an inode is simply believed. That is
not a tool deficiency and no version bump will change it.

So the eighth criterion **is not a clean tie**: for offline diagnosis of a
damaged artifact, ext4 is the more forensically legible format, by one whole
mechanism. What that is worth to C-007 is 13's to weigh, and this record notes
the counter-argument rather than resolving it: under dm-verity, no read of a
damaged block is ever served, so metadata checksums buy **diagnosis after the
fact**, not availability or integrity. Verity rejected all eight images
identically.

### The repairer is a liability where one exists

| Arm | Repairer | Run on a **pristine** image |
| --- | --- | --- |
| EROFS | **none**. `fsck.erofs` has no write path; `-a`, `-A` and `-y` are documented no-ops for fsck compatibility | not applicable |
| ext4 | `e2fsck -fy` | exit 0, **`FILE SYSTEM WAS MODIFIED`**, 72289 → 72298 blocks in use, and **`veritysetup verify` then fails** |

**Running the ext4 repairer on an undamaged authenticated artifact destroys its
authentication.** It reports no errors and returns 0, then optimizes directories
in pass 3A and writes. The bytes it writes are inside the region the signed root
hash covers, so the artifact no longer verifies against the UKI that carries it.
Nothing was wrong with the image and nothing was fixed.

This is measured on a pristine copy on purpose. Running the repairer on a
damaged image cannot separate the two reasons verity would reject afterwards —
the injected bit and the repairer's own writes — and the first draft of this
harness made exactly that mistake.

**The consequence is the same on both arms and it is a property of
authentication, not of a format**: an authenticated read-only `/usr` has no
in-place repair path, because any repair changes bytes that the signature
covers. Recovery of a damaged `/usr` is redeployment. EROFS having no repairer
is therefore not a deficit against ext4 here; ext4's is a footgun that its arm
carries and EROFS's arm cannot.

### Salvage succeeds, and both arms lie about it

Reading the damaged file back out with the format's own tool, and comparing it
byte for byte against the same file extracted from the pristine image:

| Arm | Target | Tool reported | Bytes out | Correct | Damage in the output |
| --- | --- | --- | --- | --- | --- |
| EROFS | `System.map` | success, exit 0 | 11,597,345 | **no** | 27 bytes over 3 blocks, offsets 5,901,455–5,909,544 |
| EROFS | `vmlinuz` | success, exit 0 | 18,479,464 | **no** | 1 byte at offset 9,136,631 |
| ext4 | `System.map` | success, exit 0 | 11,597,345 | **no** | 1 byte at offset 5,801,984 |
| ext4 | `vmlinuz` | success, exit 0 | 18,479,464 | **no** | 1 byte at offset 9,242,624 |

**Every cell produced a complete, plausible, wrong file and called it a
success.** No tool on either arm consults the verity tree, so offline salvage
bypasses the only mechanism that knows the bytes are wrong. An operator
recovering a file from a damaged artifact by these routes gets no signal at all.

The format difference is real and small: the compressed EROFS cluster spreads
one flipped bit into 27 wrong bytes across an 8 KB span, while ext4 and the
already-compressed EROFS target propagate exactly the one bit. That is the same
mechanism task 09 measured at the read, three orders of magnitude smaller,
because salvage has no block-granular refusal to trigger — the verity layer that
turns 1 bad byte into 4 KiB of refusal is not in this path. **The two figures
are not comparable and must not be summed or substituted for one another**: task
09's blast radius is what a running machine loses, this is what a forensic
extraction gets wrong.

### What the format layer decides

| Sub-question | EROFS | ext4 | Separates? |
| --- | --- | --- | --- |
| Detect damaged file data | no | no | no |
| Detect damaged metadata | superblock only, **exit 0**; inode not at all | both, exit 4, names the inode | **yes, ext4** |
| Repair | no repairer exists | exists, and voids the artifact's verity | no — both are "do not repair" |
| Salvage | succeeds, silently wrong, 27 bytes over an 8 KB span | succeeds, silently wrong, 1 byte | no |

**One of the four sub-questions separates the arms, and it separates them on
diagnosis rather than on availability.** The salvage asymmetry — 27 bytes
against 1 — is the same mechanism task 09 measured at the read, three orders of
magnitude smaller, and points the same way, so it adds no independent weight.
The recovery criterion is therefore **not the fifth tie this record first
claimed**: it is a tie on three sub-questions and a measured advantage to ext4
on the fourth, whose weight depends on how much a NeutrinOS operator is expected
to diagnose an artifact that dm-verity has already refused.

## The early-boot clause, and `crypttab`

Item 2 requires early boot exercised: "`fstab`, `crypttab`, and any initrd-stage
configuration consumed before `/usr` is verified". PR-0030 C-001 asked what is
done about `crypttab` given that encryption is a non-goal. The answer is an
inventory of the artifact rather than an appeal to the non-goal.

Measured over the initrd of both primaries — the same initrd, digest
`a29e59c713b9…`, 4,398 members — and over the `/usr` tree of each arm:

| Named by item 2 | In the initrd | In `/usr` |
| --- | --- | --- |
| `etc/fstab` | **absent** | — |
| `etc/crypttab` | **absent** | — |
| `etc/veritytab` | **absent** | — |
| `systemd-fstab-generator` | present | present |
| `systemd-cryptsetup`, `systemd-cryptsetup-generator`, `cryptsetup.target` | present | present |
| `systemd-veritysetup`, `systemd-veritysetup-generator` | present | present |
| `usr/lib/verity.d/verity.crt` | **present** | present |

**The machinery ships and has nothing to read.** Fedora's systemd packaging puts
the cryptsetup generator, the binary and the targets in the image whether or not
anything is encrypted; the generators run, find no `crypttab`, and generate no
units. So `crypttab` is not merely out of scope — **there is no `crypttab` in
this artifact to exercise, and no path by which one is consumed**. The same is
true of `fstab`: the mount comes from `usrhash=` and the dissection path, not
from a table.

What *is* consumed before `/usr` is verified, measured rather than assumed:

1. **the kernel command line**, inside the signed UKI;
2. **the initrd's own tree**, including `/usr/lib/verity.d/verity.crt` — the
   trust anchor for the signature — also inside the signed UKI; and
3. **the GPT partition UUIDs on the disk**, which are *not* signed.

Item (3) is the one unsigned input to the pre-verification stage, and it is not
hypothetical: it is what rejected task 10's `pair-content` and `pair-seed` cells,
which failed at device resolution before verity was ever reached. Recorded here
because exit criterion 4 asks for everything consumed before `/usr` is verified,
and the honest list is three items and not two.

**Accepted disposition of the `crypttab` element** (2026-08-15): item 2's early-boot clause is
satisfied by (1) and (2) and is **not satisfiable for `crypttab` under this
plan's encryption non-goal**, because no `crypttab` exists to consume. It goes to
DES-0006 verification item 6, which owns LUKS2 unlock, rotation, header
backup/restore and the rest, and to `S-004`. SYS-052 through SYS-056 are already
classified not applicable to this plan on the same grounds.

## The system layer, and what emergency mode does and does not settle

Task 10 measured what happens when a substituted image is rejected: **all eight
image cells reach `emergency.target`, `/usr` unmounted and the root account
locked**, on both arms and under both firmware states. That is a measured
terminal state, and it is the fact this disposition has to rule against.

Three things follow, and only the first is this task's to state.

- **It is terminal, not a loop.** The machine does not retry, does not select
  another deployment, and does not sit in an indefinite selection cycle. C-015's
  concern is a loop; nothing observed here loops.
- **It is not a recovery path.** `emergency.target` with a locked root account
  and no `/usr` is a machine that has stopped, on a fixture with no second slot
  to fall back to and no recovery image to reach. Whether that is the *right*
  terminal state for NeutrinOS is C-015's question and the owner's.
- **It is not evidence about either format.** Identical on both arms, so it
  carries no weight for C-007.

The fixture makes this narrow in a way worth stating plainly: a single-slot
disposable VM has nowhere to recover *to*. "Every eligible deployment failed" is
trivially true when there is one deployment, so item 5 cannot be exercised here
even in principle.

## Correction owed to PLN-0002-07, and to the standing fail-open count

**`fsck.erofs --extract=X --path=<file>` does not fail open.** The
[measurements](artifact-format-measurements.md) record it as the plan's seventh
fail-open — "prints `Extracted filesystem successfully`, exits 0, and writes
nothing. Only a directory path extracts anything" — and that is a harness
artifact, not a tool behaviour.

What the tool does: it writes the file's content **to `X` itself**, and refuses
with exit 1 if `X` already exists. `measure-artifact-set.py` passes a fresh path
as `X` and then searches for the file *inside* `X` with `rglob`, so it looks
past a file that is sitting exactly where it asked for it and scores zero bytes.
This harness made the identical mistake in its first draft, which is how the
behaviour came to be re-examined.

Measured on the same probe task 07 ran, `--path=/lib/os-release`, on both the
tools-tree `fsck.erofs` 1.9 and the host's 1.9.3: exit 0 and **629 bytes** at the
destination path. The four salvage cells in the table above are the same
behaviour on 11 MB and 18 MB files.

Two consequences, both the owner's:

- **PLN-0002-07's inspectability finding overstates the EROFS cost.** The
  single-file route works; the directory-extraction fallback it describes is not
  needed. The other half of that finding — that erofs-utils reaches this host
  only through the declared tools tree while e2fsprogs is already installed — is
  unaffected and still holds.
- **The plan's standing fail-open count does not drop.** The retracted instance
  is replaced by a real one **in the same tool**: `fsck.erofs` detects a
  corrupted superblock, prints both CRCs, and **exits 0**. It is still a
  measurement hazard rather than a boot hazard, so the shape of the standing
  finding is unchanged and only its evidence moves. The other instances are
  untouched, and task 10's signature fail-open, which `T4-SLICE-003` and
  `T4-SLICE-004` carry, is not affected in any way.

Both records are accepted, so neither is corrected here. **This remains a
proposal after the 2026-08-15 acceptance, which deliberately did not cover
it.**

## What this record does not claim

- **No C-007 recommendation.** A tie on the eighth criterion is still 13's to
  weigh with the rest.
- **No system-recovery claim.** No slot selection, no fallback, no blessing, no
  ineligibility marking, no recovery image. Items 3 and 5 are untouched.
- **No encryption claim.** Nothing encrypted was built, unlocked, or measured.
  SYS-051's position is unchanged.
- **The metadata cells are two sites, not a survey.** One superblock field and
  one inode field per arm. They establish that the mechanism exists on ext4 and
  is absent on EROFS below the superblock, which is a property of the formats;
  they do not measure how much of a real corrupted artifact each checker would
  characterize correctly.
- **Nothing about the *consequence* of metadata damage.** No damaged-metadata
  image was booted. Task 09 booted data-damaged copies; whether a wrong `i_size`
  or a wrong block count changes the boot is untested, and under verity it
  should never be reached.
- **No claim that e2fsck is unsafe generally.** It is unsafe *on an
  authenticated artifact*, which is the only context this plan has.
- **No physical-role claim.** Offline tooling against retained artifacts, with
  synthetic signing material.

## Carried risks

- **The synthetic signing material expires 2026-09-11.** This task built
  nothing; the artifacts are unchanged.
- **The ParticleOS command-line ruling of 2026-08-12 is still open**, and
  settling it in its own favour rebuilds the artifact set and voids these
  measurements with the rest.
- **The accepted deferral leaves item 2 partly unmet by design.** PLN-0002 exit
  criterion 2 is satisfied for recovery behaviour by a stated disposition rather
  than by a system-layer measurement, and verification items 3 and 5 carry that
  debt into the plan that owns them.
