---
id: EX-0006
title: Representative fleet intent and field-authority model
status: complete
date: 2026-08-09
exercise_type: configuration and authority tabletop
evidence_class: analysis-only
related_designs: [DES-0001, DES-0002, DES-0003, DES-0005]
---

# Representative fleet intent and field-authority model

## Purpose and evidence limit

This exercise instantiates DES-0005 for the reference VM,
`desktop-jason`, and `router`. It tests whether machine records, fixed
configuration scopes, native inputs, platform constraints, late-bound
contracts, and downstream evidence can be modeled without selecting a file
format or creating duplicate sources of intent.

The records below are illustrative structured data, not proposed YAML schemas
or build inputs. Placeholder values are deliberate where the repository does
not contain an accepted identifier, policy, or sensitive machine detail. No
serial number, MAC address, filesystem UUID, private address, secret value, or
recovery locator is introduced by this exercise.

The exercise passes on paper when:

1. every desired field has one authority;
2. later objects bind or attest to desired intent without becoming competing
   sources of it;
3. the three configuration scopes produce one deterministic composition;
4. platform observation cannot assign behavior;
5. late-bound values have bounded semantic effects; and
6. the model remains usable with mostly upstream-native configuration.

## Shared logical definitions

### Inventory root

```yaml
schema: neutrinos.fleet-inventory/v0-illustrative
revision: <immutable-source-revision>

common_configuration_sources:
  - common/system-baseline@<digest>
  - common/lifecycle@<digest>
  - common/trust-policy@<digest>

roles:
  qualification-fixture: role/qualification-fixture@<digest>
  workstation: role/workstation@<digest>
  router: role/router@<digest>

platform_classes:
  qemu-uefi-x86_64: platform/qemu-uefi-x86_64@<digest>
  x570-aorus-pro-wifi: platform/x570-aorus-pro-wifi@<digest>
  x11sdv-4c-tp8f: platform/x11sdv-4c-tp8f@<digest>

machines:
  reference-vm: machine/reference-vm@<digest>
  desktop-jason: machine/desktop-jason@<digest>
  router: machine/router@<digest>
```

The names are navigation keys. Each exact referenced object and the inventory
revision have content identity in the eventual implementation. The example
does not imply that every object needs a separate physical file.

### Common configuration sources

| Source | Representative contents | Preferred representation |
| --- | --- | --- |
| `common/system-baseline` | Base users and groups, filesystem-independent mounts, time policy, logging bounds, tmpfiles, sysusers, udev, and common service policy | Upstream-native files where possible; bounded data only for repeated project intent |
| `common/lifecycle` | Deployment identity reporting, update diagnostics, boot-attempt state, assessment hooks, and local blessing integration | Native systemd units, drop-ins, tmpfiles, and declared health-policy references |
| `common/trust-policy` | Normal-versus-recovery boot classification, release-authorization gate, local-modification reporting, and credential-consumption policy | Native policy inputs plus small project-owned evidence and gate declarations |

These sources state behavior, not packages or artifact layout. Package inputs
and build configuration remain separate pinned build inputs joined through the
deployment manifest and provenance.

### Role definitions

```yaml
qualification-fixture:
  requirements: requirements/roles/reference-platform
  configuration_sources:
    - role/qualification-lifecycle-fixtures@<digest>
  supported_platform_classes: [qemu-uefi-x86_64]
  health_policy: health/qualification-fixture@<digest>
  state_contracts:
    - state/boot-attempt-and-blessing@<digest>
    - state/update-diagnostics@<digest>
    - state/migration-fixture@<digest>
  late_bound_contracts:
    - late-bound/virtual-platform-observation@<digest>
    - late-bound/test-network-environment@<digest>

workstation:
  requirements: requirements/roles/workstation
  configuration_sources:
    - role/workstation-system@<digest>
    - role/workstation-session@<digest>
    - role/workstation-network@<digest>
  supported_platform_classes:
    - qemu-uefi-x86_64
    - x570-aorus-pro-wifi
  health_policy: health/workstation@<digest>
  state_contracts:
    - state/machine-identity@<digest>
    - state/update-diagnostics@<digest>
    - state/user-home@<digest>
    - state/rootless-containers@<digest>
    - state/virtual-machines@<digest>
  late_bound_contracts:
    - late-bound/workstation-platform-observation@<digest>
    - late-bound/workstation-normal-unlock@<digest>
    - late-bound/machine-enrollment@<digest>
    - late-bound/workstation-network-credentials@<digest>

router:
  requirements: requirements/roles/router
  configuration_sources:
    - role/router-network-services@<digest>
    - role/router-security-policy@<digest>
    - role/router-availability@<digest>
  supported_platform_classes:
    - qemu-uefi-x86_64
    - x11sdv-4c-tp8f
  health_policy: health/router-external@<digest>
  state_contracts:
    - state/machine-identity@<digest>
    - state/update-diagnostics@<digest>
    - state/router-protocol@<digest>
  late_bound_contracts:
    - late-bound/router-platform-observation@<digest>
    - late-bound/router-provider-data@<digest>
    - late-bound/router-service-credentials@<digest>
```

