---
status: active
last_updated: 2026-08-11
governing_plan: PLN-0002
---

# `/usr`-only composition from the PLN-0001 closure

PLN-0002-02. What moved out of the flattened root, where it went, and what is
verified about the result.

DES-0006 C-013 makes the authenticated artifact `/usr` alone, with `/etc`
regenerated and holding nothing durable. The PLN-0001 closure does not satisfy
that as installed. Measured on 2026-08-11 from a directory build of the declared
closure: **1352 entries land outside `/usr`**, in `/etc`, and every one of them
is a release default that a `/usr`-only artifact would simply lose.

Losing them is not hypothetical. PLN-0002-01 booted a `/usr`-only artifact with
an empty `/etc` and recorded roughly twenty `Failed to preset all unit`
messages and four failed units. This task is where that stops being an
accepted cost.

## What moved, and where

| Disposition | Content | Destination | Count |
| --- | --- | --- | --- |
| Relocate | `/etc/systemd/system`, `/etc/systemd/user`, including every `*.wants` enablement symlink | `/usr/lib/systemd/{system,user}` | 30 |
| Relocate | `/etc/pam.d` | `/usr/lib/pam.d` | 17 |
| Relocate | `/etc/sysctl.d` | `/usr/lib/sysctl.d` | 1 |
| Discard | `/etc/yum.repos.d`, `/etc/dnf`, `/etc/rpm`, shadow-utils backup copies, `/etc/.pwd.lock`, `/etc/mtab`, the build's `/buildroot` | — | 9 |
| Discard | `/etc/xdg/systemd` | — | 1 |
| Prune | empty directories | — | 47 |
| Factory | everything else, at its exact path | `/usr/share/factory/neutrinos-etc` | 68 top-level entries |

`/etc` is empty in the composed tree afterwards, and the finalize script
asserts it. A package added later that installs into `/etc` fails the build
rather than shipping an artifact whose `/etc` content exists at build time and
not at boot.

### Why these three dispositions and not one

**Relocation is preferred where the release already has a `/usr` search path.**
`/usr/lib/systemd/system/*.wants` is how the release itself expresses vendor
enablement -- 20 such directories are present before anything moves -- so the
preset symlinks are found there by the same lookup that found them in `/etc`.
Nothing is invented, and the enablement stops depending on a writable `/etc`,
which PLN-0002-01 recorded as unavailable.

**Discarding is for content that configures building, not running.** Shipping
package-manager repository definitions inside an authenticated artifact would
ship exactly the undeclared acquisition path PLN-0001-06 spent a task proving
fails open.

**The factory is systemd's own answer for the rest**, not an invention of this
plan. A factory directory holds the release's `/etc` defaults and
`systemd-tmpfiles` replays them into `/etc` at boot; the generated
`/usr/lib/tmpfiles.d/00-neutrinos-factory-etc.conf` carries one line per
top-level entry, `L` or `C` per the ruling below. This is the only disposition available for the extracted CA
trust, `nsswitch.conf`, the crypto-policy back-ends, PAM's `security`
fragments, and the shell profile, none of which has a `/usr` search path.

### The factory the closure already ships

`/usr/share/factory/etc` is not free. The closure installs one: systemd ships
factory copies of `vconsole.conf`, `issue`, `locale.conf`, `nsswitch.conf`, and
`pam.d`. The first build that produced a factory merged into it, and the result
was worse than it looked -- four package-owned files silently overwritten with
the installed `/etc` versions, and the shipped `pam.d` factory left with no
line replaying it, because `/etc/pam.d` had been relocated and never passed
through the loop that generates them.

So this task's content goes to `/usr/share/factory/neutrinos-etc` instead, the
two stay separate, and every generated line names its source explicitly
rather than relying on the tmpfiles default of `/usr/share/factory/` plus the
path -- a default that would now have two plausible meanings. The script fails
if anything is already at a destination it is about to write, because a silent
overwrite is the one outcome that must not happen twice.

