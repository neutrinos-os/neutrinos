---
id: DES-0002
title: State ownership and rollback contract
status: in-review
owners: []
reviewers: []
created: 2026-08-09
last_updated: 2026-08-09
depends_on: [DES-0001]
decision_backlog: [S-002, L-005, C-002]
related_adrs: []
---

# State ownership and rollback contract

## Problem

Replacing an OS artifact does not replace or roll back the machine's durable
state. Without explicit ownership and compatibility rules, a mechanically
successful OS rollback can boot into configuration, credentials, databases, or
user data that the older release cannot safely consume.

This design defines the lifecycle contract for state before selecting a
filesystem, partition layout, encryption scheme, configuration-delivery tool,
or update substrate.

## Goals

- Assign every durable state item to an accountable lifecycle owner.
- Separate release identity from machine, administrator, user, and workload
  state.
- Make `/etc` and local-override behavior deterministic and inspectable.
- Define when NeutrinOS may honestly advertise rollback.
- Specify migration, backup, reinstall, reset, and recovery obligations.
- Work for both workstation and router roles.

## Non-goals

- Choosing Btrfs, ZFS, LVM, a partition table, or subvolume layout.
- Selecting a secrets service, backup product, or enrollment protocol.
- Promising transparent rollback of arbitrary databases, homes, containers, or
  VM disks.
- Preventing an administrator with sufficient privilege from modifying the
  machine.
- Defining application-specific migrations.

## Requirements and constraints

Accepted project policy requires explicit ownership, migration, backup,
rollback, and reset semantics under CH-005 and Principles 3 and 4. SYS-014
through SYS-018 constrain how declared configuration is authored, composed,
deployed, and diagnosed.

SYS-004 and SYS-009 remain candidate requirements. SYS-019 through SYS-026 were
accepted as normative project policy through
[PR-0003](../../project/reviews/0003-state-ownership-requirements.md), while
this implementation design remains in review. The design must not assume that
a snapshot is a backup, that an OS rollback is a state rollback, or that a path
determines its owner.

## Decision drivers

1. The previous OS release must remain a meaningful recovery option after an
   update.
2. A machine's effective configuration must not depend on an unknowable history
   of edits and three-way merges.
3. Production-only secrets and hardware-derived values cannot be embedded in a
   generally qualified image.
4. User and workload data often outlive any OS release and may be much larger
   than it.
5. Failed-update diagnostics must survive long enough to explain the failure.
6. The router must recover without depending on the network service it is
   responsible for providing.

## Proposed ownership model

Ownership describes authority and lifecycle, not Unix UID ownership. Paths are
only examples; one path such as `/var` can contain items from several classes.

| Class | Owner and source of truth | Examples | Normal lifecycle |
| --- | --- | --- | --- |
| Release | NeutrinOS release | `/usr`, kernel/UKI, immutable defaults, release-bound extensions | Replaced and rolled back only as an identified release artifact or artifact set. |
| Declared role and machine configuration | Version-controlled role/machine input | network intent, enabled services, hardware selection, generated native configuration | Qualified with a release, rendered afresh, and selected by deployment identity; not edited in place as durable state. |
| Machine identity and enrollment | Individual machine | machine identity, host keys, device certificates, TPM-bound enrollment records | Persists across OS replacement; rotated, revoked, re-enrolled, or deliberately destroyed rather than rolled back with the OS. |
| Administrator override | Local administrator | emergency service drop-in, temporary kernel argument, break-glass policy | Explicit, attributable, time-bounded where possible, and marks the machine locally modified until removed or incorporated into declared configuration. |
| User | User or user-profile system | home data, user credentials, desktop settings, per-user application state | Persists independently of OS rollback; has separate backup, restore, quota, and reset policy. |
| Workload | Workload or service owner | databases, container writable layers and volumes, VM disks, application queues | Persists independently; every schema and migration is governed by the workload contract. |
| Operational evidence | Machine or fleet operations | journals, update records, health results, crash data, audit records | Survives failed boots according to retention and sensitivity policy; is not restored by OS rollback. |
| Ephemeral | Producing component | `/run`, disposable caches, temporary build or download state | May be discarded on reboot, retry, recovery, or space pressure without loss of authoritative data. |

Derived data is not automatically ephemeral. A cache is ephemeral only when it
can be safely and deterministically reconstructed; a queue, unsent message, or
unique local measurement is durable workload state even if stored under a
conventionally temporary-looking path.

## `/etc` and effective configuration

### Proposed default

`/etc` is a rendered runtime view, not an authoritative durable configuration
database. The normal boot constructs the effective view from ordered inputs:

1. upstream and release defaults owned by the release;
2. NeutrinOS common and role configuration;
3. declared machine configuration and hardware-derived values;
4. late-bound credentials or secret references; and
5. explicit administrator overrides.

The exact resolved inputs and rendered native files are inspectable under
SYS-016. Layers may use upstream-native configuration directly. The ordering
does not imply that every file is templated or that NeutrinOS must model every
upstream setting.

