---
status: open
last_updated: 2026-08-11
governing_plan: PLN-0002
---

# The `/etc` path carve, and two collisions it exposes

PLN-0002-03a owes three things: a confext build path, a minimal `/etc` path
carve, and the completion of the `L`/`C` exception list that PLN-0002-02 left
open. The carve and the exception list are the same question, which is why the
plan puts them in one task.

Drawing the carve found something before any of the three was built. **The
factory replay PLN-0002-02 produced and the confext merge PLN-0002-01 measured
cannot both work as they currently stand.** Neither task could have seen it:
task 01 predates the factory, and task 02 has never had a confext merged over
its output. This document states both collisions, draws the carve anyway
because the carve is not what they turn on, and takes nothing.

**Nothing here is accepted.** Options carry arguments, not outcomes. Sole
acceptance authority is the owner.

---

## Collision 1: `L` on a directory forecloses the carve inside it

### What it is

The factory fragment emits **one line per top-level `/etc` entry**. Under the
ruling of 2026-08-11 the default disposition is `L`, so `/etc/systemd` becomes a
symlink into `/usr/share/factory/neutrinos-etc/systemd`.

A confext owning `/etc/systemd/network/` then has nowhere to land. The confext
merge is an overlayfs whose lower layers are the confext's `/etc` and the
existing `/etc`. Overlayfs merges *directories* across layers; it does not merge
a directory over a symlink. The confext's `/etc/systemd` directory therefore
**replaces** the linked one wholesale, and every release default underneath it
disappears from the running system.

> **Corrected 2026-08-11 by measurement.** This section first named
> `/etc/systemd` as the case, reasoning from the retained repository's file
> list. That list describes systemd **259.5**, the version the declared
> repository publishes. The artifact ships the **261 overlay**, and systemd 261
> installs its defaults in `/usr/lib/systemd/` rather than `/etc/systemd/`.
> `/etc/systemd` therefore never reaches the factory at all, and neither does
> `/etc/udev`. The example was wrong; the collision is not.
>
> This is worth keeping visible rather than editing away. The declared
> repository's index is not the artifact's file list whenever an overlay
> replaces a package, and the overlay exists precisely because the declared
> systemd is too old. Any future reasoning from `filelists` carries the same
> defect.

Measured against the built artifact. The generated fragment carries **68
entries, 59 `L` and 9 `C`**, and the directories among them that a confext
would plausibly own are `/etc/ssh`, `/etc/dbus-1`, `/etc/X11`,
`/etc/crypto-policies`, `/etc/security`, and `/etc/profile.d`. Each is a single
`L` line covering the whole tree, so a confext contributing one file into any of
them replaces the entire directory and hides every release default beneath it.

The failure is silent: nothing errors, and the machine boots without
configuration it was composed with.

### It was predicted

The [composition record](usr-artifact-composition.md) named it when the `L`
ruling was drafted:

> `L /etc/ssh` links the whole directory; nothing can then be added beside it
> per machine. [...] This interacts directly with PLN-0002-03a's carve and is
> the reason the two should be decided together.

So this is the anticipated cost arriving, not a new defect.

**But it does not bind the carve this task draws**, and that is the measurement's
second correction. Because systemd 261 keeps its defaults in `/usr/lib/systemd`,
`/etc/systemd` is not a factory entry, so a confext owning
`/etc/systemd/network/` collides with nothing. The carve below is clean as
drawn.

The collision is therefore **real, general, and not yet load-bearing**: it binds
the next carve rather than this one. `/etc/ssh` is the nearest case, and it
becomes live the moment the closure gains an sshd.

### Options

**A. Emit factory lines at greater depth for directories the carve enters.**
`/etc/systemd` stops being one `L` line and becomes one line per file beneath
it, so `/etc/systemd/network/` is a real directory in the lower layer and the
confext merges into it rather than over it. Costs a larger generated fragment
and a rule for how deep to descend -- which is itself carve-shaped, since the
answer is "as deep as the carve goes".

**B. `C` the directories the carve enters.** A copied tree is a real directory,
so the merge composes. Costs the C-006 property the `L` ruling was made for,
precisely on the paths configuration touches -- which is the worst place to lose
it -- and costs tmpfs for the copied bytes.

**C. Carve only whole top-level entries.** A confext owns `/etc/systemd`
entirely or not at all, and if it owns it, it must also carry every release
default underneath. Keeps the fragment simple and makes the disjointness rule
trivially checkable at the top level. Costs the reuse DES-0005's several-confext
ruling exists to capture: a machine changing one `.link` file now ships every
systemd default with it, and two machines differing in one file share nothing.

**D. The release ships no `/etc/systemd` defaults at all**, relocating what is
left of it into `/usr/lib/systemd` where systemd already searches. This is
option A of the relocate/discard/factory split applied further than task 02
applied it. Only some of the entries have a `/usr/lib` search path; the ones
that do not still need the factory, so it narrows the problem rather than
removing it.

### Argument

**A, and it makes the carve the input to the generator rather than a document
beside it.** The depth rule stops being arbitrary once the carve is a declared
artifact the finalize script reads: descend exactly where a confext owns
something, link at top level everywhere else. That also makes collision 1
mechanically impossible rather than reviewed for, which is the shape this
project prefers and which the disjointness rule already assumes is available.

C is the honest cheap answer and should be named as the fallback if A proves
awkward, because it fails loudly -- a confext that must carry every default
underneath it is visibly expensive rather than silently lossy.

B should be rejected. It restores writability exactly where configuration lives,
which is the C-006 surface, and it does so as a side effect of a granularity
problem rather than for a reason about the paths themselves.

---

## Collision 2: the factory cannot replay into a merged `/etc`

### What it is

This is the harder one and it is structural.

`systemd-confext-sysroot.service` runs **in the initrd** and merges into
`/sysroot/etc`. PLN-0002-01 measured the result:

```text
/etc   confext   overlay ro,nosuid,nodev,noexec,relatime,lowerdir=...
```

Read-only. The factory replay is `systemd-tmpfiles`, which runs **after
switch-root**, at `sysinit.target`, and which must *write* 68 entries into
`/etc`. It cannot. Every replayed entry fails, and with it every release default
that PLN-0002-02 exists to preserve.

Task 01 saw the read-only `/etc` and attributed unit presets failing to it --
that is finding 2. It could not see this, because there was no factory to replay
in that closure. Task 02 built the factory and has never booted with a confext
merged, because the repository outage blocked every build after the day the
ruling landed. **The two mechanisms have never run together, and as built they
are mutually exclusive.**

