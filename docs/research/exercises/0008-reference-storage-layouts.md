---
id: EX-0008
status: proposed
last_updated: 2026-08-09
decision_gates: [S-004, L-003, L-004, L-005]
---

# Reference storage layout tabletop

## Purpose

Apply the storage proposal to the reference VM, `desktop-jason`, and `router`
without pretending that estimated partition sizes or untested TPM behavior are
implementation evidence.

The diagrams show lifecycle regions, not final partition numbers. Root A/B are
storage slots, not deployment identities.

## Common logical layout

```text
GPT disk
├── ESP
│   ├── systemd-boot and firmware fallback executable
│   ├── signed normal UKIs with boot-attempt metadata
│   └── independently authorized local recovery UKI, if retained locally
├── optional XBOOTLDR, only if the ESP cannot meet the measured lifecycle
│   └── versioned normal and recovery boot artifacts moved from the ESP
├── root slot A ─────── matching Verity slot A
├── root slot B ─────── matching Verity slot B
├── optional recovery root ─ matching recovery Verity data
├── encrypted machine-state volume
├── encrypted user/workload volume, when custody requires separation
├── encrypted or ephemeral-key swap, when enabled
└── declared expansion and recovery reserve
```

The signed UKI carries or authenticates the root hash that identifies its
matching root and Verity data. Slot letters, partition order, labels, and
version strings locate storage but never replace that binding.

## Capacity formula

Final byte counts are build outputs. A layout is invalid unless it satisfies:

- boot artifact filesystem capacity for every retained normal UKI, local recovery boot
  artifact, boot-attempt rename, update temporary, and explicit safety margin;
- two root slots each large enough for the maximum supported root artifact
  over the declared layout lifetime;
- two Verity slots derived from that maximum root size and selected block/hash
  parameters;
- recovery capacity independent of the two normal root slots when local
  recovery is promised;
- minimum state and diagnostic reserve for the role under failed-update and
  full-storage tests; and
- unused or reallocatable space for one declared layout evolution.

The layout version records these assumptions. An image that happens to fit
today but cannot stage one candidate beside the booted deployment fails the
lifecycle requirement.

## Reference VM

The VM uses one blank GPT disk with an emulated UEFI implementation and vTPM
when testing hardware-bound unlock. It first exercises an ESP-only boot artifact
store. A second case adds XBOOTLDR only if measured capacity or lifecycle
behavior shows that it is needed. Neither case uses convenient host-shared
folders for lifecycle-critical artifacts.

The VM matrix covers:

- EROFS+dm-verity and ext4+dm-verity root artifacts;
- two normal root/Verity slots and versioned UKIs;
- an encrypted Btrfs machine-state volume plus an ext4 challenger;
- recovery with state initially locked;
- update interruption before and after every finalization boundary; and
- TPM clear, PCR mismatch, recovery key, and LUKS-header restore cases.

## `desktop-jason`

Observed storage is approximately 512 GB for the current system disk and 1 TB
for the current `/home` disk. The target paper mapping is:

| Physical device | Lifecycle region | Notes |
| --- | --- | --- |
| System NVMe | ESP, optional XBOOTLDR if justified, normal root/Verity slots, optional local recovery root, encrypted machine state, swap, reserve | Existing data requires migration; no in-place repartition promise |
| Data NVMe | Encrypted user/workload volume | User home, rootless container state, VM disks, and other workload namespaces remain logically distinct state contracts even if they share one unlock boundary |

Two encrypted volumes are proposed because machine identity/reprovisioning and
user/workload backup or disk replacement have different lifecycles. This does
not require one volume per application.

The first migration rehearsal must restore onto scratch disks or VM-backed
copies, verify owner-consistent backups, enroll routine and recovery unlock
methods, boot both normal slots, and exercise recovery before the current disks
are changed.

The mutable-filesystem comparison uses actual representative data:

- source repositories with large and small files;
- rootless container image and writable stores;
- VM images under representative write load;
- backup snapshot/consistency behavior;
- full-filesystem and low-free-space recovery; and
- restore onto a blank replacement volume.

Btrfs is the leading candidate because reflinks, subvolumes, checksums,
send/receive, quotas, and compression directly address the stated container,
VM, and mutable-state goals. ext4 remains the conservative challenger. Btrfs
must still pass scrub, low-space, quota, snapshot-retention, send/receive,
VM-image, and recovery tests; stated preference does not waive operations.

## `router`

The observed router has an approximately 16 GB system disk and approximately
1 TB secondary disk. The 16 GB device must not be assumed sufficient for two
normal roots, Verity data, local recovery, boot artifacts, state, failed-update
diagnostics, and reserve until actual artifacts are measured.

Two layouts enter the spike:

### R-A: retain the small system disk

- boot and normal root/Verity slots reside on the 16 GB device;
- machine/service state resides on an encrypted volume on the secondary disk;
- recovery is a compact local artifact if it fits, otherwise independently
  staged IPMI virtual media or owner-controlled removable media; and
- loss of the secondary disk boots recovery and reports state unavailable, but
  cannot provide the production routing service.

### R-B: make the larger disk primary

- boot, both normal deployments, local recovery, encrypted router state, and
  reserve reside on the larger disk;
- the small disk is retired, used only for explicitly declared recovery, or
  erased; and
- there is no cross-disk dependency in normal selection.

R-B is simpler if the firmware and chassis boot reliably from the larger disk.
R-A preserves the current physical split but introduces a normal two-disk
dependency. Artifact sizes, firmware boot behavior, disk health, and recovery
testing decide between them.

The production encryption profile remains gated on installation and
qualification of the documented compatible TPM2 module or another accepted
hardware-bound facility. Before that, the router is a development target and
must not store production long-lived credentials under an unearned
confidentiality claim.

## Recovery transitions

| Situation | Normal root | Mutable state | Required action |
| --- | --- | --- | --- |
| Candidate boot fails before state write | Select eligible previous root | Preserve and mount normally after compatibility gate | Record failure; do not enter recovery automatically |
| Candidate state health fails | Previous root only if state contract permits | Preserve current state | Fallback or stop according to compatibility evidence |
| Normal roots corrupt | Boot independently authorized recovery | Keep locked initially | Inspect deployment and state metadata before unlock |
| TPM/PCR unlock fails | Recovery boot or normal boot with deliberate recovery input | Unlock only with independent recovery authority | Record exceptional unlock and assess credential rotation |
| Suspected compromise | Recovery only | Do not auto-mount; treat as hostile | Quarantine, selective restore, re-enroll, or destroy by owner |
| LUKS header damaged | Recovery environment | Work on a copy; use external header backup if valid | Never overwrite the sole remaining source during diagnosis |
| Disk replacement | Known recovery/provisioning artifact | Restore only named state contracts | Recreate layout, restore, verify, and re-enroll |

## Required outputs from the eventual spike

- literal `repart.d`, `sysupdate.d`, UKI, root-hash, and boot-entry mappings;
- exact artifact and partition sizes plus declared growth horizon;
- power-loss results at every transition;
- TPM event-log, PCR-policy, signed-policy, and recovery evidence;
- filesystem workload measurements and operating runbooks;
- backup, restore, header-backup, key-rotation, and disk-replacement exercises;
- router R-A versus R-B decision; and
- an inventory of every persistent mount and its state-contract owners.
