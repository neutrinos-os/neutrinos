---
id: PLN-0002
title: Authenticated `/usr` artifact format comparison
status: accepted
owner: Jason Tarasovic
created: 2026-08-11
last_updated: 2026-08-11
gate: G1
depends_on: [PLN-0001]
reviews: [PR-0030]
accepted: 2026-08-11
---

# Authenticated `/usr` artifact format comparison

Revised 2026-08-11 against [PR-0030](../project/reviews/0030-usr-artifact-format-spike-plan.md),
which found the first draft not fit to accept. Two owner rulings shaped the
revision and are marked where they land.

## Outcome

Answer DES-0006 C-007 by measurement: build the same package closure as an
EROFS `/usr` artifact and an ext4 `/usr` artifact, authenticate each through
dm-verity and a root hash carried by a signed UKI, boot each in a disposable
VM, and measure **all eight** criteria DES-0006 verification item 2 names --
image size, build time, build determinism, boot behavior, memory, update
transfer size, inspectability, corruption behavior -- plus a stated disposition
for recovery behavior.

The claim this supports is narrow: **one of the two formats is a better `/usr`
artifact for NeutrinOS, and the record says why in measured, attributable
terms.** Reaching it requires the `/usr`-only boot path C-013 accepted, so this
plan also produces the first evidence that the path boots at all.

Nothing here selects a package ecosystem, a partition layout, a state
filesystem, or an updater.

## Non-goals

- **No single criterion decides C-007** (owner ruling, 2026-08-11). Build
  determinism is one of eight criteria and is weighed like the rest. The first
  draft excluded it, citing C-013's "reproducibility is never a reason for it";
  that ruling governs the `/usr` **scope** decision, not the format comparison,
  and applying it here deleted a criterion the design named. The surviving
  guard is against any one criterion -- reproducibility included -- carrying the
  recommendation alone.
- A/B slots, staging, or finalization ordering. Those are verification items 3
  and 4 and belong to a later plan. This plan builds a second same-format
  artifact per arm **only** as a substitution source for task 10, never as a
  staging or selection demonstration.
- The DES-0005 confext lifecycle. Verification items 11-19 are a separate plan.
- Encryption, LUKS2, TPM policy, or unlock behavior.
- Capacity falsification, the minimum viable device, or the C-002 formula.
- Any physical-host effect, on `desktop-jason`, `router`, `misc`, or otherwise.
- Production signing, Secure Boot enrollment, or any real trust anchor.
- Performance tuning of either format. Measurement, not optimization.

## Mutation and authority boundary

This plan inherits PLN-0000's boundary unchanged and narrows it as follows. It
creates no new authority.

May read and change: repository paths under `src/`, `tools/`, and `docs/`;
build caches and artifacts in declared locations outside the checkout;
disposable VM disks, firmware variables, vTPM state, and an isolated test
network; and synthetic signing and credential fixtures generated for this plan.

Must not, and no task may request an exception: touch any physical host beyond
separately authorized read-only inspection; use or create production Secure
Boot, enrollment, recovery, or credential keys; enroll any key into physical
firmware; or publish or roll an artifact to any machine.

The router is specifically out of reach. R-054 records that the development
workstation reaches the network through it.

## Inputs and dependencies

| Input or dependency | Identity/status | Blocking behavior |
| --- | --- | --- |
| DES-0006 C-013 | Accepted 2026-08-11: authenticated artifact is `/usr` | Fixes the scope this plan measures; a reopening stops the plan |
| DES-0006 C-007 | Open; the question this plan answers | Its criteria define the comparison |
| DES-0006 verification item 2 | Amended 2026-08-11 | Defines done; all eight criteria are in scope |
| DES-0006 C-008 | **Accepted 2026-08-11**: `/var` belongs to the machine-state volume | Constrains the fixture; see task 04 |
| DES-0005 confext amendment | Accepted 2026-08-11 | Requires a signed confext to boot; its tooling and path carve are **not** provided by it -- see task 03a |
| PLN-0001 slice | Complete; declared Fedora 44 closure, `compose.sh`, retention, runner, five registered tests | Reused; task 11 owns keeping the tests true |
| `S-004` layout, `C-009` state filesystem | Open | Fixtures only; task 04 states fixture status in the register when created |
| mkosi v26, Fedora 44 | Candidate fixtures | Remain candidates; using them accepts nothing |

## Decision and requirement trace

