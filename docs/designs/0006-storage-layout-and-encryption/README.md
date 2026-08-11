---
id: DES-0006
title: Storage layout, immutable root, and encryption
status: in-review
owners: [Jason Tarasovic]
reviewers: [Codex]
created: 2026-08-09
last_updated: 2026-08-11
depends_on: [DES-0001, DES-0002, DES-0003, DES-0004]
decision_backlog: [S-004, L-003, L-004, L-005, C-002]
related_adrs: []
---

# Storage layout, immutable root, and encryption

## Problem

NeutrinOS needs a physical storage model that can stage and select an exact
deployment, authenticate its root, preserve independently owned state, protect
sensitive data, and recover after failed updates or lost unlock hardware.

A conventional mutable root conflates release and state. Whole-disk snapshots
conflate OS rollback with data rollback. Full-disk encryption alone conflates
public release content with several data-custody and recovery boundaries. A/B
partitions alone do not prove that a UKI, root image, Verity tree, and exact
configuration belong to the same qualified deployment.

This design defines those boundaries before choosing partition byte counts or
performing any migration on the reference machines.

## Goals

- Map the deployment-set lifecycle onto robust, standard storage objects.
- Authenticate immutable root content from the accepted platform boot path.
- Keep release artifacts physically and logically separate from persistent
  state.
- Split encrypted state by custody and unlock lifecycle without creating one
  volume per path.
- Support two retained normal deployments and independently authorized
  recovery.
- Meet workstation powered-off confidentiality and router unattended reboot
  objectives honestly.
- Make installation, resizing, backup, restore, key loss, disk replacement,
  and compromise recovery explicit.

## Non-goals

- Select final partition sizes before representative artifacts exist.
- Promise in-place conversion of the current workstation or router disks.
- Make filesystem snapshots a generic rollback or backup mechanism.
- Authenticate all mutable state cryptographically.
- Finalize the confext lifecycle that delivers configuration, the
  administrator-override surface, or the bounded experimentation path for
  unqualified configuration. Ownership and delivery remain decision-backlog
  item `C-002`; the lifecycle SYS-123 demands belongs to DES-0005. This design
  states only what storage must guarantee.
- Select the workstation hibernation policy, backup product, or workload
  volume format without representative exercises.
- Design a general storage-server, RAID, NAS, or ZFS role.

## Requirements and constraints

DES-0001 makes the deployment set the unit of staging, selection, blessing,
retention, and rollback. DES-0002 makes persistent state owner-specific and
requires compatibility gates across OS rollback. DES-0003 and accepted
SYS-030 require platform-to-root authentication. DES-0004 and ADR-0002 separate
normal release, recovery, machine, and data authorities.

SYS-034 and PR-0005 require protected workstation state and protected router
credentials while allowing role-specific unlock behavior. The router must
reboot unattended, but the observed hardware currently exposes no TPM. The
design cannot repair that hardware fact with a software key stored beside the
ciphertext.

ADR-0001 prefers systemd/UAPI mechanisms. RES-0006 establishes that GPT/DPS,
`systemd-repart`, `systemd-sysupdate`, signed UKIs, dm-verity, LUKS2, and
`systemd-cryptenroll` form a plausible direct path.

## Decision drivers

1. An interrupted update must not overwrite the booted deployment or expose a
   boot entry for incomplete root content.
2. The booted UKI and root/Verity pair must be joined by authenticated content,
   not a mutable slot name or version label.
3. Replacing a deployment must not rewrite machine identity, user data,
   workload data, or diagnostics.
4. Encryption recovery must survive TPM clear, firmware change, mainboard
   failure, and loss of the routine unlock method.
5. Recovery must remain usable without trusting the normal root, `/etc`, state
   volume, publication service, or router data plane.
6. One maintainer must be able to inspect and repair the layout without making
   OS identity depend on a custom object store or accumulated snapshot history.
7. The approximately 16 GB router system disk makes capacity and retained
   recovery real design gates rather than afterthoughts.

## Proposed decision

