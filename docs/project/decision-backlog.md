---
status: active
last_updated: 2026-08-10
---

# Decision backlog

This is the intake queue for project and architectural questions. `Stated
direction` means the design session expressed a strong preference; it does not
mean an ADR has been accepted. Accepted project-scope decisions may be recorded
in the charter or scope document; accepted architectural decisions require an
ADR.

This backlog owns question and decision state. The
[work register](work-register.md) provides the aggregate policy, mechanism,
evidence, implementation, and phase-gate view; plans and issues must not turn
this backlog into a duplicate task tracker.

## Wave 0: project identity

| ID | Question | State | Depends on |
| --- | --- | --- | --- |
| P-001 | What problem and invariant justify NeutrinOS rather than adopting an existing system? | [In review: direct systemd/UAPI composition is the default candidate under SYS-030; bootc remains the lifecycle challenger](../research/comparisons/existing-systems.md) | — |
| P-002 | Is the initial product a personal fleet, reusable framework, or public distribution? | [Accepted: personal fleet and reusable framework](scope.md#initial-operating-scope) | P-001 |
| P-003 | What are the accepted principles and non-goals? | [Accepted after adversarial review](reviews/0001-charter-principles-and-scope.md) | P-001 |
| P-004 | Which role and hardware are the first reference target? | [Accepted: VM qualification, `desktop-jason` first, `router` second](scope.md#initial-target-strategy) | P-001, P-002 |
| P-005 | Is systemd-native composition a project constraint? | [Accepted: systemd-first](../adrs/0001-systemd-first.md) | P-001 |
| P-006 | What is the canonical project name and technical identifier? | [Accepted: NeutrinOS and `neutrinos`](naming.md#decision) | P-002 |
| P-007 | Under what license, and at what visibility, is this repository published? | [Accepted: Apache-2.0 and a public repository](scope.md#licensing-and-visibility) | P-002 |


## Wave 1: system and trust model

| ID | Question | State | Depends on |
| --- | --- | --- | --- |
| S-001 | What is the independently replaceable unit of deployment? | [In review: complete content-identified deployment set](../designs/0001-system-model/README.md) | P-003 |
| S-002 | What belongs to the OS, machine configuration, administrator, user, and workload? | [Ownership boundary accepted; implementation design remains in review](reviews/0003-state-ownership-requirements.md) | S-001 |
| S-003 | How are common and role-specific artifacts composed? | [Accepted: versioned fleet intent resolves common, role, and machine configuration into an identity-bound deployment variant](../designs/0005-fleet-intent-and-configuration/README.md) | P-004, S-001 |
| S-004 | What are the disk, partition, filesystem, and encryption models? | [Storage ownership, integrity, encryption, recovery, and capacity requirements accepted; concrete layout and mechanism design remains in review](reviews/0009-storage-layout-and-encryption-requirements.md) | S-001, S-002 |
| S-005 | What threats and trust assertions govern boot and runtime? | [Boot-to-root and role objectives accepted; remaining threat model in review](reviews/0005-role-security-and-availability-objectives.md) | S-001 |
| S-006 | How are signing keys generated, used, rotated, revoked, and recovered? | [Accepted policy: separate routine, exceptional, machine, and data authorities; mechanism exercises remain](../adrs/0002-separate-authority-and-recovery.md) | S-005 |

## Wave 2: build and lifecycle

| ID | Question | State | Depends on |
| --- | --- | --- | --- |
| L-001 | Which package ecosystem and snapshot policy supply OS inputs? | [Input and snapshot requirements accepted; Fedora stable leads and a literal Arch comparison is required before ecosystem selection](reviews/0010-package-input-requirements.md) | P-002, S-001 |
| L-002 | What reproducibility, provenance, SBOM, and vulnerability guarantees are required? | [Policy boundaries accepted; concrete evidence formats, mechanisms, and costs remain in review](reviews/0011-supply-chain-evidence-requirements.md) | L-001, S-005 |
| L-003 | How is a machine installed and enrolled? | [Policy boundaries accepted; installer, enrollment protocol, record formats, and operating cost remain in review](reviews/0013-installation-and-enrollment-requirements.md) | S-001, S-004, S-006 |
| L-004 | How are releases discovered, staged, booted, blessed, and rolled back? | [Requirements accepted; substrate conformance remains in research, with direct systemd/UAPI leading under SYS-030](reviews/0007-deployment-lifecycle-requirements.md) | S-001, S-004 |
| L-005 | How does mutable state remain safe across upgrade and rollback? | [Requirements accepted; migration and recovery mechanisms remain in review](../designs/0002-state-ownership/README.md#update-and-migration-protocol) | S-002, L-004 |
| L-006 | How are releases promoted, phased, paused, and withdrawn across a fleet? | [Policy boundaries accepted; rollout records, protocol, coordination mechanisms, and operating cost remain in review](reviews/0012-fleet-rollout-requirements.md) | L-002, L-004 |
| L-007 | What are the release cadence and security-response commitments? | [Accepted: single current line and best-effort response](maintenance-policy.md) | P-002, L-001, L-002 |


## Wave 3: configuration and workloads

| ID | Question | State | Depends on |
| --- | --- | --- | --- |
| C-001 | What is the source of truth and representation for machine and role configuration? | [Accepted: TOML records, JSON Schema structural validation, literal native sources, and generated canonical JSON evidence](../adrs/0003-bounded-fleet-intent-representation.md) | S-002, S-003 |
| C-002 | How are `/etc`, local overrides, secrets, and credentials owned and delivered? | [Policy accepted: systemd credentials are the default service interface; custody, envelope, issuer, recovery, and exception mechanisms remain in review](reviews/0014-secret-and-credential-delivery-requirements.md) | C-001, S-005 |
| W-001 | What are the supported identity, UID, sub-ID, and rootless-container semantics? | [Policy accepted: stable inventory-owned durable identity and explicit per-workload maps; exact allocations, classic accounts versus systemd-homed, runtime mappings, and migration remain in review](../designs/0012-unix-identity-and-rootless-containers/README.md) | S-002, C-001 |
| W-002 | What is the microVM artifact, networking, storage, and lifecycle model? | Open | S-003, S-004, C-001 |
| W-003 | Which software belongs in the OS, user environment, project, GUI sandbox, container, or VM? | [Policy accepted: owner/lifecycle placement classes, release-owned role dependencies, effective-access boundaries, and independent update domains; exact mechanisms remain in review](../designs/0013-software-placement/README.md) | S-002, W-001 |
| W-004 | When are role-specific kernels or no-initrd variants justified? | Open | P-004, S-004, L-002 |

## Wave 4: role designs

| ID | Question | State | Depends on |
| --- | --- | --- | --- |
| R-001 | What capabilities and tests define the workstation role? | Open | P-004, C-001, W-003 |
| R-002 | What capabilities and tests define the laptop role? | Open | P-004, C-001 |
| R-003 | What capabilities and tests define the router role? | Open | P-004, C-001 |
| R-004 | What capabilities and tests define server and storage roles? | Open | P-004, C-001, W-002 |
| R-005 | What capabilities and tests define a microVM guest? | Open | P-004, W-002 |
