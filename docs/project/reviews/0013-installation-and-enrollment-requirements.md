---
id: PR-0013
subject: Installation, provisioning, and enrollment requirements
reviewer: Codex adversarial pass
date: 2026-08-10
status: accepted
---

# Installation, provisioning, and enrollment requirements review

## Decision scope

This review asks whether SYS-086 through SYS-097 should become normative before
NeutrinOS selects an installer, provisioning transport, first-boot utility,
machine-key representation, enrollment protocol, authority service, or token
format.

It reviews DES-0010 and proposed EX-0012. It does not accept
systemd-sysinstall, a custom wrapper, Ignition, cloud-init, bootc install, TPM
attestation, or an online enrollment service merely because one is a candidate.

## Summary judgment

The requirements should be accepted. They resolve the first-enrollment circle
without trusting mutable platform metadata, and they constrain an installer's
destructive and configuration authority before implementation convenience
becomes architecture.

The strongest objection is excessive machinery. Acceptance is justified only
because the requirements allow an attended offline ceremony and reuse of
upstream tools; they do not require a permanent provisioning or identity
service.

## Accepted requirement disposition

### SYS-086: Provisioning intent is exact and bounded

Every provisioning operation has authenticated, versioned intent binding its
operation type, machine record and inventory revision, installer policy,
platform and disk constraints, installable deployment scope, preservation,
required ceremonies, enrollment authorization, network policy, validity,
completion, and abort behavior. Bootstrap hints only locate candidate intent.

### SYS-087: Destructive action requires owner-aware preflight

Before storage or firmware mutation, the system resolves and displays the exact
target and topology, proposed changes, erase/preserve behavior, capacity,
backup/restore evidence, irreversible boundaries, and compromise policy. A
generic confirmation or a signed plan cannot make an ambiguously selected disk
safe.

### SYS-088: Installer capability and trust are separate

The exact installer environment and tool closure are authenticated and
reported. They carry no long-lived release, recovery, enrollment, platform-
owner, or data-recovery private authority. Booting an installer does not grant
permission to decrypt state, enroll trust, or bind identity.

### SYS-089: Provisioning is an interruption-safe transaction

Every phase and completed irreversible action is durable and attributable.
After interruption, retry must prove idempotence, reverse safely, or require a
deliberate restart/recovery. Partial storage, identity, or approval state cannot
become a normal machine.

### SYS-090: Installation consumes exact deployment sets

Installation consumes a previously built, qualified, and authorized deployment
set, verifies final target bytes and the complete closure, and makes the final
boot-selection entry point visible last. It cannot install packages or render
normal role configuration on the target.

### SYS-091: Authority ceremonies remain independent

Platform trust, data unlock/recovery, machine enrollment, normal release use,
and recovery activation each require their own accepted authority and return
path even if coordinated in one attended session. No shared token, seed, or
confirmation silently grants all of them.

### SYS-092: Machine identity has explicit key and clone semantics

A new identity key is generated locally with proof of possession. Exportability,
hardware/vTPM protection, attestation, custody, rotation, loss, clone,
replacement, and destruction are explicit. Names, SMBIOS, MACs, TPM facts, and
`/etc/machine-id` cannot substitute for the enrollment identity or overstate its
assurance.

### SYS-093: Enrollment approval binds one request and epoch

A first-enrollment voucher is single-use in authority effect and tightly scoped
to one operation and record. Approval binds an exact fresh request, public key,
proof, nonce, record, and identity epoch after independent confirmation. Races,
duplicates, expiry, and revocation fail visibly rather than using first-writer-
wins.

### SYS-094: Provisioning inputs become inert

Seed media, metadata, SMBIOS, fw_cfg, kernel arguments, URLs, Ignition,
cloud-init, and installer credentials have explicit authentication, sensitivity,
retention, deletion, and completion behavior. Reappearance or changed instance
identity after completion cannot rerun destructive work or change role,
identity, preserved state, or selected deployment.

### SYS-095: First boot is a bounded handoff

First boot may initialize machine-local identifiers, consume allowed one-time
credentials, prove identity/state access, verify binding and deployment, and
complete trial assessment. It cannot inject ordinary release-owned users,
services, network policy, executable configuration, or package changes outside
an accepted identity-bound or late-bound contract.

### SYS-096: Reinstall and reset name every lifecycle consequence

Reinstall, disk replacement, identity rotation, reprovision, factory reset, and
compromise recovery each state which identity, enrollment, platform, unlock,
machine, administrator, user, workload, diagnostic, and recovery objects are
preserved, rotated, revoked, quarantined, restored, or destroyed. Restoring or
rolling back state cannot resurrect a revoked identity.

### SYS-097: Provisioning remains diagnosable and offline-capable

Provisioning and enrollment retain attributable, secret-redacted evidence and
native diagnostics sufficient to reconstruct input, target, actions, outputs,
binding, failure, and remaining recovery. New enrollment may use online or
offline exchange, while ordinary retained boot and recovery do not depend on
the enrollment or provisioning service.

## Guardrails from adversarial review

### Do not make physical presence magical

Presence helps authorize destructive local action but does not prove request
bytes, machine identity, or safe installer code. Independent verification still
matters.

### Do not make the voucher the identity

The voucher permits one proposal. Only authority approval of a fresh proof-of-
possession request creates the binding.

### Do not use first boot as a configuration escape hatch

Generic image convenience cannot override the accepted identity-bound normal
configuration model.

### Do not equate TPM with the machine record

TPM-backed keys can improve custody and claims. Inventory and owner authority
still decide which record the machine occupies.

### Do not restore identity as ordinary backup data

Identity material has a revocation and epoch lifecycle. Restoring bytes is not
authority to reuse them.

## Strongest rejected alternatives

### Trust SMBIOS or cloud instance identity

Rejected. These are useful lookup/compatibility observations and are routinely
copyable or provider-controlled.

### Use one fleet bootstrap secret

Rejected. Theft authorizes arbitrary machines and makes rotation affect the
whole fleet.

### Let installer success mean enrollment success

Rejected. Authentic OS bytes can be installed on the wrong machine or without
an approved identity binding.

### Preserve the existing root and decide later

Rejected. It mixes release-owned and mutable state, defeats exact identity, and
can preserve compromise.

### Require a live enrollment service for boot

Rejected. It violates the router's offline availability and makes authority
outage a fleet outage.

## Required implementation evidence

Acceptance establishes policy only. DES-0010 still requires:

1. concrete provisioning intent, request, approval, binding, and completion
   records;
2. online and removable offline enrollment;
3. independent request verification;
4. exact systemd-sysinstall/direct-tool mapping;
5. target-device and power-loss failure injection;
6. exact final deployment verification;
7. TPM/vTPM/software-key and clone cases;
8. hostile bootstrap, voucher, metadata, and provisioning replay;
9. platform and data-recovery ceremony ordering;
10. owner-aware preservation and hostile-state handling;
11. reinstall, replacement, rotation, reset, and compromise recovery; and
12. measured installer/adapter and owner cost.

## Decision

Accepted by Jason Tarasovic on 2026-08-10. SYS-086 through SYS-097 are
normative policy boundaries. DES-0010 remains in review until its required
implementation evidence resolves the installer, enrollment protocol, record
formats, and operating cost.
