---
id: DES-0003
title: Initial threat and trust model
status: in-review
owners: []
reviewers: []
created: 2026-08-09
last_updated: 2026-08-09
depends_on: [DES-0001, DES-0002]
decision_backlog: [S-005, S-006]
related_adrs: []
---

# Initial threat and trust model

## Problem

NeutrinOS currently names Secure Boot, UKIs, TPMs, verity, signing, encryption,
provenance, and recovery without yet stating which attacker or failure each
mechanism must address. Selecting a boot or update substrate before defining
those claims would either accumulate security machinery without a purpose or
discard a needed guarantee because the preferred substrate cannot supply it.

This design defines the initial personal-fleet threat boundary, trust claims,
authority separation, and compromise behavior. It deliberately does not choose
cryptographic formats, key-storage products, or concrete boot mechanisms.

## Goals

- Identify protected assets and relevant attacker capabilities per role.
- Separate artifact identity, authorization, boot verification, qualification,
  freshness, and support status.
- Define the minimum boot-to-root integrity claim for production machines.
- Define authority scopes, rotation, revocation, loss, and recovery obligations.
- Distinguish availability recovery from recovery after compromise.
- Provide requirements that can fairly evaluate bootc and a direct
  systemd/UAPI lifecycle.

## Non-goals

- Preventing all compromise of a running system after an attacker gains root.
- Detecting malicious CPU, firmware, management engine, or hardware implants.
- Mandatory remote attestation before a concrete relying party and decision are
  identified.
- Hiding data from its authorized user while the machine is unlocked.
- Treating a signature as proof of correct source, trustworthy builders, passed
  tests, or absence of vulnerabilities.
- Providing enterprise certificate-authority availability or response SLAs.

## Requirements and constraints

Accepted Principles 3, 4, and 8 require owned state, designed recovery, and
security claims scoped to an attacker. CH-002 and CH-003 require release
provenance and literal-artifact qualification to remain distinct. SYS-025
requires machine identity and secret lifecycles to remain independent of OS
rollback.

SYS-001, SYS-002, and SYS-007 remain candidate requirements that this design
supports but cannot silently ratify. The initial project has one maintainer and
no external availability promise, so the authority model must be operable at
that scale.

## Assets

| Asset | Security property | Consequence of loss |
| --- | --- | --- |
| Release authorization | Only an authorized NeutrinOS authority may approve a normal deployment | Fleet-wide malicious or unintended OS execution |
| Release identity and evidence | Running bytes can be joined to source, inputs, provenance, and qualification | False confidence, inability to investigate or remediate |
| Boot and release-owned root content | Substitution or persistent mutation is prevented or detected before trust is granted | Offline persistence below normal OS inspection |
| Machine identity and enrollment | A machine cannot be impersonated and a revoked identity is not resurrected | Unauthorized fleet access or secret delivery |
| User and workload secrets/data | Confidentiality and integrity match the role's declared threats | Credential theft, personal-data loss, workload compromise |
| Signing and recovery authorities | Unauthorized use, loss, and compromise are bounded and recoverable | Fleet compromise or unrecoverable machines |
| Qualification and fleet policy | Test evidence and rollout decisions cannot be silently substituted | Unqualified or withdrawn releases deployed as trusted |
| Availability and recoverability | A failed security mechanism or lost key has a bounded recovery path | Self-inflicted outage or permanent data loss |

## Threat actors and initial scope

