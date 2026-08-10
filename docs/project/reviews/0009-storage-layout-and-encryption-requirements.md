---
id: PR-0009
subject: Storage layout and encryption requirements
reviewer: Codex adversarial pass
date: 2026-08-09
status: accepted
---

# Storage layout and encryption requirements review

## Decision scope

This review asks whether SYS-048 through SYS-056 should become normative before
NeutrinOS fixes partition sizes, immutable and mutable filesystem formats,
recovery packaging, TPM PCR policy, workstation unlock preference, or the
router's target disk.

It reviews the boundaries in DES-0006 and the reference layouts in EX-0008. It
does not claim that `systemd-sysupdate`, EROFS, TPM2 enrollment, or physical
recovery behavior has passed a spike.

## Summary judgment

The proposed requirements should be accepted because they prevent storage
mechanisms from silently changing already accepted semantics: a slot cannot
become deployment identity, a snapshot cannot become state rollback, encryption
cannot become boot authentication, and recovery cannot become automatic trust
of mutable state.

The strongest objection is premature physical commitment. It would be a
mistake to encode EROFS, Btrfs, two partitions, a separate XBOOTLDR, a PCR list, or a TPM
module in normative system requirements before artifacts and hardware are
exercised. SYS-048 through SYS-056 therefore state guarantees and ownership
boundaries, while DES-0006 keeps mechanism choices falsifiable.

## Accepted requirement disposition

### SYS-048: Every storage region has a lifecycle owner

Every persistent partition, volume, filesystem, subvolume, mount, image store,
and reserved region maps to one or more explicit deployment artifact,
recovery, lifecycle-metadata, state-contract, or capacity-reserve purposes.
Sharing physical storage is allowed; an undifferentiated mutable root or `/var`
is not an ownership model.

The requirement does not demand a partition per state owner. A new physical
boundary exists only when update, custody, unlock, backup, preservation,
destruction, capacity, or recovery semantics require it.

### SYS-049: Exact authenticated immutable root

Normal release root content is mounted read-only and authenticated against an
exact identity carried or authenticated by the selected boot artifact. Boot
must reject a substituted root, Verity artifact, configuration artifact, or
other release-owned member even when that object is independently valid.

This requirement permits EROFS, ext4, or another qualified root format. It
requires dm-verity or an alternative that satisfies the same platform-to-root
claim and failure behavior.

### SYS-050: Complete retained slot closure

Storage and selection must retain the complete booted deployment and enough
independent capacity for one complete candidate or eligible fallback. Partial
staging cannot consume the booted closure, create a boot entry, or assemble a
hybrid. A fixed A/B partition scheme and a versioned image-file store are both
eligible mechanisms if they satisfy the same interruption tests.

Recovery retention remains independently governed and cannot be counted as the
normal fallback slot.

### SYS-051: Confidentiality includes spill paths

Each role maps protected data to declared encryption and unlock boundaries.
Swap, hibernation images, crash dumps, temporary storage, diagnostics, and
workload scratch data cannot silently expose plaintext governed by a stronger
state contract.

Public authenticated release artifacts need not be encrypted. Encryption
scope follows data classification, not the marketing phrase “full disk.”

### SYS-052: Recoverable encrypted volumes

Every encrypted volume defines routine unlock, independent recovery, metadata
or header backup, enrollment, rotation, loss, compromise, restoration, and
destruction behavior. A new method is proven before the old method is removed,
and recovery material is not stored only in the failure domain it recovers.

Acceptance does not choose where the sole maintainer stores recovery material;
that ceremony remains a required S-006 exercise.

### SYS-053: Honest unattended hardware-bound unlock

An unattended unlock claim must bind a hardware-protected secret to the
accepted authenticated or measured boot policy and pass update, rollback,
firmware, reset, and recovery exercises. A plaintext or reversibly obfuscated
key stored with the encrypted data is not hardware-bound unlock.

This makes the router's current lack of an exposed TPM a qualification blocker,
not an implementation inconvenience to bypass. It does not make a TPM a common
boot-integrity prerequisite for roles that do not need unattended confidential
state.

### SYS-054: Recovery begins with mutable state untrusted

