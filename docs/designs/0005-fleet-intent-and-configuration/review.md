---
design: DES-0005
reviewer: Codex adversarial pass
perspective: operability, ambiguity, security, failure, alternatives
date: 2026-08-09
status: open
---

# Fleet intent and configuration composition review

## Summary judgment

The proposed design has the right authority boundary: checked-in intent
determines release-owned behavior, while platform observation, provisioning,
and late-bound values cannot silently reconstruct it on the machine. Fixed
three-scope composition is materially easier to review than a programmable
module graph and still leaves upstream-native configuration usable.

The strongest objection is that the metadata surrounding each input could
become a universal configuration schema in disguise. Machine records,
configuration-source declarations, composition records, late-bound contracts,
and policy validators are justified only when each field drives identity,
attribution, validation, selection, status, or recovery.

## Challenges

### C-001: Source metadata becomes more work than native configuration

- Severity: critical
- Claim: requiring owner, consumer, output key, merge policy, schema, and
  lifecycle metadata for every native file can make a simple systemd unit
  harder to add than it is upstream.
- Required response or experiment: write representative common, workstation,
  and router inputs using mostly native files; measure duplicated declarations
  and identify defaults that remain unambiguous.
- Disposition: open.
- Residual risk: a convenience schema can slowly become mandatory even though
  SYS-015 prohibits that outcome.

### C-002: Fixed precedence is deterministic but can still be unsafe

- Severity: critical
- Claim: `machine` winning over `role` can disable Secure Boot policy, health
  observation, firewall defaults, or recovery requirements while still
  producing a clean composition record.
- Required response or experiment: enumerate non-overridable project and role
  invariants and show post-composition policy rejecting representative unsafe
  machine values.
- Disposition: mitigated in the design; the concrete invariant set remains
  open.
- Residual risk: policy exceptions can recreate an unreviewed second
  authorization language.

### C-003: One primary role may be artificially restrictive

- Severity: high
- Claim: a workstation can also host storage or VM services, while a router can
  provide DNS, VPN, monitoring, and other functions. Creating a new composite
  role for every combination can multiply variants.
- Required response or experiment: classify representative functions as base
  role behavior, release-owned service, or independently managed workload and
  show that one role does not prohibit composition at those ownership
  boundaries.
- Disposition: open.
- Residual risk: arbitrary multi-role inheritance would recreate the graph the
  design is trying to avoid.

### C-004: Machine records can duplicate deployment policy

- Severity: high
- Claim: channel, platform, health, state, and late-bound references may appear
  in machine records, role definitions, deployment manifests, and release
  authorizations with inconsistent values.
- Required response or experiment: produce a field-authority table identifying
  which object owns each declaration and which later objects bind or attest to
  it without becoming another source of intent.
- Disposition: open.
- Residual risk: a signed downstream copy can appear authoritative even when it
  attests to stale source intent.

### C-005: Platform class without a configuration scope may cause duplication

- Severity: high
- Claim: several machines with the same board may need the same module,
  firmware, storage, or device policy, forcing repeated machine references.
- Required response or experiment: model a shared hardware-specific source
  explicitly referenced by several machine records and compare it with a
  platform scope. Confirm that reference reuse does not let observation assign
  behavior.
- Disposition: open.
- Residual risk: adding platform precedence later would change existing
  configuration meaning.

### C-006: Composition reproducibility can overstate build reproducibility

- Severity: high
- Claim: identical resolved configuration does not prove that renderer,
  package, filesystem, timestamp, or signing outputs are reproducible.
- Required response or experiment: scope the composition record to input and
  rendered-output attribution and keep broader build provenance under L-002.
- Disposition: mitigated by SYS-001 and the design wording.
- Residual risk: status may still present `reproduced configuration` as
  `reproducible deployment`.

### C-007: Late-bound contracts can become a target-side policy channel

- Severity: critical
- Claim: a credential or metadata value can carry units, firewall rules,
  package selections, or scripts while technically satisfying a declared
  schema.
- Required response or experiment: classify the reference-machine late-bound
  inputs, constrain their semantic effects, and reject one that attempts to
  introduce executable normal policy.
- Disposition: mitigated in principle; representative contract review remains
  open.
- Residual risk: some upstream services intentionally consume powerful policy
  as data and may need to be deployment-bound despite changing frequently.

### C-008: Bootstrap hints remain an enrollment confusion attack

- Severity: critical
- Claim: a malicious hypervisor, metadata service, or copied SMBIOS value can
  direct a blank machine to another machine record before it has an identity.
- Required response or experiment: define authenticated provisioning intent,
  duplicate-record handling, replay behavior, and what local or offline owner
  action confirms first enrollment.
- Disposition: open under L-003.
- Residual risk: first enrollment has no pre-existing machine identity and
  necessarily depends on another trust path.

### C-009: Provisioning transport may leave persistent authority behind

- Severity: critical
- Claim: Ignition, cloud-init, metadata disks, kernel arguments, or seed media
  can be re-read after enrollment and overwrite identity or release-owned
  configuration.
- Required response or experiment: define completion state, replay protection,
  evidence retention, source removal, and behavior when the input reappears.
- Disposition: mitigated by SYS-047 as proposed; mechanism remains open.
- Residual risk: some environments continuously expose instance metadata and
  make true source removal impossible.

### C-010: A separate inventory repository complicates atomic evidence

- Severity: medium
- Claim: framework, inventory, policy, and source revisions in different
  repositories can drift or make one deployment impossible to reproduce.
- Required response or experiment: treat each exact revision as a pinned input
  in one composition record and exercise both co-located and external inventory
  references before splitting repositories.
- Disposition: mitigated in the logical model; operational cost remains open.
- Residual risk: access control and availability for a private inventory can
  impair qualification or recovery.

## Missing alternatives or evidence

- Concrete machine records for the reference VM, `desktop-jason`, and `router`.
- A field-authority table across inventory, role, machine, composition,
  deployment manifest, authorization, status, and provisioning records.
- Native systemd, networkd, tmpfiles, sysusers, kernel-command-line, and mount
  examples exercising conflict and deletion rules.
- A late-bound contract inventory for both physical roles.
- An authenticated first-enrollment sequence with hostile SMBIOS or instance
  metadata.
- A comparison of explicit shared hardware sources with a fourth platform
  configuration scope.

## Required changes before acceptance

1. Produce representative machine records without selecting a final
   serialization format.
2. Produce the field-authority table and remove duplicate sources of intent.
3. Enumerate non-overridable invariants and exception authority.
4. Classify representative late-bound inputs and their permitted semantic
   power.
5. Decide whether one primary role plus services/workloads is sufficient for
   the initial fleet.
6. Review SYS-042 through SYS-047 for acceptance, revision, or rejection.

## Review disposition

DES-0005 should advance to `in-review` after the paper artifacts above resolve
C-001 through C-005 and C-007. Provisioning mechanism and first-enrollment
authentication may remain open under L-003, but the authority boundary and
replay requirements must be normative before accepting this design.