The QEMU platform class in the workstation and router definitions permits
qualification of their literal deployment variants under explicitly modeled
hardware. It does not claim that QEMU success qualifies the physical platform.

### Platform-class definitions

| Platform class | Desired constraints | Observations that may satisfy it | Not implied |
| --- | --- | --- | --- |
| `qemu-uefi-x86_64` | x86-64, controlled UEFI variables, recorded virtual hardware, optional vTPM when required by the test | Hypervisor definition, firmware digest and settings, virtual device inventory, vTPM evidence | Any role, physical-hardware support, or permission to reuse a machine identity in a cloned VM |
| `x570-aorus-pro-wifi` | x86-64; Gigabyte X570 I AORUS PRO WIFI compatibility; UEFI; required AMD GPU and Intel network support; TPM capability only when exercised | DMI and device inventory, UEFI state, TPM evidence, storage and recovery observations | `desktop-jason` identity, workstation role, enabled Secure Boot, or qualified TPM behavior |
| `x11sdv-4c-tp8f` | x86-64; Supermicro X11SDV-4C-TP8F compatibility; UEFI; required network, IPMI, and watchdog facilities; TPM absent unless later installed and qualified | DMI and device inventory, UEFI state, IPMI/watchdog tests, storage observations, optional future TPM evidence | `router` identity, router role, working out-of-band console, or encrypted unattended boot |

The physical class names replace the ambiguous use of a machine name as a
platform class in the earlier EX-0005 sketch. A platform-class definition
records compatibility claims; hardware-specific configuration remains an
explicit role- or machine-scoped source.

## Representative machine records

### `reference-vm`

```yaml
schema: neutrinos.machine-record/v0-illustrative
machine_name: reference-vm
enrollment_binding:
  policy: test-machine-reenrollment
  identity_reference: <assigned-per-managed-lifecycle-fixture>
role_assignment: qualification-fixture
platform_constraints:
  architecture: x86-64
  allowed_classes: [qemu-uefi-x86_64]
  require:
    - controlled-uefi-state
    - recorded-virtual-hardware-definition
machine_configuration_sources:
  - machine/reference-vm-topology@<digest>
late_bound_contracts:
  - late-bound/optional-vtpm-observation@<digest>
  - late-bound/test-injected-values@<digest>
state_contracts:
  - state/fixture-lifecycle@<digest>
health_policy: health/qualification-fixture@<digest>
deployment_policy: deployment/reference-testing@<digest>
```

`reference-vm` is one managed test-machine intent, not a machine-identity
template. Its firmware variables, boot attempt state, and any vTPM identity
persist for the duration required by a lifecycle exercise. Resetting the
fixture deliberately destroys or re-enrolls its machine identity. Copying the
VM definition creates another platform instance and never copies an authority
to act as `reference-vm`.

The same qualification harness may boot workstation and router variants under
modeled platforms. That activity does not reassign the fixture's role or make
those variants members of the fixture deployment policy.

### `desktop-jason`

```yaml
schema: neutrinos.machine-record/v0-illustrative
machine_name: desktop-jason
enrollment_binding:
  policy: physical-owner-enrollment
  identity_reference: <unassigned-until-neutrinos-enrollment>
role_assignment: workstation
platform_constraints:
  architecture: x86-64
  allowed_classes: [x570-aorus-pro-wifi]
  require:
    - uefi
    - owner-controlled-secure-boot-before-production
    - authenticated-release-root-before-production
  observations_to_qualify:
    - tpm2-operation-and-recovery
    - bootloader-and-esp-layout
    - physical-recovery-path
machine_configuration_sources:
  - machine/desktop-jason-hardware-policy@<digest>
  - machine/desktop-jason-storage-intent@<digest>
  - machine/desktop-jason-network-intent@<digest>
late_bound_contracts:
  - late-bound/desktop-jason-platform-observation@<digest>
  - late-bound/desktop-jason-normal-unlock@<digest>
  - late-bound/desktop-jason-network-credentials@<digest>
state_contracts:
  - state/desktop-jason-machine@<digest>
  - state/desktop-jason-user@<digest>
  - state/desktop-jason-workloads@<digest>
health_policy: health/desktop-jason@<digest>
deployment_policy: deployment/workstation-testing-then-current@<digest>
```