| ID | Applicability | Planned evidence |
| --- | --- | --- |
| SYS-049 | **Partial**, with covered cells named | Root hash in a signed UKI authenticating the exact `/usr` and Verity pair; substitution of a *same-format* valid `/usr`, its Verity tree, the confext, and the manifest. Covered cells of C-001's cross product are enumerated in task 10; uncovered cells carry forward, including every cell needing A/B slots or a physical role |
| SYS-030 | **Not applicable** | Restored from the first draft's "partial" per PR-0030 C-010. The requirement binds normal boot on a production physical role; a VM with a synthetic anchor is a different thing, not a partial instance of it. PLN-0001 classified it the same way |
| SYS-020 | Partial | Task 07 records `/etc` regenerated by `systemd-tmpfiles`/`systemd-sysusers` and whether anything durable appears there. C-013 claims to satisfy SYS-020 by construction; this plan measures that claim |
| SYS-048 | Partial | Task 04's regions are declared with owner and lifecycle purpose; the fixture's deviations from DES-0006's region table are recorded |
| SYS-051 | **Applicable, not satisfied** | Split out of the group per PR-0030 C-010. The fixture writes an unencrypted `/var` and journal to tmpfs; nothing persists, so no plaintext spill survives power-off, and that is the whole of the claim. No encryption boundary is designed or demonstrated |
| SYS-052 through SYS-056 | Not applicable | No encryption, capacity, snapshot, or recovery claim in scope |
| SYS-123 | **Partial** | Reclassified from "not applicable" per PR-0030 C-006. The plan builds a real signed confext under `image_policy_confext_strict`; content identity, authorization, and base compatibility are exercised in fact. Task 03 names what it produces and hands it back as candidate |
| SYS-018, SYS-041, SYS-059 | Inherited partial from PLN-0001 | Task 11 keeps the mechanisms and their checks true across the `/usr` split; "must keep passing" is a check, not an assertion |

Candidate mechanisms remain candidates unless a separate ADR accepts them.
EROFS winning does not accept EROFS; it produces the evidence an ADR needs.

## Work

Ordered so the plan's most likely falsification runs first (PR-0030 C-007).