The generated fragment's line order is glob order, and glob order is collated
by locale, so the script pins `LC_ALL=C`. The fragment is image content and its
bytes must not depend on the environment the build ran in.

### `C` copies versus `L` symlinks

Raised by [RES-0015](../research/comparisons/stateless-etc-configuration-delivery.md)
on 2026-08-11 and drafted the same day.

> **Owner ruling, 2026-08-11: the default is `L`, and the exceptions stay
> open.** Factory entries are symlinked into the factory unless a running
> system must write the path. The exception list is minimal and explicitly
> incomplete; the paths a confext or a machine must contribute *into* rather
> than replace are PLN-0002-03a's carve and are not known yet.
>
> The mechanism was changed at the same time so that the open half is visible
> rather than assumed. `mkosi.finalize` now states a disposition per path --
> currently 60 `L` against 8 `C` on the retained closure -- so completing the
> exception list in 03a is a data change, and the generated fragment shows what
> was decided instead of reflecting whatever the script happened to emit.
> Leaving the whole question open would not have been neutral: the script
> emitted `C` for everything, so copy would have won by inaction through 03a
> and into the artifacts task 06 builds.
>
> The `C` exceptions and their reasons: `machine-id`, which systemd writes and
> which has no home at all (finding 3); `passwd`, `shadow`, `group`, `gshadow`,
> `subuid`, `subgid`, which `systemd-sysusers` writes at boot -- NixOS asserts
> the same coupling, that sysusers and `/etc` must agree on mutability or the
> boot fails; `adjtime`, written by hwclock; and `ld.so.cache`, regenerated by
> ldconfig at runtime. A path added by a later package gets `L` by default and,
> if that is wrong, fails visibly at boot rather than being absorbed silently.
>
> Still to confirm by measurement, once the repository is reachable: that a
> write through a linked path actually fails against read-only `/usr` with no
> confext merged. That is the claim the ruling rests on and it is currently
> reasoned, not measured. PLN-0002-11 is where it becomes a registered check.

The reasoning, kept because the ruling turns on which argument is load-bearing.
This task originally generated only `C` lines, which **copy** from the factory
into `/etc` at boot. ParticleOS generates `L` lines, which **symlink**, and
states why:

> "This overrides the same file from systemd since we want to symlink
> everything into `/etc` instead of copying so updates to `/usr` propagate
> properly."

**That rationale does not transfer, and nothing here leans on it.**
ParticleOS has a persistent `/etc` on an encrypted btrfs root: a copy is made
once and then goes stale against a later `/usr`. NeutrinOS's `/etc` is a tmpfs
regenerated from tmpfiles at every boot, so a copy is remade from the *current*
factory each time and propagation is already satisfied by construction. Adopting
`L` for the reason ParticleOS gives would be importing a conclusion whose
premise NeutrinOS does not have -- the exact failure this project's defaults
name.

Two arguments do apply, and both are stronger than the imported one:

**C-006 becomes structural rather than conditional.** A durable write to `/etc`
must fail at the moment it is attempted. PLN-0002-01 measured that this holds
*only while a confext is merged* -- with none merged, the write probe succeeded
against the tmpfs. Under `L`, `/etc/foo` is a symlink into `/usr`, and `/usr` is
read-only dm-verity, so a write through it fails on the artifact's own
integrity boundary with no confext involved. That converts C-006 from a property
of the current overlay state into a property of the artifact. It is the
strongest argument available for linking, and it is one ParticleOS cannot make
because its `/etc` is writable by design.

**Memory is one of the eight criteria.** `C` copies the replayed content into a
tmpfs, so every replayed byte is resident. `L` costs a symlink inode. The size
at stake is small on the current closure, but memory is a measured criterion in
C-007 and the arms should not differ from each other for a reason unrelated to
the format under test.

What `L` costs, stated so the ruling is informed:

- **Granularity is all-or-nothing per path.** `L /etc/ssh` links the whole
  directory; nothing can then be added beside it per machine. `C` copies a
  tree that can subsequently be modified. Wherever a confext or a machine needs
  to contribute *into* a directory rather than replace it, `L` forecloses it and
  the path must stay a copy. This interacts directly with PLN-0002-03a's carve
  and is the reason the two should be decided together.
- **Software that replaces files by rename breaks the link** rather than
  writing through it. On a read-only `/etc` that is mostly moot, and where it is
  not, it is a failure mode with a different diagnostic than the one C-006
  expects.
- **Some paths must be real files regardless** -- `machine-id` above all, which
  is finding 3 and unresolved.
- ParticleOS uses `L?` (optional) for most entries, tolerating a missing source.
  A generated fragment that fails loudly on a missing source is the better
  default here, since the source is content this build just placed.

The likely answer is therefore **not uniform**: link by default, copy for the
paths the carve identifies as needing per-machine contribution, and never
silently. Whichever way it is ruled, the classifier must state the disposition
per path rather than applying one rule to everything, which is the same shape
as the relocate/discard/factory split this task already makes.

**Deadline: before PLN-0002-06.** The choice changes what `/etc` looks like at
boot and therefore what tasks 08 and 11 measure and assert. It is cheap now and
expensive after four artifacts exist. Confirming it needs a build, so it is
blocked on the same repository outage as everything else -- the decision is
draftable now, the evidence is not.

## Symlinks, and the defect that surfaced

A relative symlink can change meaning when it moves, and whether it does
depends on whether its target travels with it.

- `../getty.target` inside `/etc/systemd/system/multi-user.target.wants` stays
  inside the relocated tree and means the same thing at the destination.
- `../sysctl.conf` inside `/etc/sysctl.d` escapes it, naming `/etc/sysctl.conf`
  -- which does **not** travel; it goes to the factory and is replayed at that
  same path.

The first relocation did not distinguish them and shipped one silently broken
link. The finalize script now rewrites an escaping target to the absolute path
it already meant, and normalises it while doing so: `/etc/sysctl.d/../sysctl.conf`
names the right file only while `/etc/sysctl.d` exists, and the relocation had
just deleted that directory.

Measured afterwards, resolving every symlink under `/usr` as it would resolve
once the factory is replayed: **1906 resolve, 2 do not.** Both are the
`crypto-policies` back-end links, and both were already dangling in the
flattened PLN-0001 root -- carried, not caused. Two preset symlinks name units
absent from this closure, `authselect-apply-changes.service` and
`fips-crypto-policy-overlay.service`; those are also pre-existing, and the
relocation made them visible rather than creating them. None is repaired here:
repairing a closure defect while moving files would make the move
unattributable.

## The declared package overlay

PLN-0002-01 established by owner ruling that systemd 261 arrives as a local
package overlay. This task is where it stops being a spike fixture and becomes
a declared input.

Input-set schema version 3 adds `packages.overlays`: a name, a source, a
required `reason`, and every file pinned by SHA-256. `src/slice/acquire-overlay.py`
reads that declaration directly rather than a copy of it, fetches only what is
missing, verifies every file, and fails closed on a digest mismatch or on any
undeclared file in the overlay directory. It runs **before** the build, so an
overlay that cannot be verified stops composition instead of being discovered
in the artifact.

Verified failure-sensitive on 2026-08-11, offline, against the retained copy:
six files verified clean; one flipped byte reported the declared and found
digests and exited 1; an extra file in the directory was refused by name.

Retention keeps the two sources apart. `retain-repository.py` now takes the
overlay root and classifies a cached overlay package as declared rather than as
the fail-closed fault it would otherwise be, but does **not** copy it into the
repository retention: that tree is a copy of one repository, and mixing a
second source into it would make the retained tree claim the declared
repository contains packages it does not. The retention record carries
`overlay_package_count` alongside `package_count`.

