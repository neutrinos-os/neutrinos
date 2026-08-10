---
id: DES-0010
title: Installation, provisioning, and machine enrollment
status: in-review
owners: [Jason Tarasovic]
reviewers: [Codex adversarial pass]
created: 2026-08-10
last_updated: 2026-08-10
depends_on: [DES-0003, DES-0004, DES-0005, DES-0006]
decision_backlog: [L-003]
related_adrs: []
---

# Installation, provisioning, and machine enrollment

## Problem

A blank or reset machine has no enrolled NeutrinOS identity with which to
authenticate its machine record. It still needs to select a target disk, create
the accepted storage layout, establish platform and data-unlock policy, install
an exact authorized deployment set, generate identity, and prove that an owner
intended to bind that physical or virtual machine to one inventory record.

SMBIOS, QEMU fw_cfg, instance metadata, seed media, a kernel argument, Ignition,
or cloud-init can locate input. None inherently proves which machine record or
role the machine should receive. Conversely, requiring an already enrolled
identity before first enrollment is circular.

The design must break that circle without leaving the installer, provisioning
seed, or metadata service as a permanent configuration authority. It must also
support deliberate reinstall, disk replacement, identity rotation, and
compromise recovery without silently restoring a revoked identity or erasing
unselected state.

## Goals

- Define one authenticated first-enrollment ceremony usable online or through
  removable offline transfer.
- Keep installation, platform ownership, data unlock, machine enrollment,
  normal release authorization, and recovery as separate authorities.
- Make every destructive storage action previewable, attributable, and bound to
  an exact target and preservation policy.
- Install and verify an exact previously built deployment set rather than
  constructing normal OS policy on the target.
- Make interruption, retry, replay, cloning, reprovisioning, and factory reset
  explicit state transitions.
- Retire or neutralize bootstrap and provisioning inputs after use.
- Prefer the systemd/UAPI ecosystem for local installation where it satisfies
  the requirements.
- Preserve a practical attended path for the initial workstation and router.

## Non-goals

- Selecting final disk sizes, root filesystem, updater, or package ecosystem.
- Making `/etc/machine-id`, SMBIOS UUID, TPM endorsement identity, MAC address,
  hostname, or machine name the NeutrinOS machine identity.
- Using installation to generate ordinary role or machine configuration.
- Requiring an online enrollment service for local recovery or every install.
- Automatically preserving arbitrary existing filesystems or deciding data
  ownership from path names.
- Treating a booted installer as recovery authority, enrollment authority,
  release authority, or permission to decrypt existing data.
- Promising an in-place migration from the current NixOS disk layouts.
- Selecting a concrete CA, token format, TPM library, or device-management
  protocol before the representative exercise.

## Accepted requirements and constraints

- SYS-024 and SYS-035 require owner-aware preservation and compromise recovery,
  not wholesale restoration of a mutable filesystem.
- SYS-025 keeps identity, enrollment, and secrets independent of OS rollback.
- SYS-030 requires a complete authenticated boot-to-root chain for normal boot.
- SYS-032 defines independent authority lifecycle obligations.
- SYS-033 and SYS-054 keep recovery separately authorized and state locked by
  default.
- SYS-042 and SYS-043 make inventory authoritative and reduce platform data to
  compatibility observation or bootstrap hint.
- SYS-047 makes provisioning a deliberate lifecycle whose replay cannot change
  role, identity, preserved state, or selected deployment.
- SYS-048 through SYS-056 govern storage identity, install finalization,
  encryption, recovery, snapshots, and capacity.
- SYS-065 through SYS-074 govern evidence identity, retention, sensitivity, and
  compromise traversal.
- SYS-075 through SYS-085 prevent enrollment or provisioning self-labels from
  becoming rollout targeting authority.

## Decision drivers

1. The first physical targets contain existing data and are not disposable.
2. `desktop-jason` exposes a TPM 2.0 interface but has not completed TPM or
   Secure Boot qualification.
3. `router` has IPMI and watchdog facilities but no currently installed TPM;
   its accepted unattended-unlock posture requires a qualified hardware-bound
   facility before production enrollment.
4. The installer has high destructive capability even when it carries no
   long-lived authority.
5. Physical presence is useful but is not a cryptographic identity and may be
   unavailable for future remote or virtual enrollment.
6. A one-time token must not allow whoever copies it to enroll arbitrary keys or
   repeatedly reset the intended machine.
7. An installed deployment can be authentic while the machine-to-record binding
   is wrong; both must be verified before normal eligibility.
8. New systemd installation machinery deserves priority under ADR-0001 but is
   young enough to require a challenger and failure testing.

