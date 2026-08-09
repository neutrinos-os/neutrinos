---
id: DES-0004
title: Minimum viable authority and recovery model
status: in-review
owners: []
reviewers: []
created: 2026-08-09
last_updated: 2026-08-09
depends_on: [DES-0002, DES-0003]
decision_backlog: [S-006]
related_adrs: []
---

# Minimum viable authority and recovery model

## Problem

DES-0003 separates project-root, release, recovery, platform, enrollment,
machine, and data-encryption authorities logically. Giving every authority its
own device and ceremony would be inoperable for one maintainer. Collapsing them
into one key would allow a routine signing compromise to authorize releases,
replace recovery, enroll machines, and potentially strand encrypted data.

This design proposes the smallest custody model that preserves useful failure
boundaries and defines what happens when each authority is lost or compromised.

## Goals

- Keep routine release work independent of offline governance and recovery.
- Make normal release-signer loss or compromise recoverable.
- Keep recovery usable without silently granting normal-release authority.
- Make Secure Boot owner control and recovery compatible with SYS-030.
- Keep machine identity and data recovery independent of OS rollback.
- Produce a ceremony that one maintainer can exercise and audit.

## Non-goals

- Select a hardware token, password manager, HSM, signature format, PKI, or
  threshold-signature scheme.
- Provide unattended CI promotion or enterprise signing availability.
- Make recovery safe against malicious firmware or prolonged physical control.
- Use one project key to encrypt fleet or user data.
- Finalize release freshness, anti-downgrade counters, or offline expiry windows.

## Requirements and constraints

Accepted SYS-025 requires machine identity and secret lifecycles to remain
independent of OS selection. Accepted SYS-027 and SYS-030 require scoped claims
and an authenticated release-owned boot-to-root path. Accepted SYS-034 requires
workstation and router unlock and recovery to match their declared availability
objectives.

SYS-032 and SYS-033 are candidate requirements directly addressed here.
SYS-037 constrains revocation and recovery but remains broader than this key
layout. The initial fleet has one maintainer, no external availability promise,
and physical access to the workstation; router recovery may require a separately
secured out-of-band path.

## Design principles

1. **Separate keys before separate devices.** Each logical authority has a
   distinct key or credential even when several share custody hardware.
2. **Separate routine from exceptional authority.** A compromise during ordinary
   promotion must not replace project governance or recovery.
3. **Do not derive encryption from signing.** Data-unlock and recovery secrets
   have per-owner or per-machine lifecycles.
4. **Public trust state is reproducible.** Public keys, delegation records,
   revocations, and authorization evidence are versioned; private material is
   not stored in the repository.
5. **Loss has a declared terminal state.** The design does not call data or a
   machine recoverable when every recovery copy is gone.

## Proposed custody layout

The proposal uses four custody classes. A custody class is a shared operational
failure domain, not necessarily one physical device.

| Custody class | Distinct logical authorities | Normal availability | Primary compromise boundary |
| --- | --- | --- | --- |
| Offline authority and recovery set | Project root; recovery authorization; recovery boot signer; enrollment authority; UEFI owner authorities such as PK/KEK | Attached only for delegation, revocation, enrollment, recovery-artifact signing, or platform repair | Isolated from builders, CI, publication services, and routine promotion |
| Routine promotion signer | Release authorization; normal platform/UKI signing leaf | Available only during candidate signing and promotion | Cannot replace project root, recovery, enrollment, or data-recovery authority |
| Per-machine authority | Machine identity and any hardware-bound storage-unlock credential | Available to its one enrolled machine | Compromise does not authorize another machine or a release |
| Data-recovery vault | Per-machine or per-state-owner recovery secrets | Offline except during backup verification or recovery | Independent of all signing and enrollment keys |

The offline set must have independently stored recovery copies so that theft,
fire, filesystem failure, and one forgotten secret do not share a single failure
domain. The exact choice between duplicate encrypted material, pre-authorized
successor keys, or another recoverable construction is deferred, but a primary
device without a tested recovery copy is not an acceptable implementation.

