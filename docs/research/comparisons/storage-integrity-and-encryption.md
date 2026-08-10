---
id: RES-0006
status: complete
last_updated: 2026-08-09
evidence_cutoff: 2026-08-09
decision_gates: [S-004, L-003, L-004, L-005, C-002]
---

# Storage, root-integrity, and encryption comparison

## Question

Which existing Linux and systemd/UAPI mechanisms can realize NeutrinOS's
accepted deployment, boot-integrity, persistent-state, confidentiality, and
recovery contracts without introducing a custom updater, object store, or disk
format?

This research compares mechanism roles. It does not treat a filesystem feature
as an ownership, backup, rollback, or security policy.

## Accepted constraints

The comparison starts from accepted policy rather than from a preferred
filesystem:

- a deployment set, not a disk, is the normal replacement and rollback unit;
- production physical boot authenticates the immutable release root from the
  platform trust anchor;
- persistent state does not roll back with the OS unless its owner performs a
  separately governed checkpoint transition;
- the workstation protects sensitive persistent data after powered-off loss;
- the router both protects long-lived credentials and completes expected
  reboots unattended;
- recovery is independently authorized and must not automatically trust or
  mount normal mutable state; and
- systemd ecosystem mechanisms are preferred when they meet the requirement.

## Systemd/UAPI storage primitives

### GPT and discoverable partitions

