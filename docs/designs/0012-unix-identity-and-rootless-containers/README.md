---
id: DES-0012
title: Unix identity and rootless-container ownership
status: in-review
owners: [Jason Tarasovic]
reviewers: [Codex adversarial pass]
created: 2026-08-10
last_updated: 2026-08-10
depends_on: [DES-0002, DES-0003, DES-0005, DES-0006, DES-0011]
decision_backlog: [W-001]
related_adrs: []
---

# Unix identity and rootless-container ownership

## Problem

Unix files store numeric UID and GID ownership, while people and services are
usually discussed by name. Rootless containers add subordinate UID/GID ranges
and user-namespace mappings; idmapped mounts can present another view without
rewriting the underlying ownership. Backups, shared source trees, container
stores, user services, reinstall, and movement between hosts join these layers
whether or not NeutrinOS documents them.

The current fleet already has a real divergence. `desktop-jason` uses the
classic account `jason` at UID/GID 60503 with subordinate range
165536:65536. Jason confirmed that this machine originally used systemd-homed
roughly five years ago and retained the homed-era numeric identity when he
switched back to a classic account because rootless Docker and Podman problems
blocked the workflow. The checked-in `nixconfig` common configuration declares
the same name at UID/GID 5001 for `router` and `misc`.

The project must decide which identifiers are durable, who allocates them, how
container mappings relate to them, and how ownership is migrated. Otherwise a
reinstall can turn Jason's files into another user's files, a restored rootless
store can expose subordinate-owned data to the wrong account, or a convenient
recursive `chown` can corrupt container and workload state.

## Goals

- Define authoritative namespaces for human, system-service, workload-internal,
  subordinate, and transient container identities.
- Keep durable file ownership stable and reconstructible across reinstall,
  rollback, backup, restore, and selected cross-host movement.
- Make rootless container mappings explicit per workload rather than an engine
  default with hidden ownership consequences.
- Preserve ordinary bind-mounted source-tree workflows without recursive
  ownership rewriting.
- Prefer systemd-native user, service, directory, and identity primitives where
  they fit.
- Decide what evidence systemd-homed must satisfy before reconsideration.
- Produce a safe migration path from the fleet's current 60503/5001 divergence.

## Non-goals

- Select Podman, Docker, nspawn, Toolbx, Distrobox, or a Kubernetes runtime.
- Design container image, networking, secret, or update policy beyond identity
  and file ownership.
- Make a human UID a NeutrinOS enrollment identity or security principal across
  trust domains.
- Require the same numeric service UID on unrelated hosts when no durable or
  externally interpreted state depends on it.
- Promise transparent sharing of arbitrary rootless engine internals between
  different engines or versions.
- Adopt systemd-homed because it belongs to the preferred ecosystem.
- Choose final production UID/sub-ID numbers before collision and migration
  exercises.

## Accepted constraints

- SYS-019 through SYS-025 require owner-aware state, migration, backup,
  recovery, and identity lifecycles independent of OS rollback.
- SYS-035 treats restored user and workload state as potentially hostile after
  compromise.
- SYS-042 through SYS-047 make checked-in fleet intent authoritative and keep
  runtime observation from assigning policy.
- SYS-048, SYS-051, SYS-052, and SYS-055 keep physical storage, encryption,
  snapshots, and owner-specific state semantics distinct.
- SYS-098 through SYS-108 separate machine, user, workload, and service
  credentials and their consumers.
- A-006 explicitly requires bind-mount, backup/restore, multi-machine, and user-
  namespace evidence for stable UID/subordinate-ID policy.
- The original design session and confirmed workstation history record
  systemd-homed plus rootless Docker/Podman behavior as a prior practical
  blocker, not an abstract concern.

## Decision drivers

1. Source trees under `/home/jason` are routinely bind-mounted into development
   containers and must remain pleasant to edit on the host.
2. Rootless container images, writable layers, volumes, and source trees have
   different ownership and backup semantics even when one engine stores them
   under `$HOME`.
3. Numeric ownership survives after NSS data, container metadata, or a machine
   record is unavailable.
4. Fixed IDs simplify selected cross-host restore but create collision and
   allocation obligations.
5. Dynamic IDs reduce global allocation but are unsafe for unmediated durable
   files, shared protocols, or raw state restore.
6. Idmapped mounts can avoid recursive `chown`, but support varies by filesystem,
   kernel, runtime, and mount shape.
7. A single 65,536-ID subordinate range is the established compatibility
   baseline for full 16-bit container identity, but Podman namespace modes do
   not consume ranges interchangeably.
