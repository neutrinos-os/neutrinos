---
status: active
last_updated: 2026-08-11
governing_plan: PLN-0002
---

# `/usr`-only early-boot spike record

PLN-0002-01. The plan's most likely falsification, run first behind a hard
stop-and-return gate: if DES-0006 C-013's early-boot assumption were false,
nothing else in PLN-0002 would be worth building.

**Result: the assumption holds, and the boot path works.** A `/usr`-only
artifact, authenticated by dm-verity with its root hash carried on a signed
UKI's command line, boots to `multi-user.target` on a tmpfs root with no
persistent storage of any kind. `systemd-confext-sysroot.service` exists, runs
in the initrd, merges a confext into `/sysroot/etc` before switch-root, and the
merge survives into the running system. The gate is not triggered.

**Four findings came with it, and three of them are the owner's.** The most
consequential is not a failure of the mechanism but a consequence of it: with a
confext merged, `/etc` is a read-only overlay, so first-boot unit presets cannot
be written and four units fail. That is C-006 working as ruled, and it means
service enablement has to move somewhere it currently is not.

Nothing here accepts a mechanism. EROFS was used because one format had to be
picked to boot at all; PLN-0002-05 declares the parameters and PLN-0002-06
builds both arms, and this spike's choice is not an input to that comparison.

## What was built

A throwaway composition at `src/spike/pln0002-01`, deliberately outside
`src/slice` and deliberately not held to the slice's declaration discipline.
PLN-0002-02 owns the real composition and starts from `src/slice/composition`,
not from here.

| Element | Value |
| --- | --- |
| Distribution | Fedora 44, from the same frozen repository the slice declares |
| systemd | `261.999+1208+g827144298-4747.1`, overlaid (see below) |
| Kernel | `6.19.10-300.fc44.x86_64` |
| `/usr` format | EROFS, 244.4M minimized, read-only |
| Verity | dm-verity hash partition, 64M allocated |
| Root hash | `6cb6dbe22883a0aaf6e3c7a6a8cd1a2b0847904cad1c9f98a6f592a68fa9454c` |
| Root partition | **none** -- `root=tmpfs`, per the owner's 2026-08-11 ruling |
| Signing | Synthetic, generated per build root, 30-day, never enrolled |
| Disk image | 821.4M, of which 373.7M consumed |

The command line inside the signed UKI, read back out of its `.cmdline` PE
section:

```text
usrhash=6cb6dbe22883a0aaf6e3c7a6a8cd1a2b0847904cad1c9f98a6f592a68fa9454c root=tmpfs rw console=ttyS0
```

## The systemd overlay, and why it exists

Fedora 44 ships systemd 259.5 and stays on the 259.x series -- Bodhi shows
259.5 through 259.8, all stable, and Fedora does not rebase systemd across
major versions within a release. `systemd-confext-sysroot.service` is **new in
systemd 261**. Confirmed in both directions: absent from the shipped `/usr` tree
and the initrd of the retained PLN-0001 artifact, present in the host's 261.2,
and announced under `CHANGES WITH 261` with the limitation it was added to
overcome stated in upstream's own words --

> extensions merged from the main system itself cannot be used to modify the
> resources which are used in the early boot

which is verbatim the thing C-013 relies on it for. **So the declared closure
could not exercise the mechanism C-013 names.** That is an inputs defect, not a
design defect: the mechanism exists upstream and does what C-013 says.

Two candidate sources were examined and rejected before the third was found.
ParticleOS, the closest executable reference, solves this by setting
`Release=rawhide` on Fedora and pulling Debian experimental on Debian; it
publishes no overlay packages. Fedora's own `updates` cannot help, as shown
above, and is excluded by the declaration anyway.

**The OBS `system:systemd` project publishes builds for Fedora 44 directly**,
alongside Fedora 43, rawhide, Debian 13 and testing, Ubuntu 24.04 and 26.04,
Arch, and Tumbleweed. It carries exactly the six subpackages the closure uses.
Owner ruling, 2026-08-11: take them as a **local package overlay, one fixture**,
not as a second repository. `LocalMirror=` therefore keeps enforcing the single
frozen repository by construction, which is the guarantee F-RES-01 proved
convention does not provide.

The overlay is a nightly, replaced upstream in place, so the retained copy is
the input and the URL is only its provenance. `spike.sh` retains the six RPMs
and writes their SHA-256 digests. PLN-0002-02 is where this becomes a declared
input with a check behind it; today the digest file is compared by eye.