## Options considered

### systemd-sysinstall composition

Current systemd provides `systemd-sysinstall`, a simple interactive or command-
line installer. It validates and confirms a target disk, invokes
`systemd-repart`, links a UKI and credentials with `bootctl`, installs
systemd-boot, and can run non-interactively. ParticleOS exercises this path from
an installer UKI profile.

This is the leading local installer candidate because it composes the same
systemd/UAPI objects already leading for storage and lifecycle. It does not
solve NeutrinOS enrollment, preservation, exact deployment-set verification,
authority separation, or production migration. It is new upstream machinery
and must not be accepted solely because it is systemd-native.

### systemd-repart plus a narrow NeutrinOS installer wrapper

A small wrapper verifies provisioning intent and deployment evidence, performs
preflight and preservation gates, then calls `systemd-repart`, `bootctl`,
`systemd-cryptenroll`, and the selected updater directly.

This provides the best semantic control but risks becoming a custom installer.
It remains the fallback if `systemd-sysinstall` cannot expose dry-run plans,
multi-artifact finalization, encryption enrollment, or the required evidence.
Any wrapper should orchestrate upstream tools rather than reimplement them.

### Ignition

Ignition is mature declarative first-boot provisioning prior art. It runs in the
initrd, manipulates disks and filesystems, writes files and systemd units, has a
versioned JSON specification, and aims to produce the declared machine or fail.

It is a mandatory challenger for VM, cloud, and first-boot provisioning input.
Its broad filesystem and configuration powers exceed the desired NeutrinOS
boundary. A generated Ignition document may perform bounded installation or
handoff tasks, but it cannot become the authoring format for normal role policy
or derive identity from mutable metadata.

### cloud-init

Cloud-init is widely available and useful for compatibility with external cloud
images. Its datasource and per-boot/per-instance model is deliberately broader
than NeutrinOS provisioning. Its own documentation warns that changed or
attacker-controlled instance identity can cause first-boot behavior to rerun.

Keep it as an explicit compatibility adapter only. It must be disabled or
strictly confined after the one-time handoff, and its cached instance ID is not
the NeutrinOS enrollment state.

### bootc install

`bootc install to-disk` offers an integrated and supported installation path;
`to-filesystem` permits external storage construction. It can configure a TPM2-
bound LUKS root and records installation provenance.

It remains the lifecycle challenger. Its OCI/OSTree deployment model and
current storage assumptions must still satisfy the accepted complete-set,
boot-to-root, storage, and enrollment requirements.

### Clone a pre-enrolled disk or VM image

Reject for normal use. Cloning an unconfigured deployment artifact is useful;
cloning machine identity, host keys, enrollment state, TPM-sealed material, or
provisioning completion creates impersonation and replay failures.

### Trust hardware identifiers or a shared enrollment password

Reject. Hardware observations are forgeable or replaceable and shared secrets
expand compromise scope. They may assist human comparison or bootstrap lookup
but cannot complete enrollment.

## Proposed model

### Distinct identities and records

| Object | Meaning | Must not become |
| --- | --- | --- |
| Installer artifact identity | Exact booted provisioning environment and tool closure | Normal deployment or recovery authority |
| Provisioning intent | Authenticated bounded instruction for one install/reprovision operation | Long-lived desired-state configuration |
| Enrollment voucher | Single-use authorization to propose one new binding within exact scope | Machine credential or reusable enrollment password |
| Machine identity key | Non-exportable where feasible key generated for one machine epoch | Machine name, role, or release authority |
| Enrollment request | Proof of possession plus voucher, nonce, observations, and requested record | Approved binding |
| Enrollment binding | Authority-approved association of identity key/epoch with one current machine record | Platform compatibility or release eligibility |
| Provisioning record | Evidence of inputs, actions, outputs, and completion | Secret store or mutable source of truth |
| Completion marker | Machine-owned state making consumed input inert | Sole historical evidence or authorization |

### State machine

```text
unprovisioned
    |
    v
bootstrap located -> provisioning intent authenticated
    |
    v
preflight + target/preservation confirmation
    |
    v
installation-open
    |
    +-> layout prepared -> deployment installed -> final bytes verified
    |
    +-> platform/data-unlock ceremonies completed as applicable
    |
    +-> machine identity generated -> enrollment request approved
    |
    v
provisioned-pending-trial
    |
    v
normal trial boot -> local assessment -> enrollment completion
    |
    v
enrolled
```

Interruption leaves a durable phase and exact completed actions. A machine is
not normal merely because some partitions, keys, or certificates exist. Retry
must either prove an action idempotent, reverse it safely, or require deliberate
restart/recovery.

