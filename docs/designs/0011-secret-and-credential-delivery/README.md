---
id: DES-0011
title: Secret custody and credential delivery
status: in-review
owners: [Jason Tarasovic]
reviewers: [Codex adversarial pass]
created: 2026-08-10
last_updated: 2026-08-10
depends_on: [DES-0002, DES-0003, DES-0004, DES-0005, DES-0010]
decision_backlog: [C-002]
related_adrs: []
---

# Secret custody and credential delivery

## Problem

NeutrinOS deliberately keeps secret values and machine identity outside the OS
deployment identity. That avoids rebuilding a deployment for every password,
private key, or certificate rotation, but it creates a powerful late-bound
channel. Without a strict contract, an encrypted value can carry executable
configuration, grant unintended consumers access, survive revocation through
rollback or backup, or turn an online secret service into a boot dependency.

The systemd credentials mechanism is a strong default interface for passing
bounded data to services. It is not, by itself, an authority, issuer, inventory,
rotation protocol, backup policy, or fleet secret manager. This design must
define those missing semantics while preserving systemd credentials as the
normal last-mile interface when they fit.

## Goals

- Classify bootstrap, machine, service, user, workload, storage-unlock, and
  recovery secrets by owner and authority.
- Bind each late-bound secret or credential to one identity-bound consumption
  contract.
- Make systemd credentials the default service-delivery interface without
  making their storage format the universal custody mechanism.
- Keep secret rotation and revocation independent of OS deployment updates.
- Support an attended, offline-capable personal fleet without requiring a
  permanently available secret service.
- Prevent recovery, installer, qualification, and normal modes from silently
  sharing credentials.
- Make missing, stale, invalid, leaked, restored, and revoked credentials
  observable without exposing their values.

## Non-goals

- Select a production PKI, secret service, HSM, password manager, or CA.
- Store secret values in the fleet-intent repository or deployment evidence.
- Treat encryption at rest as proof that the intended consumer received a
  correctly authorized value.
- Hide secrets from root or a fully compromised service while that machine or
  service legitimately consumes them.
- Replace application-native short-lived identity, certificate renewal, or
  protocol key exchange where those are the better interface.
- Make every platform observation, provisioning field, or runtime value a
  credential.
- Define personal password-manager or desktop keyring product policy.
- Select exact secret file paths, record encodings, or an online control plane
  before the representative exercise.

## Accepted constraints

- SYS-017 and SYS-025 keep late-bound values, identity, enrollment, and secrets
  outside OS rollback while preserving their explicit ownership.
- SYS-032 through SYS-035 separate authorities, recovery, and compromise
  consequences.
- SYS-042 through SYS-047 bind late-bound effects without permitting runtime
  role or policy assignment.
- SYS-050 through SYS-054 separate routine unlock, recovery unlock, normal
  boot, and recovery activation.
- SYS-065 through SYS-074 require sensitive evidence policy and traversable
  compromise consequences.
- SYS-086 through SYS-097 make provisioning input bounded and inert, give
  machine identity an epoch, and prohibit first boot from becoming an ordinary
  configuration channel.
- ADR-0001 requires a strong justification before replacing a suitable systemd
  ecosystem mechanism.

## Decision drivers

1. The initial fleet is small enough that a simple attended or removable-media
   flow may be safer and cheaper than a permanent highly available service.
2. `router` must retain declared operation when WAN, DNS, publication, or an
   enrollment service is unavailable.
3. A secret value may rotate frequently without changing release-owned policy.
4. The same deployment bytes may run on several machines whose secret values
   and machine identity differ.
5. Root on a running machine can normally access secrets consumed there; the
   design must limit duration, consumer, and blast radius rather than claim an
   impossible boundary.
6. Services vary: some can read a file once, some reload, some need a socket or
   native identity API, and some cannot use systemd credentials directly.
7. Host-bound encryption improves stolen-disk protection but complicates
   preparation elsewhere, disk replacement, backup, and machine recovery.
8. One shared fleet decryption key would turn a single-machine compromise into
   fleet compromise.

## Proposed model

### Separate the contract, grant, value, and delivery

```text
identity-bound credential contract
             |
             v
credential authority issues one scoped grant
             |
             v
secret custodian supplies one versioned value/envelope
             |
             v
enrolled machine authenticates and verifies scope
             |
             v
systemd exposes plaintext to one service activation
```