**The overlay landed, and it was verified rather than assumed.** F-RES-01 is the
recorded case of a substitution passing unnoticed, so both the manifest and the
running system were checked: the manifest lists all six packages at
`261.999+1208+g827144298`, and pid 1 reports `systemd 261.999+1208+g827144298`
in the initrd and again after switch-root.

## The boot path, observed

The chain is visible end to end in the console log and every link was measured,
not inferred:

1. The signed UKI's command line carries `usrhash=`.
2. `systemd-veritysetup-generator` derives **both partition UUIDs from the root
   hash itself** -- data at `6cb6dbe2-2883-a0aa-f6e3-c7a6a8cd1a2b`, hash at
   `0847904c-ad1c-9f98-a6f5-92a68fa9454c`, which are the first and second halves
   of the hash. The command line does not name partitions; it names a hash, and
   the hash finds its own partitions.
3. `systemd-veritysetup@usr.service` sets up `/dev/mapper/usr`.
4. `sysroot.mount` mounts a tmpfs; `sysroot-usr.mount` mounts the verity device
   into it.
5. `systemd-confext-sysroot.service` merges the confext into `/sysroot/etc`.
6. `initrd-switch-root.service` switches root.

In the running system:

```text
/usr   /dev/mapper/usr   erofs   ro,relatime,user_xattr,acl,cache_strategy=readaround
/      rootfs            tmpfs   rw,relatime,mode=755,inode64
/etc   confext           overlay ro,nosuid,nodev,noexec,relatime,lowerdir=...
```

`systemd[1]: Successfully made /usr/ read-only.` SYS-049's read-only half is
demonstrated here in a way PLN-0001 could not demonstrate it; the authenticated
half is demonstrated by the verity chain above. Neither is claimed as complete
satisfaction -- SYS-049 stays **partial** in PLN-0002's trace, and the covered
cells are PLN-0002-10's to enumerate.

## Finding 1: the confext merge works, and only from inside `/usr`

`systemd-confext status` in the running system:

```text
HIERARCHY EXTENSIONS   SINCE
/etc      spike-in-usr Tue 2026-08-11 18:42:21 UTC
```

The confext was placed at `/usr/lib/confexts/spike-in-usr`, inside the
authenticated artifact. Of the four search paths, that was the **only one that
existed**: `/run/confexts`, `/var/lib/confexts`, and `/usr/local/lib/confexts`
were all absent, and so was `/.extra`.

That is not an accident of this fixture, it is what a tmpfs root means.
`systemd-confext-sysroot.service` searches `/sysroot/var/lib/confexts`,
`/sysroot/usr/local/lib/confexts`, and `/sysroot/usr/lib/confexts`. With no
persistent root partition, the first two are empty tmpfs on every boot. **The
only surviving location is inside the release artifact** -- which would put
configuration inside the thing DES-0005's amendment separates it from.

**This is the owner's to resolve and it is not resolved here.** The tmpfs root
was ruled for this plan's fixture, and it is the right fixture for a format
comparison. But if a deployment has no persistent `/var`, a separately
delivered signed confext has nowhere to live, and the amendment's delivery model
needs a location this spike did not find. Three candidates were **not** tested
and are named so nobody reads their absence as a rejection: an ESP-delivered
confext reaching `/run/confexts` before the sysroot merge, a UKI addon through
`/.extra/confext`, and a persistent `/var` supplying
`/sysroot/var/lib/confexts` as DES-0006's machine-state volume would.

The `/.extra` path deserves a specific warning. It is a search path of
`systemd-confext-initrd.service` **only**, and that service merges into the
*initrd's* `/etc`, which is discarded at switch-root. A confext delivered
beside the UKI does not reach the real `/etc` by that route.

## Finding 2: read-only `/etc` breaks first-boot presets

Four units failed: `ldconfig.service`, `systemd-logind.service`,
`systemd-journalctl.socket`, and `systemd-logind-varlink.socket`. They share one
cause, and it is upstream of all of them:

```text
systemd[1]: Failed to preset all unit: Unit /etc/systemd/system/sockets.target.wants/dbus.socket does not exist
systemd[1]: Failed to preset all unit: Unit /etc/systemd/system/dbus.service does not exist
```

and roughly twenty more of the same shape. First-boot preset works by writing
enablement symlinks into `/etc/systemd/system`. `/etc` is a read-only overlay,
so **every one of them failed**, `dbus.socket` was never enabled, and logind and
its dependents failed behind it.

The causality is worth stating precisely, because it inverts the obvious
reading: `/etc` is read-only **because a confext is merged**. With no confext,
`/etc` would be an ordinary writable tmpfs and presets would have succeeded.
This is C-006 working exactly as ruled on 2026-08-11 -- a durable write to `/etc`
fails at the moment it is attempted -- and the price is that **runtime unit
enablement is not available at all**.

