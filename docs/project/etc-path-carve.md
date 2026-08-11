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

## What this asks the owner for

Questions 1 through 4 were ruled on 2026-08-11 -- collision 1 as A, collision 2
as A with B measured alongside, the carve provisionally accepted, the exception
list left to the drafter. What the measurements then raised:

| # | Question | Blocks |
| --- | --- | --- |
| 5 | The initrd replay unit is repository content that changes the **initrd**, which is inside the signed UKI. It is a PLN-0002-05 declaration | **PLN-0002-06**, hard |
| 6 | Collision 1's option A -- deeper factory emission -- is ruled but **not implemented**, because this carve does not need it. Implement now, or when the first carve needs it | The next carve, not this one |
| 7 | The confext measured here is a **directory**, not a signed DDI. `image_policy_confext_strict` requires signed. 03a still owes the signed build path | 03a's completion |
| 8 | Should the generated fragment skip paths systemd's own `etc.conf` owns | PLN-0002-02, whose defect this is |
| 9 | Is the tools-tree reuse acceptable, and should the slice adopt it rather than keeping two build roots | Every subsequent build while the outage lasts |

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

What is **not** measured is collision 2. It needs a boot with a confext merged,
and no confext has been built yet.

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
