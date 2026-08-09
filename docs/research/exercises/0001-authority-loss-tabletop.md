---
id: EX-0001
title: Authority loss and compromise tabletop
status: complete
date: 2026-08-09
exercise_type: tabletop
evidence_class: analysis-only
related_designs: [DES-0003, DES-0004]
---

# Authority loss and compromise tabletop

## Purpose and evidence limit

This exercise tests whether the custody layout in DES-0004 has a coherent
response to loss, compromise, outage, and operator error before products or
cryptographic formats are selected.

This is a paper exercise. `Pass on paper` means that the proposed authorities
and retained inputs can reach a defined state without circular trust. It does
not prove that firmware, tokens, TPMs, recovery media, or procedures work. A
scenario requiring unselected or untested implementation is marked conditional.

No secret values, precise storage locations, accounts, or recovery factors are
recorded here.

## Starting state

The exercise assumes:

- a currently bootable normal release and one previous deployment are retained;
- a separately authorized recovery artifact is available but not automatically
  selected;
- firmware trusts distinct normal and recovery boot leaves under owner control;
- project-root, recovery, enrollment, and firmware-owner keys are distinct but
  held in the offline custody class;
- release-authorization and normal-platform keys are distinct but held by the
  routine promotion custody class;
- machine identities are scoped per machine;
- protected state has an independent per-machine or per-owner recovery secret;
  and
- public delegations, revocations, artifact identities, and audit evidence are
  available without private keys.

These are design preconditions, not observations of the current hosts.

## Custody objectives used by the exercise

### Offline authority and recovery set

The primary offline set is available for planned local ceremonies. At least one
secondary recovery copy or pre-authorized succession path must:

- survive loss of the primary workstation and its storage;
- survive a local physical disaster affecting the primary set;
- be usable without the routine promotion signer;
- be usable without the normal Git hosting, password-manager, or identity-
  provider account;
- require an independently retained unlock factor; and
- be verifiable non-destructively on a scheduled basis.

The secondary copy may take longer to retrieve than the primary because
existing qualified machines can continue running. No fixed recovery time is
claimed during the personal-fleet phase; retrieval must nevertheless be part of
the emergency runbook rather than an improvised search.

### Routine promotion signer

The routine promotion private keys do not require backup. If lost, the offline
project root delegates new release-authorization keys and the owner-controlled
platform authority enrolls or authorizes a new normal boot leaf. Avoiding backup
copies reduces ordinary exposure.

The promotion environment may cache public metadata and unsigned candidates,
but reconstruction of those inputs must not reconstruct the private keys.

### Data-recovery vault

Every data-recovery secret has at least two recoverable copies whose loss does
not correlate with the same device, local physical event, or normal online
account. Data recovery remains cryptographically and operationally separate
from project signing and enrollment even when sealed containers share physical
storage.

The inventory exposed to ordinary status records only an opaque identifier,
scope, and verification state. Exact custody details belong to a separately
protected operator record.

### Recovery artifacts

At least one recovery artifact and its public verification material remain
available without the normal publication service. A retained copy must be
bootable through a deliberate local or independently secured out-of-band path.
Possession of the artifact alone does not provide a data-unlock secret.

## Scenario results

### T-001: Routine promotion device is lost

**Event:** The device holding both distinct routine keys is destroyed. There is
no evidence of compromise.

**Expected response:**

1. Existing releases continue to boot; loss of a signer does not invalidate
   already installed bytes by itself.
2. The offline root delegates a new release signer.
3. The owner-controlled platform authority authorizes a new normal boot leaf.
4. A candidate signed by the new platform leaf is qualified as literal bytes.
5. The new release signer authorizes that qualified identity.
6. Old routine keys are marked retired or lost and are no longer accepted for
   new authorization.

**Result:** Pass on paper. No routine-key backup is required. Firmware enrollment
and delegation formats remain implementation dependencies.

### T-002: Routine promotion device is compromised

**Event:** An attacker may have used both routine keys during an uncertain
interval.

**Expected response:**

1. Pause publication and normal rollout.
2. Use the offline root and platform-owner authorities to revoke and replace
   both routine keys.
3. Bound the possible exposure interval using signing and publication evidence.
4. Classify every release authorization and boot artifact in that interval as
   known-good, withdrawn, recovery-only, or unknown pending investigation.
5. Distribute newer signed policy through normal update or deliberate recovery.
6. Rebuild and requalify rather than treating a new signature on old source as
   sufficient evidence.

**Result:** Conditional. Authority recovery is coherent, but disconnected
machines cannot learn revocation immediately. The maximum offline exposure and
policy-epoch behavior remain open under SYS-037.

### T-003: Primary offline set is lost

**Event:** The primary offline device and its local unlock material are
destroyed without suspected theft.

**Expected response:**

1. Continue running existing qualified releases while normal keys remain
   trustworthy.
2. Retrieve the independently stored recovery copy or activate the
   pre-authorized succession path.
3. Verify its public identities before using private operations.
4. Replace the lost offline credentials where the design permits rotation.
5. Recreate and verify a new independent recovery copy before retiring the
   recovered one.

**Result:** Pass on paper only if the independent-copy objective is met. A local
backup attached to the primary workstation fails this scenario.

### T-004: All project-root recovery copies are lost

**Event:** No project-root private key or authorized successor remains.

**Expected response:**

1. Existing machines may continue booting already authorized releases while
   their retained policy permits it.
2. No new authority is falsely presented as a continuation of the old project
   trust lineage.
3. Owner-controlled firmware reset and platform re-enrollment establish a new
   lineage through a visible reprovisioning or recovery event.
4. Machine identities are re-enrolled, and affected release/status history
   records the trust discontinuity.
5. Data is restored only through independently retained data-recovery secrets or
   backup.