`LocalMirror=` is untouched, so exactly one repository still exists by
construction. That was the whole reason for preferring an overlay to a second
repository.

## Also changed

`Seed=` moved from `[Content]` to `[Output]`, where mkosi parses it. It had
been in `[Content]` since PLN-0001 and mkosi warned about it on every build.
Value and effect unchanged.

`createrepo_c` joins the tools tree, in the recipe and in the declaration
together. mkosi needs it to turn the package directory into a local repository;
without it the build stops after syncing metadata.

`T2-SLICE-001`'s `unsupported schema version` violation now mutates the record
to version 4. It used version 3, which this task made real -- the violation
would have become a record the schema accepts. Two violations are added for the
new structure: an overlay file with no digest, and an overlay with no stated
reason. Eleven rejections, not nine.

## What is verified, and what is not

Verified, from three directory builds of the declared closure on 2026-08-11 and
one standalone run of the finalize script against a copy of the flattened tree:
the classification runs and is exhaustive; `/etc` is empty afterwards and the
assertion holds; the relocated enablement lands in the vendor path; the
closure's own factory is untouched; symlink resolution after replay is as
measured above; overlay verification is failure-sensitive on both its paths;
`mise run check:fast` is `passing=8 failing=0`.

The standalone run is what verified the separated factory, and it was necessary
rather than preferred: by then the tools tree was gone. It exercises the script
on real closure content with `BUILDROOT` set, which is the whole of the
script's contract, so it is good evidence for the script and no evidence at all
for the build around it.

**Not verified: the composed artifact with the overlay in it.** No build has
resolved the closure and the systemd 261 overlay together.
`dl.fedoraproject.org` began returning **403** for the declared repository on
2026-08-11, and the tools tree -- which must be rebuilt to gain `createrepo_c`
-- can only be built from that repository. The three directory builds above
predate the tools-tree change and resolved from the retained repository copy,
which is why they were possible at all.

Nothing is lost by this. The tools tree is declared by recipe precisely so it
can be rebuilt, and the retained repository copy plus the retained overlay are
intact and verified. But the following are **claims this record does not yet
make**: that the overlay resolves, that systemd 261 is what lands in `/usr`,
and that the factory replay produces a working `/etc` at boot. The first two
belong here and are owed as soon as the repository is reachable. The third is
PLN-0002-08's, which is the first task that boots this artifact.

The 403 is itself worth recording: the declared repository is frozen, which
makes its *content* an identity, but it says nothing about the URL remaining
served. Retention is what made the difference between a stalled afternoon and a
stalled plan.

### What the outage measured

Attributed on 2026-08-11. `/pub/` and `/pub/fedora/linux/releases/` both serve
200, and that index now lists 38 through 43 and **not 44**, while
`releases/44/` returns 403 and `releases/43/` returns 200. A delisted tree
returning 403 rather than 404 is a directory that exists and cannot be read.
Fedora's status page puts Fedora 45 mass branching at 2026-08-11 14:00 UTC,
which is when this started. Reproduced from a second network on IPv4 only, so
it is neither rate limiting nor specific to this host.

The declared content is intact and reachable elsewhere: `mirrors.mit.edu`
serves a `repomd.xml` whose SHA-256 is `da384542...`, byte-identical to the
declared `metadata_digest` and to the retained copy, and it serves package
payloads. **The URL is down; the identity is not.**

Repointing at a mirror was therefore available and was not taken. Owner
decision, 2026-08-11: wait. A digest match makes a substitution safe to verify,
but changing a declared input under time pressure is how a fixture becomes a
decision, and nothing downstream is blocked today.