### Measured, 2026-08-11, and worse than it was reasoned to be

Four boots of the same artifact, one difference at a time. Full results in
"Measured results" below. The confext run:

```text
## etc entry count            2          (74 with no confext merged)
## sample replayed            /etc/os-release, /etc/passwd, /etc/machine-id
                              all: No such file or directory
## tmpfiles unit              Result=success   ExecMainStatus=65
## tmpfiles journal           Failed to create symlink '/etc/services': Read-only file system
                              Failed to copy files to /etc/shadow: Read-only file system
                              ... 24 more
## sysusers                   skipped, no trigger condition checks were met
## failed units               8, including dbus-broker.service and dbus.socket
```

The machine has no `/etc/passwd`, no `/etc/os-release`, no `/etc/machine-id`,
and no D-Bus. **And `systemd-tmpfiles-setup.service` reports `Result=success`
while exiting 65.** The unit says "Finished". That is the same silent-failure
shape PLN-0002-01 recorded for a refused confext, arriving in a second
mechanism, and it is the reason this would not have been caught by watching for
failed units.

### Upstream orders the merge first, deliberately

The stock unit, read from the built artifact:

```text
# systemd-confext.service
Before=sysinit.target systemd-tmpfiles-setup.service
```

So this is not an ordering accident to be corrected. **systemd's model is that
`/etc` is already populated when the confext merges**, which is true of every
system RES-0015 surveyed, all of which give `/etc` persistent writable backing.
NeutrinOS populates `/etc` at boot from a factory, and that is precisely the
pairing RES-0015 found nobody runs. This is the mechanical reason why.

Option B was measured and **fails on this**: ordering the merge after the replay
produces `Found ordering cycle: systemd-confext.service/start after
systemd-tmpfiles-setup.service/start`, and systemd breaks the cycle by
**deleting the merge job**. The factory replays, nothing merges, and
`systemd-confext status` reports `/etc none`. A silent loss of all
configuration, which is the worse of the two failure directions.

### Options

**A. Replay the factory in the initrd, before the merge.** `systemd-tmpfiles
--root=/sysroot` ordered before `systemd-confext-sysroot.service`, so the
factory content is in the overlay's lower layer and the confext composes over
it. Correct layering: release defaults below, configuration above, which is what
both mechanisms mean. Costs a new early-boot step that must be ordered against a
unit the release does not currently order anything against, and it moves work
into the initrd, which is inside the signed artifact and is one of the
asymmetries PLN-0002-05 must declare.

**B. Merge after switch-root instead.** `systemd-confext.service` is
`After=local-fs.target Before=sysinit.target`, so it can be ordered after
`systemd-tmpfiles-setup.service`. Uses only stock units and stock ordering.
Costs the C-013 property that configuration is present before switch-root:
nothing running earlier than `sysinit.target` can be configured by a confext.
This is finding 1's option E arriving from the other direction, and it makes
collision 2 an argument *for* E that RES-0015 did not have.

**C. The factory is not replayed into `/etc` at all.** Release defaults stay in
`/usr/share/factory/neutrinos-etc` and become a lower layer of the confext
overlay directly, rather than being copied into `/etc` first. Structurally the
cleanest -- one overlay, two layers, no write -- and it is not obviously
expressible: `systemd-confext` composes the layers it finds in the search paths,
and a factory directory is not a confext. It would need the release's own
defaults packaged as a confext, which fuses release and configuration in the way
DES-0005 separates them.

**D. Nothing merges over `/etc` in the fixture.** PLN-0002 measures formats.
Boot both arms with no confext, record that the confext path is exercised only
in task 10's substitution evidence, and hand the whole interaction to 03b.
Cheapest, and it costs the plan its claim to have booted the artifact C-013
actually describes.

### Ruling and outcome

> **Owner ruling, 2026-08-11: A for the design, B measured alongside it if
> possible and non-blocking.**

Both were measured the same day. **A works and B does not.**

Option A was implemented as an initrd unit running
`systemd-tmpfiles --root=/sysroot --create`, ordered
`Before=systemd-confext-sysroot.service`. The result is both mechanisms doing
what each was ruled to do:

```text
## confext status             /etc  neutrinos-network
## etc entry count            73
## etc symlinks into factory  59
## os-release readable        NAME="Fedora Linux"
## sysusers                   Finished systemd-sysusers.service
## etc writability            write refused
## failed units               1
```

Configuration merged, release defaults present, users created, `/etc` read-only.
Against 8 failed units and an unusable machine without it.

A also turns out to be the option that **does not fight upstream**. Moving the
merge later is a cycle, because upstream declares the ordering; moving the
replay earlier is not, because upstream declares nothing about a replay it does
not expect to exist. That is a better argument for A than the one this document
originally made for it, and it was only available after B failed.

Two residuals, neither blocking and both real:

- **The replay unit exits non-zero.** `systemd-tmpfiles --root=/sysroot
  --create` returns 73 on partial failures, so the injected unit shows as
  failed even though the replay succeeded. A production version needs a stated
  success criterion rather than the exit status, or it will be a unit that is
  always failed and therefore never watched.
- **73 entries against 74** in the no-confext baseline. One entry's difference,
  not chased, and worth attributing before this becomes a registered check.

D is what would have happened by inaction, and the measurement shows what that
costs: not a subtly wrong artifact but a machine with no `/etc/passwd` and no
D-Bus, produced by a build that reports success. Exactly PR-0030 C-006's shape
-- not a fixture becoming a decision, but a defect becoming a baseline.

C is recorded and not pursued. It is the right idea and the wrong owner:
whether release defaults can be a layer rather than a copy is DES-0006's
question about the boot chain, not a task's. The measurement strengthens it as a
question, since A is a workaround for `/etc` being populated by copy when the
mechanism above it expects it to be populated already.

---

## The carve, drawn

Drawn despite the collisions, because neither turns on which paths are chosen.
**Candidate, and handed back to DES-0005**, which owns path ownership and which
the [current context](current-context.md) records as never having drawn one.

### What "minimal" means here

The plan asks for a *minimal* carve, and minimal has a specific meaning: the
smallest set that makes the fixture a real confext rather than a marker file.
The spike's confext was a marker -- one file, `spike-in-usr.conf`, which proved
the merge happens and nothing about what a merge is for. A carve that stays at
that level would let tasks 08 and 11 assert things about a confext that no
release would ever ship.

