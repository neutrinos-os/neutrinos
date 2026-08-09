---
id: PR-0005
subject: Role security and availability objectives
reviewer: Codex adversarial pass
date: 2026-08-09
status: proposed
---

# Role security and availability objectives review

## Decision scope

This review proposes the role-level policy needed to evaluate storage,
encryption, unlock, and recovery designs. It would ratify SYS-027 and SYS-034,
but it does not select a partition layout, encryption format, TPM policy,
recovery medium, or boot/update substrate.

The first production roles are the workstation on `desktop-jason` and the
router on `router`. The separate `misc` server remains inventory evidence for a
future role and does not expand the initial qualification gate.

## Common policy

Every security claim must name the protected data, relevant attacker,
assumptions, guarantee, exclusions, and compromise-recovery response for the
applicable role. A mechanism's presence is not itself a security claim.

SYS-030 boot-to-root integrity does not require a TPM. Owner-controlled UEFI
Secure Boot and authenticated release-owned root content may establish that
claim without one. A TPM can additionally protect an unattended storage-unlock
secret, record measurements, or support machine identity, but those are
separate claims with separate recovery behavior.

Normal unattended boot means that a previously enrolled, healthy machine can
return to its normal production state after an expected reboot or power loss
without a person entering a storage secret. It does not mean that recovery,
firmware replacement, trust-anchor replacement, TPM clearing, or suspected
compromise must be unattended.

An unattended unlock claim is acceptable only when the release authorization
and measured or authenticated boot policy prevent an arbitrary substituted OS
from obtaining the same secret under the configured platform-trust assumption.
The resulting claim is protection against offline extraction and boot-path
substitution, not protection against a compromised authorized release,
firmware, running kernel, or authenticated user session.

Every hardware-bound unlock path must have an independently retained recovery
secret or restoration path. Loss or clearing of a TPM, firmware-policy change,
mainboard replacement, or failed policy update may require deliberate recovery
but must not silently destroy the only copy of protected data.

## Workstation objective

### Protected state

The workstation must protect the confidentiality of the following data while
the machine is powered off and not in an authorized session:

- user home and user-managed application state;
- workload, VM, and container state unless explicitly classified as public or
  reconstructible;
- machine credentials, enrollment material, and locally retained recovery
  material;
- swap, hibernation state if supported, and temporary data that can contain the
  same plaintext; and
- administrator-maintained secrets and sensitive persistent diagnostics.

Signed public release artifacts and explicitly classified reconstructible
caches need integrity and ownership rules but do not require confidentiality.
This is a data-classification boundary, not a decision to use one encrypted
volume.

### Availability and unlock

The workstation should support normal unattended reboot so that qualified
updates, rollback, and recovery from transient boot failure do not ordinarily
stop at a local passphrase prompt. Interactive unlock remains a supported
policy choice when the owner prefers its stronger physical-presence property.

TPM-assisted unlock is permitted, not mandatory. If used, it must be bound to
the accepted normal boot policy, expose why automatic unlock was refused, and
fall back to deliberate local recovery. Authentication at the login/session
boundary remains necessary; automatic storage unlock must not be described as
protecting data from an attacker who can compromise an authorized running OS.

The minimum recovery exercise must cover a firmware update, changed Secure Boot
state, TPM clear or loss, mainboard replacement, damaged normal boot artifact,
and loss of the routine unlock method.

## Router objective

### Protected state

The router must protect long-lived administration, VPN, service, enrollment,
and machine-identity credentials against offline extraction after powered-off
loss or temporary physical access. Public configuration and reconstructible OS
content need integrity but not confidentiality. Logs and network metadata must
be classified by sensitivity and retention rather than assumed public.

A lost router is treated as a credential-compromise event until its identities
have been revoked or rotated. Encryption reduces extraction risk but does not
replace rapid revocation, narrowly scoped credentials, or re-enrollment.

### Availability and unlock

Every expected router reboot, including an update reboot and return of power,
must be unattended. Normal boot and rollback must not require WAN, public DNS,
the routed data plane, or an online NeutrinOS service. A separately managed
out-of-band path may assist recovery, but normal availability must not depend on
the router already providing the service required to unlock itself.

