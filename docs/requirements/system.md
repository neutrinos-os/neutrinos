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
| SYS-001 | Candidate | A release must be traceable to source revision, pinned inputs, build configuration, and test results. | Deployment manifest, release authorization, and provenance verification. |
| SYS-002 | Candidate | Qualification must boot and test the same complete immutable deployment-set identity that is offered for deployment. | Deployment-manifest closure, artifact hashes, and boot-test record. |
| SYS-003 | Candidate | A failed or interrupted OS update must have a documented, testable recovery path. | Failure-injection test matrix. |
| SYS-004 | Candidate | The system must identify the owners and lifecycles of OS, machine, administrator, user, and workload state. | State inventory with upgrade, rollback, backup, and reset semantics. |
| SYS-005 | Candidate | Role specialization must retain common deployment identity, release, update, status, and recovery semantics without requiring identical artifact shapes. | Cross-role architecture trace. |
| SYS-006 | Candidate | Machine and role configuration must be reviewable in version control. | Configuration provenance and deployment test. |
| SYS-007 | Candidate | Security mechanisms must state the assets, attackers, guarantees, and recovery behavior they address. | Threat-model traceability. |
| SYS-008 | Candidate | The running machine must expose enough deployment identity to correlate it with its deployment manifest and qualification results. | On-machine identity inspection test. |
| SYS-009 | Candidate | Mutable-state changes must not silently make the advertised rollback path unusable. | Forward/backward state compatibility tests. |
| SYS-010 | Candidate | Every supported role must define externally observable health and acceptance criteria. | Role qualification specification. |
| SYS-011 | Candidate | The system must distinguish the current qualified release from stale, pinned, locally modified, and unsupported deployments. | Machine inventory and release-identity inspection. |
| SYS-012 | Candidate | An emergency release must retain minimum provenance, integrity, literal-artifact boot, changed-behavior, and rollback qualification. | Emergency release test record and documented skipped checks. |
| SYS-013 | Candidate | Every deployed software component must expose who owns its vulnerability monitoring and update lifecycle. | Cross-component maintenance ownership inventory. |
| SYS-014 | Accepted | Normal machine and role intent must be expressible as bounded declarative data or upstream-native configuration; understanding it must not require evaluating a general-purpose programming language. | Representative workstation and router configurations reviewed without composition-engine knowledge. |
| SYS-015 | Accepted | A missing project convenience schema must not prevent use of a supported upstream setting; native configuration and explicit pass-through inputs must remain attributable and testable. | Exercise an unmodeled upstream setting through the documented native-input path and trace it into qualification evidence. |
| SYS-016 | Accepted | Configuration composition must have deterministic precedence and expose the fully resolved inputs and generated native configuration used for an artifact. | Composition inspection and conflicting-override tests. |
| SYS-017 | Accepted | Deployment must select a previously built and qualified artifact rather than evaluate arbitrary machine configuration or reconstruct an equivalent OS on the machine. | Deployment trace joined to the qualified artifact identity. |
| SYS-018 | Accepted | A configuration or deployment failure must identify the responsible input, configuration scope, generated output, and lifecycle stage. | Negative tests for schema, composition, generation, staging, selection, boot, and health-assessment failures. |
| SYS-019 | Accepted | Every persistent state item or namespace must identify its lifecycle owner, authority, schema or format, compatibility, migration, backup, recovery, and reset behavior. | State-contract inventory traced to workstation and router acceptance tests. |
| SYS-020 | Accepted | The normal effective `/etc` must be reconstructible from identified inputs; every persistent exception and administrator override must be explicit, attributable, inspectable, and reflected in machine support status. | Clean reconstruction, persistent-exception inventory, and locally-modified status tests. |
| SYS-021 | Accepted | Before a deployment becomes eligible for selection, its release must declare and verify read/write compatibility with the machine's state schema and every deployment offered as an automatic fallback candidate. | Compatibility matrix and candidate/fallback tests against post-update state. |
| SYS-022 | Accepted | A state migration must be idempotent or detect completion and must define its interruption, retry, reversal, checkpoint, and recovery behavior. | Failure injection at each migration boundary. |
| SYS-023 | Accepted | A release with a forward-only destructive migration must expose an explicit commit barrier and must not advertise normal automatic fallback after crossing it. | Maintenance-release exercise with backup verification and recovery evidence. |
| SYS-024 | Accepted | Reinstall, reprovision, and recovery must preserve only state selected by an ownership-aware preservation manifest rather than an undifferentiated mutable filesystem. | Recovery tests with mixed machine, user, workload, cache, secret, and diagnostic state. |
| SYS-025 | Accepted | Machine identity, enrollment records, and secrets must have lifecycles independent of OS rollback, including rotation, revocation, regeneration or restore, and destruction. | Re-enrollment, revocation, rollback, and factory-reset tests. |
| SYS-026 | Accepted | Failed-update diagnostics must remain available through rollback or recovery subject to explicit sensitivity, retention, and storage limits. | Failure evidence retrieval, redaction, rotation, and full-storage tests on each role. |
| SYS-027 | Accepted | Every security claim must identify its protected assets, attacker capabilities, trust assumptions, guarantees, non-guarantees, and compromise-recovery behavior for each applicable role. | Threat-to-control trace reviewed against workstation and router scenarios. |
| SYS-028 | Candidate | A deployable release authorization must bind the immutable artifact set, applicable role or channel, configuration identity or compatibility, and freshness policy independently of its transport location or mutable discovery name. | Registry and metadata substitution tests against a signed release authorization joined to its deployment manifest. |
| SYS-029 | Candidate | A machine must verify release authorization and content identity before a candidate can replace or outrank its currently selected deployment; failed or interrupted verification must leave that selection intact. | Corruption, substitution, interruption, and partial-staging tests. |
| SYS-030 | Accepted | Normal boot on a production physical role must authenticate, from the configured platform trust anchor, every release-owned boot artifact and the release-owned root content before executing or mounting it as normal release-owned content. | Tamper tests for bootloader, kernel, initrd, command line or equivalent policy, and immutable root. |
| SYS-031 | Candidate | Machine status must report release identity, authorization, boot integrity verification, provenance, qualification, freshness, currentness, support, and local modification as distinct properties. | Status-schema tests covering every independent combination relevant to operations and recovery. |
| SYS-032 | Accepted | Every signing, enrollment, platform, machine, recovery, and data-encryption authority must define scope, storage, delegation, rotation, revocation, audit, loss, compromise, backup or regeneration, and destruction behavior. | Exercised authority inventory and loss/rotation/revocation runbook. |
| SYS-033 | Accepted | Recovery authorization must remain independently usable after loss or compromise of the normal release signer and must not silently authorize a normal fleet release. | Offline recovery after signer loss and compromise. |
| SYS-034 | Accepted | Each role must declare the data protected against powered-off device loss and an unlock/recovery model consistent with its unattended availability requirements. | Workstation theft-confidentiality test and router unattended reboot/recovery test. |
| SYS-035 | Candidate | Compromise recovery must treat mutable executable state, machine identity, administrator overrides, user state, and workload state as potentially hostile and support owner-aware quarantine, selective restore, re-enrollment, or destruction. | Compromise-recovery exercise distinct from ordinary OS rollback. |
| SYS-036 | Candidate | Cryptographic authorization must not substitute for provenance or qualification; promotion must verify that the authorized artifact identities are the literal qualified outputs. | Negative test signing an attributable but unqualified rebuild. |
| SYS-037 | Candidate | Freshness, revocation, and downgrade policy must distinguish normal, recovery-only, and withdrawn artifacts without making declared offline recovery impossible. | Offline rollback/recovery tests after expiry, withdrawal, clock failure, and authority unavailability. |