### The carve

One confext, one subsystem, along the consumer lines DES-0005 requires:

| Confext | Owns | Failure policy | Why |
| --- | --- | --- | --- |
| `neutrinos-network` | `/etc/systemd/network/` | required, by the unclassified default | The only genuine configuration subsystem present in this closure, and the one a machine cannot usefully run without |

Everything else in `/etc` stays release-owned and stays in the factory.

### Why this subsystem and not another

The closure is declared as `systemd`, `systemd-boot`, `systemd-udev`,
`kernel-core`, `util-linux-core`, `dbus-broker`, resolving to 121 packages. It
contains no container runtime, no graphical stack, and no network manager other
than `systemd-networkd`.

Two other candidates were considered against the built artifact. `/etc/dbus-1`
is release policy rather than machine configuration, and a machine that rewrites
the system bus policy is doing something a confext should not make easy.
`/etc/ssh` is present -- `ssh_config.d/20-systemd-ssh-proxy.conf`, pulled in as
a dependency -- but the closure ships **no sshd**, so a confext configuring a
daemon the artifact cannot run would be a carve in name only. `/etc/udev` was
considered and does not exist: udev 261 keeps its defaults in `/usr/lib` too.

That leaves networking, which is real, is the thing a machine cannot usefully
run without, and -- as it turns out -- is the one candidate that collides with
nothing.

Machine identity is the other candidate and is **deliberately excluded**.
`/etc/machine-id` is finding 3, unresolved, and giving it to a confext here would
resolve `L-003` by task convenience -- the exact move the finding's argument
warns against.

### What the carve does to the exception list

**It depends entirely on how collision 1 is ruled, which is why the list cannot
be closed here.**

**Nothing, and now for a measured reason rather than a supposed one.**

Neither `/etc/systemd` nor `/etc/systemd/network` is a factory entry: systemd
261 ships its defaults in `/usr/lib/systemd`, and the finalize script prunes the
empty `network/` directory. The carve enters nothing that the factory replays,
so no disposition changes and **no new `C` exception follows from it**.

The exception list as built, measured rather than estimated:

| Disposition | Count | Entries |
| --- | --- | --- |
| `C` | 9 | `machine-id`, `passwd`, `shadow`, `group`, `gshadow`, `subuid`, `subgid`, `adjtime`, `ld.so.cache` |
| `L` | 59 | everything else |

That corrects the ruling record, which estimated 60 `L` against 8 `C` before a
build existed. The true split is **59 and 9** -- the estimate miscounted the
exception list against itself, which is a small error and exactly the kind that
only a build finds.

The list is therefore **complete for PLN-0002 and still incomplete for the
design**. What would extend it is a carve entering a populated directory, which
this carve does not do and the next one probably will.

---

## Measured results

Four boots, 2026-08-11, same artifact, one difference at a time, `snapshot=on`
with the artifact verified byte-identical after each. The probe is an injected
credential unit, so the artifact carries nothing that exists to make its own
test pass -- PLN-0001's rule, kept.

| Run | Confext | `/etc` entries | `os-release` | sysusers | `/etc` writable | Failed units |
| --- | --- | --- | --- | --- | --- | --- |
| Baseline | none | 74 | readable | ran | yes | 1 |
| Stock ordering | merged in initrd | **2** | **absent** | **skipped** | no | **8** |
| Option B | staged to `/run/confexts` | 74 | readable | ran | yes | 1, and **nothing merged** |
| **Option A** | merged after initrd replay | 73 | readable | ran | no | 1 |

The baseline's single failed unit is `authselect-apply-changes.service`, which
PLN-0002-02 already recorded as a pre-existing closure defect, carried rather
than caused.

## A defect the baseline boot found

The first boot was meant to be a control and was not. It found that **five
release paths ship as dangling symlinks**, `/etc/os-release` among them:

```text
head: cannot open '/etc/os-release' for reading: No such file or directory
```

`/etc/os-release` is a symlink to `../usr/lib/os-release`. Moved to
`/usr/share/factory/neutrinos-etc/`, that relative target means
`/usr/share/factory/usr/lib/os-release`, which does not exist. The same applies
to `issue`, `issue.net`, `fedora-release`, and `system-release-cpe`, with
`redhat-release` and `system-release` dangling through `fedora-release`.

This is **the same defect the finalize script already fixes for relocated
entries** and never applied to factory entries. The `retarget` function existed
and was simply not called on this path. The fix calls it, and the rebuild
resolves all seven; `/etc/os-release` now reads on the running machine.

Two things worth keeping from it. First, the [composition
record](usr-artifact-composition.md)'s "1906 resolve, 2 do not" measurement did
not catch this, because it resolved factory symlinks as if they were still at
their `/etc` path rather than at their factory path -- the measurement encoded
the same assumption as the bug. Second, systemd's own
`/usr/lib/tmpfiles.d/etc.conf` handles four of these paths correctly, and the
generated fragment sorts first and wins:

```text
/usr/lib/tmpfiles.d/etc.conf:10: Duplicate line for path "/etc/os-release", ignoring.
```

So the mechanism silently overrode a correct upstream line with a broken one.
Whether the fragment should skip paths upstream already owns is a real question
and is **not** answered here; it belongs to PLN-0002-02.

This is a **task-02 defect found by task 03a**, and it is recorded here because
this is where the evidence is. Task 02's disposition is the owner's.

## The signed confext, and a signature that is not enforced

Built 2026-08-11 and delivered as repository content:
`src/slice/confext/neutrinos-network/`, built by `compose.sh` before the
artifact that carries it. It is a real DDI with three partitions --

```text
neutrinos-network.raw1  504K  Linux root (x86-64)
neutrinos-network.raw2  508K  Linux root verity (x86-64)
neutrinos-network.raw3   16K  Linux root verity sign. (x86-64)
```

-- and it merges. `systemd-confext status` reports `/etc neutrinos-network`,
the factory replays beside it under option A, and `/etc` is read-only. That is
the deliverable PLN-0002-03a owed.

**It is also not enforcing its signature, and the failure is silent.** From the
same boot:

```text
device-mapper: table: 252:1: verity: Root hash verification failed (-ENOKEY)
device-mapper: ioctl: error adding target to table
erofs (device dm-1): mounted with root inode @ nid 36.
```