| Task | Status | Depends on | Output/evidence | Next action |
| --- | --- | --- | --- | --- |
| PLN-0002-01 | **complete** | — | **Early-boot spike, one format, throwaway.** What is consumed before `/usr` is verified; whether `systemd-confext-initrd`/`systemd-confext-sysroot` behave as C-013 assumed; the named failure-capture path for every later task | Complete 2026-08-11. **The assumption holds and the gate is not triggered**: the `/usr`-only path boots on a tmpfs root, and `systemd-confext-sysroot.service` merges a confext into `/sysroot/etc` before switch-root. See the [early-boot record](../project/spike-early-boot-record.md). Owner ruling 2026-08-11: systemd 261 arrives as a local package overlay from OBS `system:systemd`, because Fedora 44 stays on 259.x and the unit is new in 261. Three findings are handed back and taken nowhere: a tmpfs root leaves a separately delivered confext with nowhere to live, read-only `/etc` breaks first-boot presets so runtime unit enablement is unavailable, and `/etc/machine-id` has no home |
| PLN-0002-02 | **complete, with a defect found and fixed** | 01 | `/usr`-only composition from the PLN-0001 closure, release defaults in `/usr/lib`, declaration and retention mechanisms intact | Composition, declaration, and retention are done and recorded in the [composition record](../project/usr-artifact-composition.md): 1352 entries left `/etc`, the release's own `/usr` search paths take what they can and a generated tmpfiles factory replays the rest, `/etc` is empty and asserted so, and the systemd 261 overlay is now a declared input verified by digest before the build. **Unblocked and complete 2026-08-11**: the build resolves offline from the retained repository, the retained overlay, and the pre-outage tools tree, and the systemd 261 overlay is in the manifest. A boot then found a defect this task shipped -- five release paths, `/etc/os-release` among them, as **dangling symlinks**, because the `retarget` fix was applied to relocated entries and never to factory entries. Fixed and verified on a rebuild; see the [carve record](../project/etc-path-carve.md). Open against this task: whether the generated fragment should skip paths systemd's own `etc.conf` already owns, which it currently overrides silently. Handed back: a factory-replayed `/etc` still does not satisfy C-006 |
| PLN-0002-03a | **partial, nothing owed** | 01 | Confext build path and a minimal `/etc` path carve, both **marked candidate and handed back** to DES-0005 and the ADR-0003 spike. The delivery path is a **declared fixture in this task's text**: `/usr/lib/confexts`, per the owner ruling of 2026-08-11 on finding 1 option D. Also completes the `L`/`C` exception list, which is the same carve | The carve is drawn and provisionally accepted -- one confext, `neutrinos-network`, owning `/etc/systemd/network/` -- and the `L`/`C` list is complete for this carve at 59 `L` and 9 `C`, measured. Two collisions were exposed, ruled, and **measured across four boots**; see the [carve record](../project/etc-path-carve.md). Collision 2 is the substantial one: under stock ordering a merged confext makes the factory replay fail wholesale, leaving no `/etc/passwd` and 8 failed units while tmpfiles reports success. Option A -- replay into `/sysroot` in the initrd before the merge -- is ruled and **measured working**; option B was measured and fails on an upstream ordering cycle. Both deliverables have since landed. The confext is a **signed 3-partition DDI** built by `compose.sh` -- and its signature is **not enforced**: dm-verity resolves the key through the kernel keyring, a synthetic key is in none, and systemd falls back to unsigned verity and merges. That is the third mechanism in this plan to fail open silently, and it predicts task 10's confext substitution will pass. The initrd replay is now repository content, delivered through `$ARTIFACTDIR/io.mkosi.initrd` because mkosi offers no way to put a file in its default initrd; shipping it exposed three defects the credential probe could not, and it boots with **zero failed units**. **Still owed**: signature enforcement, which needs a synthetic key enrolled in the disposable VM's firmware. The four paths (`/etc/mtab`, `/etc/pam.d`, `/etc/credstore`, `/etc/credstore.encrypted`) the narrowed replay no longer establishes are **ruled 2026-08-11**: first named entries of the exception list, general case to 03b/DES-0005, absent meanwhile at 70 `/etc` entries and zero failed units. The PLN-0002-05 declaration it owed is **drafted and accepted as amendment 3**; it grew a route question, because mkosi's default initrd *is* `mkosi-initrd` and its module list ships `erofs` and `ext4` in both arms, which is PR-0030 C-003 measured rather than predicted. If any argument in this task depends on where the confext lives, stop and return to the [findings](../project/early-boot-findings-for-decision.md) |
| PLN-0002-03b | pending, **deferred 2026-08-14** | 03a | **Confext delivery**: where a separately delivered confext lives and when it is merged, with [RES-0015](../research/comparisons/stateless-etc-configuration-delivery.md) as its evidence | Draft for owner ruling; the drafter does not accept it. Blocks the confext partition PLN-0002-04 left out and finding 2's option B. **No task in this plan depends on it.** Depends on `S-004` and touches `C-009` and `L-003`; if it cannot be answered without one of them, stop and return to review. **Sequenced 2026-08-12 by Jason Tarasovic: after 05 and 06, before 07 through 10. Superseded 2026-08-14: deferred, and 07 runs next.** The reason for the original sequencing was to confine question 5b's live fail-open to task 06; that fail-open is now closed and registered, so the sequencing no longer buys what it was taken for. Still on no task's critical path, so this is a scheduling ruling and not a dependency. Its reason is what 03b accumulated: the delivery design, the general `L`/`C` exception list, the credstore sub-question, and question 5b's live fail-open. Running it before 07 confines that fail-open to task 06 rather than carrying it through every measurement task |
| PLN-0002-04 | **partial** | 01 | Disposable layout: ESP, one `/usr` slot, one Verity slot, **tmpfs root partition**, one confext. Fixture status recorded in the work register at creation | Build `systemd-repart` definitions. **Owner ruling 2026-08-11: tmpfs, which is the preferred direction and avoids the first draft's contradiction of the accepted C-008 ruling.** `/var` is tmpfs-backed and nothing persists; no machine-state volume is built, so C-008 is respected by not implementing the thing it governs. **Partial, 2026-08-11**: ESP, `/usr`, and the verity partition are promoted from the spike into `src/slice/composition/mkosi.repart/` and recorded as fixtures ([composition record](../project/usr-artifact-composition.md)); the tmpfs root is expressed as `root=tmpfs` on a reintroduced kernel command line, which is structural rather than a reversal of PLN-0001's reverted first-boot amendments. The verity-signature partition is deferred to task 06 with the signing material it needs. **The confext partition is not placed**: doing so decides where a separately delivered confext lives, which is finding 1 of task 01 and is not ruled. See the [drafted findings](../project/early-boot-findings-for-decision.md) |
| PLN-0002-05 | **accepted 2026-08-12** | 02, 04 | **Declared parameter set for both arms** and the pairing rule that justifies it. Filesystem: `mkfs.erofs` compression algorithm and level, EROFS cluster size, ext4 block size, inode ratio, reserved-block percentage and feature set, dm-verity hash block size and salt, and the initrd contents per arm with the asymmetry stated and its direction of advantage named. **Kernel command line** (amended 2026-08-11): `root=tmpfs` against `systemd.volatile=yes`, `systemd.image_policy=`, `systemd.image_filter=`, `systemd.confext=`, and the `usrhash=` mkosi injects. **Signing-material identity** (amended 2026-08-12): one subject for the verity signer across every build root, since the subject is what lands in the enrolled `db` and in `/usr/lib/verity.d` | Declare before building. An undeclared parameter invalidates the comparison. The command line is inside the signed UKI, so it is part of the artifact and not a setting applied to one; it affects boot behavior and memory, two of the eight criteria. **Implemented in the composition and audited against the built artifacts 2026-08-14.** The audit confirmed the ext4 superblock parameters, the ESP volume ID, the four signing subjects and the initrd unit digests, and took three corrections -- the mkosi pin and upstream module count, an `orphan_file` claim, and the module list, which over-matches to 130 modules while eight of its entries select builtins. The module list was **ruled 2026-08-14: accepted as measured, not tightened** -- no C-007 criterion needs the trim, and kernel content is `W-004`. **Two things stand between this task and PLN-0002-06's freeze**: `systemd.image_filter=` has never been ruled and task 10 needs it; and the ext4 arm now on disk predates `systemd.image_policy=` and is not a member of the declared set. See the [declaration](../project/artifact-parameter-declaration.md) |
| PLN-0002-06 | **complete** | 05 | **Three** authenticated artifacts per arm under amendment 5, accepted 2026-08-14: the primary EROFS+dm-verity and ext4+dm-verity, each with Verity pair and synthetically signed UKI, plus **two substitution sources per arm** -- a content variant and a seed variant -- which exist only for task 10. Signing key lifetime stated across the task graph | Build all **six**; retain digests. **In progress 2026-08-14**: the detached `usr-verity-sig` partition, a UKI signed by a third synthetic subject (`CN=NeutrinOS image, synthetic`, kept distinct from the two verity signers because `T4-CONFEXT-001`'s content is which signer `db` holds), and `systemd.image_policy=usr=signed` embedded in the UKI have landed, and both enrollment arms boot from `/dev/mapper/usr` with no policy complaint. **Complete. Accepted 2026-08-14 by Jason Tarasovic**: all six artifacts are built from one tree state and their digests retained, recorded in the [artifact set](../project/usr-artifact-set.md). The command line is uniform across the set, verified from each built UKI; the confext was rebuilt; the EROFS primary reproduced its prior digest exactly, so determinism is re-measured with the confext included. Both variant shapes are demonstrated on the ext4 arm -- content differs by three filesystem blocks at the same UUID, seed by UUID alone at the same block count. `systemd.image_filter=` was ruled **absent** the same day, so no parameter inside the UKI is open |
| PLN-0002-07 | pending | 06 | Offline measurements: image size, build wall time, **build determinism**, update transfer size, inspectability. Repetition count and accelerator state recorded for every timed measurement | Measure both arms identically |
| PLN-0002-08 | pending | 06 | Boot records both arms: `/usr` read-only and verity-authenticated, `/etc` regenerated, no failed units, boot behavior and memory with repetition count and accelerator state | Boot each; PLN-0001 measured the same boot at 72s TCG and 18s KVM, so accelerator state is recorded per run |
| PLN-0002-09 | pending | 06 | **Corruption behavior**: single-bit corruption injected into an authenticated region of each artifact, recording detection point, diagnostic, and blast radius per format. Compressed EROFS clusters versus ext4 blocks is where the formats are expected to diverge | Inject and record verbatim |
| PLN-0002-10 | **started out of order, one cell covered** | 06 | **Negative evidence**: same-format `/usr` substitution, Verity substitution, confext substitution, manifest substitution, and a wrong-but-valid signing key, each failing closed with a diagnostic that discriminates root-hash mismatch from signature failure from mount failure. Covered cells of C-001's cross product enumerated | Inject each; record which mechanism rejected it and how that was determined. **Started 2026-08-11 without task 06, on owner ruling** that the confext signature check belongs to this task rather than before it. `T4-CONFEXT-001` is registered in the `complete` profile and covers the **confext-substitution cell for the signature dimension**: an artifact whose UEFI `db` carries the verity signer, two confexts differing only in signer, and the assertion that the untrusted one is refused under `--image-policy=root=signed` with a **unit** failure. Verified failure-sensitive by two injections. What this does **not** cover is the rest of the row -- `/usr` substitution, Verity substitution, manifest substitution, the wrong-but-valid key against the *artifact* rather than the confext, and the C-001 cross-product enumeration -- all of which still need task 06's four artifacts. Two limits recorded in the [carve record](../project/etc-path-carve.md): the check is unreachable through `mise run`, because `sandbox.deny_env` strips its declared fixture directory exactly as it does `T3-SLICE-001`'s, and its slice-side fixture is **unrun**, having been exercised against the PLN-0002-01 spike artifact instead. Note also that this task now injects against a *configuration* rather than a missing mechanism: without `root=signed` applied, the merge fails open, so what the remaining cells measure depends on which the plan says is under test |
| PLN-0002-11 | pending | 02, 03a, 04 | The five registered slice tests updated for the `/usr` artifact, plus new checks for root-hash-to-UKI binding, read-only `/usr`, and nothing durable in `/etc`. Each verified failure-sensitive as PLN-0001-05 did | Update `T2`/`T3`/`T4-SLICE-*` and register the new checks. `T4-CONFEXT-001` was registered early under task 10 and is **not** one of this task's checks; whether registration belongs here rather than in the task that measures is a question this task should settle rather than inherit |
| PLN-0002-12 | pending | 07, 08, 09, 10 | Recovery-behavior disposition: measured, or deferred with rationale naming where it goes. The `crypttab` element of item 2's early-boot clause is addressed against the encryption non-goal | Decide and record; a deferral is a proposed amendment to item 2 and is **the owner's**, not a task's |
| PLN-0002-13 | pending | 11, 12 | C-007 recommendation with its evidence, stating which criteria decided it and which were inconclusive. **If task 08 produced no values, this task says so and recommends nothing** | Draft; **the drafter does not accept it** |
| PLN-0002-14 | pending | 13 | Retained evidence bundle, updated requirement trace, work register, and DES-0006 disposition | Assemble as PLN-0001-08 did |

## Amendments

Each amendment carries its own status. Amendments 1 and 2 -- splitting
PLN-0002-03, and widening PLN-0002-05's declared parameter set to cover the
kernel command line -- were drafted and **accepted by Jason Tarasovic on
2026-08-11**; amendment 3 on 2026-08-11 and amendment 4 on 2026-08-12.
**Amendment 5 was accepted by Jason Tarasovic on 2026-08-14.** Accepted amendments are applied to
the task table above. The reasoning is kept here because a table row records
what a task is, not why the plan changed.

## Amendment 1: split PLN-0002-03

### Why

PLN-0002-03 is blocked in full by a dependency that touches a fraction of it.
The task is two things -- build the signed confext, and carve the minimal `/etc`
path set -- and neither depends on where the confext lives. What depends on
finding 1 is only the third thing the task must do implicitly in order to
boot-test its output: put the bytes somewhere the merge finds them.

Splitting separates a question PLN-0002 must answer from one it has no business
answering. C-007 is a format comparison; none of its eight criteria is affected
by confext delivery.

### The tasks

| Task | Depends | Deliverable | Completion |
| --- | --- | --- | --- |
| PLN-0002-03a | 01 | Confext build path and minimal `/etc` path carve, both **marked candidate and handed back** to DES-0005 and the ADR-0003 spike. Delivery path declared a **fixture in the task text**, not chosen | Produce the signed confext the boot needs; record the carve as the first drawn, not the reference. Unblocked once the declared repository is reachable |
| PLN-0002-03b | 03a | **Confext delivery**: where a separately delivered confext lives and when it is merged, with [RES-0015](../research/comparisons/stateless-etc-configuration-delivery.md) as its evidence | Draft for owner ruling. Blocks the confext partition PLN-0002-04 left out and finding 2's option B. **Not on this plan's critical path** |

Task 03b depends on `S-004` and touches `C-009` and `L-003`. If it cannot be
answered without one of those, it stops and returns to review -- which is the
existing "a task needs a mechanism `S-004` or `C-009` has not made" clause,
applied deliberately rather than hit by accident.

Downstream dependencies stated as `03` (tasks 11 and the confext substitution
in task 10) now read `03a`. No task in the plan depends on `03b`.

### What the split costs

The fixture delivery path lands in 03a, and PR-0030 C-006 already flags that
task's confext tooling and path carve as becoming the reference by being first.
Three first-by-default artefacts in one task is the risk, and declaring the
delivery path a fixture *in the task text* rather than in a record afterwards
is the mitigation. It is a weaker mitigation than not having the problem.

The delivery fixture is now settled: **owner ruling 2026-08-11, option D**, the
confext at `/usr/lib/confexts`, declared as a fixture and deciding nothing about
the design. That removes the reason 03 was blocked; the split is what lets 03a
proceed without dragging 03b's unruled design question with it.

## Amendment 2: widen PLN-0002-05 to the kernel command line

### Why

PLN-0002-05 is this plan's declaration gate -- "declare before building, an
undeclared parameter invalidates the comparison." Its enumerated parameter set
is **filesystem parameters only**: `mkfs.erofs` compression algorithm and
level, EROFS cluster size, ext4 block size, inode ratio, reserved-block
percentage and feature set, dm-verity hash block size and salt, and the initrd
contents per arm.

The kernel command line is not in that list, and it is a parameter of the
comparison by the plan's own standard. It affects **boot behavior and memory**,
two of C-007's eight criteria. It is also *inside the signed UKI*, so it is not
a setting applied to an artifact -- it is part of the artifact.

The practical consequence of leaving it out is that the command line stays a
fixture inherited from PLN-0002-01 and PLN-0002-04 straight through the
measurements that decide C-007. PR-0030 C-005 and C-006 name that pattern.

### What was added to PLN-0002-05

Each declared with the value chosen, the alternative not chosen, and the reason
-- the same standard the filesystem parameters are held to.

- **`root=tmpfs` versus `systemd.volatile=yes`.** mkosi's spelling versus
  systemd's own, the latter with a documented per-mode contract (`yes`,
  `state`, `overlay`) and the property that no mode physically removes
  anything. PLN-0002-04 took the first without comparing. The two must not be
  assumed identical.
  ([RES-0015](../research/comparisons/stateless-etc-configuration-delivery.md))