The preferred substrate mode therefore provides a transient or reconstructible
`/etc`. A persistent three-way merge of image defaults and historical local
edits is not the normal NeutrinOS configuration model because its result
depends on mutation history rather than only identified inputs.

### Required exceptions

Some upstream software writes identity, credentials, or enrollment data under
`/etc`. Such content must be classified by owner and either:

- supplied through a defined late-bound interface;
- persisted in an explicitly inventoried machine-state location and projected
  into the effective view; or
- retained as a documented, tested persistent exception.

An exception does not make all of `/etc` durable. Each exception needs an
owner, sensitivity, backup or regeneration rule, reset behavior, and
compatibility test.

### Break-glass changes

Local administrative modification remains possible for recovery. It is not a
silent configuration channel. A durable override must be discoverable in
machine status, attributable to its source, included in effective-
configuration inspection, and cause the deployment to report **locally
modified** until the override is removed or committed to the declared source
of truth.

## State contract

Every persistent state item or namespace must record at least:

| Field | Meaning |
| --- | --- |
| Identifier | Stable project identifier for the state contract. |
| Owner | Component or policy responsible for writes, schema, migration, backup guidance, and recovery. |
| Location | Paths, volumes, credentials, device storage, or external service holding the state. |
| Authority | Canonical source when replicas or rendered views exist. |
| Schema | Current version and how it is detected. |
| Compatibility | Release versions that may read and write the schema safely. |
| Migration | Trigger, ordering, idempotence, interruption behavior, and reversal or checkpoint method. |
| Confidentiality and integrity | Sensitivity, access boundary, and validation mechanism. |
| Backup and restore | What is captured, consistency boundary, verification, retention, and restore test. |
| Reset and destruction | Behavior for config reset, re-enrollment, reprovisioning, factory reset, and key destruction. |
| Health | Observable evidence that the state is usable after an update or recovery. |

The inventory itself is bounded declarative data. Workload-specific migration
programs may be code, but they are separately owned implementations rather than
machine configuration.

## Update and migration protocol

For every state contract touched by a candidate release:

1. **Preflight:** identify the current schema and verify that the candidate can
   consume it.
2. **Rollback check:** verify that the previous release can consume all state
   the candidate may write before blessing, or select an owner-specific
   reversible/checkpointed migration path.
3. **Stage:** prepare the release and any migration material without changing
   authoritative state where practical.
4. **Activate:** boot or select the candidate, then run migrations at their
   declared lifecycle boundary.
5. **Assess:** include migrated-state and role-service health in the boot
   success decision.
6. **Bless:** mark the release successful only after its required state owners
   report health and the rollback contract remains true.
7. **Retire:** remove old checkpoints only after the advertised rollback window
   closes and backup policy permits it.

Migration execution must be idempotent or detect a previously completed step.
An interruption must lead to a known retry, rollback, or recovery state rather
than an ambiguous partially migrated schema.

## Rollback contract

NeutrinOS rollback reselects the previous OS release. It does **not** generally
restore persistent machine, administrator, user, workload, or operational
state.

A release may advertise normal rollback only when the previous release can boot
and meet its minimum role health criteria using every durable state mutation
the candidate is permitted to make before blessing. This can be established by
one of the following owner-specific strategies:

- no schema change;
- backward-compatible reads and writes across the rollback window;
- delayed migration or delayed use of incompatible features;
- a reversible migration; or
- an atomic owner-specific checkpoint and switch with a tested restore path.

A forward-only destructive migration is an explicit maintenance operation. It
must not silently retain the normal rollback claim. The release must instead
state the commit barrier, required backup, recovery procedure, expected outage,
and point after which the old deployment is no longer a safe automatic target.

Filesystem snapshots may implement an owner-specific checkpoint, but they do
not create application consistency, backup independence, or rollback safety by
themselves.

## Reinstall, recovery, and reset

Recovery operations have distinct scopes:

| Operation | Release | Machine identity | Admin override | User/workload data |
| --- | --- | --- | --- | --- |
| OS repair or rollback | Replace or reselect | Preserve | Preserve and report | Preserve |
| Declared-config reset | Preserve or re-render | Preserve | Remove | Preserve |
| Re-enrollment | Preserve | Rotate, revoke, or recreate | Preserve unless policy conflicts | Preserve, subject to key accessibility |
| Role reprovision | Replace | Explicit preserve-or-recreate choice | Remove | Preserve only items named in a preservation manifest |
| Factory reset | Return to recovery/factory release | Destroy or revoke | Remove | Destroy, including relevant encryption keys |

Reinstall and reprovision preserve only state named by an inventory or
preservation manifest. “Keep `/var`” is not a sufficient policy because `/var`
contains authoritative data, regenerable data, executable state, secrets, and
diagnostics with different owners.

The recovery environment must remain bootable without trusting the normal
deployment's rendered `/etc` or workload state. It must be able to inspect
release identity, state inventory, local modifications, and available recovery
actions before mutating durable data.

## Role traces

### Workstation

- `/home` and user credentials are user state, not part of OS rollback.
- Rootless container storage and VM disks are workload state even when owned by
  the same Unix user.