NeutrinOS uses a GPT layout based on Discoverable Partitions Specification
types. Normal release content is held in two independently writable storage
slot pairs: one read-only root filesystem image and one matching dm-verity hash
artifact per slot. The ESP is the initial boot artifact store for systemd-boot,
versioned signed UKIs, and the firmware fallback path. A separate XBOOTLDR is
introduced only if measured UKI capacity, firmware behavior, update safety, or
recovery isolation demonstrates that it is needed.

Each signed UKI carries or authenticates the root hash for exactly one root and
Verity pair. That binding, plus the deployment manifest, identifies the booted
deployment. `A`, `B`, partition order, GPT label, filename, and human version
are storage and discovery metadata only.

Release root content is not encrypted and contains no machine, user, workload,
or production secret. Exact normal configuration is initially flattened into
the root artifact. Persistent mutable data resides in LUKS2 volumes separated
when custody, unlock timing, recovery authority, preservation, or destruction
policy differs.

**The flattening sentence is superseded 2026-08-11 by the C-013 resolution:
the authenticated artifact is `/usr`, and configuration is delivered by signed
confexts rather than flattened into it. See
[the amendment](#amendment-2026-08-11-the-authenticated-artifact-is-usr).**

Btrfs is the leading mutable-filesystem candidate, reflecting the
[original design goal](../../background/2026-08-09-design-session-transcript.md)
of using reflinks, subvolumes, checksums, send/receive, quotas, and compression
to improve container, VM, backup, and state workflows. ext4 is the conservative
role-specific challenger. EROFS is the leading immutable image format for the
authenticated `/usr` artifact, with ext4+dm-verity retained as a mandatory
challenger under C-007.

## Physical regions and ownership

| Region | Contents and owner | Mutability | Integrity/confidentiality policy |
| --- | --- | --- | --- |
| GPT metadata | Layout version, typed partitions, slot locators | Provisioning and controlled layout migration | Redundant GPT plus captured layout evidence; not deployment authorization |
| Boot artifact filesystem | Initially the ESP: systemd-boot, firmware fallback, versioned normal UKIs, and optionally a local recovery UKI; split into ESP plus XBOOTLDR only if justified | Native updater, boot-attempt accounting, and exceptional bootloader update | Signed executable artifacts; no secrets; bounded capacity and power-loss tests |
| Normal `/usr` slots | Exact authenticated release artifact. Per C-013 this is `/usr`, not a complete root, and it carries release-owned defaults in `/usr/lib` rather than flattened `/etc` | Inactive slot replacement only; mounted read-only | dm-verity; root hash authenticated by matching signed UKI |
| Normal Verity slots | Hash tree for exact matching `/usr` slot | Replaced with inactive `/usr` | Authenticated through UKI-bound root hash |
| Configuration artifacts | Signed confexts delivering exact normal configuration, release-owned under SYS-123 | Replaced as deployment-set members; never written in place | dm-verity and signature verified under `image_policy_confext_strict`; mutable mode forbidden |
| Root partition | Mount namespace host for the state-backed writable tree; holds nothing durable in `/etc`, which is regenerated at boot | Written by state owners only | Unauthenticated state, not release content; covered by state-volume policy |
| Recovery artifact | Independently authorized recovery UKI and optional recovery root/Verity | Exceptional managed replacement | Separate recovery authorization; excluded from normal fallback |
| Machine-state volume | Machine identity, enrollment, required system state, controlled admin state, operational evidence namespaces | Persistent across deployment replacement | LUKS2 when contents are sensitive; owner contracts and quotas |
| User/workload volume | Home, rootless containers, VM disks, user and workload state | Persistent and independently preserved | Separate LUKS2 custody/recovery boundary on workstation |
| Swap | Paging and possibly hibernation image | Disposable unless hibernation is enabled | Fresh random key without hibernation; persistent protected key if hibernation is accepted |
| Reserve | Space for update temporaries, diagnostics, and one declared layout evolution | Allocated only through controlled layout policy | Must not be silently consumed by ordinary state growth |

State contracts can share a physical volume. Paths remain separately owned and
must carry independent schema, migration, backup, reset, retention, and health
rules. The filesystem or mount point does not become their lifecycle owner.

## Boot and root authentication

The normal boot chain is:

```text
owner-controlled UEFI Secure Boot
        -> authenticated systemd-boot
        -> selected signed UKI
        -> UKI-authenticated root hash
        -> dm-verity root + hash slot pair
        -> read-only release root
        -> separately classified mutable state
```

The initial mapping does not need a root-Verity signature partition when the
trusted root hash is carried inside the signed UKI. A separate Verity signature
artifact may be introduced only if the selected systemd mechanism needs it and
the deployment manifest binds it exactly; it must not create a second floating
authorization path.

dm-verity read failures fail closed for release-owned content and produce
attributable diagnostics. They do not cause recovery to be selected
automatically. Boot attempt exhaustion may select only a retained eligible
normal deployment, as required by SYS-038; what happens when every eligible
deployment fails is designed under "Staging and selection".

## Root filesystem and `/etc`

The root image is a complete, read-only filesystem rather than only `/usr`.
This keeps early boot, release defaults, and the initially flattened exact
normal configuration in one authenticated artifact.

EROFS is proposed because it is purpose-built for immutable images and can use
compression without importing an object store. ext4+dm-verity remains the
baseline challenger because its kernel and tooling path is maximally familiar.
The spike chooses between them using reproducible image output, boot behavior,
update size, memory, performance, tooling, corruption, and recovery evidence.

There is no generally persistent writable `/etc`. Initially, rendered normal
configuration is in the root deployment. Machine identity and secrets are
delivered or projected from explicit state and late-bound contracts. A future
controlled administrator override surface must remain attributable and mark
the machine locally modified; this design reserves state custody for it but
does not prematurely select the projection mechanism.

Software that insists on writing durable `/etc` is unsupported until C-002
assigns a persistent exception and tests it. Mounting the whole directory
writable is not the fallback.

### Amendment 2026-08-11: the authenticated artifact is `/usr`

Accepted by Jason Tarasovic, resolving
[C-013](review.md). This supersedes the two paragraphs above and the
corresponding line in the proposed decision.

The read-only authenticated release artifact is **`/usr`**, with its dm-verity
hash pair and a signed UKI carrying the root hash -- not a complete root
filesystem. Release-owned defaults ship in `/usr/lib` on the vendor tier of the
configuration hierarchy that every systemd component already implements.

Configuration is delivered **only** by confexts, dm-verity protected and
signature-verified under `image_policy_confext_strict`, version-bound to the
deployment through `extension-release.d`. `Mutable=` write routing through
`/var/lib/extensions.mutable/` is forbidden: SYS-123 requires an
effective-configuration-changing mechanism to be a release-owned artifact and
not an unattributed mutable administrator layer, which is what mutable mode
would create.

The real `/etc` beneath any confext overlay holds **nothing durable**. It is
regenerated at boot by `systemd-tmpfiles` and `systemd-sysusers` from `/usr`.
Durable content discovered there is a fault to report, not state to preserve.
This satisfies SYS-020's reconstruction obligation by construction rather than
by inventory discipline.

A durable write to `/etc` must **fail at the moment it is attempted**, whether
or not a confext currently covers the path (C-006, ruled 2026-08-11). The
default behavior of a regenerated tree is the opposite: an uncovered path is an
ordinary writable directory, so the write succeeds, the service works, and the
change disappears at the next boot. Silent non-durability is a worse outcome
than a hard failure on a system whose claim is attributability, because it is
discovered at the next reboot rather than at the change. Storage therefore
requires that `/etc` present no writable durable surface in normal operation;
the mechanism that guarantees it belongs to DES-0005.

Consequences this amendment accepts:

- Per-machine identity cannot live in `/etc`. It must be projected from state
  or delivered as credentials, and exactly which is deferred to L-003 rather
  than settled here.
- Early boot is the weak point. The root partition is now unauthenticated
  state, so anything consumed before `/usr` is verified is outside the
  integrity boundary. The signed UKI command line and
  `systemd-confext-initrd`/`systemd-confext-sysroot` are the intended answers
  and must be exercised, not assumed.
- Every confext inherits SYS-123 in full: content identity, base compatibility,
  authorization, qualification, activation ordering, health, rollback,
  retention, and effective-deployment status. No design owns that lifecycle
  yet; DES-0005 is its home.
- Routine configuration change becomes a release-artifact operation. A bounded
  path for testing unqualified configuration is therefore required, and it must
  be non-durable by construction rather than by discipline, visibly marked
  while active, and either unavailable on production physical roles or
  attributable when used. `/run/confexts/` is a tmpfs search path and the
  `ephemeral` mutable modes exist, so this is assembly of existing mechanism
  rather than a question needing evidence. It conflicts with
  `image_policy_confext_strict`, which requires signed extensions, so the scope
  is a role distinction of the kind SYS-030 already draws. DES-0005 selects the
  mechanism; storage only requires that nothing on this path becomes durable.
- The release artifact is no longer a disk image, so the unreproducible btrfs
  and FAT bytes the
  [composition record](../../project/slice-composition-record.md) identified
  move to state, where reproducibility is not claimed. Release reproducibility
  becomes reachable with a pinned `mkfs.erofs`, which is a consequence of this
  decision and remains **not a reason for it**.

No accepted requirement is amended. SYS-049 binds "release root content" to an
identity carried by the boot artifact without fixing its scope, and its
acceptance evidence already lists configuration beside root, Verity, and UKI;
SYS-090 treats config as a distinct deployment-set member.

## Staging and selection

For two normal slot pairs:

1. Protect every slot and UKI belonging to the booted deployment.
2. Choose only an inactive root and matching Verity slot.
3. Mark the chosen slot pair ineligible for selection, durably, before writing
   any byte into it. The previous occupant stops being a retained fallback at
   this point rather than when it is overwritten.
4. Write root and Verity bytes, then verify their literal identities and root
   hash while they remain unselected.
5. Install the exact signed UKI only after its complete backing deployment set
   is staged and eligible.
6. Commit one trial selection through the bootloader's native attempt-counting
   mechanism.
7. At early boot, independently bind the actual UKI, root, and Verity bytes to
   the selected deployment identity.
8. Bless only after the exact deployment passes role health assessment.
9. Retain the previous complete eligible deployment until its retention
   reference and state-compatibility claim are deliberately removed.

Step 3 is what makes the failure analysis below true rather than aspirational.
On a first update the inactive slot is empty and the marking is invisible; on
every later update that slot holds the previous eligible deployment, and
without the marking the first byte written destroys a fallback that the
selection mechanism still considers a candidate. Ineligibility must survive
power loss, an unreadable ESP, and hostile offline modification; surviving the
first two is an accepted fallback, and surviving only power loss requires a
recorded reason, because that is marking held on the same filesystem as the
artifacts it describes. The mechanism is chosen by the substrate spike, which
owes evidence on the strongest level rather than the first that works.

`systemd-sysupdate` partition and file transfers are the leading mechanism,
but the substrate spike must prove power-loss outcomes. The layout does not
claim that updating several partitions is one physical atomic write.

### When every eligible deployment fails

Selection driven by exhaustion is itself durably counted, and a deployment that
has already been selected by exhaustion and failed assessment is not selected
that way again.

Response depends on whether the failing deployment has ever passed assessment.
A deployment that has never passed is unproven, and exhaustion selects an
eligible fallback. A deployment that has passed before indicts the environment
rather than the image, so at most one further attempt is made before stopping;
falling back cannot address a cause the fallback shares.

When no eligible normal deployment remains unselected, automatic selection
stops. The machine does not halt: the last deployment continues running,
degraded and reachable, and reports an attributable diagnosis naming each
deployment tried and its failure. Recovery is not entered automatically, as
SYS-038 requires, and the stop is a terminal state for selection only.

This is a design commitment beyond the requirement floor, not a reading of
SYS-038, whose bounded attempt accounting governs each deployment's own trial
boots rather than the loop between deployments. It exists because assessment
evaluates the machine in an environment that moves, so the causes that matter
are the ones common to both slots -- an expired certificate, a state schema
migrated beyond what the older deployment can read, PCR values changed by a
firmware update, failing hardware, or a health check that depends on reaching
something. Fallback helps only when the failure was caused by the thing being
fallen back from. Field practice is recorded in
[RES-0014](../../research/comparisons/embedded-ab-update-field-evidence.md);
no reviewed implementation halts the machine, and notification belongs to the
degraded running system rather than to a separate boot artifact.

Two things this does not settle. The exhaustion counter and the known-good
record are both state, and state is what may be damaged in the scenarios that
trigger them; where they live is unresolved. A machine kept running while
failing assessment is also running in an unassessed condition, and what it is
permitted to keep doing there -- forwarding router traffic in particular -- is
not defined here.

## Persistent state layout

### Common machine state

One encrypted machine-state volume may contain namespaces for:

- enrolled machine identity and host credentials;
- service identities whose lifecycle is the machine rather than a user;
- state-contract and migration records;
- persistent administrative overrides and their attribution metadata;
- journals, boot assessment, update evidence, and crash diagnostics under
  quotas; and
- explicitly classified durable system service state.

It is not “persistent `/var`” as a policy. Each populated namespace must be in
the ownership inventory. Reconstructible caches may share the filesystem only
with an explicit eviction policy and must not consume the reserved diagnostic
or migration capacity.

### Workstation user and workload state

`desktop-jason` uses a separate encrypted user/workload volume on its current
approximately 1 TB data NVMe. User home, rootless container stores, source
trees, and VM disks may share this physical custody and recovery boundary
while retaining distinct logical state contracts.

Btrfs is the leading filesystem for this volume because the container and VM
workflows explicitly motivated reflinks and subvolume boundaries. ext4 remains
the bounded challenger. A Btrfs snapshot may be one owner's local checkpoint,
but normal OS selection never switches the entire user/workload filesystem to
a snapshot.

### Router state

The router uses one encrypted state volume for protected machine and service
state unless a credential has an independently managed hardware token or
external authority. Btrfs is the common leading candidate; ext4 may win for
this role if its simpler space and recovery behavior outweighs Btrfs features
the router does not use. Public release artifacts remain outside the state
volume. Logs and network metadata receive explicit sensitivity, quota, and
retention decisions.

EX-0008 leaves two physical layouts in competition: retain the 16 GB boot/root
disk and place state on the 1 TB disk, or make the larger disk the single
primary normal boot and state device. Measured artifact capacity and exercised
firmware/IPMI recovery decide the result.

## Encryption and unlock

### Common rules

- LUKS2 is the block-encryption format.
- Volume boundaries follow custody and unlock policy, not arbitrary paths.
- Every encrypted volume has at least one routine unlock method and one
  independently retained high-entropy recovery method.
- LUKS header metadata is backed up separately from the encrypted device and
  recovery key; the backup's identity, date, confidentiality, and restore test
  are recorded.
- Adding a new unlock method is verified before an old method is removed.
- Recovery material is never stored only on the volume or machine it recovers.
- Destruction records which keys, headers, backups, and external credentials
  must be destroyed or revoked.

### TPM2 profile

The leading unattended profile uses a TPM2-sealed LUKS key bound to signed PCR
policy for authorized measured UKIs, plus an offline recovery key. A signed
policy is preferred over sealing solely to today's literal PCR values because
the latter turns every normal update into resealing choreography.

Exact PCR selection, policy signing custody, firmware-update behavior, and
TPM2+PIN use remain physical qualification results. `systemd-pcrlock` may be
compared in the spike but is not a production dependency while upstream marks
it experimental.

### Workstation

The default candidate supports unattended normal reboot through TPM2 policy,
consistent with PR-0005. The owner may select a TPM2+PIN or FIDO2-assisted
interactive profile for stronger physical-presence semantics. Login/session
authentication remains separate in every profile.

### Router

Production qualification requires the documented discrete TPM2 module or an
accepted equivalent hardware-bound facility to be installed and exercised.
The router then uses unattended TPM2 unlock bound to its authenticated normal
boot path. Recovery key entry through an independently secured IPMI or local
console is exceptional and may require an outage.

Without qualified hardware, development may continue without the
confidentiality claim. NeutrinOS will not store an automatic unlock key beside
the encrypted state, weaken the accepted objective silently, or depend on WAN,
DNS, the routed data plane, or an online secret service for normal boot.

## Installation and layout evolution

`systemd-repart` definitions are the leading declaration for blank disks,
image construction, first-boot creation of missing state volumes, and safe
growth. They do not authorize role or machine assignment and do not become the
normal desired-state engine.

Provisioning must record:

- target disk identity and approved destructive scope;
- layout schema and exact applied definitions;
- created partition and filesystem identities without publishing secrets;
- deployment and recovery sets initially installed;
- state volumes created, preserved, restored, or destroyed;
- unlock and recovery enrollment results; and
- interruption and completion status.

Existing layouts are migrated by an explicit plan using verified backups and
scratch rehearsal. Shrink, move, filesystem conversion, or cross-disk
relocation is not delegated to ordinary boot. Layout changes after enrollment
are maintenance operations with their own space preflight, backup, recovery,
power-loss, and rollback plan.

## Recovery behavior

The recovery environment is separately authorized and retained independently
of both normal root slots. It may be a local signed UKI plus root/Verity pair,
an appropriately self-contained recovery UKI, or exercised owner-controlled
removable/IPMI media. The exact packaging is selected by the capacity spike.

Recovery boots with normal mutable volumes locked. It first inspects platform,
deployment, slot, Verity, layout, and available state metadata that can be
trusted without mounting those volumes. Unlock and mount are deliberate
capability transitions. Read-only or snapshot-assisted inspection is preferred
before mutation, but neither is described as safe against hostile state without
the corresponding threat controls.

Ordinary availability recovery may preserve state. Suspected compromise does
not automatically restore it; state is quarantined, selectively restored,
re-enrolled, or destroyed by owner as required by SYS-035.

## Filesystem and space operations

- Btrfs is the leading mutable default because its reflinks, subvolumes,
  checksums, send/receive, quotas, and compression address explicit container,
  VM, backup, and state-management goals.
- Btrfs adoption still requires a scrub, quota, snapshot-retention,
  send/receive-confidentiality, free-space, and VM/container CoW runbook.
- ext4 remains the conservative role-specific challenger when those features
  do not justify the added operating surface.
- XFS is not an initial candidate because it adds no demonstrated advantage for
  the stated workflows. ZFS remains a future storage/hypervisor-role candidate;
  its out-of-tree kernel integration is not justified for the common baseline.
- Filesystem health checks are evidence, not permission to mount state in
  compromise recovery.
- Every role reserves bounded space for one candidate deployment, required
  fallback, recovery, update temporaries, migration checkpoints, and retained
  diagnostics.
- Full state storage cannot evict the selected deployment, required fallback,
  recovery environment, or boot evidence.

## State and compatibility

The storage layout version and filesystem features are machine state. They are
not rolled back when an older OS is selected. Every candidate and automatic
fallback must support the current LUKS2 metadata, filesystem feature set,
layout schema, and state mounts.

Filesystem feature upgrades that an older retained deployment cannot read are
forward-only state migrations. They cross an explicit commit barrier under
SYS-023. A snapshot, root slot, or recovery image does not undo an incompatible
filesystem feature flag.

Backup and restore operate on state-contract consistency boundaries. A raw
encrypted-device copy, filesystem snapshot, and file-level backup provide
different guarantees; each inventory record names which is authoritative and
how restoration is verified.

## Security and trust

The design claims:

- authenticated release-owned root content when Secure Boot, signed UKI, root
  hash, and dm-verity checks all succeed;
- powered-off confidentiality for state whose LUKS2 unlock material remains
  unavailable to the attacker under its role-specific hardware and recovery
  assumptions; and
- preservation of independently owned state across normal OS deployment
  replacement.

It does not claim:

- confidentiality after an authorized unlock;
- authenticity or benignness of mutable state;
- protection from compromised authorized firmware, kernel, initrd, service,
  or session;
- secure deletion of every SSD remanence through file removal;
- backup independence from a same-disk snapshot; or
- production router confidentiality before its hardware-bound unlock path is
  installed and qualified.

## Failure and recovery analysis

| Failure | Required result |
| --- | --- |
| Root or Verity staging interrupted | Inactive partial bytes remain ineligible; current selection is unchanged |
| Ineligibility marking interrupted | Target remains ineligible or the marking is not observed at all; never a slot marked eligible with foreign bytes in it |
| Every eligible deployment boots and fails assessment | Automatic selection stops; last deployment keeps running and remains reachable; attributable diagnosis names each deployment tried; no automatic recovery entry |
| UKI installation interrupted | No entry point to incomplete backing artifacts; current selection remains |
| GPT label or boot selection write interrupted | Old selection, one complete trial, or attributable stop—never a hybrid |
| dm-verity detects corruption | Fail closed for affected release content; retain diagnosis; choose only eligible normal fallback |
| State volume absent or damaged | Recovery remains bootable; role health fails; no silent state reinitialization |
| TPM or PCR policy rejects unlock | Preserve encrypted state; allow deliberate recovery input; report exact failed mechanism |
| Recovery key unavailable | Do not erase or recreate automatically; follow backup or declared data-loss procedure |
| LUKS header corrupt | Preserve source; restore tested header backup to a copy or replacement target first |
| Filesystem full | Preserve boot/fallback/recovery references; bound logs/caches; block unsafe update or migration |
| State schema advances incompatibly | Remove old deployment from automatic fallback before commit barrier |
| Suspected offline tamper | Treat mutable state as hostile; recovery does not auto-mount or execute it |

## Operations and diagnostics

Machine status must expose at least:

- physical layout schema and drift;
- boot artifact filesystem identity, health, and free space, including whether
  an optional XBOOTLDR is present and why;
- each root/Verity slot's artifact identities and verification result;
- which deployment references each slot and which references protect it from
  garbage collection;
- LUKS volume identity, enrolled unlock mechanism types, recovery/header-backup
  verification dates, and policy status without secret material;
- filesystem type, feature compatibility, health, capacity, and reserved-space
  status;
- state mounts and their owning contract identifiers; and
- whether recovery or exceptional unlock changed support status.

Diagnostics distinguish corruption, authentication failure, authorization
failure, incompatible state, missing hardware, wrong recovery input, and
ordinary filesystem damage. “Could not mount root” is not sufficient.

## Alternatives considered

### One mutable encrypted root filesystem

Rejected. It makes release identity depend on mutation history, cannot provide
the accepted root-integrity and rollback boundary cleanly, and entangles OS
repair with state preservation.

### One whole-disk A/B image

Rejected. Duplicating the entire disk would duplicate or overwrite mutable
state, machine identity, and recovery material. A factory or installer image
may be whole-disk transport without becoming the normal update unit.

### Btrfs snapshots for OS and state rollback

Rejected as the common model. Snapshot selection does not authenticate the
root, establish application consistency, provide an independent backup, or
make it safe to rewind user and workload state with the OS.

### Encrypt every byte including release roots

Rejected initially. Public authenticated release bytes have no confidentiality
requirement. Encrypting them increases key and recovery coupling without
protecting the sensitive state that belongs in separate volumes.

### Store the router unlock key on disk

Rejected. It provides unattended boot but no meaningful powered-off credential
confidentiality when the disk and key are acquired together.

## Verification

The design is not implementation-ready until a bounded spike demonstrates:

1. blank-disk creation from literal partition definitions in a UEFI VM;
2. EROFS and ext4 `/usr` artifacts authenticated through the exact signed UKI
   and dm-verity path, with early boot exercised: `fstab`, `crypttab`, and any
   initrd-stage configuration consumed before `/usr` is verified;
3. two complete normal slots with interrupted staging, trial failure,
   blessing, fallback, and deliberate rollback;
4. substitution of a valid root, Verity tree, UKI, config, or slot label from
   another deployment failing the exact-binding gate;
5. recovery boot after both normal slots fail, with mutable state initially
   locked;
6. LUKS2 routine unlock, recovery-key unlock, rotation, header backup/restore,
   TPM clear, firmware change, Secure Boot change, and simulated mainboard
   replacement;
7. no plaintext leakage through swap, hibernation, dumps, temporary data, or
   diagnostics under the selected role policy;
8. owner-consistent state backup and restore to a blank replacement volume;
9. workstation Btrfs/ext4 representative workload comparison;
10. router capacity and R-A/R-B physical layout comparison;
11. router offline unattended boot, failed-update fallback, and IPMI/local
    recovery with its production network path absent; and
12. full-storage, filesystem-corruption, missing-disk, and incompatible-feature
    failure behavior.

## Accepted requirements

The project-level review accepts SYS-048 through SYS-056:

- SYS-048: every persistent storage region maps to an explicit release,
  recovery, state, lifecycle-metadata, or reserve owner.
- SYS-049: normal release root content is read-only and authenticated through
  an exact UKI-to-root/Verity binding.
- SYS-050: staging and retention preserve at least one complete current normal
  deployment and one complete candidate or fallback without hybrid selection.
- SYS-051: sensitive persistent data and all plaintext spill paths are
  protected by a declared encryption and unlock boundary.
- SYS-052: each encrypted volume has independent recovery, header backup,
  rotation, loss, and destruction behavior.
- SYS-053: unattended hardware-bound unlock is qualified against the accepted
  boot policy and never emulated by a colocated software secret.
- SYS-054: recovery does not automatically unlock, mount, execute, or restore
  normal mutable state.
- SYS-055: filesystem snapshots and checkpoints remain state-owner operations
  and do not imply OS rollback or backup.
- SYS-056: layout capacity, growth, migration, and garbage collection preserve
  booted, fallback, recovery, state, and diagnostic safety margins.

## Risks and unresolved questions

- Does EROFS materially outperform or simplify ext4+dm-verity for actual
  NeutrinOS `/usr` images? (C-007, open. C-013 is resolved, so this is now
  asked against the `/usr` artifact rather than a full root.)
- Can `systemd-sysupdate` finalize root, Verity, and UKI resources with the
  exact all-old/all-new behavior required by DES-0001 under power loss?
- Should recovery be a self-contained UKI, a separate root/Verity pair, local
  media, IPMI virtual media, or more than one of these?
- Which PCR and signed-policy design survives firmware, Secure Boot, and normal
  UKI rotation on both physical roles?
- Is a TPM2+PIN appropriate for the workstation, or is unattended unlock plus
  strong session authentication the selected owner policy?
- Does the router's compatible discrete TPM module fit, enumerate, and support
  the needed policy commands?
- Which exact state namespaces share each volume, and which `/etc` writers need
  controlled persistent exceptions?
- Does workstation hibernation enter initial scope?
- Which filesystem wins the workstation user/workload exercise?
- Does the router keep its 16 GB system disk or move the complete lifecycle to
  the larger disk?
- What recovery-time and recovery-point objectives size backup and diagnostic
  reserves for each role?

## Review disposition

The design is in adversarial review. RES-0006 supports the mechanism choices,
and EX-0008 applies them to the reference machines. The root format,
workstation mutable filesystem, router target disk, recovery packaging, and
exact TPM policy remain bounded evidence gates rather than hidden assumptions.