So enablement has to move. It can be baked into `/usr/lib/systemd/system/*.wants`
at composition, or delivered by a confext, or presets can be applied at build
time rather than first boot. **Which one is a design question and it belongs to
DES-0005 or DES-0006, not to a spike.** It is recorded here and taken nowhere.

## Finding 3: `/etc/machine-id` with a read-only `/etc`

```text
systemd[1]: System cannot boot: Missing /etc/machine-id and /etc/ is read-only.
```

The machine booted anyway -- systemd fell back to a transient identity in
`/run`, and the report shows a machine ID present. But the message is systemd
announcing a condition it considers fatal, and a transient machine ID changes
on every boot.

This lands squarely on C-013's recorded consequence that per-machine identity
cannot live in `/etc` and passes to `L-003`. It is evidence for that deferral,
not a resolution of it, and the spike takes no position on where machine
identity should come from.

## Finding 4: the write probe

```text
touch: cannot touch '/etc/spike-write-probe': Read-only file system
```

C-006 requires that a durable write to `/etc` fail at the moment it is
attempted. It did. **The qualification matters more than the result**: it failed
because the overlay is mounted read-only, and the overlay exists because a
confext is merged. On a deployment with no confext merged, this probe would
have succeeded and the write would have silently vanished at reboot -- the
"silent non-durability" outcome C-006 names as worse than a hard failure.

The mechanism that guarantees the property in the no-confext case is DES-0005's
to design, and this spike did not find one.

## Failure capture, established here for every later task

PR-0030 C-009 made this task 01's job so that later tasks are not inventing
diagnostics while something is already broken. Three failures were induced, each
one deviation from the reference artifact and nothing else.

**Two of the three did not fail the way the plan assumed, and that is the
finding.**

### Root-hash mismatch: a single byte flipped inside the authenticated `/usr`

The UKI, root hash, and signature were all left correct; one byte was flipped
1000 blocks into the `/usr` partition, in data verity covers rather than in a
header something else would reject first.

**The machine booted normally.** Same targets reached, same four failed units as
the reference, no verity complaint of any kind. dm-verity verifies **lazily, per
block, on read**: nothing in the boot path happened to read block 1000, so
nothing checked it.

The diagnostic exists and is precise, but only once the block is actually read:

```text
device-mapper: verity: 253:2: data block 1000 is corrupted
cat: /usr/bin/dbus-broker: Input/output error
```

The kernel names the exact block; userspace sees `EIO` on the specific file. It
is unmistakably distinguishable from every other failure here.

**The consequence is architectural, not incidental.** A successful boot proves
only that the blocks the boot happened to read are intact -- it is not a
statement about the artifact. Any claim that booting demonstrates artifact
integrity is false under dm-verity, for either format. `boot.sh` therefore reads
every file in `/usr` and records the result; on the reference artifact that read
completes with exit 0, which is the evidence that the whole tree verifies. The
per-format blast radius of a single flipped bit is PLN-0002-09's to measure, and
this establishes the method it will use.

### Withheld modules initrd: dm-verity cannot be set up

The artifact is valid and correctly signed; only the initrd changes.

```text
[ TIME ] Timed out waiting for device dev-mapper-usr.device - /dev/mapper/usr.
[DEPEND] Dependency failed for sysroot-usr.mount - /sysroot/usr.
[  OK  ] Started emergency.service - Emergency Shell.
```

Fails closed, in the initrd, 45 seconds to the timeout. Distinguishable from a
hash mismatch by the absence of any verity message and by failing at *device
materialisation* rather than at read.

**A driver-specific exclusion could not be produced.** Excluding EROFS alone was
attempted twice through mkosi v26's module patterns and failed silently both
times: `-*erofs*` matched nothing, because the glob does not cross the path
separators in `kernel/fs/erofs/erofs`, and a bare `-erofs` after `default` did
not exclude it either. In both cases the machine booted clean -- an injection
that looks like it worked because nothing broke, which is the F-RES-01 shape.
The withheld-modules variant is what is recorded, labelled for what it is. The
filesystem-driver-specific case carries to PLN-0002-09.

### Refused confext: base compatibility declared `ID=debian` against a Fedora base

The guard works. `/etc` has no overlay, `systemd-confext status` reports
`/etc none`, and the merged marker file is absent.

**But nothing failed.** `systemd-confext-sysroot.service` reported
`Finished`, no unit failed, and the machine booted to `multi-user.target`
**silently unconfigured**. A refused confext is not an error condition here; it
is an absence.

