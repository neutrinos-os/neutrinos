---
design: DES-0004
reviewer: Codex adversarial pass
perspective: security, operations, failure, maintainability, alternatives
date: 2026-08-09
status: open
---

# Minimum viable authority and recovery model review

## Summary judgment

The proposal preserves the highest-value boundary—routine promotion cannot
replace governance or recovery—without demanding one device per logical key.
The strongest reason to reject it is that two maintainer custody domains still
hide a substantial manual ceremony and untested offline backup scheme; paper
separation provides no protection if the same workstation, location, or operator
mistake compromises every copy.

## Challenges

### C-001: Shared offline custody collapses exceptional authorities

- Severity: critical
- Claim: project root, recovery, enrollment, and firmware-owner keys sharing a
  custody domain can all be stolen, destroyed, or misused together.
- Failure or cost if true: one offline-set compromise can replace normal and
  recovery trust, enroll machines, and alter platform policy.
- Required response or experiment: document the physical copies, locations,
  unlock factors, use environment, and succession path; exercise loss of the
  primary copy without exposing the backup during routine use.
- Author response: co-location is accepted only to isolate all exceptional
  authorities from routine signing; distinct keys and scopes remain mandatory.
- Disposition: open.
- Residual risk: one maintainer remains a shared human failure domain.

### C-002: The promotion signer may still be a fleet-wide compromise

- Severity: critical
- Claim: co-locating release authorization and normal UKI signing lets one
  compromised promotion environment create a firmware-accepted and
  release-authorized malicious OS.
- Failure or cost if true: every online machine can install an attacker release
  before the offline root distributes revocation.
- Required response or experiment: require distinct key operations, literal
  qualification between platform signing and release authorization, narrow
  role/channel scope, auditable human confirmation, and an exercised emergency
  root revocation.
- Author response: the layout accepts the shared custody risk because release
  authorization already carries fleet-wide power, while preventing escalation
  to recovery, enrollment, and governance.
- Disposition: open pending ceremony and revocation exercise.
- Residual risk: human confirmation on a compromised workstation can approve a
  substituted digest.

### C-003: Recovery authorization is an intentional backdoor

- Severity: critical
- Claim: a recovery-signed environment with data and platform access can bypass
  normal qualification and mutable-state restrictions.
- Failure or cost if true: theft or abuse of offline recovery material defeats
  the controls it exists to repair.
- Required response or experiment: minimize recovery capabilities, avoid routine
  automatic selection, require deliberate activation, separate data unlock,
  preserve durable evidence, and test recovery-signer replacement.
- Author response: accepted as inherent; restricted status semantics prevent
  silent normal promotion but cannot make privileged recovery harmless.
- Disposition: open pending recovery design and exercise.
- Residual risk: router out-of-band recovery may weaken physical-presence
  expectations.

### C-004: Offline backups may be either unavailable or not offline

- Severity: critical
- Claim: a backup stored too remotely will not be exercised, while one stored
  too conveniently will share theft, malware, and operator-error exposure.
- Failure or cost if true: an emergency either becomes unrecoverable or reveals
  that both copies were compromised together.
- Required response or experiment: name acceptable recovery time, storage
  separation, verification interval, and a non-destructive backup-use exercise.
- Author response: the design requires independent copies but intentionally does
  not invent locations or products before owner review.
- Disposition: open.
- Residual risk: geographic and account independence may be disproportionate for
  a personal fleet.

### C-005: Manual promotion impedes urgent maintenance

- Severity: high
- Claim: connecting a promotion device, verifying evidence, signing a candidate,
  qualifying the changed bytes, and signing release authorization for every
  update will be skipped under time pressure.
- Failure or cost if true: security updates are delayed or emergency releases
  bypass qualification and audit.
- Required response or experiment: perform a timed tabletop promotion and urgent
  signer-rotation exercise; automate evidence assembly without giving CI signing
  authority.
- Author response: manual promotion is proposed for the initial personal fleet,
  not declared permanently sufficient.
- Disposition: open.
- Residual risk: a best-effort maintenance policy still creates pressure during
  active exploitation.

### C-006: Revocation cannot protect an offline machine promptly

- Severity: high
- Claim: a router or workstation that boots offline cannot learn that a signer
  or release was withdrawn.
- Failure or cost if true: it continues accepting an artifact authorized during
  the exposure window, or anti-downgrade state makes recovery unavailable.
- Required response or experiment: define the maximum offline window, retained
  policy epoch, boot behavior after expiry or clock failure, and recovery-only
  exception before accepting SYS-037.
- Author response: explicitly deferred; this design prevents dependency on an
  online check but does not yet bound offline exposure.
- Disposition: open.
- Residual risk: no mechanism can provide immediate revocation to a disconnected
  machine without a pre-existing local bound.

### C-007: Data-recovery inventory can become a secret map

- Severity: high
- Claim: identifiers, locations, copy counts, and exercise dates can tell an
  attacker where the most valuable recovery material exists.
- Failure or cost if true: otherwise secure offline secrets become easier to
  target or correlate with machines.
- Required response or experiment: separate operationally useful public status
  from sensitive custody metadata and test diagnostic exports for disclosure.
- Author response: ordinary status excludes sensitive storage locators; the
  detailed inventory itself still requires an owner and protection policy.
- Disposition: open.
- Residual risk: excessive secrecy can make the inventory unusable during an
  emergency.

## Missing alternatives or evidence

- Actual Secure Boot owner-key enrollment and recovery behavior on all targets.
- A timed end-to-end promotion using disposable keys and literal qualification.
- A concrete offline-copy storage and succession proposal.
- Recovery capability minimization for workstation-local and router out-of-band
  paths.
- Evidence that two custody domains are materially more operable than three.
- A freshness and policy-epoch design for offline machines.

## Required changes before acceptance

1. Confirm whether manual promotion is acceptable for the initial fleet.
2. Define custody and recovery objectives for the offline set without recording
   secret values or precise sensitive locations in public documentation.
3. Perform tabletop loss and compromise exercises for every custody class.
4. Resolve or explicitly defer the offline freshness questions before ratifying
   SYS-037.
5. Obtain independent human review and dispose of the remaining critical
   challenges.