The machine configuration sources bind normal non-secret hardware load policy,
post-provisioning mount intent, and network consumption policy. They do not
contain storage UUIDs, unlock secrets, Wi-Fi credentials, current DHCP values,
or TPM observations. Those are provisioning state, late-bound values, or
machine realization evidence under their respective contracts.

The role definition owns generic workstation behavior. The machine record does
not restate the CPU model, installed-memory figure, board firmware version, GPU
serial identity, or current partition topology as desired configuration.
Supported constraints refer to the platform class; actual values remain dated
observations.

### `router`

```yaml
schema: neutrinos.machine-record/v0-illustrative
machine_name: router
enrollment_binding:
  policy: physical-owner-plus-out-of-band-enrollment
  identity_reference: <unassigned-until-neutrinos-enrollment>
role_assignment: router
platform_constraints:
  architecture: x86-64
  allowed_classes: [x11sdv-4c-tp8f]
  require:
    - uefi
    - ipmi-device
    - runtime-watchdog
    - unattended-normal-reboot
    - offline-fallback-control-path
  observations_to_qualify:
    - active-firmware-boot-selection
    - ipmi-console-and-power-path
    - owner-controlled-secure-boot
machine_configuration_sources:
  - machine/router-interface-intent@<digest>
  - machine/router-network-intent@<digest>
  - machine/router-storage-intent@<digest>
  - machine/router-out-of-band-policy@<digest>
late_bound_contracts:
  - late-bound/router-interface-observation@<digest>
  - late-bound/router-provider-delegation@<digest>
  - late-bound/router-service-credentials@<digest>
  - late-bound/router-normal-unlock-capability@<digest>
state_contracts:
  - state/router-machine@<digest>
  - state/router-protocol@<digest>
  - state/router-operational-evidence@<digest>
health_policy: health/router-external@<digest>
deployment_policy: deployment/router-cautious-current@<digest>
```

The machine-scoped sources contain exact non-secret WAN/LAN intent, interface-
role mapping rules, desired addressing and routing policy, and service
configuration. The illustrative record deliberately omits actual interface
identifiers and private network values. The mapping policy is identity-bound;
observed interfaces are late-bound and must match its constraints.

The absence of an observed TPM is a current platform fact. The
`router-normal-unlock-capability` contract must therefore report unsatisfied
until a discrete TPM or another acceptable hardware-bound facility is installed
and qualified. It cannot select an insecure software-only substitute merely to
make unattended boot appear satisfied.

IPMI presence is not proof of an independently secured out-of-band path. The
platform constraint requires qualification evidence before that capability can
support recovery claims.

## Composition traces

### Normal trace

For `router`, the ordered source closure is:

```text
common/system-baseline
common/lifecycle
common/trust-policy
        <
role/router-network-services
role/router-security-policy
role/router-availability
        <
machine/router-interface-intent
machine/router-network-intent
machine/router-storage-intent
machine/router-out-of-band-policy
```

Order inside each scope is the explicit order recorded by its owning inventory
or role/machine record. Filenames and directory traversal do not determine
which source wins.

A representative machine override is a router-specific journald storage bound
that narrows a common fleet default because the system disk is small. The
composition record must retain:

- the common value and source;
- the machine value and source;
- the fixed precedence rule;
- the winning resolved value;
- the rendered native journald drop-in identity; and
- the validation and storage-policy result.

This override is permitted because it narrows an operational bound without
violating the minimum failed-update diagnostic retention policy.

### Native configuration path

A router networkd file with an upstream setting not represented by a
NeutrinOS convenience schema follows this path:

```text
machine/router-network-intent native input
        -> source and destination attribution
        -> native syntax verification
        -> cross-file network policy validation
        -> exact rendered file identity
        -> immutable configuration artifact or flattened root
        -> deployment manifest and qualification record
```