That matters directly to DES-0005's amendment, which authors a per-confext
required/optional failure policy in the fleet inventory. **The default behaviour
is "optional", and a required confext will need a mechanism that does not exist
in what was observed.** Recorded and taken no further; the mechanism is
DES-0005's.

### The refusal doubled as a controlled experiment, and it confirmed finding 2

This run is the reference boot with exactly one difference -- no confext merged
-- so it isolates the cause of the preset failures:

| | Confext merged | Confext refused |
| --- | --- | --- |
| `/etc` | read-only overlay | plain writable tmpfs |
| Write probe | `Read-only file system` | **`WRITE SUCCEEDED`** |
| `Failed to preset all unit` | ~20 | **0** |
| Failed units | 4 | 1, unrelated |
| Full-tree verity read | exit 0 | exit 0 |

Finding 2's causality is therefore measured, not argued: `/etc` is read-only
**because a confext is merged**, and with none merged the machine happily
accepts a durable-looking write to `/etc` that will vanish at reboot -- exactly
the silent non-durability C-006 names as the worse outcome.

### The rest of the failure-capture path

- **Journal recovery when userspace is never reached.** Not needed, and that is
  the finding. All three faults produced complete diagnostics on the serial
  console, including the two that ended in emergency mode. PLN-0001's offline
  journal recovery from a disk copy was not required. This holds because the
  console is a harness-supplied `console=ttyS0` on the signed command line, not
  a property of the artifact.
- **Emergency mode is not interactive.** `Cannot open access to console, the
  root account is locked.` The emergency shell is reached and cannot be used.
  Diagnosis is by console transcript only, unless a later task deliberately
  supplies a credential to unlock it -- which would change the artifact under
  test and is not done here.
- **notify-vsock readiness does not apply.** PLN-0001's harness waits for the
  guest to connect back on a vsock. A pre-`/usr` failure has no userspace to
  connect from, so the readiness signal is absent for exactly the failures that
  matter most. `boot.sh` reads the console and treats a timeout as a result
  rather than an error, which is why the two emergency-mode faults produced
  evidence instead of a hung harness.
- **The artifact is never written.** `snapshot=on`, with the digest compared
  before and after every boot. A run that modified the artifact fails rather
  than reporting a result.

## What was not done

- **No second format.** EROFS only. ext4 is PLN-0002-06's, under parameters
  PLN-0002-05 declares. Nothing here compares formats and no measurement taken
  here is admissible in that comparison.
- **No substitution or signature evidence.** Corruption was injected, but
  nothing was substituted and no signature was broken. PLN-0002-10 owns those,
  and until it runs, nothing here shows the gate discriminates a substituted
  artifact from a corrupted one.
- **No signed confext.** The confext was a plain directory. Signature
  verification under `image_policy_confext_strict` is PLN-0002-03's.
- **No Secure Boot enforcement.** The UKI is signed with a synthetic key and
  the firmware was not asked to check it. SYS-030 stays **not applicable**.
- **No reproducibility claim.** The artifact was built repeatedly during
  debugging and no two builds were compared.

## Retention and cleanup

Evidence retained outside the repository at
`$XDG_CACHE_HOME/neutrinos/pln0002/evidence/pln0002-01`: four console
transcripts, the reference manifest and root hash, and the overlay digest
record, 416 KiB across 8 files, one SHA-256 per file in `SHA256SUMS`, unsafe
output scan clean.

VM firmware variables and the fault artifact copies are destroyed at task end.
**The synthetic signing keys are deliberately kept**: PLN-0002 states they live
for the whole task graph, because PLN-0002-10 must distinguish a substitution
failure from a signature failure and needs a second wrong-but-valid key to prove
the gate discriminates. They are never enrolled anywhere and are destroyed at
plan end.

## Reproducing

```sh
./src/spike/pln0002-01/spike.sh build --force
./src/spike/pln0002-01/boot.sh
./src/spike/pln0002-01/faults.sh hash-mismatch
./src/spike/pln0002-01/faults.sh no-modules
./src/spike/pln0002-01/faults.sh bad-confext
```

The tools tree is built once into the spike's own build root. It is the slice's
recipe plus `createrepo_c`, which mkosi needs to turn a package directory into a
local repository; the slice's own tools tree is a declared PLN-0001 input and
was left untouched rather than edited to serve this plan.

`boot.sh` passes the artifact `snapshot=on` and compares its digest before and
after, so a run that modified the artifact is a failure rather than a silent
result.
