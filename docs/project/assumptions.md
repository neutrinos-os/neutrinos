---
status: draft
last_updated: 2026-08-09
---

# Assumption register

Assumptions are propositions that permit design work to proceed but have not
yet been accepted as requirements or decisions.

| ID | Assumption | Evidence needed or review trigger |
| --- | --- | --- |
| A-001 | A systemd-first lifecycle, including strongly justified non-systemd substrate components, can cover all intended roles. | Trace each role through build, boot, configuration, update, and recovery; reject exceptions whose benefit does not exceed their integration and maintenance cost. |
| A-002 | The package manager can remain a build-time concern for the base OS. | Identify runtime operations that would still require package-manager semantics. |
| A-003 | One deployment-set identity and lifecycle model can span bare metal and virtual machines even when their artifact and storage shapes differ. | EX-0005 traces the model on paper; instantiate reference VM, workstation, and router variants and exercise build, qualification, staging, boot selection, status, rollback, and recovery. |
| A-004 | Mutable state can remain compatible across OS rollback. | Define state schemas and exercise forward/backward transitions. |
| A-005 | Existing upstream tooling can provide most of the image lifecycle. | Gap analysis against bootc, mkosi, repart, sysupdate, boot tooling, and fleet rollout needs. |
| A-006 | Stable UID and subordinate-ID policy is sufficient for initial rootless-container workflows. | Test bind mounts, backup/restore, multi-machine use, and user namespace modes. |
| A-007 | Btrfs is a suitable general default for mutable state. | Workload, failure, repair, quota, encryption, and operational comparison. |
| A-008 | A common, data-first configuration model can express both desktop and network-appliance roles without becoming a general-purpose language or gating native upstream configuration. | Produce representative workstation and router inputs, resolved outputs, and tests; reject the model if ordinary use requires open-ended operator-authored logic. |
| A-009 | A production-supported bootc path may eventually satisfy accepted SYS-030 and the failed-boot requirements. | Reevaluate upstream production support and exercise boot-to-root integrity, signed update, boot assessment, fallback, rollback, and recovery; until then bootc is not the default substrate candidate. |
| A-010 | The accepted manual platform-signing and release-authorization ceremony will remain practical for the initial personal fleet, including an urgent release. | Owner accepted the operating cost on 2026-08-09; test the remaining practicality assumption with a timed disposable-key promotion, emergency gate, and signer-replacement exercise. |
| A-011 | The required offline authority recovery copy or succession path can be implemented outside the primary local-disaster and normal-account failure domains. | Owner confirmed feasibility on 2026-08-09; test it with a private custody worksheet and non-destructive retrieval exercise. |
| A-012 | Two independently enforced routine signing compartments can remain practical for a single-maintainer release flow while sharing a replacement and availability policy. | Select candidate mechanisms, then run timed normal, urgent, substitution, and single-compartment compromise exercises with disposable keys. |
| A-013 | A capability-staged recovery path can remain usable on both a locally serviced workstation and a headless router without collapsing deliberate activation, data unlock, enrollment, platform repair, or normal status into one authority. | Select mechanisms, then exercise workstation-local and router out-of-band recovery with the normal data plane unavailable, disposable identities, scoped test data, and independent evidence retention. |
| A-014 | A production-supported substrate can enforce the complete deployment-set identity and transactional-selection model without NeutrinOS creating its own updater or object store. | RES-0004 completes the documentation mapping and bounds two thin project joins; run symmetric interruption and mismatch spikes against direct systemd/UAPI and bootc paths. |
| A-015 | Binding exact checked-in normal machine configuration to deployment identity can remain practical through shared artifacts or immutable configuration artifacts. | EX-0005 demonstrates the factoring on paper; measure artifact reuse and qualification cost by comparing flattened workstation/router rebuilds with separately bound configuration artifacts. |
