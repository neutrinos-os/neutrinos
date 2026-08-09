---
id: PR-0006
subject: Authority and recovery policy
reviewer: Codex adversarial pass
date: 2026-08-09
status: accepted
---

# Authority and recovery policy review

## Scope of acceptance

This decision accepts the authority topology and recovery-policy boundaries in
[DES-0004](../../designs/0004-authority-and-recovery/README.md), records them in
[ADR-0002](../../adrs/0002-separate-authority-and-recovery.md), and ratifies
SYS-032 and SYS-033.

Acceptance does not select a token, key format, HSM, firmware key layout,
storage-encryption mechanism, recovery medium, out-of-band controller, or
freshness policy. It does not claim that the paper exercises are physical
implementation evidence.

## Accepted policy

- Every authority has a distinct logical scope and declares its custody,
  delegation, rotation, revocation, audit, loss, compromise, recovery or
  regeneration, and destruction behavior.
- Exceptional project, recovery, enrollment, and owner-platform authorities
  remain offline from routine release work.
- Normal-platform signing and release authorization may share correlated loss
  and replacement policy but not a runtime compromise compartment.
- Promotion authorizes the literal platform-signed and qualified artifact;
  platform-signed but unreleased candidates remain inventoried hazards.
- Data-recovery and machine authorities remain independent of OS selection and
  project signing.
- Recovery remains independently usable after normal-signer failure, is never
  an automatic fallback, and cannot silently produce normal-release status.
- Recovery boot authorization does not grant plaintext data, enrollment, or
  owner-platform authority. Normal automatic unlock is unavailable to generic
  recovery policy.
- Manual promotion, including urgent releases, is acceptable for the initial
  personal fleet.
- A secondary offline authority recovery copy or succession path outside the
  primary local-disaster and normal-account domains is required.

## Adversarial disposition

The owner reviewed the revised design after these paper exercises:

1. [EX-0001](../../research/exercises/0001-authority-loss-tabletop.md) tests
   authority loss, compromise, and terminal unrecoverable states.
2. [EX-0002](../../research/exercises/0002-promotion-substitution-tabletop.md)
   rejects one ordinary host with access to both routine signing operations.
3. [EX-0003](../../research/exercises/0003-recovery-capability-tabletop.md)
   separates recovery activation, data access, enrollment, platform repair, and
   return to normal service.

The remaining risks are accepted as validation work or follow-on decisions:

- concrete offline custody and retrieval remain unexercised;
- the two routine compartments and independent qualification-evidence path have
  not been selected or tested;
- malicious recovery code can steal deliberately exposed plaintext;
- router out-of-band recovery introduces a privileged management surface;
- the detailed recovery inventory needs a protection policy; and
- freshness, expiry, offline revocation, and anti-downgrade remain open under
  SYS-037.

These gaps prevent claims of implementation conformance, but they do not leave
the accepted authority boundaries ambiguous.

## Decision

Accepted by Jason Tarasovic on 2026-08-09. DES-0004 and ADR-0002 are accepted,
and SYS-032 and SYS-033 are normative project requirements.

Physical keys and storage locations must not be created as production
authorities until the disposable-key, custody, firmware, unlock, recovery, and
router out-of-band exercises named by DES-0004 have passed. SYS-035, SYS-036,
and SYS-037 remain candidate requirements for their own reviews.