| Actor or failure | Initial treatment |
| --- | --- |
| Unauthenticated remote attacker | In scope for every reachable service and update source. |
| Compromised or malicious registry, mirror, network, or publication host | In scope; transport security alone is insufficient. |
| Compromised upstream package or source | In scope for provenance, applicability, containment, rebuild, and withdrawal; cryptographic boot verification does not detect an authorized malicious input. |
| Compromised build or CI worker | In scope for provenance and incident recovery; stronger build isolation and reproducibility remain later design choices. |
| Lost or stolen powered-off workstation | In scope for confidentiality of user, workload, machine, and recovery secrets. |
| Temporary physical access to a powered-off production machine | In scope for unauthorized boot-artifact or release-root substitution, subject to the explicit firmware boundary below. |
| Attacker with administrator/root on a running machine | In scope for containment, evidence, credential rotation, and compromise recovery; prevention of all runtime actions is out of scope. |
| Project-owner error, signing-key loss, or accidental revocation | In scope and treated as a primary recovery scenario. |
| Malicious firmware, CPU, peripheral firmware, or physical implant | Out of scope initially; the configured platform trust anchor is assumed to execute its verification policy correctly. |
| Destructive attacker with prolonged physical possession | Confidentiality depends on role encryption policy; availability and hardware integrity are not guaranteed. |

The owner is an authorized administrator, not an adversary the system attempts
to control. However, owner actions that bypass qualification or normal trust
policy must remain visible and must not be reported as a normal supported
deployment.

## Distinct trust statements

The following properties must never be collapsed into one “trusted” boolean:

| Property | Question answered |
| --- | --- |
| Identified | Which exact artifact and configuration inputs are present? |
| Authorized | Did an accepted authority approve this identity for the stated role/channel? |
| Integrity-verified | Did activation or boot authenticate the bytes against that identity? |
| Provenanced | Can the output be traced to source, inputs, builder, and build process? |
| Qualified | Did this literal identity pass the required tests? |
| Current | Is it the current release under the maintenance policy? |
| Supported | Are configuration, local modifications, security actions, and role policy within the supported envelope? |
| Fresh | Is the authorization still acceptable under expiry, withdrawal, and downgrade policy? |

A valid signature proves authorization by a key under a policy. It does not, by
itself, prove any other row.

## Proposed trust claims

### Release authorization and acquisition

- Every deployable release has an immutable identity and a signed authorization
  that binds its complete artifact set, role applicability, configuration
  identity or compatibility, and freshness metadata.
- The target verifies authorization and content identity before the candidate
  can replace or outrank the current deployment.
- Mutable registry tags, filenames, version strings, and HTTPS endpoints are
  discovery hints rather than release identity.
- Interrupted or failed verification leaves the current deployment selected and
  does not create a partially authorized candidate.

### Boot-to-root integrity

For production physical roles, normal boot begins at the configured platform
trust anchor and authenticates every release-owned boot artifact and the
release-owned root content before that content is treated as trusted. The claim
must cover the kernel, initrd, command line or equivalent policy, and immutable
root—not only the first EFI executable.

This does not authenticate mutable `/etc`, machine state, administrator
overrides, user state, or workloads. Executable mutable inputs remain part of
the effective trust surface and must be identified, constrained, or reflected
in support status.

The reference VM must exercise the same claim with controlled UEFI state and,
where the mechanism requires it, a vTPM. A development or recovery boot may use
a different explicitly authorized path, but it must not report the normal
qualified-production state.

### Confidentiality at rest

Each role declares which data must remain confidential after powered-off device
loss and how unattended reboot, remote recovery, and key loss constrain that
claim.

- The workstation must protect user data, workload data, machine credentials,
  and locally retained recovery secrets at rest.
- The router must protect long-lived credentials and other declared secrets,
  but its availability requirements may justify a different data-encryption and
  unlock design from the workstation.
- Encryption does not claim confidentiality after authorized unlock or against
  a compromised running kernel.

### Provenance and qualification

Release authorization consumes, but does not replace, provenance and test
evidence. Promotion policy must verify that the authorized artifact identities
are the literal qualified outputs. Signing an unqualified rebuild, even from
the same source revision, does not make it the qualified release.

### Recovery after failure and compromise

Availability recovery preserves state when its integrity is still trusted.
Compromise recovery assumes that machine identity, administrator overrides,
mutable executable configuration, user state, and workload state may contain
attacker persistence.

The recovery environment must therefore:

- have an authorization path independent of the normal online release signer;
- boot without trusting normal mutable state;
- inspect release and local-modification status before preservation;
- support revocation and re-enrollment without OS rollback resurrecting old
  credentials; and
- permit selective restore, quarantine, or destruction by state owner.