**Result:** Pass on paper as an explicitly destructive trust reset, not as
continuity. Data remains recoverable only because its authority is separate.

### T-005: Recovery signer or recovery artifact is compromised

**Event:** A recovery private key is exposed, or a retained recovery artifact is
found to contain exploitable or malicious code.

**Expected response:**

1. Prevent automatic or casual use of affected recovery artifacts.
2. Use the project root and platform-owner authority to revoke and replace the
   affected recovery leaves.
3. Build and qualify a replacement recovery artifact through a path that does
   not trust the compromised artifact.
4. Inspect machines on which the recovery path was used and rotate machine and
   workload credentials as indicated.
5. Keep recovery boots visibly distinct; never reclassify the affected artifact
   as normal solely because it still boots.

**Result:** Conditional. Logical replacement works, but the proposal still needs
a minimal recovery capability design and proof that normal boot cannot select a
recovery artifact automatically.

### T-006: TPM is cleared or a mainboard is replaced

**Event:** Hardware-bound machine identity and automatic storage unlock stop
working after legitimate maintenance or hardware failure.

**Expected response:**

1. The machine refuses automatic unlock rather than silently weakening policy.
2. The owner supplies the independent data-recovery secret through the declared
   recovery path.
3. Old machine identity is revoked or marked lost.
4. New hardware generates a new identity and is enrolled through the enrollment
   authority.
5. Storage is rebound to the new qualified hardware policy only after data and
   machine state are inspected.

**Result:** Pass on paper. Actual TPM behavior, firmware updates, mainboard
replacement, and headless recovery must be physically exercised.

### T-007: One machine identity is compromised

**Event:** The router or workstation identity is copied or misused, while
project signing authorities remain trustworthy.

**Expected response:**

1. Revoke only the affected machine identity and any secrets scoped to it.
2. Leave other machine identities and release authorizations valid.
3. Recover or reprovision the machine without trusting its normal mutable state.
4. Generate a new identity and re-enroll it.
5. Verify that booting an old OS deployment does not restore the revoked
   identity or secret-delivery eligibility.

**Result:** Pass on paper and directly supports SYS-025. Concrete enrollment and
secret-delivery mechanisms remain open.

### T-008: All unlock and recovery copies for one state owner are lost

**Event:** Hardware-bound unlock is unavailable and every independent recovery
copy for one encrypted state scope is gone.

**Expected response:**

1. Report the state as cryptographically unrecoverable.
2. Do not use project-root, release, recovery-signing, or enrollment keys as an
   undocumented master decryption path.
3. Reconstruct only release-owned content, configuration inputs, and state
   explicitly covered by a separate backup.
4. Reset and re-enroll the affected machine or state owner.

**Result:** Pass on paper because the terminal state is honest and bounded. This
is intentional data loss, not successful recovery.

### T-009: Network and normal infrastructure are unavailable

**Event:** WAN, public DNS, registry, Git hosting, normal SSH, and the routine
signer are unavailable simultaneously.

**Expected response:**

1. A retained authorized release boots without an online freshness check.
2. The router returns to service after an expected reboot without depending on
   its own data plane.
3. Deliberate recovery uses locally retained public trust material and an
   available recovery artifact.
4. Exceptional recovery is recorded and does not silently claim current normal
   status.

**Result:** Conditional. The direction is coherent, but expiry, clock failure,
anti-downgrade, and the router's out-of-band path are unresolved.

### T-010: An urgent security release is required

**Event:** Active exploitation requires an expedited release while broad
qualification time is constrained.

**Expected response:**

1. Automated tooling assembles pinned inputs, candidate identities, provenance,
   and the minimum emergency test evidence.
2. The maintainer invokes the platform signing operation before literal
   qualification.
3. The signed candidate passes the accepted minimum emergency gate.
4. The maintainer separately authorizes the exact qualified identity as a
   release.
5. Skipped non-critical tests and the planned follow-up remain visible.

**Result:** Pass on paper if manual promotion is accepted for the initial fleet.
The ceremony adds two deliberate owner operations but does not require the
offline root during a normal emergency release.

## Cross-scenario findings

1. **Routine private-key backup is unnecessary and undesirable.** Exceptional
   authority can replace routine keys, so additional routine copies only expand
   exposure.
2. **Data recovery is the irreducible backup obligation.** Signing recovery
   cannot decrypt data and must not become a hidden master key.
3. **The offline set needs disaster and account independence.** Merely labeling
   a file offline does not satisfy T-003.
4. **Recovery artifact availability and recovery authorization are separate.**
   An artifact may be copied widely if its activation and data access remain
   separately controlled.
5. **The logical model survives total root loss only through visible trust
   reset.** It cannot promise continuity without a surviving root or successor.
6. **SYS-037 remains the largest policy gap.** Offline revocation, expiry, clock
   failure, and anti-downgrade must be resolved together.
7. **Manual promotion is viable on paper but needs owner acceptance and a timed
   exercise.** Automation should assemble and verify evidence without holding
   promotion keys.

## Follow-up gates

- Owner confirmation that manual promotion is acceptable for the personal-fleet
  phase.
- Owner confirmation that an offline backup outside the primary local and
  normal-account failure domains is feasible.
- A private custody worksheet naming actual copies, access factors, and
  retrieval procedure without committing sensitive details publicly.
- A timed disposable-key promotion and replacement exercise once implementation
  work begins.
- Physical Secure Boot, TPM-loss, and recovery-boot exercises on the reference
  VM before either production host.
- A freshness and downgrade design before SYS-037 is considered for acceptance.

## Conclusion

DES-0004 is internally recoverable on paper and reduces the initial custody
problem to two maintainer decisions: accepting manual promotion and providing
one genuinely independent offline recovery domain. It is not yet operational
and does not justify creating production keys.
