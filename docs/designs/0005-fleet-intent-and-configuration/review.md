---
design: DES-0005
reviewer: Codex adversarial pass
perspective: operability, ambiguity, security, failure, alternatives
date: 2026-08-09
status: accepted
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
- Author response: EX-0006 models source-level metadata defaults. EX-0007 then
  translates sanitized router intent into literal networkd, unit, timer,
  sysctl, tmpfiles, sysusers, nftables, mount, and kernel-command-line inputs.
  Its representative source manifest defaults scope, owner, consumer, target
  mapping, and mode while listing the exact file closure.
- Disposition: resolved at the paper and local-intent level; implementation
  effort remains a spike measurement.
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
- Author response: EX-0006 enumerates the accepted project and role invariants
  that ordinary precedence cannot override.
- Disposition: mitigated at the policy level; enforcement representation
  remains open.
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
- Author response: EX-0006 classifies the initial functions as one primary role,
  release-owned role services, or independently owned workloads without using
  multi-role inheritance.
- Disposition: mitigated and accepted for the initial fleet; multi-role
  composition remains a review trigger.
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
- Author response: the EX-0006 field-authority table assigns desired intent to
  inventory and role/machine records, exact output binding to the deployment
  manifest, claims to qualification, permission to release authorization, and
  observations to status.
- Disposition: resolved at the model level.
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
- Author response: EX-0006 applies one reusable hardware-specific source through
  explicit role or machine references and rejects platform precedence for the
  initial fleet.
- Disposition: resolved for the initial model; measured duplication is a review
  trigger.
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
- Author response: EX-0006 inventories representative contracts and adds
  semantic-power limits that prohibit nominal data from carrying undeclared
  units, scripts, package selections, or privileged policy.
- Disposition: mitigated at the paper-model level; real consumer schemas remain
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
- Disposition: mitigated by accepted SYS-047; mechanism remains open.
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

## Remaining evidence

- An authenticated first-enrollment sequence with hostile SMBIOS or instance
  metadata.
- Parser, JSON Schema validator, and canonicalization agreement over positive
  and negative fixture corpora.
- Literal native-output validation and inspection using built artifacts rather
  than the EX-0007 paper fixtures.

## Required changes before acceptance

1. **Complete on paper:** EX-0006 provides representative machine records
   without selecting a final serialization format.
2. **Complete on paper:** EX-0006 provides the field-authority table and removes
   duplicate sources of intent.
3. **Complete at policy level:** EX-0006 enumerates non-overridable invariants;
   enforcement and exception representation remain open.
4. **Complete on paper:** EX-0006 classifies representative late-bound inputs
   and their permitted semantic power.
5. **Complete:**
   [PR-0008](../../project/reviews/0008-fleet-intent-and-configuration-requirements.md)
   accepts one primary role plus services/workloads for the initial fleet, with
   multi-role composition retained as a review trigger.
6. **Complete at requirement level:** PR-0008 accepts SYS-042 through SYS-047
   with explicit minimal-metadata, native-composition, semantic-power, and
   provisioning guardrails. Implementation evidence remains open.
7. **Complete on paper:** RES-0005 compares TOML, restricted YAML, JSON, CUE,
   and native-only alternatives and proposes a bounded authoring/validation
   split with explicit falsification and implementation gates.
8. **Complete on paper:** EX-0007 exercises native formats, consumer-specific
   semantics, explicit deletion, and bidirectional inspection against
   sanitized current router intent.

## Review disposition

DES-0005 and its ADR-0003 representation boundary are accepted. Parser/tool
selection remains a required spike, while provisioning mechanism plus first-
enrollment authentication remain follow-on work under L-003; the already
accepted SYS-047 boundary remains normative.
