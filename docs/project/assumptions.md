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
| A-003 | One artifact model can span bare metal and virtual machines. | Compare role requirements and identify unavoidable variants. |
| A-004 | Mutable state can remain compatible across OS rollback. | Define state schemas and exercise forward/backward transitions. |
| A-005 | Existing upstream tooling can provide most of the image lifecycle. | Gap analysis against bootc, mkosi, repart, sysupdate, boot tooling, and fleet rollout needs. |
| A-006 | Stable UID and subordinate-ID policy is sufficient for initial rootless-container workflows. | Test bind mounts, backup/restore, multi-machine use, and user namespace modes. |
| A-007 | Btrfs is a suitable general default for mutable state. | Workload, failure, repair, quota, encryption, and operational comparison. |
| A-008 | A common, data-first configuration model can express both desktop and network-appliance roles without becoming a general-purpose language or gating native upstream configuration. | Produce representative workstation and router inputs, resolved outputs, and tests; reject the model if ordinary use requires open-ended operator-authored logic. |
| A-009 | A production-supported bootc path may eventually satisfy accepted SYS-030 and the failed-boot requirements. | Reevaluate upstream production support and exercise boot-to-root integrity, signed update, boot assessment, fallback, rollback, and recovery; until then bootc is not the default substrate candidate. |
| A-010 | The accepted manual platform-signing and release-authorization ceremony will remain practical for the initial personal fleet, including an urgent release. | Owner accepted the operating cost on 2026-08-09; test the remaining practicality assumption with a timed disposable-key promotion, emergency gate, and signer-replacement exercise. |
| A-011 | The required offline authority recovery copy or succession path can be implemented outside the primary local-disaster and normal-account failure domains. | Owner confirmed feasibility on 2026-08-09; test it with a private custody worksheet and non-destructive retrieval exercise. |