Keys that share a custody class remain distinct. For example, the project-root
key may delegate a new release signer, while the recovery signer can authorize
only recovery artifacts. Sharing offline storage does not allow software to
treat those signatures as interchangeable.

## Logical authority inventory

| Authority | Permitted action | Explicitly prohibited | Loss or compromise response |
| --- | --- | --- | --- |
| Project root | Delegate, constrain, rotate, and revoke project release, recovery, and enrollment authorities | Routine artifact or UKI signing; data decryption | Restore an independently held copy or use a pre-authorized succession path; total loss without succession ends the existing project trust lineage |
| Release signer | Authorize a literal qualified release identity for named roles, channels, configuration compatibility, and policy epoch | Recovery authorization, machine enrollment, qualification rewriting, or data unlock | Existing releases remain identifiable; revoke and replace through project root, then classify releases signed during the exposure window |
| Normal platform signer | Sign the exact normal-boot EFI artifact accepted by the enrolled platform policy | Release promotion, recovery status, enrollment, or data unlock | Revoke or replace through owner-controlled platform authority and re-sign only qualified candidates |
| Recovery signer | Authorize a retained recovery identity and exceptional recovery operation | Normal release promotion or automatic normal boot | Replace through project root; inspect all recovery use and replace possibly exposed recovery artifacts |
| Recovery platform signer | Sign recovery EFI artifacts independently of the normal platform leaf | Normal release or automatic-selection authorization | Replace through owner-controlled platform authority; normal release signing remains unaffected |
| Enrollment authority | Admit, rotate, and revoke one machine identity | Release, platform, recovery, or data authorization | Revoke affected enrollment credentials and re-enroll machines from a trusted path |
| Machine identity | Authenticate one enrolled machine and receive its scoped policy or secrets | Another machine, a release, or project delegation | Revoke, clear or destroy old material, and re-enroll without restoring identity through OS rollback |
| Data-unlock credential | Unlock one declared storage or state scope under its role policy | Any signing, enrollment, or release action | Use the independent recovery secret or restore data from backup; loss of all unlock and recovery paths makes that data unrecoverable |

## Platform trust enrollment

Owner-controlled firmware policy should trust distinct normal and recovery boot
leaves. The private owner authorities used to alter firmware trust policy stay
with the offline set. The normal boot leaf stays with the routine promotion
signer; the recovery boot leaf stays offline.

Firmware acceptance alone does not establish normal NeutrinOS status. Normal
boot additionally requires valid release authorization, the expected complete
release-root identity, qualification evidence, and supported effective state.
A recovery-signed boot must enter an explicitly marked recovery state and must
not become an automatically promoted normal deployment.

The concrete UEFI PK/KEK/db layout and handling of vendor certificates remain a
platform-enrollment design detail. The invariant is that loss or compromise of
the normal platform leaf can be repaired without trusting that same leaf or
destroying data-recovery authority.

## Release signing and promotion flow

1. An unprivileged builder produces candidate artifacts, an immutable artifact
   manifest, provenance, and configuration identity.
2. The normal platform signer signs the exact candidate boot artifact. Signing
   changes its identity, so it occurs before literal-artifact qualification.
3. Qualification tests the complete signed candidate and records its literal
   identities and results.
4. The maintainer verifies the join among source, inputs, candidate identities,
   provenance, and required test evidence.
5. The release signer authorizes only that qualified identity and its declared
   role, channel, compatibility, and policy metadata.
6. Publication copies immutable artifacts and signed metadata. Publication
   infrastructure cannot mint a different authorized release.

The routine keys may share one promotion device, but they are invoked as
distinct operations with distinct audit records. CI and the builder do not hold
either private key and cannot promote their own output.

## Recovery authorization and artifacts

At least one recovery environment must be built, qualified for its narrower
purpose, signed by the offline recovery authorities, and retained independently
of the normal publication path before physical production enrollment.