The source declaration may inherit unambiguous defaults from its containing
machine configuration source: scope, owner, and consuming component do not need
to be repeated beside every file. Destination, exceptional ordering, merge
behavior, or policy exemption must remain explicit when defaults cannot
determine them uniquely.

### Conflict and deletion fixtures

The following are synthetic composition tests, not proposed production values:

| Fixture | Expected result |
| --- | --- |
| Two router role sources emit the same complete native destination without a consumer merge policy | Reject as same-scope conflict and identify both sources. |
| A machine input changes a role-provided value | Accept precedence, retain both origins, then apply complete-policy validation. |
| A machine input attempts to disable boot-to-root authentication | Resolve the attempted value for diagnosis, then reject it as a policy violation. |
| A machine input explicitly tombstones an optional common service | Remove it only if the named policy permits removal; record the tombstone and removed source. |
| A lower-scope input is absent from a later source | Preserve the lower-scope value; absence is not deletion. |
| Two drop-ins have distinct native filenames and upstream-defined ordering | Preserve both exact files and let the named upstream interpretation policy define their semantics. |

The final fixture is not treated as a conflict merely because both files affect
one systemd unit. Native composition belongs to systemd when its ordering is
explicit and qualified; NeutrinOS still records the exact file set.

## Non-overridable policy invariants

Machine precedence does not authorize exceptions to accepted project policy.
At minimum, ordinary configuration cannot override:

- authenticated normal boot-to-root under SYS-030;
- complete deployment identity and literal qualification under SYS-002;
- authorization and eligibility gates under SYS-028 and SYS-029;
- separation of normal and recovery authorization under SYS-033;
- the prohibition on automatic recovery entry under SYS-038;
- state-compatibility and migration barriers under SYS-021 through SYS-023;
- independent machine-identity and secret lifecycles under SYS-025;
- explicit executable-input ownership and local-modification reporting;
- role security and unattended-availability objectives already accepted for
  the workstation and router; or
- composition attribution required by SYS-014 through SYS-018.

Changing an invariant requires an accepted project-policy or architectural
decision and a new qualified deployment claim. It is not represented as a
machine exception flag. Development, emergency, and recovery modes retain
their separately declared status and authorization rather than weakening the
normal invariant.

## Late-bound contract inventory

| Value class | Owner/source | Permitted semantic power | Explicitly prohibited | Failure/status behavior |
| --- | --- | --- | --- | --- |
| Enrolled machine identity | Enrollment authority and machine | Authenticate this machine and bind its current record | Assign another role, authorize a release, or restore revoked identity through rollback | Ineligible or re-enrollment-required when missing, revoked, or mismatched |
| TPM or platform observation | Platform observation under declared verifier | Establish whether a named platform constraint or unlock policy is satisfied | Select policy, role, package, unit, or fallback by itself | Compatible, incompatible, degraded, or unknown with exact observation evidence |
| Storage-unlock result | Machine data-unlock authority | Release the already declared storage scope under the bound boot policy | Deliver normal configuration or grant recovery plaintext automatically | Stop, degrade, or request deliberate recovery according to role policy |
| Service credential | Machine, administrator, user, or workload owner | Supply opaque bytes to one named consumer under a declared schema and scope | Carry units, scripts, package selections, firewall rules, or undeclared consumers | Service unavailable or machine degraded; never log the value |
| Interface observation | Platform/kernel observation | Match observed devices to an identity-bound interface-role mapping rule | Decide WAN/LAN meaning without the bound mapping policy | Incompatible or router health failure when ambiguous or missing |
| Provider delegation and dynamic network data | External protocol peer | Supply addresses, prefixes, routes, leases, or peer facts consumed by fixed policy | Replace firewall, service, or role policy | Operational health changes; deployment identity does not |
| Qualification test injection | Qualification harness | Exercise a contract using bounded representative and invalid values | Become a production secret or persistent machine authority | Test failure; fixture evidence names the injected class, not sensitive values |

Powerful policy delivered as nominal data is not automatically late-bound. If a
service consumes executable code, firewall policy, admission policy, or another
value that defines normal privileged behavior, that input is identity-bound
unless it is explicitly assigned to an independently authorized workload or
administrator owner with the corresponding status consequence.

## Field-authority table

`Binds` means an immutable downstream object identifies the authoritative
value; it does not become permission to edit or reinterpret that value.
`Attests` means evidence reports a claim about it.

