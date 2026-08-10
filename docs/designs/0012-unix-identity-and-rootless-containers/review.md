---
design: DES-0012
reviewer: Codex adversarial pass
perspective: security, operations, failure, maintainability, alternatives
date: 2026-08-10
status: open
---

# Unix identity and rootless-container ownership review

## Summary judgment

The proposal makes the right object durable: an allocation and mapping contract,
not every runtime-visible UID. It also resists two tempting shortcuts—assuming
homed has become transparent because idmapped mounts exist, and solving mapping
friction by running containers as root.

The strongest challenge is that “same UID and sub-ID everywhere” can be cargo
cult. Stable host numbers help raw state movement, but idmapped mounts, logical
exports, and workload-local ownership can remove that need. The policy should
accept explicit stability where durable state depends on it without requiring
one global numeric namespace for every transient service and container.

## Challenges

### C-001: UID 5001 is chosen from convenience, not a fleet allocation policy

- Severity: high
- Claim: an existing number on two hosts may collide with future directory
  services, shared storage, restored images, or another administrator.
- Failure or cost if true: later migration repeats the same ownership rewrite.
- Required response or experiment: inventory all managed and reference images,
  reserved ranges, shared filesystems, and likely external identity domains;
  record why 5001 is supportable before accepting it.
- Author response: 5001 is leading only; requirements do not fix the number.
- Disposition: open pending EX-0014.

### C-002: stable subordinate ranges are unnecessary coupling

- Severity: high
- Claim: container images and application data can be exported logically, while
  idmapped mounts can adapt raw trees without matching host numbers.
- Failure or cost if true: scarce ranges and cross-runtime collisions are
  reserved forever for no benefit.
- Required response or experiment: test logical and raw backup/restore plus
  cross-host moves with stable, changed, and idmapped allocations; require
  stability only for demonstrated raw dependencies.
- Author response: subordinate stability is scoped to hosts/state that need it.
- Disposition: mitigated; exact scope open.

### C-003: homed has already solved this with idmapped home mounts

- Severity: critical
- Claim: rejecting homed repeats stale experience and ignores current systemd
  container UID ranges and idmapped mounts.
- Failure or cost if true: NeutrinOS carries a weaker custom account/storage
  model unnecessarily.
- Required response or experiment: run literal homed plus current Podman/Docker,
  source binds, graph storage, user services, logout, suspend, collision,
  backup, and recovery rather than relying on the old report.
- Author response: homed is the mandatory systemd challenger, not rejected.
- Disposition: open pending EX-0014.

### C-004: moving the graph root outside home avoids the real homed problem

- Severity: high
- Claim: subordinate-owned engine data can live under a dedicated workload path
  while source trees contain only the user's UID and work with `keep-id`.
- Failure or cost if true: the design overstates the remaining blocker.
- Required response or experiment: separate graph-root, named-volume, and source-
  bind tests; do not infer failure of one from another.
- Author response: these state classes are explicitly separated.
- Disposition: resolved in design; behavior test open.

### C-005: `keep-id` is not a harmless default

- Severity: high
- Claim: Podman currently consumes all of the user's subuids/subgids for
  `keep-id`, preventing simultaneous `auto` or `nomap` allocations.
- Failure or cost if true: one development container blocks other namespace
  policies or causes runtime-specific behavior.
- Required response or experiment: run the concurrency matrix and define
  mapping per workload.
- Author response: `keep-id` is a candidate, not fleet default.
- Disposition: mitigated; test required.

### C-006: idmapped mounts are being treated as universal

- Severity: critical
- Claim: filesystem, kernel, runtime, overlay, network filesystem, and bind-mount
  support differ, and stacked mappings can be difficult to reason about.
- Failure or cost if true: workloads fail or see surprising ownership after a
  kernel/runtime change.
- Required response or experiment: qualify the literal Btrfs/ext4, source bind,
  volume, overlay, nested, and backup cases; retain explicit failure fallback.
