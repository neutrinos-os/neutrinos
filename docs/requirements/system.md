---
status: active
last_updated: 2026-08-09
---

# System requirements

These requirements are extracted from the design session and subsequent
research. The status of each requirement is tracked independently; `accepted`
means the requirement is normative project policy, not that a design has yet
satisfied it.

| ID | Status | Requirement | Acceptance evidence |
| --- | --- | --- | --- |
| SYS-001 | Candidate | A release must be traceable to source revision, pinned inputs, build configuration, and test results. | Release manifest and provenance verification. |
| SYS-002 | Candidate | Qualification must boot and test the same immutable artifact identity that is offered for deployment. | CI artifact hashes and boot-test record. |
| SYS-003 | Candidate | A failed or interrupted OS update must have a documented, testable recovery path. | Failure-injection test matrix. |
| SYS-004 | Candidate | The system must identify the owners and lifecycles of OS, machine, administrator, user, and workload state. | State inventory with upgrade, rollback, backup, and reset semantics. |
| SYS-005 | Candidate | Role specialization must retain a common build, release, update, and recovery model. | Cross-role architecture trace. |
| SYS-006 | Candidate | Machine and role configuration must be reviewable in version control. | Configuration provenance and deployment test. |
| SYS-007 | Candidate | Security mechanisms must state the assets, attackers, guarantees, and recovery behavior they address. | Threat-model traceability. |
| SYS-008 | Candidate | The running machine must expose enough release identity to correlate it with its manifest and qualification results. | On-machine identity inspection test. |
| SYS-009 | Candidate | Mutable-state changes must not silently make the advertised rollback path unusable. | Forward/backward state compatibility tests. |
| SYS-010 | Candidate | Every supported role must define externally observable health and acceptance criteria. | Role qualification specification. |
| SYS-011 | Candidate | The system must distinguish the current qualified release from stale, pinned, locally modified, and unsupported deployments. | Machine inventory and release-identity inspection. |
| SYS-012 | Candidate | An emergency release must retain minimum provenance, integrity, literal-artifact boot, changed-behavior, and rollback qualification. | Emergency release test record and documented skipped checks. |
| SYS-013 | Candidate | Every installed software layer must expose who owns its vulnerability monitoring and update lifecycle. | Cross-layer maintenance ownership inventory. |
| SYS-014 | Accepted | Normal machine and role intent must be expressible as bounded declarative data or upstream-native configuration; understanding it must not require evaluating a general-purpose programming language. | Representative workstation and router configurations reviewed without composition-engine knowledge. |
| SYS-015 | Accepted | A missing project convenience schema must not prevent use of a supported upstream setting; native configuration and explicit pass-through inputs must remain attributable and testable. | Exercise an unmodeled upstream setting through the documented native-input path and trace it into qualification evidence. |
| SYS-016 | Accepted | Configuration composition must have deterministic precedence and expose the fully resolved inputs and generated native configuration used for an artifact. | Composition inspection and conflicting-override tests. |
| SYS-017 | Accepted | Deployment must select a previously built and qualified artifact rather than evaluate arbitrary machine configuration or reconstruct an equivalent OS on the target. | Deployment trace joined to the qualified artifact identity. |
| SYS-018 | Accepted | A configuration or deployment failure must identify the responsible input, role or machine layer, generated output, and lifecycle stage. | Negative tests for schema, composition, generation, staging, activation, and health failures. |

## Interpretation of SYS-014 through SYS-018

`Bounded declarative data` means an operator-facing format without user-defined
functions, arbitrary evaluation, or a programmable module system. References,
explicit overlays, and conditional behavior supplied by separately owned and
tested tooling are not prohibited.

An upstream-native or pass-through path is not an uncontrolled bypass. It must
identify its owner and target, participate in deterministic composition, and
remain subject to policy, validation where available, and role qualification.

SYS-017 does not require secrets, enrollment records, or hardware-derived
values to be embedded in a release artifact. Late-bound inputs may be supplied
through a separately defined and qualified contract; they must not cause the
target to build or evaluate a different OS release.

SYS-014 through SYS-018 are derived from the
[NixOS configuration and deployment retrospective](../research/experience/nixconfig-retrospective.md)
and were accepted through the
[configuration authoring boundary review](../project/reviews/0002-configuration-authoring-boundary.md).