Signed verity is attempted, the kernel cannot resolve the signing key, the
device-mapper target is rejected -- **and systemd retries without the signature,
mounts the data partition, and merges.** Nothing fails. `systemd-confext status`
looks identical to a correctly validated merge.

### Why the key does not resolve

dm-verity signature validation resolves the signing key through the **kernel
keyring**, not through a file. Placing the certificate in `/usr/lib/verity.d/`
is where systemd looks and is not sufficient: the synthetic key is in no
keyring, so the kernel returns `-ENOKEY` regardless.

Getting it into a keyring needs a trust anchor -- firmware enrollment, MOK, or a
key built into the kernel. PLN-0002's boundary forbids production enrollment and
permits synthetic material in a disposable VM's own varstore, so this is
*achievable* within the plan and is **not** achievable by shipping a certificate
in the image, which is what was tried.

### Which keyring, verified against the pinned kernel

Checked offline on 2026-08-11 against `kernel-core 6.19.10-300.fc44` -- the
version the artifact manifest records, read from the cached RPM of the same
version, so this is the kernel under test and not a nearby one.

```
CONFIG_DM_VERITY_VERIFY_ROOTHASH_SIG=y
CONFIG_DM_VERITY_VERIFY_ROOTHASH_SIG_SECONDARY_KEYRING=y
CONFIG_DM_VERITY_VERIFY_ROOTHASH_SIG_PLATFORM_KEYRING=y
CONFIG_LOAD_UEFI_KEYS=y
CONFIG_INTEGRITY_MACHINE_KEYRING=y
CONFIG_INTEGRITY_CA_MACHINE_KEYRING_MAX=y
```

`..._SIG_PLATFORM_KEYRING=y` is decisive: root-hash signature validation on this
kernel accepts the **`.platform`** keyring, and `CONFIG_LOAD_UEFI_KEYS=y`
populates `.platform` from UEFI `db` and MokList. So enrolling the synthetic
certificate in the disposable VM's own `db` is sufficient. No MOK, no shim, no
kernel build.

The drafter had expected the opposite -- that MOK would be needed because db
keys stop at `.platform` -- and recorded the expectation as an expectation
before checking it. It was wrong. Worse for that route,
`CONFIG_INTEGRITY_CA_MACHINE_KEYRING_MAX=y` restricts `.machine` to CA
certificates, so the flat synthetic leaf would not be admitted there without
becoming a chain. The route reached by argument would have cost more and might
not have worked.

**One thing is read and not measured**: whether `.platform` is populated with
Secure Boot off. The reading is that the UEFI key load runs whenever EFI runtime
services are available, independent of Secure Boot state. Given that three
mechanisms in this plan have already failed open while reporting success, it is
listed as a measurement -- enroll, boot with Secure Boot off, inspect
`%:.platform` -- and not as a fact. If it is empty, Secure Boot must be enabled,
which widens the signed artifact and returns to the owner.

### The keyring route, measured in a VM

Run 2026-08-11, four boots, disposable varstore, artifact opened `snapshot=on`
and its digest verified unchanged after every boot.

Two defects in the harness were found first, and the first one matters beyond
this probe. **`boot.sh` uses `/usr/share/edk2/x64/OVMF_CODE.4m.fd`, which is
the firmware build with no Secure Boot support**: `SetupMode` and `SecureBoot`
do not exist as variables, there is no `db`, and therefore no UEFI certificate
could ever have reached the kernel. Every earlier statement in this plan about
signatures was measured on firmware where the mechanism was structurally
absent. Switching to `OVMF_CODE.secboot.4m.fd` also revealed that **mkosi
auto-enrolls its own Secure Boot keys**: systemd-boot finds
`\loader\keys\auto\{PK,KEK,db}.auth` on the ESP, enrolls them, and reboots, so
Secure Boot comes on by itself and `SecureBoot=1`. That was not known and is
not stated anywhere in the plan.

With that firmware, the keyring question is answered:

```
integrity: Loading X.509 certificate: UEFI:db
integrity: Loaded X.509 cert 'NeutrinOS PLN-0002-01 spike (synthetic, ...)'
keyring  .platform: 1
keyring  .machine: empty
```

`db` reaches `.platform`, exactly as the kernel config predicted, and
`.machine` stays empty, exactly as `CONFIG_INTEGRITY_CA_MACHINE_KEYRING_MAX=y`
predicted. Enrolling the **verity** certificate as well -- by rebuilding
`\loader\keys\auto\db.auth` as a two-certificate signature list, signed by the
key mkosi already enrols -- puts it there too:

```
keyring  .platform: 2
asymmetric  NeutrinOS PLN-0002-01 spike verity, synthetic: 25d0bcc0...
```

Guest-side enrollment was tried first and does not work after auto-enrollment:
efivarfs marks existing variables immutable, the write fails `Operation not
permitted`, and the artifact carries neither `chattr` nor python to clear it.
Enrolling at build time through the ESP is both simpler and closer to what a
real deployment does.

### What this does **not** yet show

**Enforcement is still not demonstrated.** The controlled pair is one boot with
the verity certificate in `db` and one without, everything else identical:

| | `.platform` | confext | `ENOKEY` on console |
| --- | --- | --- | --- |
| control | 1 key | merged | none |
| enrolled | 2 keys | merged | none |

The confext merges either way. A merge that is indifferent to whether its
signer is trusted is not a validated merge, so this is the **fourth** mechanism
in this plan observed to fail open, and the first one measured with the trust
anchor actually present rather than absent.

### The negative control, run

Two confexts built from the same source, differing only in signer: one signed by
the certificate enrolled in `db`, one by the valid-but-unenrolled second key.
Delivered through `/run/confexts` -- so this measures the **system** merge, not
the initrd merge -- into the same artifact, whose `.platform` holds both the
Secure Boot and the verity certificates.

| | kernel | `systemd-confext refresh` | merged | `/etc/systemd/network/` |
| --- | --- | --- | --- | --- |
| enrolled signer | no error | exit 0 | yes | `10-neutrinos-default.network` |
| unenrolled signer | `verity: Root hash verification failed (-ENOKEY)` | exit 0 | **yes** | `10-neutrinos-default.network` |

This is the clearest result the plan has produced on the question, and it
separates two things that were previously conflated.

**Signature validation now happens.** The enrolled key is the only difference
between the two runs, and the kernel discriminates on it: the correct signer
produces no error, the wrong signer produces `-ENOKEY` from
`device-mapper: table: verity` followed by `error adding target to table`. The
earlier `-ENOKEY` was the absence of any trust anchor; this one is a trust
anchor present and a signature genuinely rejected.

