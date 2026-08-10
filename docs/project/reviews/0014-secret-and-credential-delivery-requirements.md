---
id: PR-0014
subject: Secret custody and credential delivery requirements
reviewer: Codex adversarial pass
date: 2026-08-10
status: accepted
---

# Secret custody and credential delivery requirements review

## Decision scope

This review asks whether SYS-098 through SYS-108 should become normative before
NeutrinOS chooses a secret backend, PKI, envelope format, recipient key,
`systemd-creds` mode, online service, or user/workload secret mechanism.

It reviews DES-0011 and proposed EX-0013. It does not accept SOPS, age, Vault,
SPIFFE/SPIRE, a custom agent, or a custom protocol merely because they appear
as candidates.

## Summary judgment

The requirements should be accepted after owner review. They make systemd
credentials the preferred process-delivery interface while preventing it from
absorbing issuance, authorization, recovery, and policy semantics it does not
provide.

The principal risk is building too much infrastructure. The requirements allow
static grants, attended removable transfer, and local sealing, so no daemon or
online service is required for conformance.

## Accepted requirement disposition

### SYS-098: Secret classes retain distinct owners and authority

Bootstrap, machine identity, routine unlock, recovery, system service, user,
workload, and break-glass material have explicit ownership, authority, custody,
consumers, backup, compromise, and destruction semantics. Sharing a key or
mechanism does not merge those authorities.

### SYS-099: Every late-bound credential has an identity-bound contract

The contract fixes the value's class, name, owner, issuer, authority, subject,
consumer, schema, semantics, source, delivery, lifecycle, offline behavior,
failure policy, and evidence. The contract changes deployment identity; a
conforming value rotation does not.

### SYS-100: Credentials cannot smuggle ordinary policy or code

Secret or encrypted data cannot introduce units, scripts, packages, firewall
rules, arbitrary templates, executable plugins, or undeclared consumers. A
value with such power is configuration/code or an explicit override regardless
of its encryption or label.

### SYS-101: Systemd credentials are the default service interface

Bounded file-like values reach system/user services through the systemd
credentials mechanism where it fits, scoped to one activation and consumer.
Environment, command-line, and persistent-file exceptions require explicit
justification and equivalent lifecycle/redaction controls.

### SYS-102: Protection binds the intended recipient and recovery policy

Every stored or transported secret names its confidentiality and authenticity
claims, recipient capability, machine/epoch/consumer scope, replay behavior,
backup/recovery, and replacement semantics. Host binding and encryption at rest
do not imply recoverability or delivery authorization, and no unreviewed fleet-
wide decryption secret is permitted.

### SYS-103: Enrollment identity is not secret entitlement

Each delivery requires an attributable grant bound to the current enrollment
binding/epoch, contract, exact consumer, instance or issuance parameters,
validity, and prerequisites. Metadata, repositories, and transport services
cannot assign role or expand scope.

### SYS-104: Rotation is an explicit cross-consumer transaction

Rotation distinguishes prepare, overlap, activation, verification, retirement,
abort, and recovery. It proves which value a running consumer adopted and does
not retire the old value or peer acceptance prematurely.

### SYS-105: Revocation and currentness do not roll back with the OS

Restored ciphertext, backup, machine state, or an older deployment cannot make
an expired/revoked credential current. Ordered status and reconciliation drive
rotation or quarantine independently of deployment selection.

### SYS-106: Offline use is bounded and makes no freshness claim

Offline machines use only explicitly cacheable, locally valid values for a
declared interval and clock policy. They gain no new authority and expose their
knowledge time and unseen-revocation risk before safe reconciliation.

### SYS-107: Boot modes and owners receive only their credential classes

Normal, installer, qualification, maintenance, and recovery modes use explicit
allowlists. Synthetic qualification values confer no production authority;
provisioning values become inert; recovery and privileged boot do not bulk-load
normal, user, workload, or data-recovery secrets.

### SYS-108: Evidence is useful without becoming a secret leak

Status and audit bind contract, non-secret instance identity, machine epoch,
deployment, consumer activation, grant, source, result, rotation, and time while
excluding values and unsafe derivatives. Compromise of any issuer, custodian,
recipient, broker, machine, or instance identifies its dependents and required
response.

## Guardrails from adversarial review

### Do not overclaim runtime secrecy

Root or the intended process can usually access plaintext while it is consumed.
Systemd credentials narrow exposure; they do not create an enclave.

### Do not infer recovery from ciphertext backup

TPM/host-bound ciphertext may be deliberately unrecoverable after hardware or
host-key loss. Each contract must choose reissue or independent recovery.

### Do not create a general privileged broker by accident

An agent that can fetch every secret needs exact local caller authorization and
its own compromise analysis. The per-unit credentials directory does not limit
what the broker already saw.

### Do not mistake encryption for configuration review

Encrypted shell code remains shell code. An authenticated issuer can still
exceed its intended semantics.

### Do not require a control plane prematurely

Static records plus attended transport are valid initial implementations. Add
an online service only when measured requirements justify its availability and
maintenance burden.

## Strongest alternatives rejected at policy level

### Put secrets in deployment artifacts

Rejected. It couples rotation and disclosure scope to OS publication and makes
shared artifacts machine-specific.

### Use one fleet bootstrap/decryption secret

Rejected. It destroys per-machine scope and makes compromise/recovery affect the
entire fleet.

### Place root-owned plaintext files manually with no contract

Rejected as the normal model. File permissions do not define issuer, scope,
currentness, rotation, backup, or rollback behavior.

### Require Vault/SPIRE or another online service now

Rejected. The initial requirements do not demonstrate enough scale or dynamic
issuance to justify that control-plane dependency.

## Required implementation evidence

Acceptance establishes policy only. DES-0011 still requires:

1. literal workstation and router contracts;
2. equivalent online and offline grants;
3. selected envelope recipient/key semantics;
4. local encrypted-store and hardware-replacement recovery results;
5. native systemd unit integrations and exception inventory;
6. restart/native renewal rotation results;
7. router offline-validity bounds;
8. boot-mode, hostile-consumer, clone, restore, and rollback tests;
9. remanence and redaction inspection;
10. compromise traversal; and
11. measured operator and maintenance cost.

## Decision

Accepted by Jason Tarasovic on 2026-08-10. SYS-098 through SYS-108 are
normative policy boundaries. DES-0011 remains in review until representative
evidence supports concrete custody, recipient, rotation, recovery, and service
choices.