These may be implemented by fewer components in the initial personal fleet,
but their records and authority effects remain distinguishable.

| Object | Meaning | Must not become |
| --- | --- | --- |
| Credential contract | Identity-bound declaration of allowed name, owner, issuer, consumer, semantics, delivery, lifecycle, and failure behavior | Secret value or mutable authorization |
| Credential grant | Authority decision permitting one exact subject and consumer to receive a bounded credential instance | Release authorization or general machine policy |
| Credential instance | One versioned value or proof with issuer, subject, scope, validity, and status | Executable configuration or an unversioned “current” value |
| Secret envelope | Protected representation addressed to declared recipient capability and context | Proof that plaintext was safely consumed |
| Credential realization | Evidence that one machine/service activation received or could not receive an exact instance under one contract | Secret-bearing audit log |

### Secret and credential classes

| Class | Primary owner/authority | Normal consumer | Required separation |
| --- | --- | --- | --- |
| Provisioning bootstrap secret | Provisioning/enrollment authority | Bounded installer or first-boot handoff | Single operation; retired after completion; never steady-state service authority |
| Machine identity key | Machine/enrollment authority | Machine authentication component | Independent identity epoch; not a general secret-decryption key by default |
| Platform or routine data-unlock material | Platform/data owner | Initrd or storage activation | Separate from enrollment, service secrets, and recovery activation |
| Data-recovery secret | Data owner | Deliberately authorized recovery flow | Not supplied to normal services or a generic recovery environment |
| System service credential | Machine or service owner | One named system unit or native daemon endpoint | Cannot assign role, enable units, or rewrite normal policy |
| User secret | User | User session/application | Not automatically visible to the system manager or other users |
| Workload credential | Workload owner | One container, VM, or workload identity | Separate from host machine identity and sibling workloads |
| Administrative break-glass credential | Administrator/recovery authority | One exceptional operation | Time-bounded, attributable, and followed by rotation or explicit residual-risk review |

Combining classes requires an explicit decision that shows why the shared
custody and compromise scope are acceptable. Convenience is not sufficient.

### Credential contract

Each service-consumed late-bound value has an identity-bound contract naming:

- stable contract identifier and schema version;
- value class, semantic purpose, and confidentiality classification;
- owner, issuer/custodian, grant authority, and permitted subject;
- exact system unit, user unit, workload, or native consumer interface;
- credential name, expected encoding/schema, maximum size, and multiplicity;
- permitted source and delivery adapters;
- machine, identity epoch, role, service, and environment scope as applicable;
- validity, freshness, rotation, overlap, revocation, and destruction behavior;
- boot/service behavior when absent, invalid, stale, unavailable, or revoked;
- whether an offline cached instance is permitted and for how long;
- reload, restart, drain, and rollback behavior;
- evidence, redaction, retention, backup, restore, and compromise policy; and
- an explicit statement of the semantic effects the value may have.

Changing this contract changes the resolved configuration and deployment
identity. Changing a conforming credential instance does not.

### Policy power is not made safe by encryption

A credential may contain opaque key material or bounded data such as a
certificate chain, token, password, or provider-assigned address within a
declared schema. It may not carry shell code, unit files, package selections,
firewall policy, arbitrary templates, executable plugins, or undeclared
consumer lists.

If a late-bound value can materially choose privileged behavior beyond its
declared schema, it is configuration or code regardless of whether it is named
“secret,” stored by Vault, encrypted by SOPS, or delivered by systemd. It must
move into the deployment identity or become an explicit administrator/workload
override with the resulting status.

### Default last-mile interface: systemd credentials

For a system or user service that consumes bounded file-like data, the default
interface is the systemd credentials mechanism:

- the unit declares `LoadCredential=`, `LoadCredentialEncrypted=`, or
  `ImportCredential=` under the accepted contract;
- plaintext appears only for the service activation in its credentials
  directory;
- the service reads via `$CREDENTIALS_DIRECTORY`, `%d`, or an explicitly
  qualified path adapter;
- mount namespacing and ordinary unit sandboxing limit visibility to the
  intended unit where practical; and
- plaintext is released when the service stops.