An independently authorized recovery environment boots without automatically
unlocking, mounting, executing, or restoring normal mutable state. Each action
is a deliberate, attributable capability transition governed by the applicable
state owner and failure or compromise context.

Ordinary availability recovery may choose a documented preservation path.
Suspected compromise defaults to quarantine and selective action under SYS-035.

### SYS-055: Checkpoints do not change rollback semantics

A filesystem snapshot, reflink copy, block snapshot, or application checkpoint
belongs to a named state owner. It does not extend the deployment identity,
constitute an independent backup, establish application consistency, or permit
whole-state rewind merely because an OS fallback occurred.

An owner-specific checkpoint may satisfy a state migration strategy when its
consistency, interruption, restore, capacity, and retirement behavior are
tested.

### SYS-056: Capacity and layout evolution preserve recovery

Every layout declares capacity for the booted deployment, required candidate
or fallback, retained recovery, update temporaries, state migration, bounded
diagnostics, and an explicit safety reserve. Garbage collection, filesystem
growth, and full-storage behavior preserve those references and fail before
violating the lifecycle contract.

Partition shrinking, movement, filesystem conversion, and disk relocation are
explicit maintenance or provisioning operations with backup and recovery, not
ordinary boot side effects.

## Guardrails from adversarial review

### Do not standardize unmeasured slot sizes

The approximately 16 GB router device is the limiting case. Actual root,
Verity, UKI, recovery, diagnostic, and reserve measurements decide whether it
remains the system disk. A paper estimate does not become a partition ABI.

### Do not let PCR policy collapse authority roles

A key that signs PCR authorization can indirectly permit volume unlock. Its
scope and custody must be evaluated as a data-encryption authority even if the
same toolchain also signs UKIs. Convenience is not sufficient reason to use the
normal release or platform private key for both operations.

### Do not make local recovery the only recovery

Local recovery is convenient for root corruption but shares disk, firmware,
and platform-key failure domains. At least one separately stored recovery path
must be exercised for disk and mainboard replacement.

### Do not make filesystem choice a common semantic dependency

State ownership, compatibility, backup, and rollback contracts must work on
the leading Btrfs design and any ext4 or later role-specific selection.
Snapshots and subvolumes are implementation aids, not required system meaning.

## Strongest rejected alternatives

### Ratify EROFS and Btrfs directly as system requirements

Rejected. EROFS is a promising root-format candidate and Btrfs has useful
workstation features, but neither is an accepted guarantee. Reproducibility,
boot, workload, recovery, and owner-effort evidence must decide them.

### Require one encrypted whole-disk container

Rejected. It encrypts public artifacts unnecessarily, makes recovery dependent
on one key boundary, and prevents independent preservation or destruction of
machine and user/workload state.

### Use snapshots as the deployment mechanism

Rejected. Snapshot identity and selection do not provide the accepted
platform-to-root authentication or application-consistent state contract.

### Allow the router to fetch its unlock key

Rejected for normal boot. It makes the router depend on the network path it is
responsible for restoring and moves powered-off confidentiality to an online
service without solving local boot substitution.

## Required implementation evidence

Acceptance would establish policy only. DES-0006 still requires:

1. symmetric EROFS/ext4 root artifacts and literal UKI/root/Verity binding;
2. power-loss and substitution testing across all slot resources;
3. exact capacity measurement and router R-A/R-B selection;
4. workstation and router Btrfs/ext4 workload and recovery comparison;
5. concrete local and separately stored recovery packaging;
6. TPM2 signed-policy, recovery, and authority-custody exercises;
7. an `/etc` persistent-writer and exception inventory; and
8. backup, header restore, disk replacement, full-storage, plaintext-spill,
   and hostile-state exercises.

## Decision

Accepted by Jason Tarasovic on 2026-08-10. SYS-048 through SYS-056 are
normative with the interpretations above. This accepts the storage-ownership,
authenticated-root, complete-retention, encryption, recovery, checkpoint, and
capacity boundaries without selecting final filesystems, partition sizes,
recovery packaging, TPM policy, or the router's target disk.

DES-0006 remains in review until the required implementation evidence resolves
its bounded mechanism choices. In particular, acceptance does not select
XBOOTLDR, make Btrfs snapshots part of OS rollback, or elevate EROFS from a
root-format candidate.