- Wi-Fi, VPN, and desktop secrets need an explicit user-versus-machine owner.
- A failed graphical boot must preserve enough journal and crash evidence for
  diagnosis from the previous deployment or recovery environment.

### Router

- Firewall, routing, address, and service policy are declared configuration and
  must be reconstructible without historical `/etc` edits.
- Host keys, VPN identity, and delegated credentials are machine state with
  regeneration and revocation procedures.
- Leases, learned data, and caches require individual durability decisions;
  their conventional path does not decide their owner.
- Rollback and recovery cannot require working WAN, DNS, or the normal remote
  administration path.

## Options considered

### Persist and three-way merge `/etc`

This maximizes compatibility with traditional packages and permits familiar
local editing. It is not proposed as the default because effective
configuration becomes history-dependent, image-default changes can conflict
with local mutations, and qualification cannot fully identify what will run.
It remains a possible explicit exception for software that cannot yet operate
with a reconstructed view.

### Make the entire root filesystem immutable and keep only `/var` and `/home`

This is simple at the diagram level but treats `/var` as one lifecycle domain.
It fails to distinguish machine identity, secrets, caches, logs, databases, and
workload images. The design instead classifies individual state contracts and
maps them to storage later.

### Snapshot all mutable state before every update

This provides a useful local recovery primitive but cannot guarantee
application consistency, may couple recovery to one disk, and can revert user
work that occurred after the update. Snapshots are allowed only as
owner-specific checkpoints within a larger contract.

### Leave state management to each application

Applications must own their schemas, but NeutrinOS still needs promotion,
rollback, health, backup, and recovery gates across those owners. Complete
delegation would make the system-level rollback claim unverifiable.

## Failure and recovery analysis

| Failure | Required behavior |
| --- | --- |
| Rendering or validation fails | Do not stage or activate; identify the input and output involved. |
| Migration is interrupted | Detect partial progress and follow the declared retry, restore, or recovery transition. |
| Candidate boots but state health fails | Do not bless; automatically roll back only if the recorded compatibility contract permits it. |
| Previous release cannot consume current state | Refuse automatic rollback and enter the declared recovery path; record a violated contract as a release defect. |
| Local override breaks boot | Expose and disable the override from recovery without modifying declared source. |
| Machine credential is lost or revoked | Re-enroll through an independent authority or recovery credential; OS rollback must not resurrect revoked identity. |
| Backup is corrupt or incomplete | Restore verification fails before destructive replacement where possible; preserve original state for further recovery. |
| Persistent storage is unavailable | Recovery remains independently bootable and reports which state owners are unavailable. |

## Security and trust

- Secrets are state with an owner, not ordinary configuration values. Checked-in
  configuration contains references or policy, never secret material.
- OS rollback must not roll back revocation, monotonic security state, or audit
  evidence unless a later threat model explicitly justifies it.
- Rendered configuration can contain secrets and therefore needs access,
  logging, diagnostic-redaction, and destruction rules even when the input
  model is safe to commit.
- Factory reset must define whether destroying encryption keys is the deletion
  boundary and how external credentials are revoked.
- Persistent executable configuration is part of the effective trust surface
  even when stored outside the immutable release.

## Verification

The design is not acceptable until tests can demonstrate:

1. a clean machine reconstructs identical non-secret effective configuration
   from the same identified inputs;
2. an unmodeled upstream setting remains usable and attributable;
3. a local override changes machine status to `locally modified` and can be
   disabled from recovery;
4. candidate and rollback releases are tested against the same post-update
   state for every touched contract;
5. interruption at each migration boundary has one documented next action;
6. workstation user/container data survives OS repair without being confused
   with OS rollback;
7. router identity and declared network policy survive a failed update while
   recovery remains available without normal networking;
8. restore tests verify owner-consistent backups rather than file presence
   alone; and
9. config reset, re-enrollment, role reprovision, and factory reset affect only
   their declared state classes.

## Risks and unresolved questions

- Which components cannot operate with reconstructed `/etc`, and which exact
  persistent exceptions do they require?
- Is declared machine configuration always bound to the release artifact, or
  can a separately identified configuration artifact be promoted against more
  than one OS release?
- Which state inventory is compiled into a release, and which portions are
  discoverable only on the machine?
- What is the minimum boot health required before a state-writing service may
  run?
- How are UID/GID allocations owned when they affect release files, machine
  identity, user homes, and rootless workload storage simultaneously?
- Which diagnostics must persist on space-constrained router systems?
- What maximum recovery time and data-loss objective applies to each role?

## Review disposition

The policy direction and derived requirements were
[accepted in PR-0003](../../project/reviews/0003-state-ownership-requirements.md).
The implementation-level adversarial review remains [open](review.md). Its
critical challenges are compatibility with software that writes `/etc`, honest
handling of forward-only migrations, and avoiding an inventory whose
maintenance cost exceeds its value.

No ADR should be written until those challenges are reviewed by the project
owner and the derived requirements are accepted or revised.