`SetCredential=` is not permitted for secret values because unit definitions
and their D-Bus representation are not confidential. `SetCredentialEncrypted=`
may carry an encrypted blob only when its recipient and rotation model meet the
same contract; embedding ciphertext does not make a secret release-owned.

Environment variables and command-line arguments are rejected for normal
secret delivery because they propagate or are exposed too broadly. A legacy
daemon may receive the path to a systemd credential, or use a narrowly scoped
adapter that renders a runtime file and removes it at stop. A persistent secret
file requires an explicit exception, owner, permissions, cleanup, rotation, and
backup policy.

Systemd credentials are immutable for one service activation. A rotating
credential therefore requires an application-native renewal interface or an
ordered reload/restart that creates a new activation. Silently replacing the
backing file is not proof that a running service adopted the new value.

### Custody and transport are separate from delivery

The systemd credential store and `systemd-creds` encrypted blobs are leading
local representations where their behavior fits. The default host encryption
combines TPM2 material and `/var/lib/systemd/credential.secret` when both are
available, making the ciphertext installation-bound and unsuitable for
preparation on another machine. This property is useful for local custody but
cannot be assumed for remote issuance, disk replacement, or offline restore.

Candidate custody/transport paths are:

1. an administrative or removable-media envelope encrypted to a current
   machine/operation recipient, verified and re-sealed locally;
2. an authenticated online response scoped to the enrolled machine identity,
   contract, consumer, epoch, and validity;
3. a locally created `systemd-creds` encrypted value for a machine-owned secret;
   or
4. an application-native short-lived identity API where retaining static secret
   bytes would be the worse abstraction.

The machine identity key is not automatically a general decryption key. If a
separate machine encryption key or key-agreement capability is needed, its
generation, enrollment binding, exportability, rotation, attestation, and loss
behavior must be explicit.

No normal design uses one fleet-wide plaintext secret, shared host key, or
unscoped recipient identity. Repository encryption such as SOPS/age may be an
administrative custody and review tool, but decryption rights and the resulting
delivery still follow the credential contract; encrypted files do not belong
in the deployment merely because their plaintext is hidden.

### Authorization and machine enrollment

Successful enrollment establishes the current machine record and identity
epoch. It does not entitle the machine to every secret associated with its role.
Each credential grant additionally binds:

- the exact enrollment binding and current epoch;
- credential contract and requested consumer;
- instance identity or permitted issuance parameters;
- grant authority, decision time, validity, and ordering;
- prerequisite deployment/support/health state where applicable; and
- whether cached use is allowed after the authority becomes unreachable.

The receiving machine verifies this scope before storing or exposing the value.
A secret service, seed, metadata endpoint, or encrypted repository cannot assign
the machine's role or expand its consumer list.

### Rotation, revocation, rollback, and offline operation

Credential instances have explicit ordered versions or epochs. Rotation uses
an overlap policy when the protocol requires it, verifies the new value, moves
consumers, retires the old value, and records any incomplete cleanup. A service
restart or drain is coordinated independently from OS activation.

OS rollback does not roll back credential currentness. Restoring machine state
or ciphertext from backup cannot make an expired or revoked instance current.
When online authority is available, the machine reconciles retained instances
and current status before acquiring new grants. When offline:

- the machine may continue using only cached instances whose contract permits
  it and whose locally verifiable validity has not ended;
- loss of trustworthy time follows the contract's conservative clock policy;
- it gains no new grant, scope, consumer, or freshness claim; and
- status reports the knowledge time and possibility of unseen revocation.

High-availability roles may deliberately accept longer offline use. That is an
availability/confidentiality tradeoff recorded per contract, not a global
default.

### Boot modes and recovery

Normal, installer, qualification, maintenance, and recovery modes each have an
allowlist of credential classes and consumers. Merely booting signed code does
not release normal service, user, workload, enrollment, or data-recovery
secrets. Recovery receives only the exact credential explicitly authorized for
the selected capability transition.

Qualification uses synthetic credentials that satisfy the same shapes and
failure behavior but confer no production authority. Installer and first-boot
credentials follow DES-0010 completion and retirement rules. Normal service
credentials are not placed in the installer image, UKI, kernel command line,
generic SMBIOS strings, or reusable seed media.

### Evidence and compromise response

Audit and status record identifiers and outcomes, never values. They can answer:

- which contract and credential instance a consumer attempted to realize;
- which machine identity epoch, deployment, unit activation, and boot mode were
  involved;
- which grant and source were verified and when;
- whether the result was present, missing, invalid, stale, expired, revoked,
  unavailable, or redacted;
- which reload/restart and retirement steps completed; and
- which machines and consumers require rotation after an issuer, machine,
  store, envelope recipient, or credential instance is compromised.

Values, plaintext-derived hashes vulnerable to guessing, bearer tokens,
private locators, and overly precise topology are excluded or separately
protected. Native service, systemd, issuer, and adapter diagnostics remain
available with the same redaction policy.

## Candidate mechanism disposition

| Mechanism | Proposed disposition | Reason |
| --- | --- | --- |
| systemd service credentials | Leading last-mile delivery interface | Activation-scoped, file-like, binary-safe, and aligned with ADR-0001 |
| `systemd-creds` encrypted blobs | Leading local at-rest representation where recipient/recovery semantics fit | Strong host binding is useful but complicates remote preparation and restore |
| Authenticated online secret service | Challenger for issuance, rotation, and dynamic credentials | Adds availability, bootstrap, authorization, upgrade, and recovery burden |
| Administrative offline envelope | Required challenger for the initial personal fleet | Preserves offline enrollment/recovery and avoids premature control-plane dependence |
| SOPS/age repository encryption | Administrative custody candidate, not runtime delivery | Useful review workflow; repository access and decryption scope must not become fleet authority |
| Application-native identity API such as SPIFFE | Workload-scale challenger | Strong short-lived workload identity semantics but excessive until a concrete workload requires it |
| Environment variables or command-line values | Rejected for normal secrets | Excess visibility and inheritance |
| Persistent plaintext files | Exception-only compatibility adapter | Broad lifetime, backup, permission, and cleanup risks |
| UKI, image, kernel command line, SMBIOS, or generic metadata plaintext | Rejected | Reuse, observation, logging, and authority-boundary violations |

## Verification

EX-0013 must exercise at least:

1. a machine-owned key, router service key, workstation network secret, and a
   synthetic user/workload credential;
2. online and removable offline delivery into the same systemd credential
   consumer;
3. host-bound encrypted storage plus TPM clear, disk replacement, and restore;
4. exact unit scoping and a hostile sibling/rootless workload;
5. missing, invalid, wrong-name, wrong-machine, wrong-epoch, expired, revoked,
   and replayed instances;
6. application-native renewal and restart-based rotation, including failure
   during overlap and retirement;
7. offline operation, stale clock, unseen revocation, and reconnect;
8. normal, installer, qualification, maintenance, and recovery boot-mode
   allowlists;
9. config/code smuggled through a nominal credential;
10. logs, coredumps, diagnostics, backup, and returned-media remanence; and
11. issuer, machine, custodian, and adapter compromise traversal.

## Risks and unresolved questions

- What exact key capability receives an offline or online machine-addressed
  envelope without overloading the machine authentication key?
- Can the initial fleet use only attended transfer and local encrypted stores,
  or do any required services justify an online issuer immediately?
- Which base services natively support `$CREDENTIALS_DIRECTORY`, and which need
  path or runtime-file adapters?
- How will user-manager credentials be provisioned without giving the system
  manager unnecessary access to user secrets?
- Which router credentials must survive an extended WAN outage, and what
  maximum unseen-revocation interval is acceptable?
- Should machine/service certificates use a small project PKI, protocol-native
  keys, or a workload identity system?
- How are host-bound encrypted credentials rewrapped after TPM, motherboard, or
  disk replacement without weakening independent recovery?
- What exact status is safe to expose for secret inventory on a personal
  workstation and router?

## Accepted requirements

PR-0014 accepts SYS-098 through SYS-108 as policy boundaries. They define
secret-class separation, identity-bound credential contracts, bounded semantic
effects, systemd-first service delivery, recipient and recovery semantics,
separate grants, rotation/currentness, offline behavior, boot-mode isolation,
and redacted compromise evidence without selecting concrete custody services,
envelopes, keys, or protocols.

## Review disposition

The design is in adversarial review. Accepted policy selects systemd
credentials as a last-mile service interface, not a universal secret manager,
and keeps concrete custody, envelope, PKI, and online-service choices open
until EX-0013 provides representative evidence.
