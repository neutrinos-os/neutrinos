---
id: ADR-0002
title: Separate routine, exceptional, machine, and data authorities
status: accepted
date: 2026-08-09
amended: 2026-08-11
deciders: [Jason Tarasovic]
designs: [DES-0004]
supersedes: []
superseded_by: []
---

# Separate routine, exceptional, machine, and data authorities

## Context

NeutrinOS must authorize normal releases, authenticate physical boot, recover
after signer loss or compromise, enroll machines, and unlock protected state.
One shared authority would make ordinary release compromise fleet-wide and
could also destroy the independent path needed to recover. Giving every logical
authority its own hardware, backup, and ceremony would be unreliable for the
initial single-maintainer personal fleet.

[DES-0004](../designs/0004-authority-and-recovery/README.md) and its three paper
exercises test a minimum model against authority loss, promotion substitution,
and abuse of privileged recovery. They do not select key-storage products,
cryptographic formats, firmware layouts, or recovery media.

## Decision

NeutrinOS separates these authority and recovery custody classes:

1. An offline authority and recovery set contains distinct project-root,
   recovery, enrollment, and owner-platform authorities.
2. Routine promotion custody contains distinct normal-platform and release-
   authorization keys. They may share an owner, location, replacement policy,
   and correlated loss event, but they must occupy separate runtime compromise
   compartments. No ordinary host or coordinator may invoke both.
3. Each machine has a separately scoped identity and, where applicable, a
   hardware-bound normal unlock credential.
4. Data-recovery secrets have an independent lifecycle and are not derived from
   any signing, platform, enrollment, or machine authority.
5. Measurement-policy authority is a distinct custody class. It signs predicted
   platform measurements so that a TPM will release a sealed secret, and it is
   therefore a data-unlock authority despite operating as a signing key. It
   occupies its own runtime compromise compartment, separate from
   release-authorization and normal-platform custody. No ordinary host,
   coordinator, or build environment may invoke both measurement-policy signing
   and release authorization. Its scope, rotation, revocation, and replacement
   are exercised as a distinct compromise scenario, not as a variant of routine
   signer compromise.

Amended 2026-08-11 to add class 5. The class did not previously exist because
the model was written before a signed-measurement mechanism was selected. See
[C-004](../designs/0006-storage-layout-and-encryption/review.md).

Routine promotion signs a platform artifact before qualification. Release
authorization independently validates an immutable bundle and names the exact
qualified artifact, role or channel, configuration compatibility, and policy
metadata. Platform-signed but unreleased candidates are hazardous intermediates
and must be inventoried.

At least one offline authority recovery copy or succession path must survive the
primary local disaster and normal online-account domains. Replaceable routine
keys do not require backups.

Recovery authorization is independent of normal release authorization and is
never an automatic failed-boot fallback. It does not itself authorize plaintext
data access, enrollment, owner-platform changes, or normal status. Hardware-
bound normal automatic unlock must not release its secret to generic recovery
policy. Sensitive recovery operations use separately scoped authorities, and a
machine returns to normal status only through the normal boot, release,
qualification, compatibility, and effective-state gates.

Manual routine and urgent promotion is accepted for the initial personal fleet.
Automation may assemble evidence but may not collapse the independent signing
compartments or authorize its own output.

## Alternatives considered

### One master authority

Rejected. Routine compromise could replace governance and recovery, enroll
machines, and potentially become an undocumented data-recovery path. Loss would
also end every authority at once.

### One ordinary promotion host with two keys or tokens

Rejected. A compromised coordinator can substitute bytes, misrepresent the
qualification record, and invoke both operations. Multiple prompts or key files
on the same compromised execution path do not form independent controls.

### One separately administered device per logical authority

Rejected as a general initial requirement. It creates more custody, backup,
rotation, and exercise work than the personal fleet is likely to perform
reliably. Separation is defined by permitted operations and compromise
boundaries, not device count alone.

### Recovery as automatic fallback

Rejected. Firmware acceptance of a recovery artifact cannot silently cross the
normal-to-recovery authorization boundary or trigger access to protected state.

### Online CI-held promotion authority

Rejected initially. A compromised build or CI environment must not be able to
sign and promote its own output.

## Consequences

### Benefits

- Loss or compromise of routine signing does not replace project governance,
  recovery, enrollment, or data authority.
- Routine keys can be replaced without maintaining private-key backups.
- Recovery remains usable after normal-signer failure without becoming a silent
  fleet release or data-unlock path.
- Machine identity and encrypted data remain independent of OS rollback and
  project signing.
- The model retains meaningful compromise boundaries without requiring one
  physical device per logical authority.

### Costs and constraints

- Even one maintainer must operate two independently enforced routine signing
  compartments, and a third for measurement-policy signing where sealed unlock
  is used. Because that key is produced during the same build that produces a
  UKI, keeping it out of the release-signing compartment is deliberate work
  rather than a default.
- Promotion requires literal-artifact qualification followed by independent
  release authorization.
- Offline custody needs an independently retained and exercised recovery copy
  or succession path.
- Recovery needs deliberate activation, scoped data unlock, quarantine and re-
  enrollment handling, and evidence independent of a failed target disk.
- Router recovery requires physical service or a separately secured out-of-band
  path when its normal data plane is unavailable.

### Accepted risks

- One maintainer remains a shared human decision and error domain.
- Malicious recovery code can steal any plaintext or credential deliberately
  supplied to it.
- Shared offline custody can correlate compromise of multiple exceptional
  authorities even though their keys and semantics remain distinct.
- Manual promotion may delay urgent updates until later evidence justifies safe
  automation.
- Disconnected machines cannot receive immediate signer revocation; freshness
  and offline exposure remain a separate decision under SYS-037.

## Validation and review triggers

Compliance requires the authority inventory and exercises specified by
DES-0004. Before production enrollment, disposable and physical tests must show
that one routine compartment cannot obtain both authorizations, recovery cannot
trigger normal automatic unlock or automatic selection, an offline copy can be
retrieved, and each authority can reach its declared loss or compromise state.

Revisit this decision when:

- the manual ceremony repeatedly delays normal or urgent maintenance;
- the selected mechanisms do not enforce the stated runtime compartments;
- a role cannot recover within its declared availability objective;
- threshold or independently staffed authorization becomes practical;
- an upstream signing, boot, or recovery mechanism materially changes the
  available compromise boundaries; or
- an exercise shows that shared custody or recovery capability exceeds the
  accepted blast radius.
