---
design: DES-0001
reviewer: Codex adversarial pass
perspective: lifecycle, integrity, failure, roles, operations, alternatives
date: 2026-08-09
status: open
---

# System model and deployment unit review

## Summary judgment

The deployment-set model closes a real ambiguity: the atomic unit is the bound
closure of release-owned artifacts, not whichever one happens to be easiest to
name in a chosen substrate. It is compatible with both a direct systemd/UAPI
resource set and a bootc/OCI implementation.

The strongest reason to reject it is operational. A project-level manifest,
per-machine variants, combined qualification evidence, and cross-resource
selection could become a custom lifecycle product layered over upstream tools.
The design is valuable only if the selected substrate can enforce most of the
model natively and NeutrinOS owns policy and evidence rather than another
updater or object store.

## Challenges

### C-001: “Atomic deployment set” may be a fiction over torn resources

- Severity: critical
- Claim: boot, root, extension, configuration, and selection metadata can be
  updated independently, so a power loss or bootloader behavior may expose a
  hybrid even when the project manifest describes a complete set.
- Failure or cost if true: a machine boots bytes that were never jointly
  qualified or cannot fall back to the prior complete deployment.
- Required response or experiment: fault-inject every transfer and selection
  boundary on each substrate; verify inactive staging, complete-closure checks,
  one commit point, boot-time binding, and preservation of the prior selection.
- Author response: atomicity is explicitly selection eligibility rather than a
  claim of one physical write. Partial content is inert and early boot must bind
  what it uses to the selected manifest.
- Disposition: mitigated at the policy level; remains a critical substrate
  acceptance test.
- Residual risk: firmware and bootloader variables may have weaker transactional
  behavior than the root storage mechanism.

### C-002: Late-bound configuration can recreate an unqualified machine

- Severity: critical
- Claim: schemas and representative tests do not prove the actual network,
  hardware, secret, or machine inputs produce the qualified behavior.
- Failure or cost if true: the project advertises literal-artifact testing while
  important normal behavior is assembled only on the target.
- Required response or experiment: classify representative workstation and
  router inputs; require exact non-secret normal configuration to determine the
  deployment or a named immutable configuration artifact; enumerate the narrow
  value classes that remain late-bound and their observable failures.
- Author response: the design reserves late binding for independently owned
  secret, hardware, and environment values. Normal checked-in configuration is
  part of the deployment identity, while actual late-bound values remain
  visible in machine realization and support status.
- Disposition: mitigated at the policy level; concrete configuration artifacts
  and input schemas remain open under decision-backlog items C-001 and S-003.
- Residual risk: pressure to reuse a generic image can gradually move behavioral
  policy into unqualified first-boot logic.

### C-003: Extension mechanisms can bypass the deployment identity

- Severity: critical
- Claim: sysext, confext, portable services, bootloader add-ons, kernel modules,
  containers, administrator units, and user services can execute code without
  changing the base root identity.
- Failure or cost if true: an exact and boot-authenticated base deployment gives
  a misleading trusted or qualified status while privileged mutable code
  persists across rollback.
- Required response or experiment: inventory every executable input on the
  reference VM, workstation, and router; bind release-owned privileged
  extensions into the deployment set and assign every remaining input an owner,
  authorization, lifecycle, and effective-status consequence.
- Author response: the design denies inherited qualification to all executable
  content outside the deployment closure and requires release-owned privileged
  extensions to be named by it. EX-0004 assigns platform, release, machine,
  administrator, user, workload, and recovery inputs separate identity,
  authorization, lifecycle, and status consequences.
- Disposition: resolved at the design-policy level through
  [EX-0004](../../research/exercises/0004-executable-input-inventory.md).
  Concrete artifact and loader inventories remain required evidence.
- Residual risk: the boundary between OS extension and independently managed
  workload may be contested by real desktop and networking software.

### C-004: Exact machine variants may create a build and test explosion