- **`systemd.image_policy=`.** Per-partition integrity requirements asserted on
  the signed command line -- ParticleOS requires `usr=signed` this way. Today
  NeutrinOS asserts `/usr` integrity by having mounted it successfully, which
  is the weaker claim PLN-0002-01 already showed to be unsafe when it found
  that dm-verity is lazy and a corrupt artifact booted normally. This is the
  natural mechanism for making PLN-0002-10's negative evidence fail closed for
  a stated reason rather than incidentally.
- **`systemd.image_filter=`.** Partition selection by label. Becomes load-
  bearing at task 06, which builds a second same-format artifact per arm as a
  task-10 substitution source.
- **`systemd.confext=`.** Whether the merge happens at all is a UKI-carried
  assertion. Relevant to the finding-1 fixture and to whatever 03b decides.
- **`usrhash=`**, which mkosi injects today. Declared rather than inherited, so
  that the binding between root hash and UKI that PLN-0002-11 registers a check
  for is a stated property and not an observed one.

### Deadline

**Before PLN-0002-06.** The command line is inside the UKI, so a change after
06 means tasks 07 through 10 measured a different artifact and are void. Task
05 already sits between 04 and 06, so this is a widening of scope and not a
reordering.

## Amendment 3: widen PLN-0002-05 to the initrd itself