| Field or object | Authoritative source | Downstream relationship | Consumer or gate | Must not become |
| --- | --- | --- | --- | --- |
| Inventory revision | Fleet inventory source control | Composition record binds | Composition and audit | Mutable discovery identity |
| Machine name | Machine record history | Enrollment and composition records bind | Operator lookup and status correlation | Machine credential or DMI match |
| Role assignment | Current reviewed machine record | Composition record and deployment manifest bind; release authorization constrains role scope | Configuration composition, qualification, and selection | Hardware-derived fact or mutable boot choice |
| Role requirements and defaults | Role definition | Composition record binds exact definition | Composition, policy validation, qualification | A claim that every role machine has identical bytes |
| Platform constraints | Role definition plus machine-record narrowing | Deployment manifest binds; platform evidence attests | Eligibility and support | Role assignment or observed hardware state |
| Platform observation | Dated qualification or machine evidence | Status and qualification record attest | Compatibility, health, unlock, and support gates | Desired configuration or authorization |
| Common configuration sources | Fleet inventory | Composition record binds | Composition | Implicit filesystem discovery |
| Role configuration sources | Role definition | Composition record binds | Composition | Machine-specific secret or observation store |
| Machine configuration sources | Machine record | Composition record binds | Composition | Mutable administrator override |
| Composition precedence | Accepted project policy and versioned interpretation | Composition record identifies policy | Resolver and diagnostics | Per-machine programmable ordering |
| Resolved configuration | Deterministic composition output | Composition record identifies | Renderer and policy validation | A second source of editable intent |
| Rendered configuration | Renderer output from resolved inputs | Composition record and deployment manifest bind exact outputs | Build, native validators, qualification, boot | Historical mutable `/etc` state |
| Composition record | Composition process over exact inputs | Deployment evidence and manifest join bind | Reproduction, attribution, status | Mutable desired-state database |
| Deployment manifest and identity | Exact release-owned artifact closure | Qualification and authorization bind | Staging, selection, boot, status | Role or fleet inventory authority |
| Qualification record | Qualification authority observing exact deployment | Release authorization binds its identity | Promotion and eligibility | New desired intent or global guarantee beyond its claim |
| Release authorization | Release authority | Machine verifies | Eligibility within named scope and freshness | Qualification evidence, enrollment, or role assignment |
| Deployment policy reference | Machine record | Release authorization and local policy interpret within bounded semantics | Discovery, pinning, rollout, selection | Artifact identity or automatic permission to use a channel head |
| Enrollment binding | Enrollment authority and current machine record | Machine state and status attest | Machine-record lookup and selection | OS rollback state or release authority |
| Bootstrap hint | Provisioning environment | Provisioning evidence records | Locate candidate provisioning intent | Role assignment, enrollment proof, or deployment authorization |
| Provisioning intent | Separately authenticated provisioning authority | Provisioning record attests completion | Storage preparation and enrollment | Continuing normal configuration authority |
| Late-bound contract | Resolved identity-bound configuration | Deployment manifest and composition record bind | Runtime consumer, health, support | Secret value or arbitrary target-side policy channel |
| Late-bound value | Declared machine, platform, environment, user, or workload owner | Machine status attests without exposing sensitive bytes | One declared consumer | Deployment content or inherited qualification |
| State contract | Accepted owner-specific intent | Deployment manifest binds compatible contract identities | Eligibility, migration, backup, recovery | State contents or filesystem-path inference |
| Local blessing | Machine lifecycle state | Status attests for exact deployment identity | Subsequent local selection | Release authorization or global qualification |
| Administrator override | Administrator state | Machine realization reports exact effect | Support, health, recovery | Silent release-owned configuration |

The table resolves the apparent duplication in machine records, deployment
manifests, and release authorizations: the machine record owns role assignment;
the deployment manifest binds the exact result produced for that assignment;
the qualification record attests what was tested; and release authorization
permits that exact identity within a role scope. None can silently edit the
upstream source of intent.

## One-primary-role check

The initial fleet does not require arbitrary multi-role inheritance:

| Machine | Primary role | Other functions and their ownership |
| --- | --- | --- |
| `reference-vm` | `qualification-fixture` | Workstation and router boot tests are qualification workloads, not additional roles of the fixture. |
| `desktop-jason` | `workstation` | Development containers and microVMs are user/workload state; a future release-owned host service is explicitly part of the workstation role or independently attached with visible status. |
| `router` | `router` | DHCP, DNS, VPN, firewall, monitoring, watchdog, and administration are role services when NeutrinOS owns them; unrelated applications are workloads, not inherited system roles. |

