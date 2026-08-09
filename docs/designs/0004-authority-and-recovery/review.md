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
  authorities from routine signing; EX-0001 additionally requires an offline
  recovery copy outside the primary local and normal-account failure domains.
- Disposition: mitigated at the policy level; concrete custody and retrieval
  remain open.
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
- Author response: EX-0001 requires a locally usable primary and a secondary copy
  or succession path independent of the primary machine, local disaster, routine
  signer, normal online accounts, and primary unlock factor. The owner confirmed
  on 2026-08-09 that this is a required and feasible initial-fleet constraint.
- Disposition: mitigated at the policy level; a concrete construction and
  retrieval exercise remain open.
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
- Author response: the owner accepted manual promotion, including urgent
  releases, for the initial personal fleet on 2026-08-09. It is not declared
  permanently sufficient.
- Disposition: owner-choice objection resolved; timed normal and urgent
  promotion exercises remain implementation evidence.
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

1. **Complete:** the owner confirmed manual promotion for the initial fleet,
   including urgent releases, on 2026-08-09.
2. **Complete at policy level:** the design defines offline custody and recovery
   objectives without recording secret values or sensitive locations. A private
   custody worksheet and retrieval exercise remain implementation evidence.
3. **Complete on paper:** EX-0001 exercises loss and compromise of every custody
   class. Disposable-key and physical exercises remain implementation evidence.
4. **Complete for this design:** offline freshness is explicitly deferred to
   SYS-037 and must be resolved before that requirement is accepted.
5. **Open:** obtain independent human review and dispose of C-002 and C-003, the
   remaining critical design challenges.