**Drafted 2026-08-11 by PLN-0002-03a. Accepted 2026-08-11 by Jason Tarasovic.**
It states what 03a put inside the signed UKI and what task 05 must therefore
declare. Accepting it accepts the *obligation to declare*; it selects no route
and no module list. The route question at the end remains open and is task 05's
to answer.

### Why

PLN-0002-03a landed two files -- `neutrinos-etc-factory.service` and its
drop-in on `systemd-confext-sysroot.service` -- into the initrd. The initrd is
hashed into the unified kernel image, so those files are **inside the
artifact's signature**. They are release content, not configuration, and
PLN-0002-05 is where the artifact's contents are declared.

That much was known when they landed. Two things found since enlarge it.

**The default initrd is `mkosi-initrd`.** `finalize_default_initrd()`
(`config.py:5165`) parses `resources/mkosi-initrd` in place. It is not a dracut
initrd and not a separate mechanism: it is `MakeInitrd=yes` over distro
packages (`systemd`, `udev`, `bash`, `less`, `gzip`), an explicit
`KernelModules=` list, `RemoveFiles=` trimming, and a small `mkosi.extra` tree.
Verified against the pinned revision `84af2089`.

**Its module list ships both filesystem drivers.** `erofs` and `ext4` are both
in that list. So as things stand today, each arm's initrd carries the other
arm's driver -- which is precisely the outcome PR-0030 C-003 named: "both
drivers ship in both arms and neither artifact is the one that would ship."
The risk row below has recorded this as a hypothetical since the plan was
written. It is now a measured property of the pinned inputs.