One primary role is sufficient for the initial fleet on paper. A future need to
combine independently maintained base roles is a review trigger. It must not be
approximated with ordering-dependent mixins.

## Shared hardware source versus platform scope

Suppose two future machines use the same board-specific kernel-module and
device policy. The proposed model stores one exact reusable configuration
source and references it from each applicable role or machine source closure.
Its configuration scope is determined by the reference that applies it, while
its bytes and provenance remain shared.

This is slightly more explicit than automatic platform composition, but it
preserves the authority rule: the reviewed machine or role record applies
behavior; observed hardware only proves compatibility. A fourth `platform`
precedence scope is not justified for the initial fleet. Reconsider it only if
measured duplication or error rates exceed the clarity benefit and the design
can prevent observation from becoming intent.

## Adversarial scenarios

| Scenario | Expected result | Paper result |
| --- | --- | --- |
| Hypervisor copies `reference-vm` SMBIOS data into an unrelated guest | Bootstrap lookup may find the record, but enrollment binding fails or requires deliberate re-enrollment; role is not inherited | Pass |
| Router board DMI appears on a test VM | Platform constraint may match only under the declared modeled class; it cannot assign router role | Pass |
| Machine source disables a common trust gate | Value is attributable but post-composition policy rejects the variant | Pass |
| Native setting has no convenience schema | Exact native file proceeds through attribution, native validation, integration qualification, and deployment binding | Pass |
| Credential contains a systemd unit instead of an opaque service value | Contract semantic-power validation rejects it as undeclared normal policy | Pass on paper; schemas remain open |
| Provisioning seed reappears after ordinary reboot | Completion and replay policy make it inert or require deliberate reprovisioning; it cannot overwrite normal configuration | Pass by requirement; mechanism open |
| Same board policy is used by two machines | Both reviewed records reference one exact source; observation alone does not apply it | Pass |
| Release authorization names router scope for workstation-produced bytes | Deployment manifest role binding and qualification identity mismatch; candidate remains ineligible | Pass |
| Old inventory revision produced the currently booted deployment | Status reports the bound historical revision exactly; current desired intent may differ without rewriting deployment evidence | Pass |

## Findings

1. **The three-scope model is sufficient for the initial fleet.** Shared
   sources provide reuse without role inheritance or platform precedence.
2. **One primary role is sufficient initially.** Other functions fit role
   services or independently owned workloads without pretending that a machine
   has several ordered base identities.
3. **The reference VM needs explicit identity lifecycle.** It is a managed
   fixture that may be deliberately reset and re-enrolled, not an identity
   copied into every test guest.
4. **Metadata can default at the source boundary.** Native files need exact
   attribution, but unambiguous scope, owner, and consumer declarations may be
   inherited from their named configuration source rather than repeated per
   file.
5. **Post-composition policy is mandatory.** Fixed precedence explains which
   value wins but cannot authorize violation of accepted invariants.
6. **Machine records own intent; later objects bind or attest.** The field-
   authority table removes the largest apparent duplication among inventory,
   deployment, qualification, authorization, and status.
7. **Late-bound values require semantic-power limits.** A schema and named
   consumer are insufficient when nominal data can introduce privileged policy
   or executable behavior.
8. **Provisioning authentication remains the largest open boundary.** The
   model contains replay and residual-authority requirements but does not yet
   identify the first-enrollment trust path.

## Design and review disposition

EX-0006 resolves DES-0005 review challenges C-001, C-004, and C-005 at the
paper-model level and materially mitigates C-002, C-003, and C-007. C-008 and
C-009 remain open pending the provisioning and enrollment design.

The exercise supports advancing DES-0005 to `in-review`. It did not itself
ratify SYS-042 through SYS-047; those requirements were subsequently accepted
through
[PR-0008](../../project/reviews/0008-fleet-intent-and-configuration-requirements.md).
Neither the exercise nor that review selects serialization or tooling or proves
that the model remains lightweight when instantiated with real native
configuration.

## Follow-up work

- Owner review of one-primary-role, no-platform-scope, and source-level metadata
  defaults.
- Extract representative native configuration from the current private
  `nixconfig` intent without copying secrets or treating Nix expressions as the
  target format.
- Define the first-enrollment authority and provisioning replay state machine.
- Decide which non-overridable invariants need mechanically enforced policy
  identifiers versus qualification tests.
- Review SYS-042 through SYS-047 after incorporating the owner decisions.