**And rejection changes nothing.** systemd falls back to unsigned verity,
mounts the image anyway, reports exit 0, and the configuration from the
untrusted confext is merged into `/etc` and present on disk. A confext signed
by a key the machine does not trust is applied exactly as if it were trusted.

So the mechanism is not "unavailable pending enrollment", which is what the
earlier reading allowed. It is **available, working, and not enforcing**. The
fallback is the defect, not the key.

This also gives the plan something it did not have: a harness that
discriminates. Any future attempt to make the merge fail closed -- an image
policy, a dissect option, a systemd version -- can now be tested against a pair
that is known to differ only in signer, instead of against an image whose
signature could not be checked at all.

### One attempt at making it fail closed, which did not

`systemd-confext --image-policy=root=signed` was applied to the sysroot merge
through a drop-in. The merge still succeeded with the same `-ENOKEY`. The most
likely reading is that the image policy governs **partition presence and flags
on the image** -- and the image genuinely has a verity-signature partition, so
`signed` is structurally satisfied -- while the cryptographic validation is a
separate kernel operation that failed and was fallen back from.

Stated as what it is: **one attempt with one documented flag, not a proof that
no policy prevents this.** `image_policy_confext_strict` exists as a named
built-in and was not reached through the CLI. What is measured is that the
obvious spelling does not close it.

**Superseded in part, 2026-08-11.** Passed directly to the CLI against an
enrolled key, the same spelling *does* close it -- see the matrix below. This
section stands as the record of the drop-in form, which still does not.

### The same flag, re-run against a trust anchor, and it does fail closed

Measured 2026-08-11, eight boots plus a warm-up, one policy per boot on a fresh
varstore, artifact digest unchanged. The disk is the enrolled one: the verity
certificate is in `db` and reaches `.platform`. Each boot receives one confext
as a second virtio disk, copies it to `/run/confexts`, and runs a single
`systemd-confext refresh`. Nothing else varies.

| policy | enrolled signer | unenrolled signer |
| --- | --- | --- |
| *(default)* | exit 0, merged | exit 0, **merged** |
| `root=verity` | exit 0, merged | exit 0, **merged** |
| `root=signed` | exit 0, merged | **exit 1, not merged** |
| `=signed` | **exit 1, not merged** | exit 1, not merged |

**`--image-policy=root=signed` is a fail-closed control.** It admits the image
signed by the enrolled key and refuses the one signed by a valid but unenrolled
key, with a non-zero exit and an empty `/etc/systemd/network/`. So the answer
to the pre-task-10 question is yes: a policy exists, it is a documented CLI
flag, and it discriminates on the signer rather than on the shape of the image.

Three things bound that:

- **`verity` is not enough.** `root=verity` merges both. The image genuinely
  carries a verity-signature partition either way, so only `signed` reaches the
  validation result.
- **`=signed` is the wrong spelling and fails closed on everything**, including
  the good image, because it demands the flag of every partition including the
  verity and signature partitions themselves. A policy that rejects the correct
  artifact is not a control; it is an outage. The designator has to be named.
- **This is the system merge**, `/run/confexts` through the `systemd-confext`
  CLI. It is not the initrd merge and not the unit-level default.

**This contradicts the attempt recorded above, and the contradiction is not
explained.** That attempt applied the same flag through a drop-in on the
sysroot merge and saw it merge anyway. Two differences are candidates -- there
was no enrolled key at all then, and the firmware had no Secure Boot support
(see the harness defect above) -- but the most likely reading is simply that
the drop-in did not govern the merge that ran. Recorded as unresolved rather
than reconciled: **the flag works when passed directly to the CLI, and has not
been shown to work when configured on a unit**, which is the form NeutrinOS
would actually ship.

### Why this matters more than it looks

This is the same shape as PLN-0002-01's central finding, in a third mechanism. A
corrupt `/usr` booted normally because dm-verity is lazy; a refused confext
reported `Finished`; and now an unvalidated signature merges and reports
success. **Three times, the mechanism that was supposed to fail closed failed
open and said nothing.**

It also converts PLN-0002-05's `systemd.image_policy=` item from a
completeness argument into a measured requirement. The plan's amendment argued
that NeutrinOS asserts `/usr` integrity by having mounted it successfully, which
is the weaker claim. This is that claim failing on the configuration half, in a
build, today.

And it bears directly on DES-0005's independent-signing question. RES-0015 found
medium-confidence evidence that confexts validate against the same key as EFI
binaries, so a confext partition buys independent delivery and not independent
signing. This measurement adds that **with no enrolled key at all, a signed
confext is indistinguishable from an unsigned one at merge time.**

### What it does not say

The image is not unprotected. Verity still runs against the root hash carried
in the image, so corruption is detected. What is absent is the binding between
that root hash and an authority: anyone who can replace the whole DDI supplies
their own root hash and it verifies. That is exactly the substitution PLN-0002-10
exists to inject, and this finding is a **prediction that it will pass** unless
signature enforcement is real by then.

That prediction now has a condition attached. With the signer enrolled and
`root=signed` passed to the merge, substitution is refused; with either missing,
it is not. **PLN-0002-10 therefore measures the configuration, not the
mechanism**, and the plan should say which of the two it is injecting against.

## The replay unit, landed, and what landing it changed

The option-A replay existed only as an SMBIOS credential a probe script injected.
It is now repository content:

| Path | What it is |
| --- | --- |
| `src/slice/composition/initrd/usr/lib/systemd/system/neutrinos-etc-factory.service` | the replay |
| `.../systemd-confext-sysroot.service.d/10-neutrinos-etc-factory.conf` | binds it to the initrd merge |
| `src/slice/composition/mkosi.finalize.d/10-initrd-etc-factory` | packs the two into a cpio for mkosi |

### There is no supported way to put a file in mkosi's default initrd

`ExtraTrees=` is not among the settings the synthesized `default-initrd` image
inherits, and the initrd-scoped settings are packages and profiles only. The
documented route is `$ARTIFACTDIR/io.mkosi.initrd`; finalize scripts run before
`install_kernel`, so a cpio written there reaches the UKI built from it.

Ours-last is structural rather than alphabetical, which the first version of
this section got wrong. `finalize_initrds()` returns
`config.initrds + sorted(artifacts glob)`, and mkosi injects its default initrd
into `config.initrds` -- so an artifact-dir entry already follows it whatever it
is called, and a repeated path in concatenated cpio archives resolves to the
last one. The `zz-` prefix orders us only against other artifact-dir entries,
of which there are none.