### Provisioning intent and voucher

The owner creates a short-lived, single-use provisioning intent for one
operation. It binds:

- operation type: new install, reinstall, disk replacement, identity rotation,
  reprovision, or factory reset;
- intended machine record and inventory revision;
- allowed installer artifact identities and tool policy;
- expected platform constraints and observation policy;
- exact installable release authorization or permitted release set;
- target-disk selection constraints and whether erase is allowed;
- preservation manifest identity or explicit `preserve nothing`;
- required platform-key, encryption, recovery, and identity steps;
- enrollment voucher identity, nonce, expiry, use count, and approver;
- network/offline mode and allowed endpoints;
- evidence, completion, abort, and input-retirement behavior.

The voucher permits the holder to submit one enrollment request for the named
record and operation. Approval still verifies proof of possession, nonce,
observations, expected context, and owner confirmation. A stolen voucher cannot
authorize another role, release, machine record, or unlimited identities.

For an attended physical install, owner confirmation may be an independent
administrative-device or removable-media round trip. For an unattended VM,
the hypervisor or provisioning service may authenticate the operation, but its
authority and clone behavior must be explicit. Online and offline paths produce
the same canonical request, approval, and binding records.

### Installer trust and capability

The installer is a separately identifiable artifact booted under an accepted
platform or explicit owner-verification path. It carries public verification
material and only the short-lived inputs needed for this operation. It does not
carry release, recovery, enrollment-CA, platform-owner, or data-recovery private
keys.

Booting the installer grants local code the practical ability to alter disks.
Policy therefore requires physical/console activation, exact artifact display,
target preflight, and destructive confirmation. Cryptographic authorization
does not make an accidentally selected disk safe.

### Storage preflight and preservation

Before mutation, the installer records and displays:

- stable target path plus non-secret model, size, topology, and current layout;
- conflicts between observed storage and intended platform/disk constraints;
- proposed partition and encryption operations;
- every filesystem or partition to retain, replace, create, or leave untouched;
- required external backup and verified restore evidence;
- whether preservation is forbidden because compromise is suspected;
- capacity calculation and reserve; and
- the irreversible boundary for each action.

Existing state is preserved only through an ownership-aware preservation
manifest. The first physical migrations use scratch disks or restored copies;
the design makes no in-place conversion promise. Destructive confirmation
names the stable target and operation identity rather than accepting a generic
`yes` detached from the plan.

### Install and finalization

Installation consumes a previously built, qualified, and authorized deployment
set. It does not install packages or render normal configuration on the target.

The preferred order is:

1. validate installer, provisioning intent, target, backup, and capacity;
2. create or validate the GPT/storage structure with the accepted layout
   definition;
3. populate inactive root, Verity, state, and recovery regions;
4. establish LUKS2 metadata and separately custody routine and recovery unlock;
5. write normal boot artifacts and platform public material as authorized;
6. verify the final bytes and complete deployment closure from the target;
7. install or activate the final boot entry last;
8. generate machine identity locally and complete enrollment;
9. select exactly one bounded normal trial; and
10. record completion only after the normal environment proves the intended
    deployment, binding, state mounts, and applicable role-health baseline.

Tool constraints may change local ordering, but no boot-selectable hybrid may
appear and no enrollment binding may mask an incomplete deployment.

### Authority ceremonies

The following may occur in one attended session but remain independently
authorized:

- **platform ownership:** enroll or replace Secure Boot/platform public keys;
- **data unlock:** enroll TPM/FIDO2/passphrase methods and an independent
  recovery method, then back up LUKS metadata;
- **machine enrollment:** approve a new machine identity binding;
- **normal release selection:** verify an existing release authorization; and
- **recovery:** invoke a separately authorized environment only when needed.

The installer coordinates public inputs and outputs. It cannot use one
credential or confirmation to grant all authorities. Platform setup mode is an
observation, not permission to enroll whichever key the installer supplies.

### Machine identity

The machine generates a fresh asymmetric identity key locally. The enrollment
request proves possession. Hardware protection and attestation strength are
reported separately:

- TPM-backed non-exportable key with qualified policy;
- vTPM-backed key within a named VM trust boundary;
- software key protected by a declared machine-state contract; or
- unavailable/unassessed protection.

Enrollment does not claim a hardware-bound identity when only a software key
exists. A disk or VM clone must not result in two concurrently valid machines
with the same identity. Clone detection, deliberate test-fixture reset, and
identity epoch changes are part of the protocol.

The router's production profile requires the accepted hardware-bound facility
to be installed and exercised; an IPMI interface or board serial is not a TPM
substitute.