Factory reset restores a known authorization baseline but does not establish
the integrity of firmware or externally restored data.

## Authority model

These are logical authority scopes. Later designs may co-locate some keys only
after evaluating the resulting blast radius.

| Authority | Permitted use | Must not imply |
| --- | --- | --- |
| Project root | Delegate and revoke release, recovery, and possibly enrollment authorities | Routine online release signing |
| Release signer | Authorize a specific release identity, role/channel, and validity policy | Authority to enroll machines, decrypt data, or rewrite qualification evidence |
| Recovery signer | Authorize independently retained recovery artifacts and exceptional recovery actions | Authority to silently promote a normal fleet release |
| Platform boot authority | Authorize firmware-loaded boot artifacts on owned hardware | Proof that the authenticated OS was qualified or current |
| Enrollment authority | Admit, rotate, and revoke machine identities | Release publication or data decryption |
| Machine identity | Authenticate one enrolled machine and receive scoped secrets/policy | Authorization of another machine or a new OS release |
| Data-encryption authority | Unlock a defined state owner or storage scope | Release authenticity or fleet enrollment |

Upstream distribution and package-signing keys authenticate upstream inputs.
They are not NeutrinOS release authorities; NeutrinOS remains responsible for
the selected input set, produced artifact identity, and qualification.

## Key lifecycle obligations

Every authority must define:

- generation environment and required entropy;
- storage and permitted execution environments;
- scope, delegation, validity, and machine/role/channel constraints;
- rotation procedure that can be exercised before expiry;
- revocation and withdrawal distribution, including offline machines;
- audit evidence for each authorization;
- independent backup or regeneration capability where recovery is possible;
- loss response and the point at which machines or data become unrecoverable;
- compromise response and how previously authorized artifacts are classified;
  and
- destruction and succession when a machine, key, or project phase ends.

The design must avoid one credential whose compromise authorizes releases,
enrolls machines, unlocks data, and replaces recovery. It must also avoid a key
hierarchy so elaborate that the sole maintainer cannot test or recover it.

## Freshness, revocation, and rollback

Rollback creates tension between recovery and revocation. An old artifact can
be the last known bootable environment while also containing a known
vulnerability or authorization signed by a compromised key.

NeutrinOS therefore distinguishes:

- **mechanically retained:** bytes remain available;
- **authorized for normal boot:** current policy permits automatic selection;
- **recovery-only:** explicit local action may boot it under restricted policy;
  and
- **withdrawn:** policy prohibits its use except for a separately documented
  forensic or data-extraction procedure.

Freshness or anti-downgrade state must not make offline recovery impossible
after clock failure, network loss, or online-authority loss. Exceptional use
must require a deliberate recovery authority or physical-owner action and must
remain visible after boot.

## Role-specific emphasis

### Workstation

- Powered-off theft and access to user/workload data are primary threats.
- Development activity increases exposure to untrusted code; authenticated base
  OS integrity does not make user tools or containers trusted.
- Local recovery must remain possible after network, graphical-session, TPM,
  or primary-key failure.
- Administrator/developer boot paths are allowed but must be distinguishable
  from the qualified production path.

### Router

- Remote exploitation, credential theft, and availability are primary threats.
- Unattended reboot and recovery must work without the WAN, DNS, or fleet
  service the router normally reaches.
- Physical confidentiality and tamper resistance depend on actual deployment
  location and hardware; those assumptions must be recorded for the reference
  router.
- A rollback must not restore revoked VPN or administration credentials.

## Alternatives considered

### Trust the registry and TLS

Rejected as the complete authorization model. It does not protect against a
compromised publication service, mutable tag, copied artifact, or offline disk
substitution and does not bind qualification evidence.

### Secure Boot only through the kernel

Rejected as an adequate boot-integrity claim. Authenticating a bootloader and
kernel while accepting an unauthenticated release root leaves most privileged
userspace substitutable.

### Mandatory measured boot and remote attestation

Not proposed initially. Measurements are useful only when a relying party has
a policy decision to make and recovery behavior for mismatches. The vTPM
remains available for experiments and local key-sealing designs.