### The subimage route, considered and not taken

`mkosi.images/initrd/` with `Include=mkosi-initrd` would give upstream's initrd
definition plus a plain `mkosi.extra/` tree and no packing script. It works:
subimages inherit `Distribution=`, `Release=`, `LocalMirror=`, `ToolsTree=` and
`PackageDirectories=` as **universal** settings, so nothing would need
restating -- the obvious objection does not hold.

Two things decided against it. `Initrds=` has no output-directory specifier
(`%C`, `%P`, `%D`, `%I` and `%F` are all there is), so it would become another
absolute path passed from `compose.sh`, restating a declared input. And setting
it makes `want_default_initrd()` return `False`, so the default initrd is not
built at all -- the image stops *adding to* mkosi's initrd and starts *owning*
it. `Include=` would keep the content upstream, but not the wiring.

The deciding argument is PLN-0002-05's, not mkosi's: task 05 declares what is
inside the signed UKI, and "the default initrd plus these two files" is a
smaller claim than "our own initrd image that includes mkosi's definition".
Worth revisiting if that stops being true.

The cpio is built with pinned mtimes and `--owner=0:0`, because the initrd is
hashed into the UKI and the UKI's identity is how PLN-0001-07 verifies a
reconstruction. Verified in the built artifact: both files present, uid 0, mode
0644, mtime 0.

### Three defects, each found by a boot and none by review

**The scope was wrong.** `systemd-tmpfiles --root=/sysroot --create` exits
65/DATAERR in the initrd. `--root=` redirects the files tmpfiles writes; user
and group names still resolve through the *running* NSS, which is the initrd's,
and the initrd has no `audio`, `disk`, `kvm`, `systemd-journal` or `utmp`. Those
lines belong to `systemd-tmpfiles-setup.service` after switch-root anyway, so
the unit now names the one fragment it exists to replay.

**The fragment path is not `--root=`-relative.** A positional config path is read
by the running process from the running root. With the unprefixed path the unit
failed `No such file or directory` and `/etc` reached the merge with **7
entries**, which is the collision-2 failure again with a different cause.

**The unit outlived the initrd.** systemd serializes unit state across
switch-root and deserializes it against the artifact's units, where an
initrd-only unit does not exist -- so a `RemainAfterExit` oneshot returns as
`not-found failed` on the running machine even though its work succeeded.
`Conflicts=`/`Before=initrd-switch-root.target` stops it first.
`systemd-confext-sysroot.service` needs none of this only because the artifact
installs the same unit system-wide.

None of the three is exotic, and all three were introduced by writing the same
unit into a different place. The credential probe measured option A; it did not
measure shipping option A.

### Measured, with no credential supplied

| | |
| --- | --- |
| `confext status` | `/etc  neutrinos-network` |
| `/etc` entries | 70 |
| symlinks into factory | 59 |
| `os-release` readable | `NAME="Fedora Linux"` |
| `/etc` writability | write refused |
| replay unit | `Result=success`, stopped cleanly before switch-root |
| failed units | **0** |

### The cost of naming one fragment: four paths

70 entries, where the full initrd `--create` produced 73 and a boot with no
confext merged produces 74. The difference is systemd's own `etc.conf` lines for
`/etc/mtab`, `/etc/pam.d`, `/etc/credstore` and `/etc/credstore.encrypted`: no
longer applied before the merge, and afterwards `/etc` is read-only and they
fail.

This is not a defect of the unit. It is the `C`/`L` exception list question --
which paths must be established before the merge because a running system writes
them -- and those four are now concrete instances rather than hypotheses. The
list is this task's carve and is still unruled.

### Fail-closed, but only at one of the two merge points

The drop-in's `Requires=` was measured against a genuinely failing replay, and
`/etc` was still overmounted by the confext: the *post-switch-root*
`systemd-confext.service` merged it. That unit has no such dependency and cannot
acquire one, because the replay unit does not exist after switch-root.

So the guard covers the merge point it names and not the hierarchy. Closing the
second one is outside this carve; it is recorded so the gap is visible.

## Draft registration: T4-CONFEXT-001

Everything above is evidence produced by scratchpad scripts that do not exist
in the repository. `boot.sh` now asserts its own firmware, but nothing asserts
that `root=signed` still discriminates. A systemd bump that widened the
fallback, or a policy-parser change, would land silently and in the direction
that makes tests pass -- which is this plan's recurring failure mode, observed
four times. **Landed 2026-08-11**, after both of its open questions were ruled: the unit
form is what it tests, and it belongs to PLN-0002-10. What follows is the draft
as written, kept because the reasoning is the check's specification; the
"as built" section at the end records where it differs.

Proposed entry, in the shape `check.py` already uses:

```python
Test(
    id="T4-CONFEXT-001",
    level="T4",
    profiles=("complete",),
    timeout_seconds=900,
    traces=("PLN-0002/PLN-0002-10", "SYS-123", "DES-0005"),
    capabilities=(
        "declared slice artifact",
        "user-owned disposable VM",
        "Secure Boot firmware build",
    ),
    fixtures=(
        "composed disk image with the signer enrolled in db",
        "confext signed by the enrolled key",
        "confext signed by the unenrolled key",
        "disposable firmware variable store",
    ),
    cleanup_owner="validation runner",
    function="check_confext_signature_policy",
),
```

**The assertion is the 2x2, not the happy path.** Four boots, fresh varstore
each, one confext and one policy per boot. Per the ruling below, the policy is
applied as a drop-in on `systemd-confext.service` and the outcome read from the
unit, not from a command line:

| | `root=signed` | default policy |
| --- | --- | --- |
| enrolled signer | `success/0`, merged | merged |
| unenrolled signer | **`exit-code/1`, not merged** | merged |

Three of the four cells are the check. A run where the enrolled image is
refused is a broken control, not a pass; a run where the unenrolled image is
admitted under `root=signed` is the regression this exists to catch; and the
default-policy row is asserted as *merging* on purpose, because the day it
starts failing closed by itself is a fact this plan needs to learn rather than
a silent improvement. Artifact digest unchanged across all four, as T4-SLICE-001
already does.

### What it needed, and how each was met

