---
status: active
last_updated: 2026-08-09
---

# System requirements

These requirements are extracted from the design session and subsequent
research. The status of each requirement is tracked independently. `Accepted`
means the requirement is normative project policy, not that a design has yet
satisfied it. `Superseded` preserves an earlier requirement whose normative
replacement is identified by its acceptance review.

| ID | Status | Requirement | Acceptance evidence |
| --- | --- | --- | --- |
| SYS-001 | Accepted | A release must be traceable to source revision, pinned inputs, build configuration, and test results. | Deployment manifest, release authorization, and provenance verification. |
| SYS-002 | Accepted | Qualification must boot and test the exact deployment identity and complete deployment closure that are offered for deployment. | Deployment manifest, deployment closure, artifact digests, and boot-test record. |
| SYS-003 | Accepted | A failed or interrupted deployment-lifecycle transition must leave the prior valid selection intact, select another eligible retained deployment, or preserve a documented, testable path to deliberate recovery. | Failure-injection test matrix for every lifecycle transition. |
| SYS-004 | Superseded | The system must identify the owners and lifecycles of OS, machine, administrator, user, and workload state. | Superseded by SYS-019. |
| SYS-005 | Accepted | Role specialization must retain common deployment identity, release, update, status, and recovery semantics without requiring identical artifact shapes. | Cross-role architecture trace. |
| SYS-006 | Superseded | Machine and role configuration must be reviewable in version control. | Superseded by SYS-014 through SYS-018. |
| SYS-007 | Superseded | Security mechanisms must state the assets, attackers, guarantees, and recovery behavior they address. | Superseded by SYS-027. |
| SYS-008 | Accepted | The running machine must expose its exact booted deployment identity and the evidence needed to correlate it with its deployment manifest, release authorization, and qualification record. | On-machine identity and evidence-correlation test. |
| SYS-009 | Superseded | Mutable-state changes must not silently make the advertised rollback path unusable. | Superseded by SYS-021 through SYS-023. |
| SYS-010 | Accepted | Every supported role must define externally observable health and acceptance criteria. | Role qualification specification. |
| SYS-011 | Superseded | The system must distinguish the current qualified release from stale, pinned, locally modified, and unsupported deployments. | Superseded by SYS-031. |
| SYS-012 | Accepted | An emergency release must retain minimum provenance, content integrity, literal-artifact boot, changed-behavior qualification, and an applicable fallback, rollback, or maintenance-recovery exercise; skipped normal checks and reduced claims must remain explicit. | Emergency release evidence, exercised return path, and documented skipped checks and reduced claims. |
| SYS-013 | Accepted | Every deployed software component must expose who owns its vulnerability monitoring and update lifecycle. | Cross-component maintenance ownership inventory. |
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
| SYS-028 | Accepted | A deployable release authorization must bind the exact deployment identity, qualification record, authorization scope, configuration identity or compatibility, and freshness policy independently of transport location or mutable discovery name. | Registry and metadata substitution tests against a release authorization joined to its deployment manifest and qualification record. |
| SYS-029 | Accepted | A candidate must be fully staged and eligible before it can replace or outrank the currently selected deployment; failed or interrupted acquisition, verification, or eligibility evaluation must leave that selection intact. | Corruption, substitution, interruption, policy-gate, and partial-staging tests. |
| SYS-030 | Accepted | Normal boot on a production physical role must authenticate, from the configured platform trust anchor, every release-owned boot artifact and the release-owned root content before executing or mounting it as normal release-owned content. | Tamper tests for bootloader, kernel, initrd, command line or equivalent policy, and immutable root. |
| SYS-031 | Accepted | Machine status must report deployment identity, authorization, boot integrity verification, provenance, qualification, freshness, currentness, compatibility, health, blessing, support, and local modification as distinct properties. | Status-schema tests covering every independent combination relevant to operations and recovery. |
| SYS-032 | Accepted | Every signing, enrollment, platform, machine, recovery, and data-encryption authority must define scope, storage, delegation, rotation, revocation, audit, loss, compromise, backup or regeneration, and destruction behavior. | Exercised authority inventory and loss/rotation/revocation runbook. |
| SYS-033 | Accepted | Recovery authorization must remain independently usable after loss or compromise of the normal release signer and must not silently authorize a normal fleet release. | Offline recovery after signer loss and compromise. |
| SYS-034 | Accepted | Each role must declare the data protected against powered-off device loss and an unlock/recovery model consistent with its unattended availability requirements. | Workstation theft-confidentiality test and router unattended reboot/recovery test. |
| SYS-035 | Accepted | Compromise recovery must treat mutable executable state, machine identity, administrator overrides, user state, and workload state as potentially hostile and support owner-aware quarantine, selective restore, re-enrollment, or destruction. | Compromise-recovery exercise distinct from ordinary OS rollback. |
| SYS-036 | Accepted | Cryptographic authorization must not substitute for provenance or qualification; promotion must verify that the authorized artifact identities are the literal qualified outputs. | Negative test signing an attributable but unqualified rebuild. |
| SYS-037 | Accepted | Freshness, revocation, and downgrade policy must distinguish deployments authorized for normal use, recovery-only use, and withdrawn use without making declared offline recovery impossible. | Offline rollback and recovery tests after expiry, withdrawal, clock failure, and authority unavailability. |
| SYS-038 | Accepted | Every trial boot must have durable bounded attempt accounting, and a deployment may be blessed only after its exact booted identity passes the applicable role-health assessment. Exhaustion must select an eligible normal fallback or stop with an attributable diagnosis; it must not enter recovery automatically. | Power-loss and repeated-failure tests before, during, and after boot assessment and blessing. |
| SYS-039 | Accepted | Blessing must apply only to one deployment identity on one machine and must not create or replace release authorization, provenance, qualification, compatibility, or fleet-wide health evidence. | Cross-machine and substituted-identity tests proving that one machine's blessing cannot authorize or qualify another deployment. |
| SYS-040 | Accepted | Retention and garbage collection must preserve the complete deployment closure and required selection metadata of every selected or booted deployment and every deployment or recovery environment with a retention reference until that reference is removed. | Shared-content reachability and interruption tests across selection, fallback, rollback, recovery, and garbage collection. |
| SYS-041 | Accepted | Once the required deployment sets, policy, and evidence are retained locally, the control path for normal boot, health-result recording, blessing, fallback, and deliberate rollback must not require a publication service, discovery service, package repository, signing environment, WAN, public DNS, or the machine's own production service path. A failed production service may fail health assessment, but it must not prevent recording that result or selecting an eligible fallback. | Offline lifecycle tests for the reference VM, workstation, and router with all named dependencies unavailable. |
| SYS-042 | Accepted | The authoritative fleet inventory must version machine records, exactly one primary role assignment per machine, platform constraints, and exact configuration-source references independently of runtime observations. | Inventory reconstruction, role-conflict, and observation-drift tests for every reference machine. |
| SYS-043 | Accepted | Platform observations and bootstrap hints must not assign a role or authorize a deployment; normal selection must join an enrolled machine identity's current machine-record binding and role assignment with a compatible platform and eligible deployment identity. | Hostile SMBIOS, metadata substitution, duplicate-record, and re-enrollment tests. |
| SYS-044 | Accepted | Configuration composition must use fixed `common < role < machine` precedence, explicit same-scope conflict and deletion rules, and policy validation after precedence resolution. | Override, tombstone, same-scope conflict, and forbidden-override tests. |
| SYS-045 | Accepted | Every deployment variant must retain an immutable composition record identifying its ordered inputs, tool identities, precedence decisions, validations, resolved configuration, rendered outputs, and declared exceptions. | Bidirectional source-to-output attribution and reproduction tests. |
| SYS-046 | Accepted | Every late-bound input must have an identity-bound contract covering ownership, source, consumer, schema, constraints, delivery or observation, failure behavior, status effect, and qualification fixtures. | Workstation and router late-bound inventories with absent, invalid, stale, and substituted-value tests. |
| SYS-047 | Accepted | Provisioning and enrollment must remain separate from normal configuration and deployment selection, and replay must not silently change role assignment, machine identity, preserved state, or selected deployment. | Interrupted provisioning, replay, reprovision, and ordinary-reboot tests. |

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
SYS-028, SYS-029, SYS-031, and SYS-035 through SYS-037 were accepted through
the [deployment lifecycle requirements review](../project/reviews/0007-deployment-lifecycle-requirements.md).

SYS-038 through SYS-041 sharpen the trial-boot, blessing, retention, garbage-
collection, and offline-operation behavior proposed by
[DES-0001](../designs/0001-system-model/README.md). They were accepted through
the [deployment lifecycle requirements review](../project/reviews/0007-deployment-lifecycle-requirements.md),
which also accepted SYS-001 through SYS-003, SYS-005, SYS-008, SYS-010,
SYS-012, and SYS-013 and superseded SYS-004, SYS-006, SYS-007, SYS-009, and
SYS-011.

SYS-042 through SYS-047 are derived from
[DES-0005](../designs/0005-fleet-intent-and-configuration/README.md) and were
accepted through the
[fleet intent and configuration requirements review](../project/reviews/0008-fleet-intent-and-configuration-requirements.md).