### Use only distribution-controlled boot and release keys

This reduces key operations but delegates authorization of NeutrinOS-specific
artifacts and recovery to an upstream product boundary. Distribution keys may
authenticate inputs or shims, but the project owner needs final control over
normal and recovery authorization for the personal fleet.

### Apply identical encryption and unlock policy to every role

Rejected because workstation theft confidentiality and unattended router
availability create different tradeoffs. The lifecycle semantics remain common
while the role mechanisms and claims may differ.

## Failure and recovery analysis

| Failure | Required response |
| --- | --- |
| Artifact digest or authorization fails | Reject candidate without changing current selection; retain attributable diagnostics. |
| Release signer is lost | Continue operating already accepted releases under explicit policy; rotate through the root or recovery authority before new promotion. |
| Release signer is compromised | Stop rollout, withdraw affected authorizations, determine affected artifacts, rotate authority, rebuild/requalify as needed, and classify retained rollback artifacts. |
| Project root is lost | Use independently tested root backup/recovery or explicitly re-establish trust with physical control of every machine; no silent replacement. |
| Platform key or firmware variables are lost | Enter a documented physical recovery/enrollment path that authenticates recovery material independently. |
| Machine identity is compromised | Revoke and re-enroll; OS rollback must not restore the old identity. |
| TPM state changes or hardware is replaced | Require recovery authorization and explicit re-binding; preserve or restore data only under its own authority. |
| Encrypted-state key is lost | Recover from an independently protected key or backup, or declare the data unrecoverable; OS recovery must not weaken encryption silently. |
| Boot verification succeeds but runtime compromise is suspected | Treat mutable state and credentials as untrusted; use compromise recovery rather than ordinary rollback. |
| Revocation/freshness service is unreachable | Apply recorded offline policy; do not silently treat “cannot check” as either current or permanently unrecoverable. |

## Verification

Before accepting the eventual architecture, tests must demonstrate:

1. registry, mirror, DNS, and network substitution cannot authorize different
   bytes under the same release identity;
2. modifying each release-owned boot/root component prevents normal trusted
   activation;
3. running status reports identity, authorization, integrity verification,
   qualification, freshness, currentness, and support independently;
4. the literal signed identity is the literal qualified identity;
5. signer rotation and revocation work on an online machine and under the
   declared offline window;
6. a withdrawn rollback artifact is not selected automatically but the defined
   recovery path remains usable;
7. machine re-enrollment survives OS rollback without restoring revoked
   identity;
8. workstation powered-off storage does not disclose the declared protected
   state without a recovery/unlock authority;
9. router reboot and recovery meet their availability target without normal
   network services;
10. loss of each authority has an exercised recovery or an explicit
    unrecoverable outcome; and
11. compromise recovery can boot independently and distinguish quarantined,
    preserved, restored, and destroyed state.

## Risks and unresolved questions

- Does “authenticate release-owned root content” require a DDI/verity layout,
  sealed composefs, or another mechanism supportable on bootc's production
  backend?
- Which physical machines support owner-controlled Secure Boot and usable
  recovery without vendor-key dependence?
- Is the initial router physically trusted enough to permit unattended
  unsealing, and what attack does TPM binding prevent there?
- Where can the sole maintainer keep project-root and recovery material so that
  theft, fire, account loss, and operator error do not share one failure domain?
- What is the acceptable offline freshness window for each role?
- Which build provenance claims are feasible before reproducible-build evidence
  exists?
- Which mutable executable inputs cause a machine to become locally modified or
  unsupported?
- What party, if any, would consume measured-boot evidence?

## Review disposition

The boot-to-root integrity target and SYS-030 were
[accepted in PR-0004](../../project/reviews/0004-boot-to-root-integrity.md).
The role-specific security and availability objectives and SYS-027 and SYS-034
were [accepted in PR-0005](../../project/reviews/0005-role-security-and-availability-objectives.md).
The remaining [adversarial review](review.md) is open, including physical key
layout, mutable executable inputs, and compromise recovery.