`/etc/machine-id` remains an application identifier with systemd lifecycle
semantics, not the enrollment credential. It may be generated at first boot and
correlated as an observation, but restoring it cannot restore a revoked
NeutrinOS identity.

### First boot and handoff

First boot performs only machine-local completion that cannot honestly exist in
the generic artifact:

- initialize non-authoritative system identifiers;
- consume narrowly scoped one-time system credentials;
- prove access to intended machine-owned state and identity key;
- verify enrollment binding and exact booted deployment;
- complete trial assessment and record provisioning outcome; and
- make provisioning inputs inert or require explicit reprovision activation.

Locale, keymap, and timezone may be handed through systemd credentials when
they are truly machine-owned late-bound values. Normal role services, network
policy, privileged users, and release-owned `/etc` remain identity-bound build
inputs or follow accepted late-bound contracts; they are not casually injected
by the installer.

Ignition or cloud-init adapters, when present, receive a generated bounded
handoff document. After completion they cannot continue applying per-boot or
changed-instance metadata. Their raw inputs and secret exposure are handled by
explicit retention and retirement policy.

### Reinstall, reprovision, and re-enrollment

- **reinstall** replaces release-owned artifacts while retaining the same
  machine identity and only explicitly preserved compatible state.
- **disk replacement** creates the target layout on a new disk, restores named
  state contracts, and either retains or rotates identity according to its
  custody and compromise status.
- **identity rotation** proves the old or exceptional authority, creates a new
  key/epoch, updates the binding, and revokes the old identity without requiring
  OS replacement.
- **reprovision** reruns a named provisioning operation with fresh intent and
  explicit preservation/destruction choices.
- **factory reset** destroys the selected machine, administrator, user, and
  workload state scopes and returns to unprovisioned state; it does not create a
  valid new identity by itself.
- **compromise recovery** begins with identity revocation/quarantine and treats
  preserved executable state as hostile; ordinary reinstall is not sufficient.

No operation may infer permission from old seed media or an old completion
marker. Re-enrollment creates a new binding record and never edits the history
of the previous identity epoch.

### Initial implementation posture

1. Use a signed installer UKI or equivalent exact installer artifact.
2. Exercise `systemd-sysinstall` with NeutrinOS repart definitions as the
   leading path.
3. Use `systemd-repart`, `bootctl`, `systemd-cryptenroll`, and systemd
   credentials directly where their boundaries fit.
4. Implement the smallest separate enrollment request/approval exchange needed
   to bind a locally generated key to an existing machine record.
5. Use local/removable transfer first so production enrollment does not require
   a permanent fleet service.
6. Map the VM flow to a generated Ignition document and bootc installation as
   challengers.
7. Keep cloud-init outside the initial trusted path unless a target environment
   requires compatibility.

## State and compatibility

Provisioning phase, completion, machine identity, enrollment binding, recovery
references, storage metadata, and preservation state are machine-owned and
survive OS rollback according to their individual contracts. The provisioning
record and approval are project/private-fleet evidence.

Installer schema, provisioning-intent schema, enrollment protocol, storage-
layout version, preservation-manifest schema, and evidence format are all
versioned. Unknown versions fail before mutation. Migration derives new records
without rewriting prior operations.

Normal fallback is allowed only after installation completes the state-
compatibility and commit boundaries accepted in DES-0002. The installer must
not restore application state merely because a filesystem was preserved.

## Security and trust

Relevant attackers include malicious install media, a compromised metadata or
provisioning server, a copied voucher, a hostile old disk, a cloned VM, an
attacker controlling SMBIOS or instance identity, a malicious local network,
and an operator selecting the wrong disk.

The design guarantees attributable intent, local proof of possession, bounded
enrollment scope, exact installed deployment verification, and replay-resistant
handoff when implemented correctly. It does not prove that firmware, a TPM, or
an installer is free of compromise; make physical presence infallible; or make
restored mutable state benign.

Secrets must not appear in command lines, public logs, provisioning evidence,
or durable seed media unless that medium has an explicit encrypted custody and
destruction policy. Prefer AF_UNIX/file-descriptor credential transfer and
redacted identifiers. Enrollment services learn only the machine and platform
facts necessary for their decision.

## Failure and recovery

