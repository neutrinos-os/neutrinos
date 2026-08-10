---
id: EX-0013
title: Representative secret custody and credential flow
status: proposed
date: 2026-08-10
exercise_type: tabletop and implementation spike
evidence_class: analysis-first
related_designs: [DES-0011]
---

# Representative secret custody and credential flow

## Purpose and evidence limit

This exercise tests whether DES-0011 can remain simple for the initial fleet
while preserving its authority, recovery, rotation, and configuration
boundaries. The first pass uses synthetic values and static records. Literal
systemd and TPM behavior requires a later disposable-VM implementation pass.

No production secret, private key, network credential, or recovery locator may
enter the exercise corpus, logs, or committed fixtures.

## Fixtures

Exercise four distinct contracts:

| Fixture | Owner | Consumer | Important property |
| --- | --- | --- | --- |
| Router tunnel private key | Machine/service owner | Exact VPN unit | Long offline availability and deliberate rotation |
| Workstation Wi-Fi credential | User or machine, to be decided by network | Exact network consumer | Must not enter image, logs, or unrelated services |
| Machine service certificate | Machine/service authority | One administrative endpoint | Shorter validity and renewal/restart behavior |
| Synthetic workload token | Workload owner | One rootless container or VM | Must not inherit host-wide service access |

Use a blank QEMU VM with vTPM, a no-TPM VM, a cloned/restored VM, and the
reference router policy with its expected hardware-bound facility.

## Canonical records

Create candidate inspectable representations for:

| Record | Minimum non-secret content |
| --- | --- |
| Credential contract | stable ID, schema, class, owner, issuer, authority, subject, consumer, name, semantic bounds, delivery, validity, offline, failure, rotation, evidence |
| Credential grant | contract, exact machine binding/epoch, consumer, permitted instance/issuance, authority, ordering, validity, prerequisites |
| Credential instance metadata | issuer, subject, scope, version/epoch, validity, status, envelope identity; never plaintext or guessable digest |
| Delivery/realization record | machine, deployment, boot mode, unit activation, contract/instance, verification result, timestamps, source class, redacted failure |
| Rotation transaction | old/new instance, prepare, overlap, activate, verify, retire, abort/rollback and peer state |
| Compromise action | affected issuer/store/recipient/instance, dependency traversal, rotation/revocation/re-enrollment decisions |

Determine which records can be views of the existing acyclic evidence graph
without creating redundant mutable databases.

## Baseline flows

### Offline attended flow

1. Resolve the identity-bound contract from the selected deployment.
2. Verify the current enrollment binding and exact identity epoch.
3. Authorize one scoped grant on an administrative system.
4. Protect a synthetic value for the intended operation/machine capability and
   transfer it on removable media.
5. Target verifies grant, subject, contract, epoch, consumer, validity, and
   replay state, then creates the chosen local protected representation.
6. The media value becomes inert or is securely retired under recorded policy.
7. Systemd exposes the value to one named service activation.
8. Status records successful realization without logging secret-derived data.

### Online flow

Repeat with an authenticated endpoint. The canonical grant, target validation,
local representation, consumer interface, and realization result should remain
equivalent; transport differences must not alter authority.

## Scenario matrix

### E-001: Exact consumer scoping

Attempt access from the intended unit, sibling root service, user service,
rootless container, VM, recovery environment, and installer.

Pass if the intended consumer works, ordinary isolation blocks unprivileged
siblings, privileged limits are documented honestly, and other boot modes do
not receive the credential without separate authorization.

### E-002: Host-bound local encryption

Create values using each viable systemd-creds mode. Copy storage, clear the
vTPM, remove/restore `/var/lib/systemd/credential.secret`, replace the disk, and
restore an old backup.

Pass if results match the declared protection/recovery class, failure is
diagnosable, and no ciphertext-only backup is called recoverable.

### E-003: Wrong scope and replay

Replay valid envelopes and grants against the wrong machine, old identity
epoch, wrong unit/name, incompatible contract, wrong boot mode, and after
expiry/revocation.