Recovery activation requires deliberate owner action or an independently
secured out-of-band action. It must:

- identify itself as recovery rather than normal production;
- boot without trusting the normal release signer or normal mutable state;
- record the recovery identity, authorization, reason, and operations performed;
- avoid automatically restoring withdrawn credentials or mutable executable
  state;
- require a separate data-recovery credential for decryption where applicable;
  and
- leave the machine locally modified, quarantined, or re-enrolled until the
  applicable normal-production gates pass again.

The recovery signer is necessarily powerful: it can authorize software capable
of inspecting or replacing a machine. Its restricted semantics prevent silent
normal promotion, not malicious behavior after deliberate recovery activation.

## Data recovery and machine identity

Each protected machine or state owner receives an independently generated
recovery secret. It is not derived from the project root, release, platform,
recovery-signing, enrollment, or machine-identity keys.

Recovery secrets are inventoried by opaque identifier, scope, creation and
verification date, copy count, storage locations, rotation status, and
destruction status. The inventory may be versioned, but secret values and
sufficient material to reconstruct them must not enter the repository.

Machine identities should be generated on the target and hardware-bound when
the role provides a qualified facility. Exportable fallback identities require
encrypted storage and narrower validity. Reinstall and OS rollback preserve or
replace identity only through the enrollment contract, never by copying an old
OS deployment.

## Delegation, rotation, and revocation records

Every signed authorization records the authority identity, subject identity,
scope, policy epoch or sequence, creation time, and available validity bounds.
Routine rotation is exercised before an emergency and allows an overlap in
which old and new public keys are recognized while only the intended signer may
authorize new work.

Revocation cannot depend only on an online service because the router must boot
and recover offline. Machines retain the last valid signed policy state and
receive newer revocation or withdrawal state through normal updates, explicit
policy refresh, or recovery. The maximum offline exposure window and
anti-downgrade mechanism remain open under SYS-037.

A signer compromise does not prove every artifact it signed was malicious.
Incident response must bound the exposure interval, classify each affected
authorization, withdraw or re-authorize artifacts deliberately, and preserve
evidence. Merely rotating the key does not perform that classification.

## State and compatibility

Public authority metadata and audit records are project-owned inputs or release
evidence. On-machine accepted-policy state, enrollment, and recovery history are
machine-owned state governed independently of OS rollback. Per-owner data
recovery secrets belong to the corresponding machine, user, or workload state
contract.

Authority metadata schemas must be forward-readable across the retained normal
and recovery environments needed to rotate or revoke them. A release that
cannot interpret the current policy epoch is not an automatic rollback target.

## Failure and recovery exercises

Before production use, the following must be performed with disposable keys and
test data, then repeated with the real procedure without disclosing secrets:

| Failure | Required demonstrated outcome |
| --- | --- |
| Routine release signer lost | Existing machine boots; offline root delegates a replacement; a newly authorized release installs normally |
| Routine release signer compromised | Root revokes it; exposure-window releases are classified; recovery remains independently bootable |
| Normal platform signer lost or compromised | Owner platform authority replaces the leaf; recovery boot remains available; a candidate is re-signed and requalified |
| Primary offline set lost | An independently stored copy or succession path restores governance without the routine signer becoming root |
| All project-root recovery copies lost | The procedure explicitly declares the old trust lineage irrecoverable and requires owner-controlled platform reset and re-enrollment |
| Recovery artifact damaged or signer lost | Another independently retained artifact or signer copy is verified before the old copy is retired |
| TPM cleared or mainboard replaced | Per-machine data recovery unlocks declared state; identity is re-enrolled rather than resurrected from rollback |
| One machine identity compromised | Only that identity is revoked and replaced; release and other machine identities remain valid |
| All unlock and recovery secrets for one state owner lost | The procedure reports the data as unrecoverable and rebuilds only reconstructible state |
| Network, DNS, registry, and normal signer unavailable | Retained normal boot and deliberate recovery remain usable within the declared offline policy |