**The gap it exposed is real and outlives the outage.** Retention covers the
image closure and not the tools closure. The image rebuilds offline from the
retained repository subset; the tools tree is declared by recipe rather than by
digest -- deliberately, since its export timestamps make its own digest
unstable -- and its packages are retained nowhere, so it can only be rebuilt
while the repository is reachable. That is why deleting the tools tree to add
`createrepo_c` turned a reachable-repository assumption into a blocked task.
Recorded as an open sub-question under `L-002`. The candidate answer is to
retain the tools closure the same way the image closure is retained, once.

## The disposable layout (PLN-0002-04)

Promoted from the PLN-0002-01 spike, where it booted, into
`src/slice/composition/mkosi.repart/`. **Every partition here is a fixture.**
PLN-0002 selects no partition layout, `S-004` is open, and the work register
records the fixture status at creation so that nothing acquires the authority
of a decision by being first.

| Partition | Type | Notes |
| --- | --- | --- |
| ESP | `esp`, vfat, 512M fixed | Unauthenticated by construction; what protects it is the signature on the UKI it carries |
| `/usr` | `usr`, EROFS, `Minimize=guess` | The whole of the authenticated artifact under C-013 |
| `/usr` verity | `usr-verity`, 64M fixed | Root hash carried on the signed UKI's command line |

The root is `root=tmpfs` on the kernel command line, not a partition. That
reintroduces a kernel command line to a composition PLN-0001 deliberately
stripped of one, and the record is explicit that this is not a reversal: what
PLN-0001 reverted was first-boot configuration, on the finding that none of it
is necessary for reachability, and `root=tmpfs` is structural -- without it the
artifact cannot mount its own `/usr`. mkosi supplies the other half by parsing
the root hash out of repart's JSON and injecting `usrhash=`, which is what
makes the mount verity-authenticated rather than merely successful. Nothing
else was added; `console=` in particular is still the harness's.

Two things the plan lists for this task are **not** here.

The **detached verity signature partition** is deferred to PLN-0002-06. It
needs signing material, whose lifetime across the task graph that task states,
and PLN-0002-10 is what needs the signature and the root hash separable so a
substitution failure and a signature failure can be told apart. The spike built
one and it worked; the definition is preserved at
`src/spike/pln0002-01/mkosi.repart/12-usr-verity-sig.conf`.

The **confext partition cannot be placed yet, and this is a blocker rather than
a deferral.** PLN-0002-01 found that on a tmpfs root the only confext search
path that survives is inside the authenticated `/usr` itself, and a confext
delivered beside the UKI reaches only the initrd's `/etc`, which is discarded
at switch-root. Placing a confext partition means choosing where a separately
delivered confext lives, and that contradicts DES-0005's separation of the
release artifact from configuration. It is one of the three findings handed
back on 2026-08-11 and not ruled. Task 04 stops here rather than deciding it in
passing, which is what the plan's own failure clause requires of an accidental
deferred decision. PLN-0002-03a runs into the same question immediately.

## Handed back, not decided

- **Factory-replayed `/etc` is writable and non-durable.** DES-0006 C-006 asks
  for a durable write to `/etc` that fails at the moment it is attempted.
  PLN-0002-01 observed that holding only while a confext is merged. A factory
  replay does not change that: it populates a tmpfs. **Partly overtaken on
  2026-08-11** by the `L` ruling above -- a linked path resolves into read-only
  `/usr`, so a write to it fails on the artifact's integrity boundary with no
  confext involved. That is the mechanism C-006 asks for, for the 60 of 68
  entries that are linked. It does not cover the 8 that must stay writable,
  `machine-id` and the sysusers files among them, and it is reasoned rather
  than measured until a build confirms it.
- **The factory is a second copy of the release's `/etc` defaults inside the
  authenticated artifact.** It costs image size in both arms equally, so it
  does not bias the C-007 comparison, but PLN-0002-07 measures image size and
  should name it rather than absorb it.
- **Two dangling `crypto-policies` links and two dangling presets** are carried
  from the PLN-0001 closure. Whether the closure should be corrected is a
  question about the closure, not about the `/usr` split.