Pass if exact scope fails before plaintext exposure and each failure remains
distinguishable without revealing the value.

### E-004: Configuration smuggling

Supply unit text, shell code, a firewall fragment, executable data, template
expressions, consumer lists, and an overlarge value through nominal contracts.

Pass if semantic/schema bounds reject these or classify the result as a new
deployment or explicit override rather than an ordinary secret rotation.

### E-005: Restart-based rotation

Prepare instance B while A is active, establish peer overlap, restart or reload
the unit, verify B, retire A, and remove overlap. Interrupt at each boundary.

Pass if status never claims B before the consumer proves it, rollback or resume
is explicit, and A is not retired before a verified return path exists.

### E-006: Application-native renewal

Use a synthetic short-lived certificate or identity endpoint with a daemon that
can renew without restart. Disconnect the issuer before, during, and after
renewal.

Pass if the contract states cached validity and failure behavior, stale identity
is visible, and online renewal does not create broader local access than the
static systemd interface.

### E-007: Router offline operation

Disconnect WAN, DNS, trustworthy time, and credential authority separately and
together. Revoke the credential while the router is disconnected.

Pass if the router uses only locally valid instances within an accepted bound,
cannot claim knowledge of unseen revocation, gains no new scope, and reconciles
safely on reconnect.

### E-008: Enrollment and provisioning boundary

Deliver a bootstrap voucher, machine identity material, and a service credential
through the same physical transport. Replay it after provisioning completion.

Pass if the three classes retain distinct consumers/authority, bootstrap input
is inert, and enrollment alone does not grant service secrets.

### E-009: Recovery isolation

Boot normal, maintenance, and recovery environments with local credential
stores present. Request routine service credentials and one explicitly scoped
data-recovery capability.

Pass if recovery does not bulk-load normal secrets and only the separately
authorized capability transition releases the selected recovery input.

### E-010: Remanence

Use recognizable high-entropy canary values, then inspect journal, audit,
command line, environment, unit properties, process listings, coredumps, swap,
temporary/runtime paths, backups, support bundles, and returned media.

Pass if no unexpected plaintext or guessable derivative remains and every
intended retained envelope follows its declared custody and deletion policy.

### E-011: Clone, restore, and rollback

Clone a VM with active credentials, restore an old state backup after rotation,
and roll the OS deployment backward.

Pass if duplicate identity/currentness rules apply, revoked instances do not
become current, and OS rollback neither rewinds nor expands secret grants.

### E-012: Compromise traversal

Simulate compromise of one credential instance, machine, envelope recipient,
local broker, issuer, and administrative custodian.

Pass if each case identifies exact affected consumers and machines, avoids
automatic fleet-wide rotation where scope was narrower, and drives explicit
revocation, reissue, re-enrollment, or accepted risk.

## Mechanism matrix

Complete with measured results rather than architectural reputation:

| Measure | systemd-creds local | Offline envelope | Online service | Native identity API |
| --- | --- | --- | --- | --- |
| Components and privileged code | TBD | TBD | TBD | TBD |
| Authority/custody records | TBD | TBD | TBD | TBD |
| Owner steps per initial delivery | TBD | TBD | TBD | TBD |
| Owner steps per rotation | TBD | TBD | TBD | TBD |
| Network/time dependencies | TBD | TBD | TBD | TBD |
| Maximum offline operation | TBD | TBD | TBD | TBD |
| Hardware/disk replacement recovery | TBD | TBD | TBD | TBD |
| Plaintext lifetime and locations | TBD | TBD | TBD | TBD |
| Consumer integration work | TBD | TBD | TBD | TBD |
| Recurring upgrade/backup burden | TBD | TBD | TBD | TBD |

## Acceptance output

- literal contract and static-record examples;
- selected terminology and schema boundary;
- systemd unit examples using native credential directives;
- online/offline equivalent-flow comparison;
- recipient/key-capability decision inputs;
- rotation and offline-validity state machines;
- recovery and remanence results;
- measured operating cost; and
- proposed ADR only if evidence justifies concrete mechanism selection.