## Operations and diagnostics

An authority inventory reports public identifier, logical scope, custody class,
delegation chain, status, policy epoch, creation, rotation due date, last
exercise, and replacement or destruction evidence. It reports no private key,
unlock secret, or sensitive storage locator in ordinary machine status.

Promotion and recovery emit append-only evidence suitable for repository or
release retention. A failed signing or recovery operation identifies the
authority and artifact identities involved without logging secret material.

## Initial tabletop evidence

The [authority loss and compromise tabletop](../../research/exercises/0001-authority-loss-tabletop.md)
walked through routine-signer loss and compromise, primary and total offline-set
loss, recovery compromise, TPM or mainboard replacement, machine-identity
compromise, total data-recovery loss, infrastructure outage, and an urgent
release.

The model is internally recoverable on paper with two conditions:

- manual promotion remains acceptable for the initial personal fleet; and
- at least one offline recovery copy or succession path survives the primary
  local disaster and normal-account failure domains.

On 2026-08-09, the owner confirmed both conditions for the initial personal-fleet
phase. Manual promotion, including an urgent release, is an accepted operating
cost. An independent secondary offline copy or succession path is a required
part of the eventual custody implementation, not an optional hardening measure.

These are design decisions, not proof that the procedures work. The exercise
also found that routine signing keys should be replaceable rather than backed
up. Physical implementation, timed ceremony, firmware behavior, and offline
freshness remain unproven.

## Alternatives considered

### One master key

Rejected. Routine compromise would authorize normal boot, recovery, enrollment,
and governance, while loss could strand the whole fleet.

### One physical device per logical authority

Rejected for the initial personal fleet. The ceremonies, backups, and expiry
work would likely go untested. Distinct logical keys in two maintainer custody
domains preserve the most important routine-versus-exceptional boundary.

### Online CI-held release and platform keys

Rejected initially. It would let a compromised builder or CI control plane sign
and promote its own output. Later automation requires an independently enforced
promotion policy and evidence that its operational value justifies the expanded
attack surface.

### Vendor-only platform trust

Rejected as the complete platform authority model. It cannot independently
authorize and revoke NeutrinOS normal and recovery boot paths under owner
control.

## Verification

The design is viable when:

1. every logical authority has an owner, public identifier, scope, custody,
   rotation, revocation, loss, compromise, backup or regeneration, and
   destruction record;
2. the routine signer cannot produce an artifact reported as recovery-authorized
   or enroll a machine;
3. the recovery signer cannot produce an artifact reported as a qualified normal
   release;
4. a signed boot candidate is qualified before release authorization, and the
   authorized identity exactly matches the qualified identity;
5. each failure exercise reaches its declared outcome without an undeclared
   network, signer, clock, or mutable-state dependency; and
6. restoring an OS deployment cannot restore a revoked authority or machine
   identity.

## Risks and unresolved questions

- What custody construction and retrieval procedure will provide an independent
  secondary offline copy or succession path without recording sensitive
  locations in the repository?
- What time and operator-effort budget should the accepted manual promotion
  ceremony meet in normal and urgent-release exercises?
- Can firmware enroll separate normal and recovery leaves and provide usable
  owner-controlled revocation on every physical target?
- Can router out-of-band recovery require sufficient deliberate authorization
  without depending on the failed router data plane?
- What offline exposure window and policy-epoch mechanism satisfy SYS-037?
- Which recovery operations are safe enough to expose before data decryption?
- What audit record is useful without leaking authority or recovery metadata?

## Review disposition

The owner accepted the two operating conditions exposed by
[EX-0001](../../research/exercises/0001-authority-loss-tabletop.md). The
[adversarial review](review.md) remains open on promotion-environment compromise,
recovery capability, physical custody, and offline freshness. No physical keys,
storage locations, cryptographic formats, or firmware enrollments have been
selected or created.