- Severity: high
- Claim: binding all checked-in normal machine configuration can produce a
  separate artifact set and full qualification matrix for every host.
- Failure or cost if true: routine updates become too slow, storage-heavy, or
  manual, causing skipped qualification or pressure for unsafe generic images.
- Required response or experiment: build representative workstation and router
  manifests, measure shared artifact reuse and test duration, and compare a
  separate immutable configuration artifact with per-machine root rebuilds.
- Author response: machine variants are permitted, not required to duplicate
  every artifact. Content sharing and separately bound immutable configuration
  artifacts may preserve exact identity without pretending configuration is
  late-bound state. EX-0005 demonstrates flattened and shared-artifact
  workstation/router manifests and limits evidence reuse to exact tested
  artifacts and claims.
- Disposition: mitigated at the paper level through
  [EX-0005](../../research/exercises/0005-representative-deployment-manifests.md);
  measured build, transfer, retention, and qualification cost remains open.
- Residual risk: a personal fleet may hide costs that become prohibitive for the
  intended reusable framework.

### C-005: Deployment rollback can still overpromise state rollback

- Severity: critical
- Claim: users may interpret reselecting old OS bytes as restoring the complete
  machine even after schemas, credentials, or user data changed.
- Failure or cost if true: automatic fallback corrupts or exposes state, or a
  nominally successful rollback restores revoked identity.
- Required response or experiment: make compatibility a pre-selection gate,
  remove old sets from automatic eligibility after a forward-only barrier, and
  show machine identity and state do not roll back with OS bytes.
- Author response: accepted SYS-019 through SYS-025 and DES-0002 define exactly
  those boundaries; the design uses `deployment rollback` only for immutable
  set reselection.
- Disposition: resolved at the requirement level; substrate and role exercises
  remain open.
- Residual risk: user interfaces and operator shorthand may continue saying
  “system rollback” without exposing the state boundary.

### C-006: A release collection can hide cross-role incompatibility

- Severity: high
- Claim: one release label for workstation and router variants implies they are
  mutually compatible and maintained together even when one role is delayed or
  lacks a passing artifact.
- Failure or cost if true: machines report the same version while their shared
  protocols, administration expectations, or support states conflict.
- Required response or experiment: define release membership and cross-variant
  compatibility claims explicitly; exercise a release where the router variant
  is withheld while the workstation advances.
- Author response: each variant retains independent identity, qualification,
  rollout, and support. Shared membership makes only declared compatibility
  claims and cannot reconstruct or authorize a missing variant.
- Disposition: mitigated at the policy level; concrete release metadata remains
  open under L-006.
- Residual risk: human-readable versions can still be mistaken for a complete
  fleet state.

### C-007: Blessing can be mistaken for security or global qualification

- Severity: high
- Claim: a booted candidate can report health dishonestly or pass shallow checks,
  and one successful machine may be treated as proof for every target.
- Failure or cost if true: a malicious or role-broken release becomes the stable
  default and its local success launders weak pre-release qualification.
- Required response or experiment: distinguish pre-release qualification from
  per-machine boot assessment; use role-specific external observations where
  feasible; scope blessing to one deployment on one machine.
- Author response: blessing affects local selection only and is reported apart
  from qualification, authorization, freshness, and compromise status.
- Disposition: mitigated; actual health policies remain open under SYS-010 and
  L-004.
- Residual risk: the router needs an observer outside its failed data plane, and
  the workstation has important health visible only after user interaction.

### C-008: A project manifest may duplicate substrate-native identity

- Severity: high
- Claim: OCI, OSTree, DDI, or sysupdate resource identities may already bind the
  necessary bytes, while another NeutrinOS manifest creates adapters, schemas,
  migration, and signing work.
- Failure or cost if true: the project recreates the lifecycle infrastructure it
  explicitly intends to borrow.
- Required response or experiment: map every deployment-set field to each
  production-supported candidate; use the substrate's native immutable identity
  directly when it covers the full closure and evidence joins.
