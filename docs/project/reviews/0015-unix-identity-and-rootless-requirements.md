---
id: PR-0015
subject: Unix identity and rootless-container ownership requirements
reviewer: Codex adversarial pass
date: 2026-08-10
status: accepted
---

# Unix identity and rootless-container ownership requirements review

## Decision scope

This review asks whether SYS-109 through SYS-120 should become normative before
NeutrinOS selects exact UID/sub-ID numbers, a human account manager, a rootless
OCI runtime, namespace modes, or a graph-storage path.

It reviews DES-0012 and proposed EX-0014. It does not accept UID 5001,
165536:65536, classic accounts, systemd-homed, Podman, Docker, idmapped mounts,
or a migration tool merely because one is a leading candidate or fixture.

## Summary judgment

The requirements should be accepted after owner review. They make persistent
numeric ownership explicit without confusing it with cryptographic identity and
allow dynamic allocation when no durable external state depends on the number.

The most important guardrail is refusing automatic recursive ownership repair.
Every convenient runtime can make a demo work by changing files; the project
needs proof that the intended owner, backup, restore, and other workloads remain
correct afterward.

## Proposed requirement disposition

### SYS-109: Every numeric namespace has an authority

Human, system, service, administrator, workload, subordinate, and transient
namespace IDs come from an identity-bound allocation record with owner, scope,
collision domain, native output, state dependencies, migration, and reuse rules.

### SYS-110: Durable human ownership cannot silently rebind

A human identity whose state moves or restores among managed hosts has a stable
numeric binding in that scope plus a distinct non-numeric identity. Collision
fails or invokes deliberate migration; numeric equality is not authentication.

### SYS-111: Service IDs are fixed only when semantics require it

Release-owned services use native systemd identity declarations. Dynamic IDs
are allowed only where all durable state and recovery remain safely mediated;
otherwise a collision-checked fixed allocation is part of deployment evidence.

### SYS-112: Subordinate IDs are explicit durable delegations

Every subordinate UID/GID range binds an owner, purpose, hosts/runtimes, size,
collision proof, dependent state, and retirement rule. Old ranges cannot be
reused while retained data may still carry them.

### SYS-113: Workload IDs do not become host identities

Container/VM image users and workload identities remain namespace-local unless
an explicit host mapping contract joins them. Matching names or numbers grant
no host, machine, user, or secret authority.

### SYS-114: Rootless mappings are per workload and inspectable

Each supported workload declares exact namespace mode/map, ranges, host subject,
mounts, output ownership, group/device/socket assumptions, state portability,
and failure behavior. Rootless is a privilege reduction, not a blanket safety
or qualification claim.

### SYS-115: Bind mounts preserve backing ownership

Source and shared-tree access must use compatible explicit maps or qualified
idmapped views. No normal runtime operation recursively changes backing
ownership; unsupported mappings copy into workload state or fail explicitly.

### SYS-116: Identity state has an owner-aware backup contract

Backups and restores retain an allocation manifest and inventory numeric owners,
ACLs/xattrs, namespace maps, subordinate dependencies, collisions, and security
status before preserving, remapping, idmapping, or rejecting state.

### SYS-117: UID/sub-ID changes are state migrations

Durable identity changes quiesce affected owners, verify backup, inventory exact
dependencies, prove a collision-free target, checkpoint, handle interruption,
verify results, retain a return path, and tombstone old allocations.

### SYS-118: Account and home managers must pass the workload lifecycle

Any account/home mechanism must pass rootless storage, source bind, namespace,
session/linger/logout/suspend, backup, collision, recovery, encryption, and
host-movement tests. A systemd ecosystem preference does not waive the user's
previous blocker.

### SYS-119: OS rollback cannot rewrite durable identity

Reinstall, rollback, package-baseline changes, and recovery preserve or
deliberately migrate current human/subordinate ownership independently of OS
selection, while service-account changes remain exact deployment inputs.

### SYS-120: Effective ownership and maps are diagnosable

Status joins semantic owner, backing UID/GID, resolved record, allocation,
namespace/idmapped view, subordinate ranges, workload maps, state dependencies,
and portability/currentness without replacing native NSS, userdb, mount,
filesystem, `/proc`, or runtime diagnostics.

## Guardrails from adversarial review

### Stable where required, not globally fixed by ideology

Persistent raw ownership may justify a fixed number. Transient namespace and
fully mediated service IDs usually do not.

### Do not make UID an authentication mechanism

The same UID on two hosts supports filesystem meaning only. Machine enrollment,
user authentication, network authorization, and secret grants remain separate.

### Do not assume homed is still broken—or now fixed

The previous blocker requires current literal testing. Current feature lists and
idmapped-mount support are not end-to-end evidence.

### Do not make `keep-id` a universal default

Its range and concurrency behavior is runtime-specific. Select it for the
workload whose bind-mount semantics require it.

### Do not repair ownership blindly

Recursive chown can cross owner boundaries, misclassify subordinate IDs, and
leave partial changes. It is only one controlled migration operation after an
exact inventory, never automatic runtime fallback.

## Strongest alternatives rejected at policy level

### Let each host allocate ordinary users independently

Rejected for state that is restored or shared between managed hosts. It moves
mapping complexity into every backup and bind operation without an authority.

### Give every service and workload a fleet-wide static UID

Rejected. It creates unnecessary allocation coupling and package-universe
conflicts where systemd or namespaces can mediate identity safely.

### Run containers rootfully when ownership is awkward

Rejected as the normal solution. It increases privilege and leaves the original
state/ownership contract undefined.

### Store only names in backup metadata

Rejected. Filesystems and archives carry numbers, names can be renamed or
reassigned, and workloads have namespace-local names.

## Required implementation evidence

Acceptance establishes policy only. DES-0012 still requires:

1. exact current-host, package, backup, and collision inventory;
2. canonical human UID/GID and sub-ID selection;
3. Podman and Docker rootless bind/volume/restore results;
4. qualified idmapped-mount matrix;
5. systemd-homed challenger results;
6. fixed and DynamicUser service recovery results;
7. raw-versus-logical state movement;
8. interrupted UID and sub-ID migration rehearsals;
9. range retirement/reuse evidence; and
10. measured operating cost.

## Decision

Accepted by Jason Tarasovic on 2026-08-10. SYS-109 through SYS-120 are
normative policy boundaries. DES-0012 remains in review until the exercise
supports exact allocations, account/home mechanism, namespace mappings, and
migration.