The current delivery route -- a cpio written to `$ARTIFACTDIR/io.mkosi.initrd`
by `mkosi.finalize.d/10-initrd-etc-factory` -- can only **add** files to the
initrd. It cannot remove a module from a config the composition does not
invoke. So the declaration below is not satisfiable without a route decision.

### What task 05 must declare

Each with the value chosen, the alternative not chosen, and the reason -- the
same standard the filesystem parameters and the command line are held to.

- **The two NeutrinOS units**, by path and content digest, named as signed
  release content rather than as a build convenience. This is the declaration
  PLN-0002-03a owed and the reason for this amendment's deadline.
- **`KernelModules=` per arm**, and specifically whether the EROFS arm ships
  `ext4` and the ext4 arm ships `erofs`. If both, say so and name the direction
  of advantage; a shared list is a defensible choice but not an undeclared one.
- **The package set and `RemoveFiles=` set**, since they are what
  `mkosi-initrd` actually builds from and they bear on boot time and memory,
  two of C-007's eight criteria.
- **The delivery route**, because it bounds the other three. Two exist:
  - the current one, `$ARTIFACTDIR/io.mkosi.initrd` -- additive only, no
    config control, no per-arm module list;
  - a `mkosi.images/initrd/` subimage with `Include=mkosi-initrd` -- the same
    `mkosi-initrd`, invoked by the composition instead of implicitly, with its
    config editable. Subimages inherit `Distribution=`, `Release=`,
    `LocalMirror=`, `ToolsTree=` and `PackageDirectories=` as universal
    settings, so nothing would need restating. Its costs are that `Initrds=`
    has no output-directory specifier, so the path comes from `compose.sh`, and
    that setting it makes `want_default_initrd()` return False.

  The drafter's recommendation is the subimage, on the ground that the per-arm
  module declaration is not expressible without it. That is a recommendation
  and not a ruling; the additive route is defensible if the owner accepts a
  shared module list across both arms and declares it as such.