- **Enrolment as a build step.** The enrolled disk was produced by hand:
  `sbsiglist` per certificate, concatenate the ESLs, `sbvarsign` with the
  synthetic PK, then `mcopy` the result into the ESP at
  `\loader\keys\auto\db.auth`. That is four tools (`sbsigntools`, `mtools`) not
  currently declared by the slice, and a partition offset currently hard-coded
  in a scratchpad script. It has to become a declared, reproducible step.
- **Two confexts from one source.** `compose.sh` builds one. The second must be
  the same tree signed by `verity-wrong.key`, so that the *only* difference is
  the signer -- otherwise a refusal does not distinguish a bad signature from a
  bad image, which is the whole reason the second key exists.
- **A warm-up boot, and a reason it is not load-bearing.** mkosi auto-enrols
  its own Secure Boot keys and reboots on first boot. The check must not
  measure that boot.
- **`sbsigntools` and the secboot firmware as declared capabilities.** Both are
  host facts the contract currently does not name. A host without the secboot
  OVMF build must **block**, not skip: a skip here reports the same shape as a
  pass, which is the defect the guard above was written for.

### Both open questions, ruled 2026-08-11 by Jason Tarasovic

1. **The unit form is what the check tests**, because it is what NeutrinOS
   would ship.
2. **It lands as part of PLN-0002-10**, not before it.

### The unit form, measured, and it closes

The ruling landed on the form previously recorded as *not* closing, so it was
measured before being written down as settled. Three boots on the enrolled
disk, digest unchanged. The policy arrives as a drop-in on
`systemd-confext.service` overriding `ExecStart`, confirmed in effect by
`systemctl show`:

```
/usr/bin/systemd-confext --image-policy=root=signed --mutable=ephemeral merge
```

| | enrolled signer | unenrolled signer |
| --- | --- | --- |
| unit result | `success/0` | **`exit-code/1`** |
| merged | yes | **no** |
| `/etc/systemd/network/` | `10-neutrinos-default.network` | **absent** |

**The unit form is strictly stronger than the CLI form**, and not only because
it is what ships. The failure is a *unit* failure -- `Failed to start
systemd-confext.service` -- so it is visible to the rest of the transaction and
other units can order and depend on it. A CLI exit code inside a script is
visible only to that script.

One methodological note, because the first attempt at this measured nothing.
The confext arrives on a second disk and so cannot be present for the unit's
boot-time run; restarting the unit is therefore how the drop-in gets exercised.
But `merge` refuses a hierarchy that is already merged, and **both arms failed
identically on `Hierarchy '/etc' is already merged'` before policy was ever
reached** -- a difference-free result that would have read as "fails closed for
everything" if taken at face value. An explicit `unmerge` first is what makes
the restart measure the policy.

**The contradiction with the earlier drop-in attempt is attributed, not
proven.** That attempt targeted the *sysroot* merge rather than the system one,
ran on the firmware with no Secure Boot support, and had no key enrolled
anywhere. Any of the three is sufficient to explain it. The earlier
configuration was not re-run.

## What this asks the owner for

Questions 1 through 4 were ruled on 2026-08-11 -- collision 1 as A, collision 2
as A with B measured alongside, the carve provisionally accepted, the exception
list left to the drafter. What the measurements then raised:

| # | Question | Blocks |
| --- | --- | --- |
| 5 | The initrd replay unit **is now repository content**, and it changes the initrd, which is inside the signed UKI. The PLN-0002-05 declaration is still owed | **PLN-0002-06**, hard |
| 5a | Four paths -- `/etc/mtab`, `/etc/pam.d`, `/etc/credstore`, `/etc/credstore.encrypted` -- are no longer established before the merge and now fail against a read-only `/etc`. They are instances of the exception-list question, not a separate one | **Ruled 2026-08-11 by Jason Tarasovic: option 3.** They become the first named entries of the exception list proper, and the general case is ruled by PLN-0002-03b/DES-0005, not here. They stay absent meanwhile: `/etc` is 70 entries instead of 74, with zero failed units. The replay is **not** widened to systemd's own `etc.conf`, which would re-open the exit-65 NSS problem. Carried into the list as a named sub-question: whether `/etc/credstore` and `/etc/credstore.encrypted` are separable from the other two, being credential-delivery paths that C-002 and DES-0011 own. **The sub-question is ruled 2026-08-12 by Jason Tarasovic: deferred to PLN-0002-03b** with the general exception-list question it belongs to, rather than answered here where answering it would settle credential delivery as a side effect of a tmpfiles list |
| 5b | `Requires=` on the replay is fail-closed for the **initrd** merge only. A failing replay still ends with `/etc` overmounted, by the post-switch-root merge | **Ruled 2026-08-12 by Jason Tarasovic: record only, carry to PLN-0002-03b.** It is a property of the delivery design rather than of this carve, and 03b owns that. The cost is stated rather than discounted: a known fail-open stays live through tasks 06 to 10, so any result in that range that depends on the replay having succeeded must say so, and a green boot is not evidence the replay ran |
| 6 | Collision 1's option A -- deeper factory emission -- is ruled but **not implemented**, because this carve does not need it. Implement now, or when the first carve needs it | **Ruled 2026-08-12 by Jason Tarasovic: when the first carve needs it.** Implementing against no failing case would add a code path nothing exercises. The trigger is named rather than left to memory: the first carve that enters a factory directory, `/etc/ssh` being the nearest, which goes live the moment the closure gains an sshd. Until then this row *is* the guard -- a carve that enters a factory directory and does not implement A silently replaces it |
| 7 | **Signature enforcement.** The signed DDI exists and merges, but its signature does not validate and the merge proceeds anyway. Making it real needs a synthetic key enrolled in the disposable VM's own firmware, which the plan permits and nobody has done | **Answered by measurement, 2026-08-12.** The key is enrolled, the control is `--image-policy=root=signed` applied as a drop-in on `systemd-confext.service`, and it is registered as `T4-CONFEXT-001` against PLN-0002-10 per the owner ruling of 2026-08-11. The prediction this row made -- that task 10's substitution would pass -- was correct for the mechanism as it stood, and is what the check now guards against |
| 8 | Should the generated fragment skip paths systemd's own `etc.conf` owns | **Ruled 2026-08-12 by Jason Tarasovic: skip them.** The fragment defers to `etc.conf` wherever upstream states a disposition. The argument is the defect's own history: upstream handled four of the five dangling release paths correctly while the generated fragment, sorting first, silently overrode it with a broken target. Re-deriving what upstream already gets right is surface that can only be wrong. Implementation is PLN-0002-02's, and it must be measured rather than assumed -- the entry count and the resolve/dangle counts both move |
| 9 | Is the tools-tree reuse acceptable, and should the slice adopt it rather than keeping two build roots | **Ruled 2026-08-12 by Jason Tarasovic: consolidate on the slice tree.** The spike's stated reason for a separate tree was the missing `createrepo_c`, and PLN-0002-02 added it to the slice recipe, so the two declarations are now byte-identical in package list and pinned base digest. One tools tree, one build root. The reuse that prompted this was never verified byte-for-byte because the repository was unreachable; it is reachable now, so consolidation is confirmed by a rebuild rather than by the declaration alone |

