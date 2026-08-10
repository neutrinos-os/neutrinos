---
id: EX-0014
title: Unix identity mapping, rootless bind, and restore exercise
status: proposed
date: 2026-08-10
exercise_type: tabletop and implementation spike
evidence_class: analysis-first
related_designs: [DES-0012]
---

# Unix identity mapping, rootless bind, and restore exercise

## Purpose and safety boundary

This exercise determines whether proposed stable human/subordinate allocations,
rootless namespace mappings, idmapped mounts, and the classic-versus-homed
choice preserve ownership in real workflows.

All mutation occurs first on disposable VMs, restored scratch filesystems, or
reflinked test data. Do not recursively change ownership on the current
workstation, router, misc server, or their production backups during this
exercise.

## Initial inventory

Record for every reference host and retained state source:

- complete NSS/userdb user and group views;
- `/etc/passwd`, `/etc/group`, subuid/subgid delegation source and effective
  ranges;
- systemd special ranges and package-baseline account allocations;
- every UID/GID owning inodes in user/workload and machine-state regions;
- ACL named/numeric identities and security/capability xattrs;
- rootless graph stores, named volumes, source binds, snapshots, archives, and
  backups;
- running namespace `uid_map`/`gid_map` and idmapped mounts;
- service users with durable state or external protocol meaning; and
- collisions with 5001, 60503, 165536…231071, and candidate alternatives.

The checked-in starting hypothesis is:

| Subject | Workstation | Router/misc desired configuration |
| --- | --- | --- |
| `jason` UID/GID | 60503:60503 | 5001:5001 |
| `jason` subuid/subgid | 165536:65536 | Undeclared |

The workstation's 60503 allocation is confirmed retained state from its former
systemd-homed account. The current classic account is the result of moving away
from homed roughly five years ago because rootless Docker and Podman behavior
blocked the user's workflow.

Fresh live-host observations may update evidence but not silently rewrite this
historical starting point.

## Representative state fixture

Create a synthetic restored tree containing:

- ordinary source files and Git worktrees owned by the human UID;
- files created as container root and as several container service UIDs;
- a rootless image/writable store and named volumes;
- hardlinks, symlinks, sparse files, POSIX ACLs, capabilities, and xattrs;
- Btrfs subvolumes, reflinks, snapshots, send/receive output, and a tar archive;
- a systemd fixed-user state directory and DynamicUser state directory;
- a deliberately colliding unrelated user and subordinate range; and
- canary files inaccessible to the intended user/container.

No production credentials or source repositories are required.

## Mapping fixtures

Exercise:

1. classic `jason` at 60503 with sub-ID 165536:65536;
2. classic `jason` at 5001 with the same sub-ID;
3. classic `jason` with a different sub-ID;
4. systemd-homed with preferred 60503 and with a forced collision;
5. `DynamicUser=` and fixed `sysusers.d` services;
6. Podman rootless `keep-id`, `auto`, `nomap`, and explicit maps;
7. Docker rootless default mapping;
8. idmapped and ordinary bind mounts; and
9. a systemd-nspawn automatic container allocation for collision testing.

## Scenario matrix

### E-001: Source-tree bind and created files

For every rootless mode, mount a host-owned source tree read/write, run as
container root and a non-root application user, create/rename/delete files, run
Git operations and a representative build, then inspect from host and container.

Pass if intended access works, output ownership is declared and useful, no
unrelated files are rewritten, and a failed mapping is diagnosed before a broad
permission workaround.

### E-002: Concurrent Podman namespace modes

Run `keep-id`, `auto`, `nomap`, and explicit-map containers concurrently in
every supported combination.

Pass if supported combinations match documented maps, conflicts fail clearly,
and per-workload policy does not rely on an unavailable range.

### E-003: Idmapped volume and fallback

Present the same Btrfs and ext4 test trees through ordinary and idmapped mounts.
Repeat with unsupported/invalid maps and any required overlay path.

Pass if backing ownership never changes, the visible map is inspectable, access
is scoped correctly, and fallback is explicit map/copy/failure rather than
recursive chown.