- **`SOURCE_DATE_EPOCH` and the cpio's ownership and mtime pinning**, already
  implemented, declared because the initrd's identity is what PLN-0001-07
  verifies a reconstruction against.

### Deadline

**Before PLN-0002-06**, the same deadline and the same reason as amendment 2:
the initrd is inside the UKI, so a change after 06 means tasks 07 through 10
measured a different artifact and are void.

## Amendment 4: widen PLN-0002-05 to the signing material's identity

**Drafted 2026-08-12. Accepted 2026-08-12 by Jason Tarasovic.** Same deadline
and same reason as amendments 2 and 3: what this covers is inside the signed
artifact, so a change after PLN-0002-06 voids tasks 07 through 10.

### Why

The verity signer's certificate subject differs by build root --
`/CN=NeutrinOS slice verity, synthetic/` in `src/slice/compose.sh` against
`/CN=NeutrinOS PLN-0002-01 spike verity, synthetic/` in
`src/spike/pln0002-01/spike.sh`. That looked cosmetic while the two build roots
were independent. It stopped being cosmetic when signature enforcement became
real: the subject is what is enrolled in the disposable VM's `db` and what sits
in `/usr/lib/verity.d`, so it is the name by which the machine decides a signer
is trusted. Two subjects for one role is drift in a declared parameter, not a
label.

The backlog ruling of the same day on the tools tree removes the reason for the
divergence rather than papering over it: one build root implies one key set.

### What task 05 must declare

- **One subject for the verity signer**, used by every build root.
- **The distinct subjects that remain distinct and why** -- the image signer,
  the valid-but-unenrolled second verity key, and the platform key each name a
  different authority, and collapsing them would make `T4-CONFEXT-001`'s
  measurement unreadable, since its whole content is which signer `db` holds.
- **That all of it is synthetic**, generated into the build root and destroyed
  with it, per this plan's boundary.

## Amendment 5: two substitution sources per arm, so six artifacts rather than four

**Drafted 2026-08-14, recording an owner ruling of 2026-08-12 reaffirmed on
2026-08-14. Accepted by Jason Tarasovic on 2026-08-14** and in force: task 06's
completion criterion is six artifacts, and the task table above is updated. It
is written here because the ruling had until now no home outside the running
context summary, which is not a record.

### Why

Task 06 builds a second same-format artifact per arm purely as task 10's
substitution source. That was drafted before the build became bit-reproducible.
It now is, so rebuilding the same tree yields a byte-identical artifact and the
substitution is vacuous: it would boot fine, and a passing boot would read as a
fail-open rather than as the artifact being the one the UKI names.

Task 10 needs a substitute that is **validly signed by the enrolled key and
carries a root hash the UKI does not name**. One variant cannot supply both
shapes of that.

### What changes

- Per arm, build **two** substitution sources rather than one: a **content
  variant** (the tree differs) and a **seed variant** (the tree is identical and
  the repart seed differs, so UUIDs and the verity salt move). Six artifacts
  total.
- Task 06's completion criterion becomes "build all six; retain digests".
- Nothing else moves. The substitution sources remain substitution sources: no
  selection, staging, or finalization is exercised or claimed, and the non-goal
  above is unchanged.

### Cost

Two more builds per arm and two more digests to retain. The alternative is a
task 10 whose `/usr`-substitution cell cannot discriminate, which is the cell
the plan's negative evidence rests on.

## Failure, interruption, and cleanup

Stop and return to review if: task 01 falsifies C-013's early-boot assumption;
the `/usr` split cannot preserve PLN-0001's declaration and attribution
guarantees; either format cannot be authenticated through a signed UKI with
available tooling; or a task needs a mechanism selection `S-004` or `C-009` has
not made.