8. `router` and `misc` already declare UID/GID 5001, while changing the
   workstation may touch a large user/workload filesystem.

## Proposed model

### Identity classes

| Class | Authority | Durability | Numeric rule |
| --- | --- | --- | --- |
| Fleet human identity | Fleet inventory plus user authority | Survives machine and deployment replacement | Stable canonical UID/GID on managed hosts that exchange or restore its files |
| Host system-service identity | Release-owned native configuration | As long as service/state contract requires | Dynamic where state is safely mediated; fixed and registered when durable numeric ownership or protocol requires it |
| Machine-local administrator identity | Explicit administrator state | Until removed/reset | Cannot collide with fleet, system, dynamic, or subordinate allocations |
| Workload-internal identity | Exact workload artifact/configuration | Workload lifecycle | Namespace-local; does not automatically claim the same host numeric ID |
| Subordinate-ID allocation | Fleet/machine identity-allocation policy | As long as raw namespace-owned state is retained | Explicit non-overlapping UID/GID ranges bound to one owner and purpose |
| Transient namespace mapping | Container/namespace runtime under declared policy | One namespace or workload realization | May vary if no persistent external ownership depends on it |

Names, numeric IDs, user UUIDs, NeutrinOS machine identities, workload
identities, and container-internal users remain distinct. Matching numbers do
not merge authorities.

### Authoritative allocation record

Fleet intent contains an identity-allocation record, not a target-side allocator
script. It declares:

- stable identity and human-readable name;
- identity class and lifecycle owner;
- exact UID, primary GID, supplementary groups, or allowed allocation class;
- subordinate UID/GID ranges and purpose;
- hosts, roles, state contracts, and workloads on which the allocation applies;
- collision domains and reserved ranges;
- persistence, portability, backup, restore, and deletion semantics;
- source of native `sysusers.d`, user/group, subuid/subgid, or userdb output;
- migration history and superseded allocations; and
- evidence needed before reuse.

The resolved allocation and native outputs are identity-bound configuration.
The machine reports the effective NSS/userdb view and namespace mappings rather
than allocating a different durable number silently.

### Human identities

For a managed human identity whose state may be restored or shared among fleet
machines, NeutrinOS assigns one canonical UID and matching primary GID. A local
collision fails enrollment/configuration or requires an explicit migration; it
does not silently rebind the person or recursively rewrite their files during
ordinary login.

UID/GID 5001 is the leading candidate for `jason` because it is already declared
on two managed hosts and lies in the ordinary human-user range rather than a
systemd special range. UID/GID 60503 remains the observed workstation source
allocation, not the target merely because it exists. Exact selection remains
open until EX-0014 inventories collisions and rehearses the ownership migration.

The stable numeric allocation is a filesystem interoperability choice, not an
authentication claim. The user record also needs a stable non-numeric identity
for attribution and future directory/userdb integration. Its concrete UUID or
record format remains open.

### System and service identities

Release-owned service accounts are declared through native `sysusers.d` and
unit configuration. Prefer `DynamicUser=` plus systemd-managed runtime, state,
cache, log, and configuration directories when:

- no external protocol or durable unmanaged file requires a fixed numeric ID;
- systemd can mediate every persistent directory and restore its ownership
  safely; and
- backup/restore does not interpret the dynamic number as durable identity.

Use a fixed registered service UID/GID when persistent files, external storage,
shared access, container bind mounts, network protocols, or recovery tools must
interpret ownership without the original service activation. The exact number
and collision analysis become deployment-bound evidence.

Package defaults do not gain permanent allocation authority merely because a
distribution package creates a user. The composed image must expose the
resolved identity and ownership result.

### Subordinate UID/GID allocations

Subordinate IDs are authorization to construct namespace mappings, not human or
service accounts. Each allocation binds an owner, matching UID/GID ranges,
purpose, applicable hosts/engines, size, collision proof, state dependencies,
and retirement rule.

The initial candidate for Jason is the workstation's existing matching range
`165536:65536`, subject to collision inventory on every applicable target. It
is outside systemd's currently documented special container range and provides
the normal full 16-bit namespace. Reusing the same range on another host is
permitted only because allocation collisions are host-local; moving raw
subordinate-owned state between those hosts then has predictable numbers.

This range is not accepted merely because it exists. If the selected runtime,
homed model, nested-container requirements, or systemd namespace allocation
cannot safely coexist with it, EX-0014 must compare a deliberate replacement.
Old ranges remain reserved until every dependent inode, archive, snapshot,
backup, and container store is migrated or destroyed.

### Rootless workload mapping contract

Each supported rootless workload declares:

- runtime and version/policy identity;
- container-visible user/group and expected host subject;
- namespace mode and exact UID/GID map or allocation policy;
- subordinate ranges consumed and whether they are exclusive while running;
- source-tree, named-volume, image-store, and writable-layer mount semantics;
- ownership of newly created host-visible files;
- idmapped-mount use and fallback;
- supplementary-group, device, socket, and network access assumptions;
- backup/export/restore boundary;
- behavior after UID/sub-ID change; and
- inspection commands and failure status.

`keep-id` is a workload option, not a fleet-wide default. It is a strong
candidate for development containers that edit a bind-mounted source tree, but
current Podman semantics consume the user's subordinate ranges and conflict
with simultaneous `auto` or `nomap` containers. The exercise must test the
actual concurrency and ownership result.

Rootless remains the default privilege direction for user-owned development
containers. A rootful or privileged attachment is an explicit administrator or
release-owned workload decision with separate status and qualification.

### Bind mounts and idmapped mounts

Ordinary source trees remain owned by the host user. A container mapping must
make the intended container process operate as that user for read/write work,
or use an explicit idmapped mount. The runtime must not recursively `chown` a
source tree as a convenience.

Idmapped mounts are preferred when the filesystem and runtime can present the
same tree safely under the required mapping without changing on-disk ownership.
They are a view, not a new owner or migration. The contract records the backing
ownership and mapping, and tests access from the host, intended namespace,
sibling containers, backup, and recovery.

When idmapped mounts are unsupported, the fallback is a compatible explicit
namespace map, a workload-owned copy/volume, or failure. Recursive `chown` is
not the automatic fallback because interruption and shared-state ambiguity can
corrupt unrelated owners.

### Container stores and workload state

Moving a rootless engine's graph root outside `$HOME` may avoid homed and network
filesystem limitations, but it does not solve source-tree bind mounts. Treat:

- images and reconstructible caches as workload cache with bounded eviction;
- writable layers as workload state unless disposable;
- named volumes as individually declared workload state;
- source trees as user/project state; and
- runtime namespace and lock data as engine-owned operational state.

They may share the workstation's user/workload Btrfs volume while retaining
separate state contracts, quotas, backup policies, and identity dependencies.
Backing up the engine's raw store is not automatically a portable container
backup. Logical image export, workload definition, application-consistent data,
and raw storage restore are separate claims.

### systemd-homed disposition

Systemd-homed remains an evidence-gated challenger, not the default. Its user
record, portable home, storage, authentication, resource-control, and idmapped
mount work are relevant systemd prior art. Current upstream behavior also
permits a preferred UID to change on another host after collision, and its
default home idmap maps selected UID ranges rather than arbitrary subordinate
ownership.

The leading baseline is therefore a classic, fixed-UID account on the accepted
encrypted Btrfs user/workload volume. Homed can replace it only after literal
tests show all of the following are boring:

1. rootless Podman and Docker image/writable storage;
2. bind-mounted source trees with expected created-file ownership;
3. `keep-id`, `auto`, explicit maps, and idmapped volumes;
4. current and candidate subordinate ranges;
5. user services, lingering container engines, multiple sessions, logout,
   suspend, and home deactivation;
6. backup, restore, disk replacement, UID collision, and interrupted remap;
7. console, SSH, recovery, and authentication-factor behavior;
8. the whole-volume encryption/custody model from DES-0006; and
9. owner effort and failure diagnosis compared with the classic baseline.

This is not an exception to ADR-0001: systemd-homed receives priority as the
challenger, but the user's prior blocker and the simpler accepted state model
are strong justification for retaining classic accounts until it passes.

### Backup, restore, and migration

Every backup of numeric-owned state retains or references the applicable
identity-allocation manifest. Restore verifies:

- names and stable non-numeric identities;
- source and target numeric maps;
- all owners present in the payload, ACLs, and relevant xattrs;
- subordinate ranges and container/runtime dependencies;
- target collisions and reserved ranges;
- whether restore preserves numbers, applies an explicit idmapped view,
  performs a recorded ownership migration, or rejects the payload; and
- current credential, enrollment, compromise, and state-schema policy.

Changing a durable UID/GID or subordinate allocation is a state migration. It
requires a quiesced owner/workload, verified backup, exact inode/ACL/xattr and
runtime-store inventory, collision-free target, checkpoint, interruption-safe
progress, post-change verification, and a return or recovery path. A blind
`chown -R` over `/home`, `/var`, or a shared volume is prohibited.

For the current fleet, EX-0014 must compare at least:

