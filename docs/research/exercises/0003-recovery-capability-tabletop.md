---
id: EX-0003
title: Recovery capability and abuse tabletop
status: complete
date: 2026-08-09
exercise_type: tabletop
evidence_class: analysis-only
related_designs: [DES-0002, DES-0003, DES-0004]
---

# Recovery capability and abuse tabletop

## Purpose and evidence limit

This exercise tests C-003 from the DES-0004 adversarial review: whether an
independently authorized recovery environment becomes an easier path around
normal release, platform, enrollment, and data protections.

It is a paper exercise. It does not select recovery media, an unlock mechanism,
an out-of-band controller, a signature format, or an audit store. `Pass on
paper` means that authority and capability boundaries contain the stated abuse
without circular trust. It does not prove that firmware, storage encryption,
hardware-bound unlock, or a recovery implementation enforces those boundaries.

Recovery remains privileged by design. This exercise does not claim that code
which the owner deliberately authorizes and then gives plaintext can be made
harmless. It instead minimizes what possession of a recovery artifact or one
recovery authority grants before those additional decisions.

## Question and success condition

The question is not whether recovery can modify a machine; modification is its
purpose. The question is which additional authorities must be presented before
it can read protected state, restore identity, change platform trust, or return
the machine to normal service.

The minimum success condition is:

> Possession or compromise of a recovery artifact or recovery-signing authority
> alone must not provide automatic boot, plaintext data access, machine
> enrollment, platform-owner control, or normal-release status.

Denial of service by an attacker with prolonged physical control is outside this
guarantee. Protection against malicious firmware is also outside scope.

## Recovery authority is not data authority

The exercise separates capabilities that a generic “recovery mode” can easily
blur:

| Capability | Minimum additional authority | Resulting status |
| --- | --- | --- |
| Boot an immutable recovery environment | Recovery artifact authorization plus deliberate local or independently secured out-of-band activation | Explicitly recovery-only |
| Inspect public boot, release, policy, partition, and encrypted-container metadata | No data-unlock credential | Recovery-only; no confidentiality claim for deliberately public metadata |
| Export encrypted or deliberately redacted diagnostics | Explicit destination and export confirmation | Recovery-only; export is recorded |
| Replace release-owned partitions or reinstall a retained normal artifact | Destructive-operation confirmation and an already valid normal release authorization for installed bytes | Locally modified or quarantined until normal gates pass |
| Read or copy plaintext protected state | Separately presented data-recovery authority scoped to the selected state owner | Recovery-only and sensitive; no automatic normal transition |
| Preserve or restore mutable state | Ownership-aware preservation manifest and explicit selection after integrity classification | Quarantined until the relevant owner and compatibility checks pass |
| Generate and enroll a replacement machine identity | Enrollment authority through its independent ceremony | Re-enrolled; old identity remains revoked or lost |
| Change firmware trust or platform keys | Owner-controlled platform authority through its independent ceremony | Platform repair, not release promotion |
| Return to normal service | Valid normal platform artifact, release authorization, qualification and effective-state gates | Normal only after leaving recovery and booting the accepted normal path |

These are authorization transitions, not merely different buttons in one
interface. An implementation that silently loads every credential at recovery
startup has collapsed the boundaries even if its user interface presents the
steps separately.

## Minimum recovery profile

The retained recovery artifact may provide only the code needed to:

1. identify its literal artifact and authorization identities before sensitive
   input;
2. inspect public platform, release, storage-layout, and state-inventory
   metadata without mounting protected state as plaintext;
3. verify retained immutable artifacts and signed policy material;
4. copy encrypted data or explicitly redacted diagnostics to an owner-selected
   destination;
5. reinstall or replace release-owned content without treating mutable state as
   trusted;
6. request a separately scoped data-recovery credential only for an explicitly
   selected state operation;
7. consume narrowly scoped outputs from a separate enrollment or platform-owner
   ceremony without receiving those private authorities; and
8. emit a recovery-session record and finish in recovery-only, locally modified,
   quarantined, reset, or re-enrollment-required state.

It must not:

- be automatically selected by normal failed-boot logic merely because it is
  firmware-accepted;
- receive a hardware-bound normal automatic-unlock secret under the generic
  recovery boot policy;
- mount, execute, or restore mutable executable state by default;
- restore a withdrawn machine identity, administrator override, workload
  credential, or secret merely because it exists on disk or in backup;
- carry the project root, platform-owner, enrollment, or data-recovery private
  authorities inside the artifact;
- mint or claim normal release authorization;
- provide a permanently enabled remote shell or depend on the failed normal data
  plane; or
- erase the distinction between availability recovery and compromise recovery.

The normal automatic-unlock policy may satisfy a role's unattended reboot
objective, but it must be bound to the authenticated normal boot path. Recovery
uses an independent data-recovery credential. Otherwise, possession of a
recovery-signing key would become possession of every machine's plaintext.

## Activation and evidence

Normal boot selection must not fall through automatically to a recovery-signed
artifact. Activation requires a deliberate act tied to the target machine and
recovery identity:

- the workstation uses local owner presence and a trusted boot-selection or
  equivalent pre-boot action;