The [Discoverable Partitions Specification](https://uapi-group.org/specifications/specs/discoverable_partitions_specification/)
defines architecture-specific root, root-Verity, root-Verity-signature, `/var`,
`/home`, `/srv`, swap, ESP, and optional XBOOTLDR partition types. It also defines
read-only, no-auto, and grow-filesystem flags and a convention that derives the
root and Verity partition UUIDs from the Verity root hash.

These types give NeutrinOS a standard discovery vocabulary. They do not decide
which duplicate root slot is selected, authorize a deployment, establish state
ownership, or make an encrypted volume safe to unlock.

### `systemd-repart`

Current [`repart.d`](https://github.com/systemd/systemd/blob/main/man/repart.d.xml)
definitions can create and grow GPT partitions, format `ext4`, Btrfs, XFS,
VFAT, EROFS, or SquashFS, populate new filesystems, create LUKS2 containers,
and generate matching Verity data and signature partitions. Population happens
before a newly created partition is registered, preventing a new partition
from appearing partially initialized.

The important limit is equally useful: ordinary repart operation does not
shrink, move, or delete existing partitions. A conversion from the current
mutable ext4 layouts to the proposed layout is therefore a deliberate
provisioning or migration operation with backup and restore, not a clever
first-boot resize assumption.

### `systemd-sysupdate`

Current [`sysupdate.d`](https://github.com/systemd/systemd/blob/main/man/sysupdate.d.xml)
supports versioned regular-file and GPT-partition targets. An empty partition
slot is populated before its label records the installed version; multiple
transfers can be coordinated by one version; and the UKI or other entry-point
transfer can be ordered last. `InstancesMax=` retains at least two instances
and `ProtectVersion=` protects the booted version.

That maps naturally to two root slots, two matching Verity slots, and versioned
UKIs. The version and partition label remain locators, not deployment identity.
DES-0001's manifest and boot-time artifact binding are still required to
prevent a valid but unqualified hybrid.

### LUKS2 enrollment

[`systemd-cryptenroll`](https://github.com/systemd/systemd/blob/main/man/systemd-cryptenroll.xml)
and `systemd-cryptsetup` support LUKS2 passphrases, high-entropy recovery keys,
FIDO2 tokens, PKCS#11 tokens, and TPM2 enrollment. A TPM2 signed PCR policy can
authorize any UKI measurement signed by the policy key rather than sealing to
one literal current PCR value, which is specifically intended to permit OS
updates. TPM2 enrollment can additionally require a PIN.

[`systemd-pcrlock`](https://www.freedesktop.org/software/systemd/man/devel/systemd-pcrlock.html)
can predict measured-boot states and bind LUKS2 unlock to an NV-backed policy,
but upstream still marks the tool experimental. It is valuable spike material,
not an initial production dependency.

LUKS2 protects confidentiality at the block-device boundary after correct key
management. It does not authenticate an OS release, qualify an update, protect
plaintext after unlock, replace credential revocation, or make its header and
recovery material self-backing-up.

### Root discovery and image construction

Systemd's [boot and root filesystem discovery](https://systemd.io/ROOTFS_DISCOVERY/)
model composes systemd-boot, signed UKIs, discoverable root images, dm-verity,
`systemd-repart`, and mkosi. The kernel's
[dm-verity](https://docs.kernel.org/admin-guide/device-mapper/verity.html)
target verifies reads from a read-only block device against a trusted root
hash. If that root hash is carried by an authenticated UKI, the platform-to-root
integrity chain required by SYS-030 has a direct mapping.

NeutrinOS does not initially need to encrypt its release root: release artifacts
contain no machine or user secret, while confidentiality would make identical
plaintext produce machine- or build-specific ciphertext and add an unlock
dependency to otherwise public recovery material.

## Immutable root format comparison

The filesystem format lives *inside* a root artifact. It is not the deployment
identity, update transaction, or trust root.

| Candidate | Strengths | Costs and risks | Initial disposition |
| --- | --- | --- | --- |
| EROFS + dm-verity | Purpose-built read-only image filesystem; optional compression; block-aligned reads; supported by systemd image dissection and `systemd-repart` | Less operational history in this fleet; kernel/tool versions and reproducible image behavior need qualification | Leading root-format candidate |
| ext4 image + dm-verity | Extremely familiar tooling and repair inspection; supported throughout the Linux/systemd path | Carries writable-filesystem machinery that the root will not use; generally less space-efficient without outer transport compression | Baseline challenger and fallback |
| SquashFS + dm-verity | Mature compressed read-only image format | Compression/runtime trade-offs and tooling add no demonstrated initial advantage over EROFS | Secondary challenger only if measurements justify it |
| Btrfs subvolume | Native snapshots, reflinks, checksums, and `systemd-sysupdate` subvolume targets | A writable filesystem and snapshot graph complicate exact immutable-root identity; boot authentication needs another binding scheme | Rejected for the initial release root |

The [EROFS kernel documentation](https://docs.kernel.org/filesystems/erofs.html)
describes it as a read-only image filesystem suitable for immutable system and
container images. dm-verity remains necessary for the accepted block-level
authentication claim; read-only format and cryptographic authenticity are
different properties.

## Persistent filesystem comparison

Persistent state needs a different choice from immutable release content.

The original design session supplies important project-specific evidence: the
owner is partial to Btrfs or ZFS and explicitly wants filesystem features to
improve container and VM workflows. The stated direction was Btrfs for general
mutable `/var` and `/home`, using reflinks for cheap VM/DDI copies, while
reserving ZFS for a possible storage or hypervisor role. See the
[design-session transcript](../../background/2026-08-09-design-session-transcript.md).

| Candidate | Useful properties | Operational consequence | Proposed use |
| --- | --- | --- | --- |
| Btrfs | Checksummed data/metadata, subvolumes, reflinks, compression, snapshots, send/receive, and quotas directly support the stated container/VM and state-boundary goals | Requires scrub, free-space, quota, snapshot-retention, send/receive confidentiality, and VM/database CoW policy; snapshots share failure domain | Leading general mutable-filesystem candidate |
| ext4 | Broad tooling and recovery familiarity; metadata checksums; stable behavior on ordinary single devices | No native subvolume, reflink, send/receive, or snapshot boundary; owner checkpoints require application or backup tooling | Conservative challenger for roles that do not benefit from Btrfs features |
| XFS | Strong large-filesystem, reflink, and quota capabilities | No shrink path and no demonstrated initial fleet advantage over Btrfs for the stated workflows | Not selected initially |
| ZFS | Integrated checksums, snapshots, send/receive, pools, and rich storage management | Out-of-tree kernel integration and a separate operational ecosystem need strong justification under ADR-0001 | Deferred to a future storage role |

The [Btrfs subvolume documentation](https://btrfs.readthedocs.io/en/latest/Subvolumes.html)
is explicit that a snapshot is not a backup because snapshot and origin share
the same storage and failure domain. NeutrinOS may use snapshots as one
state-owner's checkpoint implementation, never as evidence that OS rollback or
backup requirements are satisfied.

The leading default is therefore Btrfs inside LUKS2 for mutable system, user,
and workload state. ext4 remains the conservative challenger, especially for a
role whose actual state does not benefit from reflinks, subvolumes, checksums,
send/receive, or quotas. The exercise must use actual VM, container,
source-tree, backup, restore, low-space, and corruption workflows. Btrfs
adoption remains conditioned on an explicit scrub, quota, snapshot,
send/receive, and CoW runbook; filesystem-specific features must not leak into
the common state contract.

## Encryption-boundary options

### Encrypt the whole disk as one volume

Rejected. The boot artifact filesystem and authenticated public release
artifacts do not need confidentiality, while machine, user, workload,
diagnostic, swap, and recovery data can have different unlock and destruction
lifecycles. One volume also makes independent preservation or key destruction
harder.

### One encrypted volume per directory or state owner

Rejected as a default. Perfect physical separation would create excessive
fixed sizing, unlock slots, header backups, recovery secrets, mounts, and
failure combinations. State contracts can share a physical volume when their
custody, unlock, backup, and destruction policies are compatible.

### Volumes by custody and unlock boundary

Preferred. A machine-state volume may contain several state-contract
namespaces with the same machine custody and early-boot unlock. A workstation
user/workload volume may be independently recoverable from system state. A
separate volume is required when confidentiality, unlock timing, recovery
authority, preservation, or destruction differs materially—not merely because
two paths have different application owners.

## Unlock profiles

### Workstation

The accepted objective allows either normal unattended reboot or an owner-
selected interactive policy. The initial candidate is LUKS2 with TPM2 unlock
bound to authorized measured UKIs plus an independently stored recovery key.
TPM2+PIN is the stronger optional profile when physical presence at each cold
boot is acceptable. Exact PCRs and whether the system may auto-unlock after a
routine firmware update are qualification questions, not configuration copied
from an internet recipe.

### Router

The observed router cannot presently satisfy both unattended reboot and
powered-off credential confidentiality. Its production profile requires an
installed and qualified hardware-bound secret facility; the documented
Supermicro TPM2 module is the leading path. LUKS2 TPM2 unlock must be bound to
the authenticated/measured normal boot policy and retain an offline recovery
key usable through the independent console path.

Until that hardware path is exercised, the router may test unencrypted public
release content and non-production state, but it cannot claim the accepted
production confidentiality objective. A key file beside the encrypted volume,
an obfuscated secret, or a network service reached through the router's own
data plane is not an acceptable substitute.

## Swap, hibernation, diagnostics, and temporary data

- Unencrypted swap is prohibited when it can contain protected plaintext.
- Without hibernation, swap may use a fresh random key at each boot and have no
  recovery obligation.
- Hibernation requires persistent encrypted swap and resume authorization
  joined to the workstation unlock and boot-integrity policy; hibernation
  remains a workstation-role decision.
- Crash dumps and persistent journals follow their data classification and
  must have explicit quotas and retention. A public diagnostic partition may
  not silently receive secrets.
- `/tmp` may be ephemeral. `/var/tmp` and caches are not declared ephemeral by
  path alone; their state contracts decide.

## Mutable-state integrity

LUKS2/dm-crypt without authenticated encryption does not detect every offline
modification. Filesystem checksums primarily detect corruption, not malicious
replacement under a trusted key. dm-integrity or authenticated LUKS modes add
write amplification, capacity, recovery, and hardware-performance concerns.

The initial claim is confidentiality against powered-off extraction plus
authenticated release content, not cryptographic authenticity of all mutable
state. Unexpected offline access or compromise moves mutable state into the
hostile-state recovery path under SYS-035. An authenticated-encryption option
may be revisited only with workload and power-loss measurements.

## Recommendation

Proceed with this paper baseline:

1. GPT using DPS types, managed by `systemd-repart` for blank-image creation
   and safe growth—not for magical in-place conversion.
2. An ESP-backed boot artifact store, two root slots, two matching dm-verity
   hash slots, and an independently retained recovery artifact or environment.
   Add a separate XBOOTLDR only if measured UKI capacity, firmware behavior, or
   lifecycle isolation justifies it.
3. An unencrypted, read-only EROFS root candidate authenticated by a root hash
   bound into its signed UKI; ext4+dm-verity remains the required comparison.
4. Exact normal configuration flattened into the root until a separate config
   artifact can prove exact boot-time binding.
5. LUKS2 state volumes split by custody and unlock policy, with Btrfs as the
   leading mutable default and ext4 as the conservative bounded challenger.
6. A signed-PCR-policy TPM2 unlock candidate plus a separately retained
   recovery key; `systemd-pcrlock` remains experimental spike material.

## Falsification and implementation gates

Reject or revise the baseline if a spike cannot demonstrate:

- exact UKI-to-root-and-Verity binding across both slots and deliberate
  rollback;
- old selection, complete new selection, or diagnosable stop under power loss
  at each root, Verity, UKI, label, and boot-entry transition;
- acceptable EROFS kernel/tool compatibility and measured boot performance;
- recovery after TPM clear, firmware and Secure Boot changes, mainboard loss,
  damaged LUKS metadata, and loss of the routine unlock path;
- offline router reboot and fallback without its production network path;
- no plaintext spill into swap, crash dumps, temporary storage, or diagnostics;
- state-volume backup and restore by owner rather than by undifferentiated
  `/var`; and
- usable capacity on the 16 GB router system disk or an explicitly accepted
  migration to a different target disk.