### E-004: Rootless graph store versus source bind

Place engine storage inside home, in a separate workload subvolume/path, and
under a homed-managed home. Keep source binds independent.

Pass if conclusions distinguish image/writable-store failures from source-bind
and named-volume behavior and backup policy names each state class.

### E-005: Classic UID migration

On a scratch restore, migrate 60503 -> 5001 with a declared mapping. Interrupt
after discovery, checkpoint, each ownership class, account switch, verification,
and retirement boundary.

Pass if retry is safe, no inode/ACL/xattr is silently missed within declared
coverage, container subordinate ownership is not rewritten as human ownership,
and the original remains recoverable until verification.

### E-006: Subordinate-range migration

Move from 165536:65536 to a non-colliding candidate range with rootless state
present, then restore old snapshots and backups.

Pass if every raw dependency is migrated or rejected, old ranges remain
tombstoned while retained data refers to them, and no new owner gains access.

### E-007: Cross-host raw and logical restore

Restore source, named-volume data, raw engine store, image export, and
application-level backup onto hosts with same/different user and subordinate
numbers, both with and without an idmapped view.

Pass if each portability claim is precise, collisions fail safely, and a
logical export does not inherit raw-store guarantees or vice versa.

### E-008: systemd-homed workflow

Test subvolume and applicable encrypted storage modes with Podman and Docker
stores, source binds, idmapped volumes, multiple sessions, lingering user
services, logout, suspend, SSH, console, backup, UID collision, disk replacement,
and recovery.

Pass only if container and source workflows remain reliable, deactivation does
not strand intended services/state, collision behavior is explicit, and owner
effort compares favorably with the classic baseline.

### E-009: DynamicUser state and recovery

Create state through a `DynamicUser=` service using systemd-managed directories,
stop it, roll the OS backward, restore raw state offline, and inspect/recover it
without the original activation.

Pass if identity and ownership remain understandable and usable under the
declared recovery path; otherwise the service requires a fixed registered ID.

### E-010: Collision and reuse

Introduce conflicts for human UID, primary/supplementary GID, service UID, and
all or part of a subordinate range. Attempt allocation and then range reuse
while old backups/snapshots remain.

Pass if collision blocks activation/enrollment before exposure and reuse waits
for explicit evidence that dependent state is gone or intentionally migrated.

### E-011: OS lifecycle independence

Reinstall and roll between retained deployments whose account/runtime packages
differ. Restore machine, user, and workload state separately.

Pass if human/subordinate ownership remains current independently of OS
selection, package service users resolve exactly, and fallback does not silently
change maps.

### E-012: Hostile rootless workload

Attempt access to sibling user files, supplementary-group-only files, service
sockets, devices, systemd credentials, and another workload's named volume.

Pass if the map grants only intended filesystem identities and status does not
claim that rootless alone qualifies every attachment.

## Measurements

| Measure | Classic stable | Classic + idmap | systemd-homed | Per-host dynamic |
| --- | --- | --- | --- | --- |
| Source-bind correctness | TBD | TBD | TBD | TBD |
| Rootless graph/volume correctness | TBD | TBD | TBD | TBD |
| Session/linger behavior | TBD | TBD | TBD | TBD |
| Raw restore steps/time | TBD | TBD | TBD | TBD |
| Logical restore steps/time | TBD | TBD | TBD | TBD |
| UID/sub-ID migration time | TBD | TBD | TBD | TBD |
| Collision handling | TBD | TBD | TBD | TBD |
| Recovery without normal user manager | TBD | TBD | TBD | TBD |
| Owner maintenance/debug cost | TBD | TBD | TBD | TBD |

## Acceptance output

- authoritative identity-allocation example and reserved-range policy;
- accepted or rejected canonical UID/GID and subordinate-range candidates;
- workload mapping contracts for representative development containers;
- fixed-versus-dynamic service-identity rule;
- idmapped-mount support matrix;
- classic-versus-homed evidence and decision input;
- ownership-aware backup/restore and migration runbook;
- current-host remediation plan with no production mutation; and
- proposed ADR only after literal evidence supports mechanism selection.