Question 5 is the one with a deadline that is not the plan's, and it is now
sharper than when this document was drafted: option A is not a configuration
choice but a **unit inside the signed initrd**, so it is part of the artifact
tasks 07 through 10 measure.

## Evidence status

**A build ran on 2026-08-11**, and everything above except collision 2 is
measured on the artifact rather than reasoned about it.

`dl.fedoraproject.org` still returns 403. The build did not need it. It composed
entirely offline from three things already on disk: the retained repository copy
as `--local-mirror=file://`, the retained systemd 261 overlay, and the tools
tree the PLN-0002-01 spike built before the outage. That last one is the part
worth stating carefully, because it is a declared input being reused rather than
rebuilt -- see "The tools tree" below.

The artifact is the `/usr`-only one PLN-0002-02 describes and had never
produced: a 246.7M EROFS `neutrinos-usr` partition with a 64M
`neutrinos-usr-verity` beside it and a 512M ESP, and **the systemd 261 overlay
is in the manifest**, which is the specific thing task 02 was blocked on. `/etc`
is empty in the tree and the finalize assertion passed.

Superseded, and kept because the sequence matters: when this was first written,
collision 2 was the one thing not measured, because no confext had been built.
Both have since happened -- the signed DDI exists, and collision 2 was measured
across four boots with it merged, then a further five while landing the replay
unit.

A superseded note, kept because it explains the correction above: the first
version of this document drew its `/etc` inventory from the retained
repository's `filelists` and `primary` indexes -- 1341 paths across 108
top-level entries in the declared 121-package closure. That method is sound for
the declared closure and wrong for this artifact, because the overlay replaces
the package whose paths mattered most.

## The tools tree

The build was possible because `~/.cache/neutrinos/pln0002/tools` survives from
before the outage. Reusing it is a reuse of a declared input and is recorded
rather than assumed:

- The tools-tree package list in `src/slice/compose.sh` and
  `src/spike/pln0002-01/spike.sh` is **byte-identical**, and so is the pinned
  base-image digest. The spike's stated reason for a separate tree -- that the
  slice recipe lacked `createrepo_c` -- was removed by PLN-0002-02, which added
  it. The two recipes have converged and nothing now distinguishes them.
- The tree resolved 83 packages from the declared repository, per its retained
  build log.
- **It was not rebuilt, so it is not verified byte-for-byte against the recipe.**
  Identical recipes produce identical trees only if the repository served
  identical bytes, and the repository is currently unreachable to check. This is
  a reuse justified by an identical declaration, not by a comparison.

Whether that reuse is acceptable, and whether the slice should simply adopt this
tree as its own rather than keeping two build roots, is the owner's. The
alternative that was **not** taken is switching the declared `LocalMirror=` to
the `download.fedoraproject.org` redirector, which serves the path with a 200
and which would change a declared input to route around an outage.

One note on the outage, since it bears on when this can be settled: the
retained repository copy under the slice build root holds the **image** closure,
121 packages, and not the tools-tree closure. The tools tree needs
`createrepo_c`, `erofs-utils`, `systemd-ukify`, `mtools`, and `squashfs-tools`,
none of which is retained, so retention does not unblock a tools-tree rebuild
and the recorded blocker stands as recorded. Two things were observed that are
not currently declared inputs and are **not** proposed here: the
`download.fedoraproject.org` redirector serves the same path with a 200, and the
PLN-0002-01 spike build root holds a tools tree built from the identical package
list before the outage. Either would unblock a build, and both change or reuse a
declared input, so both are the owner's.

### T4-CONFEXT-001 as built

`tools/validation/confext_policy.py`, registered in the `complete` profile,
five boots of which four are measured. Verified twice over: it passes against
the real fixture, and it **fails against two injected faults** --

- the unenrolled confext replaced by the enrolled one, which is a harness that
  cannot tell signers apart: *"an untrusted confext merged under root=signed;
  signature enforcement is not closing"*, plus a second failure for the unit
  having reported success;
- the non-Secure-Boot firmware restored, which is the defect that produced a
  whole spike's worth of signature evidence with the mechanism absent:
  `SecureBoot is '', expected 1`, in all four cells.

Secure Boot is asserted **per cell** rather than once, because a firmware
regression is invisible in exactly the cells it invalidates.

Four things differ from the draft, all found by running it:

- **db carries the image-signing certificate as well as the verity one.** The
  first fixture enrolled the verity certificate alone. That machine cannot
  boot: Secure Boot no longer trusts its own UKI, the firmware refuses it, and
  the run times out with an empty console. Enrollment replaces db rather than
  adding to it, so anything already trusted has to be re-supplied.
- **One variable store for the whole run, not one per boot.** A fresh store is
  in setup mode, so systemd-boot enrolls and reboots; a per-boot store makes
  every boot a first boot and the probe never runs.
- **`unmerge` before restarting the unit.** `merge` refuses an already-merged
  hierarchy, and without this both arms fail identically before policy is
  reached -- a difference-free result that reads as "fails closed for
  everything".
- **`/proc/keys` prints the type truncated to `asymmetri`.** Matching
  `asymmetric` counts zero keys on a machine that has them.

Two limits stand, and neither is the check's to fix:

- **It is unreachable through `mise run`.** `sandbox.deny_env = true` strips the
  declared fixture directory, so the check blocks. This is not new and not
  specific to it: `T3-SLICE-001` blocks the same way for the same reason, and
  the environment allowlist is governed by the validation contract.
- **The slice-side fixture has not been built.** It was exercised end to end
  against the PLN-0002-01 spike artifact, because this host has no slice tools
  tree and composition needs the network. `enroll-fixture.sh` is artifact-
  agnostic for exactly that reason, but the `compose.sh` wiring -- the second
  confext and the fixture staging -- is **written and unrun**.