- Author response: `deployment manifest` is a semantic role, not necessarily a
  new file format. A substrate-native object may fill it if it satisfies the
  complete model. RES-0004 maps a sysupdate host target and a bootc OCI digest
  to that role, identifies their remaining closure gaps, and limits proposed
  NeutrinOS ownership to a detached evidence envelope and read-only status/gate
  join.
- Disposition: mitigated at the documentation level through
  [RES-0004](../../research/comparisons/deployment-set-substrate-mapping.md);
  symmetric production-supported spikes must prove the joins remain thin.
- Residual risk: policy metadata not native to either candidate may still force
  a small project-owned signed envelope.

### C-009: Signing and qualification can create an identity cycle

- Severity: high
- Claim: platform signing changes boot bytes, qualification adds evidence, and
  release authorization signs the result; an incautious “release manifest” can
  recursively contain its own signatures or cause testing of pre-signing bytes.
- Failure or cost if true: the final deployed object differs from the qualified
  object or cannot have a stable identity.
- Required response or experiment: model the literal objects and exercise
  substitution at every join.
- Author response: platform signing precedes artifact identity and deployment
  manifest creation; qualification binds that immutable identity; detached
  release authorization binds deployment and qualification identities. EX-0002
  already rejects pre-signing qualification and coordinator-controlled joins.
- Disposition: resolved at the design-policy level; format validation remains
  open.
- Residual risk: implementation tooling may use the overloaded word `manifest`
  for several objects and accidentally reorder the flow.

### C-010: Installation and storage migration can escape the lifecycle

- Severity: high
- Claim: a full-disk installer or repartitioning update modifies boot policy,
  trust state, and mutable containers beyond the normal deployment set.
- Failure or cost if true: the project labels a destructive machine operation
  as an ordinary atomic OS update and has no independent rollback boundary.
- Required response or experiment: classify installer and disk-layout changes as
  explicit provisioning or maintenance operations with their own state,
  authority, interruption, and recovery plans.
- Author response: the design treats disk and VM images as transport wrappers
  and storage migration as a separate operation rather than release identity.
- Disposition: mitigated; concrete storage design remains open under S-004 and
  installation under L-003.
- Residual risk: upstream tooling may make ordinary image and layout updates
  look syntactically identical despite different failure domains.

## Missing alternatives or evidence

- Instantiated field-by-field mappings using literal production-supported bootc
  and direct systemd/UAPI objects and observed machine behavior.
- Concrete artifact and loader inventories confirming the EX-0004 paper model
  on both substrate candidates and all reference roles.
- Instantiated workstation and router manifests using the literal objects and
  native configuration outputs from both substrate candidates.
- Power-loss injection across multi-resource staging and boot selection.
- A delayed or withdrawn role variant within one release collection.
- Role-specific external health and boot-success definitions.
- Garbage-collection proof for shared artifact closure and retained recovery.

## Required changes before acceptance

1. **Open:** obtain owner review of the deployment-set boundary and the meaning
   of atomic selection.
2. **Complete at policy level:** EX-0004 inventories executable inputs and
   disposes of C-003 without claiming that immutable base identity covers
   mutable code. Concrete substrate and role inventories remain open evidence.
3. **Complete at paper level:** EX-0005 provides representative VM,
   workstation, and router manifests, configuration classifications, factoring
   alternatives, and qualification boundaries. Literal substrate manifests and
   measurements remain open evidence.
4. **Complete at documentation level:** RES-0004 maps the model to both
   candidates, rejects a custom updater/object store, and bounds the two
   justified project joins. Symmetric production-supported spikes remain open.
5. **Open:** review which candidate lifecycle requirements should become
   normative before the substrate ADR.

## Review disposition

DES-0001 should advance from `sketch` to `in-review`, but not to `accepted`.
Its core deployment-set boundary and executable-input ownership rule are
coherent on paper. No critical policy ambiguity remains in C-003, but the
substrate and role evidence needed to show that the abstraction is complete and
operable has not yet been produced.