## Interpretation of SYS-014 through SYS-018

`Bounded declarative data` means an operator-facing format without user-defined
functions, arbitrary evaluation, or a programmable module system. References,
explicit overlays, and conditional behavior supplied by separately owned and
tested tooling are not prohibited.

An upstream-native or pass-through path is not an uncontrolled bypass. It must
identify its owner and consuming component, participate in deterministic
composition, and remain subject to policy, validation where available, and
role qualification.

SYS-017 does not require secrets, enrollment records, or hardware-derived
values to be embedded in a release artifact. Late-bound inputs may be supplied
through a separately defined and qualified contract; they must not cause the
machine to build or evaluate a different OS release.

SYS-014 through SYS-018 are derived from the
[NixOS configuration and deployment retrospective](../research/experience/nixconfig-retrospective.md)
and were accepted through the
[configuration authoring boundary review](../project/reviews/0002-configuration-authoring-boundary.md).

SYS-019 through SYS-026 are derived from
[DES-0002](../designs/0002-state-ownership/README.md) and were accepted through
the [state ownership requirements review](../project/reviews/0003-state-ownership-requirements.md).

SYS-027 through SYS-037 are derived from
[DES-0003](../designs/0003-threat-and-trust-model/README.md). SYS-030 was
accepted through the
[boot-to-root integrity review](../project/reviews/0004-boot-to-root-integrity.md).
SYS-027 and SYS-034 were accepted through the
[role security and availability review](../project/reviews/0005-role-security-and-availability-objectives.md).
SYS-032 and SYS-033 were accepted through the
[authority and recovery policy review](../project/reviews/0006-authority-and-recovery-policy.md).
The others remain candidate requirements pending review.
