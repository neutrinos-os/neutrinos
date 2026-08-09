---
design: DES-0003
reviewer: Codex adversarial pass
perspective: security, failure, operations, maintainability
date: 2026-08-09
status: open
---

# Initial threat and trust model review

## Summary judgment

The proposal correctly separates authorization, boot integrity, provenance,
qualification, and support. Its strongest reason for rejection is that the
boot-to-root and key-separation goals may force an experimental substrate and a
key ceremony whose operational risk exceeds the personal fleet's actual threat.

## Challenges

### C-001: Boot-to-root integrity may be a mechanism-driven requirement

- Severity: critical
- Claim: the project already prefers UKIs, verity, and DDIs, so the threat model
  may be reverse-engineered to require them without evidence of likely physical
  substitution attacks.
- Failure or cost if true: NeutrinOS rejects a stable bootc path, adopts an
  experimental backend, and assumes key-management burden for little practical
  risk reduction.
- Required response or experiment: the owner must explicitly accept temporary
  powered-off physical access as an in-scope threat and compare the claim's
  lifecycle cost on production-supported substrate paths.
- Author response: the claim is proposed, not accepted, and is called out as a
  substrate discriminator.
- Disposition: resolved as a requirement question. The owner accepted
  powered-off substitution as in scope and ratified SYS-030 through PR-0004.
- Residual risk: architectural taste can still dominate the likelihood and
  impact assessment when selecting the concrete mechanism.

### C-002: Authenticated immutable root leaves mutable persistence paths

- Severity: critical
- Claim: `/etc`, credentials, boot variables, firmware state, user services,
  extensions, containers, and workload data can all execute privileged or
  user-session code outside the authenticated release root.
- Failure or cost if true: the system reports boot integrity while attacker
  persistence remains active in mutable state.
- Required response or experiment: enumerate executable mutable inputs, include
  them in effective status and compromise recovery, and avoid claiming that
  authenticated root equals an uncompromised machine.
- Author response: the design limits the claim and treats executable mutable
  state as a separate trust surface; concrete enumeration remains open.
- Disposition: open.
- Residual risk: user-facing status may still compress nuance into a reassuring
  green indicator.

### C-003: Signing still trusts the build and inputs

- Severity: critical
- Claim: a compromised CI worker or authorized malicious upstream package can
  produce a correctly signed, boot-verified release.
- Failure or cost if true: cryptographic delivery controls legitimize the
  compromised artifact and make it uniformly deployable.
- Required response or experiment: define provenance, build isolation, input
  review, signer isolation, and qualification joins separately; exercise
  rebuild and withdrawal after build compromise.
- Author response: explicitly separated, with detailed build trust deferred to
  L-002.
- Disposition: mitigated; architecture remains open.
- Residual risk: the personal fleet may not support meaningfully independent
  build verification.

### C-004: Key separation may be inoperable for one maintainer

- Severity: critical
- Claim: root, release, recovery, platform, enrollment, machine, and encryption
  authorities create backup, rotation, expiry, and disaster-recovery work that
  will not be exercised reliably.
- Failure or cost if true: security machinery causes outages, stale keys, or
  unsafe emergency shortcuts.
- Required response or experiment: define logical scopes first, then minimize
  physical keys and ceremonies using a recoverability budget; exercise loss of
  each remaining authority.
- Author response: co-location is permitted after blast-radius analysis; the
  model explicitly rejects untested complexity.
- Disposition: open.
- Residual risk: co-location can collapse the intended separation in practice.

### C-005: Revocation and anti-downgrade can destroy recovery

- Severity: critical
- Claim: withdrawing old keys or releases can make the only bootable recovery
  environment unavailable when the network, clock, or online authority is also
  down.
- Failure or cost if true: an attempted security response bricks machines or
  strands encrypted data.
- Required response or experiment: test offline recovery after signer
  revocation and define recovery-only authorization separate from automatic
  normal boot.
- Author response: the design introduces normal, recovery-only, and withdrawn
  states and requires an independent recovery authority.
- Disposition: open pending implementation evidence.
- Residual risk: retained recovery artifacts may contain exploitable code.

### C-006: The recovery environment is a privileged backdoor

- Severity: critical
- Claim: an independently authorized recovery system that can preserve,
  decrypt, modify, or reset state can bypass normal release and enrollment
  policy.
- Failure or cost if true: compromise or theft of recovery material defeats the
  controls it exists to repair.
- Required response or experiment: minimize recovery capabilities, require
  explicit physical presence where appropriate, audit actions, protect keys
  independently, and test recovery compromise and replacement.
- Author response: retained as a required recovery-design constraint.
- Disposition: open.
- Residual risk: physical-presence requirements conflict with remote router
  recovery.

### C-007: Encryption policy can conflict with unattended availability

- Severity: high
- Claim: TPM-bound automatic unlock may add little protection against device
  theft, while manual recovery cannot satisfy unattended router reboot.
- Failure or cost if true: the design either overstates confidentiality or
  creates unacceptable outages.
- Required response or experiment: state the physical attacker and PCR/policy
  conditions precisely per role, then test hardware replacement, firmware
  update, TPM clear, and headless recovery.
- Author response: the design requires role-specific claims and does not mandate
  one unlock method.
- Disposition: open.
- Residual risk: convenience pressure can silently weaken the declared claim.

### C-008: Remote attestation is correctly deferred but may return by inertia

- Severity: medium
- Claim: vTPM availability and measurement terminology can lead to collecting
  attestations without a relying party or useful enforcement decision.
- Failure or cost if true: complex enrollment and privacy-sensitive telemetry
  are maintained without improving security.
- Required response or experiment: require a named verifier, decision, failure
  response, and threat before adding remote attestation.
- Author response: accepted as a continuing non-goal and review gate.
- Disposition: resolved for the initial phase.
- Residual risk: local key sealing can still accrete attestation-like policy.

## Missing alternatives or evidence

- Actual workstation and router firmware, Secure Boot, TPM, and recovery
  capabilities.
- Lifecycle cost of boot-to-root integrity on production bootc versus a direct
  systemd/UAPI path.
- A minimal personal-fleet key ceremony and disaster-recovery exercise.
- Inventory of mutable executable inputs outside the release root.
- Quantified powered-off theft, temporary-access, and router availability
  assumptions.

## Required changes before acceptance

1. Define a minimum viable physical key layout and recovery exercise.
2. Record role-specific confidentiality and unattended-recovery objectives.
3. Trace accepted trust requirements into the substrate comparison.
4. Obtain independent human review and dispose of all remaining critical
   challenges.

## Owner direction

Jason Tarasovic accepted powered-off substitution as an in-scope threat and
ratified SYS-030 on 2026-08-09 through
[PR-0004](../../project/reviews/0004-boot-to-root-integrity.md). This resolves
whether the project wants the claim; it does not establish that either substrate
implements it through a production-supported path.