The current router has no TPM exposed to Linux. Manufacturer documentation
identifies compatible discrete TPM 2.0 modules, but the design must treat that
capability as absent until a module is installed and exercised. Satisfying both
offline unattended boot and powered-off credential confidentiality requires a
proven hardware-bound secret facility or a comparably explicit physical trust
mechanism. If no such mechanism is qualified, the router may be a development
target but does not meet this production confidentiality objective.

Router recovery must work after WAN and normal SSH loss. A person or
independently secured out-of-band console may supply recovery authorization;
that exceptional path must be visible, must not silently restore withdrawn
credentials, and need not preserve normal service availability.

## Future server objective

`misc` does not yet establish a generic server policy. Its documented Intel PTT
support is useful future evidence, but the project will declare server data,
availability, physical-access, and recovery objectives when that role enters
scope. It must not inherit workstation or router claims by accident.

## Adversarial challenges and guardrails

### C-001: Automatic unlock can overstate theft protection

- Severity: critical
- Claim: a stolen machine that automatically decrypts itself appears to defeat
  full-disk encryption.
- Disposition: the permitted claim is narrower. Hardware-bound unlock protects
  against offline extraction and unauthorized boot substitution under the
  platform assumption. Session authentication, service hardening, external-port
  policy, and timely credential revocation still protect the running machine.
- Residual risk: a vulnerability in the authorized pre-login system may expose
  decrypted data.

### C-002: Firmware or TPM changes can strand encrypted data

- Severity: critical
- Claim: ordinary firmware maintenance, Secure Boot key changes, TPM clearing,
  or mainboard failure can invalidate sealed secrets.
- Disposition: hardware-bound unlock is prohibited as the only recovery path;
  the listed failure cases become mandatory exercises.
- Residual risk: independently retained recovery material creates its own theft,
  loss, rotation, and testing burden, to be resolved under S-006.

### C-003: Router policy creates an undeclared hardware prerequisite

- Severity: critical
- Claim: confidentiality plus offline unattended reboot cannot be honestly
  delivered on the observed router merely through software configuration.
- Disposition: accepted. A compatible TPM or alternative hardware-bound secret
  mechanism must be acquired and qualified before making the production claim;
  development may continue without it.
- Residual risk: module compatibility documentation does not prove firmware,
  Linux, PCR-policy, or physical-clearance behavior on this machine.

### C-004: Recovery becomes a bypass around normal authorization

- Severity: critical
- Claim: a recovery key or console that decrypts state can defeat boot and
  enrollment controls.
- Disposition: recovery must require deliberate owner or independently secured
  out-of-band action, be separately authorized, leave durable evidence, and
  trigger support-status and credential-rotation decisions.
- Residual risk: the physical storage and use ceremony remains open under
  S-006.

### C-005: Encrypting everything impairs diagnosis and rebuild

- Severity: high
- Claim: treating all bytes as secret complicates remote recovery, diagnostic
  preservation, and reconstruction without protecting meaningful assets.
- Disposition: the policy classifies data by content and owner instead of
  mandating a single encrypted volume. Public release artifacts and explicitly
  reconstructible caches may remain unencrypted.
- Residual risk: later state contracts must prevent sensitive values from
  leaking into nominally public caches or diagnostics.

### C-006: A TPM becomes a lowest-common-denominator architecture

- Severity: high
- Claim: requiring every role and VM to expose identical TPM behavior could
  distort otherwise portable lifecycle design.
- Disposition: a TPM is not a common boot-integrity prerequisite. Each role
  qualifies the specific hardware-backed function needed for its security and
  availability claim, while retaining non-TPM recovery.
- Residual risk: role-specific unlock methods increase the qualification
  matrix.

## Proposed decision

Accept the common, workstation, router, and future-server objectives above and
ratify SYS-027 and SYS-034. Acceptance would establish the claims and test
boundaries while leaving physical key layout, recovery authorization, concrete
storage design, and TPM acquisition as later decisions.

Acceptance would also resolve DES-0003 review challenge C-007 at the requirement
level. It would not resolve implementation evidence for unattended boot,
hardware loss, offline recovery, or credential revocation.