- Author response: idmapping is preferred only where qualified.
- Disposition: open pending EX-0014.

### C-007: DynamicUser can orphan restored state

- Severity: critical
- Claim: activation-time IDs and systemd directory remapping may not match raw
  restores performed in recovery or by other tools.
- Failure or cost if true: services cannot read state or an old allocation is
  reassigned unsafely.
- Required response or experiment: restore state while the service is absent,
  inspect backing ownership and idmapped views, and test release rollback plus
  recovery tools.
- Author response: fixed IDs remain required for unmediated durable semantics.
- Disposition: open.

### C-008: a blind migration inventory will miss numeric ownership

- Severity: critical
- Claim: ACLs, xattrs, sparse snapshots, hardlinks, archives, container layers,
  databases, NFS identities, and disconnected backups can retain old IDs.
- Failure or cost if true: 60503 or an old sub-ID is later reassigned and gains
  access to forgotten state.
- Required response or experiment: define scan coverage and keep old allocations
  tombstoned until every retained dependency is migrated or expired.
- Author response: reuse is evidence-gated, not immediate after visible chown.
- Disposition: open pending migration exercise.

### C-009: matching UID across machines overstates identity

- Severity: critical
- Claim: UID 5001 on an unmanaged or compromised machine is not Jason and must
  not authorize network access or secret delivery.
- Failure or cost if true: numeric coincidence becomes cross-host authentication.
- Required response or experiment: trace NFS, SSH, backup, and secret paths and
  require cryptographic/enrollment identity separately.
- Author response: numeric stability is explicitly a filesystem choice only.
- Disposition: resolved in design.

### C-010: rootless does not mean harmless

- Severity: critical
- Claim: user namespaces reduce host privilege but bind mounts, devices,
  sockets, kernel attack surface, supplementary groups, and user-owned secrets
  can still make a container highly privileged relative to the user.
- Failure or cost if true: status calls a dangerous workload “safe” because it
  is rootless.
- Required response or experiment: inventory attachments and test hostile
  container access separately from UID mapping.
- Author response: rootless is a privilege direction, not a qualification
  claim.
- Disposition: accepted limitation; broader workload design remains.

### C-011: fixed service IDs pollute a cross-distribution package universe

- Severity: high
- Claim: Fedora, Arch, and project-built packages may assign different service
  numbers and file ownership.
- Failure or cost if true: package baseline changes collide or require private
  downstream UID patches.
- Required response or experiment: inventory the representative closures,
  prefer dynamic identities, and register only service IDs with demonstrated
  state/protocol need.
- Author response: package allocation is an input, not final authority.
- Disposition: open with DES-0007 evidence.

### C-012: the migration risk outweighs cosmetic consistency

- Severity: critical
- Claim: changing a working 1 TB workstation tree from 60503 to 5001 may cause
  more damage than leaving per-host UIDs and using mapping at transfer time.
- Failure or cost if true: data loss or long downtime before NeutrinOS boots.
- Required response or experiment: perform the full migration on restored
  scratch copies, measure time/diffs, and compare explicit transfer mapping.
- Author response: no physical change is authorized by this design.
- Disposition: open pending EX-0014.

## Acceptance blockers

Before accepting concrete numbers or mechanisms, the project needs:

1. a collision and durable-owner inventory for all current hosts and retained
   backups;
2. literal source-bind and created-file results for current rootless runtimes;
3. raw and logical restore results with same and different mappings;
4. a systemd-homed challenger run including session lifecycle;
5. fixed and DynamicUser service restore results;
6. an interruption-safe 60503/5001 migration rehearsal; and
7. measured operator cost.

## Recommendation

The owner accepted the substrate-neutral requirements for explicit ownership
and mapping. Keep UID 5001, sub-ID 165536:65536, classic accounts, Podman
mapping modes, idmapped mounts, and homed as proposed mechanisms until EX-0014.