1. migrate workstation 60503 -> canonical 5001 and retain 165536:65536;
2. retain workstation 60503 and migrate the other managed hosts;
3. select a new ordinary-range UID everywhere; and
4. adopt homed with an explicit portable/local binding model.

The first is the leading path, but no physical ownership change occurs in the
documentation phase.

### Inspection and status

For any path or running workload, status must answer:

- Which user/group or namespace identity owns it semantically?
- What numeric UID/GID is stored on disk and what name resolves now?
- Which allocation record and state contract authorize that number?
- Is an idmapped mount or user namespace changing the visible ownership?
- Which subordinate ranges and exact maps does the workload consume?
- What owns the raw store, bind source, named volume, and created output?
- Would backup/restore or movement to another host preserve meaning?
- Is the current mapping exact, migrated, collided, stale, unsupported, or
  locally modified?

Native `getent`, `userdbctl`, `/proc/*/{uid,gid}_map`, mount information,
container-runtime inspection, filesystem ownership, and ACL diagnostics remain
available. A project status view does not replace them.

## Candidate mechanism disposition

| Mechanism | Proposed disposition | Reason |
| --- | --- | --- |
| Classic fixed human account | Leading initial baseline | Predictable ownership and best fit with current container-heavy workflow |
| `sysusers.d` fixed service identity | Leading when durable numeric ownership is required | Native, build-time reviewable, and reconstructible |
| `DynamicUser=` plus managed directories | Preferred for eligible services | Avoids permanent allocation when systemd mediates state safely |
| Explicit `/etc/subuid` and `/etc/subgid` output | Leading initial subordinate delegation | Supported by current rootless engines; must derive from one allocation record |
| Podman `keep-id` | Development-workload candidate | Good source-tree semantics, but consumes ranges and constrains concurrent modes |
| Idmapped bind/volume mounts | Preferred mapping primitive where supported | Changes the view without recursive ownership mutation |
| systemd-homed | Mandatory challenger, not default | Valuable systemd integration; prior rootless/session/restore blockers require literal proof |
| Dynamic cross-host human UID | Rejected for initial portable/restored state | Silent collision remap conflicts with predictable raw ownership |
| Recursive `chown` as routine runtime adaptation | Rejected | Destructive, slow, interruption-prone, and owner-ambiguous |
| Rootful container merely to avoid mapping work | Rejected as default | Expands privilege instead of defining ownership |

## Verification

EX-0014 must exercise:

1. the current 60503/5001 and 165536:65536 inventory;
2. literal classic-account migration alternatives on disposable copies;
3. Podman and Docker rootless creation, bind mounts, volumes, build, export,
   backup, restore, and concurrent namespace modes;
4. idmapped and non-idmapped paths on the leading Btrfs and ext4 challenger;
5. fixed `sysusers.d` and `DynamicUser=` services with retained/restored state;
6. homed activation, sessions, lingering services, rootless stores, source
   binds, collision, backup, recovery, and storage integration;
7. wrong/colliding/reused UID and subordinate ranges;
8. OS rollback, reinstall, disk replacement, host-to-host state movement, and
   compromise restore;
9. ACL, xattr, archive, snapshot, and ownership-remanence inspection; and
10. measured user and administrator cost.

## Risks and unresolved questions

- Is 5001 the right canonical human UID, or should NeutrinOS reserve a new
  documented range distinct from current hosts and systemd special ranges?
- Should the 165536 subordinate range be identical on every host or only on
  hosts that can receive raw rootless state?
- Which container workloads genuinely need full 65,536-ID mappings, `keep-id`,
  `auto`, nested containers, or only a single mapped user?
- Can Podman idmapped volumes cover all bind-source cases on the selected
  kernel/filesystem/runtime versions?
- Where should rootless graph storage live on the Btrfs user/workload volume,
  and which user-session lifecycle owns its engine?
- Which services qualify for `DynamicUser=` without making backup or recovery
  depend on activation-time remapping?
- Does a stable user UUID add useful portability now, and which userdb record
  owns it without introducing another account manager?
- Can homed preserve the full workflow without per-user LUKS duplication or
  incompatible subordinate-owned inodes?
- How should supplementary groups and device ACLs behave inside rootless
  namespaces and graphical sessions?

## Proposed requirements

SYS-109 through SYS-120 capture the accepted policy in this design. PR-0015 is
the accepted adversarial requirements review.

## Review disposition

The design is in adversarial review. It proposes stable inventory-owned human
and subordinate allocations, systemd-native service identities, explicit
per-workload namespace mappings, and a classic-account baseline. Exact numeric
allocations, runtime selection, and homed adoption remain open pending EX-0014.