**Failure capture is named before it is needed** (PR-0030 C-009). Task 01
established it on 2026-08-11 by inducing three failures; see the
[early-boot record](../project/spike-early-boot-record.md). Every later task
uses: how the journal is recovered when the
machine never reaches userspace, which PLN-0001 had to do offline from a disk
copy; the console path, given PLN-0001's composition amendments were reverted;
whether notify-vsock readiness applies to a pre-`/usr` failure, which it does
not; and the diagnostics that distinguish a missing filesystem driver from a
root-hash mismatch from a refused confext. A failure that cannot be attributed
to one of those is itself a finding.

If task 08 yields no boot values, task 13 recommends nothing and exit criterion
2 is met by recorded reasons rather than measurements. That is a real outcome,
not a formality.

Synthetic signing keys live for the whole task graph, not per task, because
task 10 must distinguish a substitution failure from a signature failure and
needs a second wrong-but-valid key to prove the gate discriminates. Their
lifetime is stated per artifact in task 06. They never leave the plan's scratch
location, are never enrolled anywhere, and are destroyed at plan end.

All VM disks, firmware variables, and vTPM state are destroyed at task end.
Evidence is retained outside the repository with one SHA-256 per file, scanned
for unsafe output, as PLN-0001-08 established. Partial artifacts are discarded
rather than measured: a half-built `/usr` is the hybrid C-001 warns about.

## Risks and unknowns

| Risk or unknown | Effect | Disposition |
| --- | --- | --- |
| C-013's early boot is its own stated residual risk | Task 01 may falsify part of an accepted amendment | Scheduled first for exactly that reason. A falsification returns to DES-0006 review; it is not worked around |
| The initrd cannot be identical across arms, since each needs its own filesystem driver | Boot and memory partly measure the initrd, not the format | Task 05 declares the asymmetry and which arm it advantages; task 13 names it as a threat to the finding. **No longer hypothetical, 2026-08-11**: `mkosi-initrd`'s `KernelModules=` ships `erofs` and `ext4`, so both arms currently carry both drivers -- the C-003 outcome, measured. Amendment 3 states what 05 must declare and that the additive delivery route cannot express a per-arm list |
| mkosi may not express a `/usr`-only artifact with Verity as directly as PLN-0001's flattened root | Task 02 cost, possibly a different composition path | **Closed by task 01, 2026-08-11.** It expresses it directly through `mkosi.repart` definitions, and parses the root hash out of repart's JSON to inject `usrhash=` into the UKI itself. No second composition path is needed |
| Task 03 draws the first confext path carve and builds the first confext tooling | Both become the reference by being first -- the implementation-accident failure mode | Marked candidate at creation and handed back to DES-0005 and ADR-0003. The plan states it does not own them |
| The tmpfs root partition is a fixture, and the persistence question DES-0006 records as open stays open | A fixture could look like a decision | Task 04 records fixture status in the register at creation. tmpfs is the cheaper and less committal of the two, which is why the owner chose it |
| The comparison could be decided by `mkfs` flags rather than by the formats | Wrong answer to C-007 -- the failure C-007 predicts | Task 05 declares every parameter before task 06 builds; an undeclared parameter invalidates the comparison |
| Second same-format artifacts could be read as A/B staging | Scope creep into verification items 3 and 4 | Built only as substitution sources; no selection, staging, or finalization is exercised or claimed |

## Exit criteria

1. Every task is satisfied, cancelled with rationale, or moved to a linked plan.
2. Each of verification item 2's eight criteria has a measured value for both
   formats or a recorded reason it could not be measured, and recovery
   behavior has a stated disposition.
3. SYS-049 has retained positive and negative evidence, with covered and
   uncovered cells of C-001's cross product enumerated.
4. Early-boot behavior is recorded as observed, including everything consumed
   before `/usr` is verified.
5. Every claim this plan makes is behind a registered check, and each check is
   verified failure-sensitive.
6. A C-007 recommendation exists with its evidence and its stated threats, and
   is **open for owner decision rather than accepted by the plan**.
7. Native diagnostics and failure evidence are retained.
8. The work register, DES-0006, and affected records are updated together.
9. Remaining unknowns are linked and assigned to a later gate or plan.

## Decision

Open for owner review.

Accepting this plan would authorize NeutrinOS source work again, bounded to the
scope above, on the basis PLN-0001 had: G1 is satisfied and PLN-0000's mutation
boundary requires G1 plus an accepted follow-on plan. The frontmatter carries
`gate: G1` -- the gate this plan executes under, per PR-0030 C-012 -- not G2.

It would **not** authorize: G2 or any G2 qualification claim, any physical-host
effect, any production key or enrollment, an ADR accepting EROFS or ext4, a
partition layout, a state filesystem, a confext path carve, or a package
ecosystem. It would not settle `S-004`, `C-009`, or `C-002`, and completing it
would not satisfy SYS-030, which is not applicable to a VM with a synthetic
anchor.