- the router uses physical service or an independently secured out-of-band path
  that remains separate from the normal router data plane; and
- an out-of-band request is authenticated, bounded to one recovery session, and
  does not expose a standing generic recovery shell.

Offline unattended *normal* router reboot does not imply unattended entry into
privileged recovery. If neither the independent out-of-band path nor physical
service is available, recovery waits rather than weakening its activation or
data-unlock policy.

Before accepting a data-recovery credential, the environment exposes its
literal identity, authorization, and recovery-only status through evidence the
ordinary mutable OS cannot rewrite. The exact independent display or
verification mechanism is deferred and must be physically tested. A label
rendered only after arbitrary recovery code runs is not by itself proof to the
operator that the intended artifact booted.

The session record includes the machine identity if available, recovery artifact
and authorization identities, activation path, reason, operations requested,
state scopes unlocked, artifacts installed, identities changed, result, and
remaining quarantine or re-enrollment obligations. It excludes secrets and
unnecessary plaintext metadata. The record is exported to operator-controlled
media or an independent out-of-band sink when local state is unavailable or
untrusted; a best-effort local copy alone is not durable evidence of compromise
recovery.

## Scenario results

### RCV-001: A retained recovery artifact is stolen

**Event:** An attacker obtains the exact bytes and public metadata of an
authorized recovery artifact but no private authority or target machine.

**Expected containment:**

1. Recovery bytes and public verification material are not treated as secrets.
2. The artifact supplies neither a data-unlock secret nor enrollment or
   platform-owner authority.
3. A target still requires deliberate activation and separately authorized
   state operations.

**Result:** Pass on paper. Confidentiality must not depend on hiding recovery
media.

### RCV-002: A recovery signer is compromised

**Event:** An attacker can authorize malicious recovery artifacts and may also
hold the recovery platform leaf, but not project-root, data-recovery,
enrollment, or platform-owner authorities.

**Expected containment:**

1. Recovery signatures cannot create normal release authorization.
2. Normal boot and hardware-bound automatic data unlock do not select or trust
   the recovery identity.
3. Remote possession of the signer does not activate recovery on a target.
4. Project-root and platform-owner authorities revoke and replace affected
   recovery leaves through a path that does not boot the compromised artifact.
5. Every machine with a recovery session in the exposure interval is inspected;
   data, machine, and workload credentials disclosed to those sessions are
   rotated according to scope.

**Result:** Pass on paper against remote signer-only compromise. A signer
attacker who also obtains activation and convinces the owner to provide a data
credential can gain the deliberately unlocked plaintext; this is an explicit
residual risk, not something signature separation can prevent.

### RCV-003: Normal failed-boot handling tries recovery automatically

**Event:** Repeated normal boot failures cause selection logic to choose any
firmware-accepted recovery artifact without an owner action.

**Expected containment:** The transition is rejected. Automated fallback may
select another qualified normal deployment, stop at a diagnosable state, or
request recovery activation, but it cannot cross from normal to recovery-only
authorization by itself.

**Result:** Fail for automatic recovery selection. Deliberate recovery remains
available offline.

### RCV-004: A physical attacker boots recovery to obtain data

**Event:** An attacker with temporary or prolonged physical control deliberately
boots an authorized recovery artifact and attempts to read protected state.

**Expected containment:**

1. Generic recovery policy does not release the normal hardware-bound automatic
   unlock secret.
2. The artifact can observe public metadata and destroy or copy ciphertext, but
   cannot obtain plaintext without the independent data-recovery authority.
3. Platform or enrollment changes require their independent authorities.

**Result:** Pass on paper for powered-off confidentiality under the declared
hardware and credential assumptions. Denial of service and malicious firmware
under prolonged control remain non-guarantees.

### RCV-005: A malicious recovery environment phishes the owner

**Event:** The owner deliberately activates attacker-authorized recovery code,
which imitates the expected interface and asks for a recovery credential.

**Expected containment:**

1. The owner verifies literal recovery identity and authorization using a path
   the recovery code cannot solely fabricate before entering the credential.
2. A credential is scoped to the selected state owner rather than the fleet or
   project.
3. Use of an identity from an exposed recovery interval triggers rotation or
   restore-from-backup treatment.

**Result:** Conditional. The authority model limits scope, but no paper policy
can protect plaintext voluntarily exposed to malicious privileged code. The
independent identity-verification UX and actual secret-unlock behavior require a
physical exercise.

### RCV-006: Recovery restores hostile mutable state

**Event:** A compromise-recovery session finds usable home, administrator,
workload, and machine state and restores it wholesale after reinstalling the OS.

**Expected containment:**

1. The default is no automatic mount, execution, or restoration.
2. The preservation manifest classifies each state owner and selects quarantine,
   selective restore, regeneration, re-enrollment, or destruction.
3. Machine identities and credentials are never resurrected by OS or filesystem
   rollback.
4. The machine remains quarantined until normal qualification, enrollment, and
   owner-specific checks succeed.

**Result:** Pass on paper under SYS-024, SYS-025, and accepted SYS-035. The
state-contract inventory and malicious-state exercise remain implementation
evidence.