| Failure | Required behavior |
| --- | --- |
| Bootstrap names wrong record | Stop before mutation or enrollment; observation cannot override intent |
| Provisioning signature/expiry invalid | Stop without destructive action |
| Wrong disk selected | Preflight and identity-bound confirmation block mutation |
| Power loss during repart/install | Resume verified idempotent phase, reverse safely, or require deliberate restart |
| One artifact is partial or substituted | No final boot selection; report exact failed closure member |
| Platform-key enrollment fails | Preserve diagnosable non-normal state; do not claim authenticated boot |
| TPM enrollment or unseal fails | Use separately tested recovery only by explicit action; do not weaken silently |
| Voucher is replayed | Reject spent nonce/use and expose original binding |
| Two machines present one identity | Quarantine both or apply explicit conflict policy; never silently choose |
| Approval service unavailable | Complete offline round trip or stop before normal enrollment |
| Seed/metadata reappears | Treat as inert; require fresh authenticated reprovision intent |
| Old disk contains hostile state | Keep locked/quarantined; preserve or destroy only by owner manifest |
| Normal first boot fails | Use eligible fallback or maintenance recovery without rerunning provisioning automatically |
| Completion record is lost | Reconstruct from binding/evidence or require deliberate repair; never accept seed replay as reconstruction |
| Identity key is lost/compromised | Revoke and re-enroll through independent authority; rollback cannot restore it |

## Operations and diagnostics

Before mutation the operator sees one plan with exact installer, intent,
inventory revision, target disk, erase/preserve actions, deployment, authorities,
and recovery prerequisites. Afterward, status answers:

- Which exact installer and provisioning intent ran?
- Which target and storage-layout version were used?
- What was preserved, destroyed, created, and verified?
- Which exact deployment set is installed and selected for trial?
- Which platform, unlock, identity, and enrollment ceremonies completed?
- What is the current machine identity epoch and binding status?
- Are any voucher, seed, metadata, or first-boot inputs still live?
- Is the machine unprovisioned, pending trial, enrolled, quarantined, or
  reprovision-required?
- What recovery or owner action can safely resume the current phase?

Raw `repart`, `cryptsetup`, `bootctl`, installer, first-boot, and enrollment
diagnostics remain accessible with secret redaction. A high-level status does
not replace them.

## Verification

EX-0012 must exercise:

1. clean VM install online and through removable offline transfer;
2. systemd-sysinstall and direct-composition mappings;
3. exact target-disk preflight and a wrong-disk attempt;
4. interruption before and after every irreversible/finalization boundary;
5. exact deployment closure verification and entry-point-last behavior;
6. TPM/vTPM-backed and explicit software-key identity cases;
7. voucher theft, replay, expiry, wrong-record use, and proof-of-possession
   substitution;
8. hostile SMBIOS, QEMU fw_cfg, metadata, Ignition, cloud-init, and seed replay;
9. cloned disk/VM and duplicate identity;
10. reinstall, disk replacement, identity rotation, factory reset, and
    compromise re-enrollment;
11. preservation and restore of each selected state owner; and
12. normal first-boot failure with fallback or maintenance recovery.

The first physical migration requires verified backups and a rehearsal on
scratch storage before modifying `desktop-jason`. The router requires verified
IPMI/alternate access and the accepted hardware-bound secret facility before
production enrollment.

## Risks and unresolved questions

- Is `systemd-sysinstall` mature and available enough in the selected package
  baseline, or must NeutrinOS temporarily compose its lower-level tools?
- Can its repart and bootctl flow install the exact multi-resource deployment
  set and finalization order without a large wrapper?
- What signs the provisioning intent and voucher, and can that responsibility
  safely share the accepted enrollment authority?
- Which independent display or transfer lets the owner verify a physical
  machine's first request without trusting the installer alone?
- Should the enrollment binding use certificates, signed statements, or both?
- Which machine identity operations genuinely benefit from TPM attestation,
  versus non-exportable key storage and physical owner confirmation?
- How is a deliberately cloned reference VM distinguished from an accidental
  clone of production identity?
- What is the minimum offline artifact set for installer, deployment, platform
  public keys, enrollment approval, and recovery?
- Can Ignition be reduced to an acceptable generated handoff, or does including
  it only increase the trusted computing base?
- Which environments justify cloud-init compatibility despite its replay and
  continuing-datasource risks?

## Accepted requirements

PR-0013 accepts SYS-086 through SYS-097 as policy boundaries. They define
authenticated provisioning intent, destructive preflight, installer capability,
transaction state, exact installation, authority separation, identity
generation, enrollment, input retirement, bounded first boot, reprovisioning,
and evidence without selecting concrete formats or services.

## Review disposition

The design is in adversarial review. RES-0010 compares current installer and
provisioner candidates, and EX-0012 remains the first-enrollment and replay
gate. The accepted requirements do not select an installer, enrollment
protocol, record format, or service. No physical production enrollment should
occur until the relevant mechanism and recovery exercises pass.