### RCV-007: The retained recovery artifact is old or vulnerable

**Event:** The only locally retained artifact is bootable but has a known flaw,
withdrawn authority, or cannot interpret the current state schema.

**Expected containment:**

1. Retention, mechanical bootability, recovery authorization, vulnerability
   status, and state compatibility are reported separately.
2. When a newer independently obtained artifact is available, it is verified
   before the old artifact is used.
3. Exceptional use of the old artifact is deliberate, capability-minimized,
   recorded, and does not restore normal status.
4. If no safe operation is available, the procedure preserves ciphertext and
   stops rather than improvising plaintext access.

**Result:** Conditional. The status distinctions are coherent; expiry,
withdrawal, clock failure, and maximum offline exposure remain open under
SYS-037.

### RCV-008: The target disk cannot retain an audit record

**Event:** The disk is failed, untrusted, replaced, or about to be erased.

**Expected containment:**

1. Recovery does not depend on the target disk as its only evidence sink.
2. It produces a minimal session record for operator-controlled media or an
   independent out-of-band destination.
3. Failure to preserve evidence is reported before destructive action and
   requires an explicit exception if recovery must continue.

**Result:** Pass on paper. The record format, signing or attestation, redaction,
and storage mechanism remain unselected.

### RCV-009: Router data plane and normal administration are unavailable

**Event:** The router is headless, its WAN/LAN service path is broken, and normal
SSH is unavailable.

**Expected containment:**

1. Normal retained releases may still perform unattended offline boot under the
   router's role policy.
2. Privileged recovery requires physical service or the independent out-of-band
   path, not the failed data plane.
3. The action is one-session, attributable, and bound to the selected recovery
   identity.
4. Protected router state still requires its separate data-recovery authority.

**Result:** Conditional. This is a viable policy boundary, but the reference
router's actual out-of-band controller, isolation, credential custody, and
recovery UX require a threat review and physical test.

### RCV-010: Recovery tries to restore normal service directly

**Event:** After repair, the recovery environment changes a status flag or
continues running services and declares itself the current normal release.

**Expected containment:**

1. Recovery authorization has no semantic operation that mints normal release
   status.
2. Installed normal bytes retain their pre-existing literal release
   authorization; modified or newly assembled bytes do not inherit it.
3. Returning to normal requires leaving recovery and booting through the normal
   platform, release, qualification, compatibility, and effective-state gates.
4. Re-enrollment and quarantine obligations survive reboot as machine-owned
   state rather than being cleared by the recovery environment alone.

**Result:** Pass on paper if normal status is derived from independently
verified evidence rather than a mutable recovery-set flag.

## Findings and design consequences

1. **Recovery authorization is not data authorization.** This is the decisive
   containment boundary. Automatic unlock must bind to normal boot, not merely
   to any owner-trusted EFI signer.
2. **Recovery cannot be an automatic fallback class.** Failed-boot automation
   may fall back only among artifacts still authorized for normal selection.
3. **Capabilities are staged.** Public inspection and release-owned repair occur
   before explicit, scoped plaintext access; enrollment and platform repair use
   still other authorities.
4. **Recovery never blesses its own output.** A recovery session ends in an
   exceptional state until independently verified normal boot and applicable
   re-enrollment gates complete.
5. **Compromise recovery defaults to distrust.** Mutable executable state and
   identities are selected by owner-aware policy, not restored wholesale.
6. **Evidence needs an independent sink.** A broken or hostile target disk
   cannot be the only record of what recovery did.
7. **Router recovery is deliberate, not routinely unattended.** Offline
   unattended normal boot and an independently reachable recovery path are
   compatible only when the latter is separately authenticated and bounded.

These constraints resolve C-003 at the design-policy level. They do not accept
SYS-032, SYS-033, SYS-035, or SYS-037 and do not prove a conforming recovery
implementation.

## Required implementation evidence

Before physical production enrollment:

- verify that recovery signing cannot trigger normal hardware-bound automatic
  unlock on the workstation or router;
- demonstrate that failed-boot policy cannot automatically select recovery;
- boot a disposable recovery artifact and inspect public metadata without
  plaintext mounts or mutable-state execution;
- exercise scoped data unlock, selective preservation, reinstall, quarantine,
  re-enrollment, and return to independently verified normal boot using test
  data and disposable identities;
- replace a disposable compromised recovery signer without using an artifact it
  authorized;
- preserve and review a recovery-session record when the target disk is absent;
- verify recovery identity to the operator through the selected pre-unlock
  mechanism; and
- exercise router recovery with the normal data plane unavailable.

## Residual risks

- One maintainer still decides whether to trust and unlock through a recovery
  artifact.
- A malicious but valid recovery environment can steal any plaintext or secret
  deliberately exposed to it.
- The router's out-of-band controller may be a privileged networked attack
  surface with weaker maintenance than the main OS.
- A retained recovery artifact may age into a conflict between availability and
  known vulnerability.
- Recovery-session evidence may reveal machine, incident, or state-inventory
  information even when secret values are excluded.
- Firmware compromise and prolonged physical control can invalidate pre-boot
  identity and activation assumptions.
