---
id: DES-0005
title: Fleet intent and configuration composition
status: accepted
owners: [Jason Tarasovic]
reviewers: [Codex]
created: 2026-08-09
last_updated: 2026-08-11
amendment_proposed: 2026-08-11
depends_on: [DES-0001, DES-0002, DES-0003, DES-0006]
decision_backlog: [S-003, C-001, C-002, L-003]
related_adrs: [ADR-0003]
---

# Fleet intent and configuration composition

## Problem

NeutrinOS has accepted an operator-facing configuration boundary but has not
defined the concrete model that turns fleet intent into a deployment variant.
Without that model, `common`, `role`, and `machine` can become informal
directories with order-dependent behavior, a generic image can reconstruct
normal policy at boot, or SMBIOS and provisioning metadata can accidentally
become role-assignment authorities.

The design must preserve the useful parts of checked-in machine configuration
without recreating a programmable module system. It must also allow upstream-
native configuration immediately, including settings for which NeutrinOS has no
convenience schema, while keeping every effective input attributable and
qualified.

## Goals

- Define the authoritative records for fleet, role, platform, and machine
  intent.
- Make role assignment explicit and independent of hardware observation.
- Define deterministic `common < role < machine` composition.
- Preserve upstream-native configuration as a first-class input.
- Produce inspectable resolved configuration, rendered configuration, and a
  composition record for every deployment variant.
- Separate identity-bound configuration from late-bound machine, secret, and
  environmental values.
- Bound SMBIOS, Ignition, cloud-init, and similar facilities to observation or
  provisioning rather than ongoing normal configuration authority.
- Keep the model usable for the initial VM, `desktop-jason`, and `router`
  without assuming a large fleet service.

## Non-goals

- Select a concrete TOML parser, JSON Schema validator, canonicalization
  library, implementation language, or repository split.
- Define a universal schema for systemd, kernel, network, desktop, or workload
  configuration.
- Select a configuration renderer or write its implementation.
- Select an Ignition implementation, cloud-init data source, credential store,
  enrollment protocol, or fleet database.
- Put secret values, private keys, or sensitive recovery locators in version
  control.
- Let one machine have an arbitrary graph of inherited roles or profiles.
- Make provisioning an ordinary OS update or make a provisioner the permanent
  desired-state engine.

## Requirements and constraints

Accepted SYS-014 through SYS-018 require bounded declarative or upstream-native
inputs, deterministic and inspectable composition, deployment of qualified
artifacts, and attributable failures. SYS-019, SYS-020, and SYS-025 keep
effective `/etc`, machine identity, secrets, and persistent exceptions under
explicit ownership. SYS-028, SYS-029, and SYS-031 require exact authorization,
eligibility gates, and independent status properties.

DES-0001 requires normal checked-in non-secret configuration to determine the
deployment identity. EX-0004 denies inherited qualification to mutable
executable inputs, and EX-0005 demonstrates both flattened variants and an
immutable configuration artifact without allowing boot-time reconstruction.

The [project glossary](../../project/glossary.md) is canonical. In particular,
a platform observation can establish compatibility but cannot assign a role or
authorize a deployment.

## Decision drivers

1. An operator must be able to review one machine's effective intent without
   evaluating a general-purpose language.
2. A supported upstream setting must not wait for a project schema addition.
3. The exact configuration qualified in a deployment variant must be
   reconstructible from immutable evidence.
4. Hardware replacement or SMBIOS variation must not silently turn a machine
   into another role.
5. Secrets, enrollment identity, and environmental facts need independent
   lifecycles without becoming an excuse for target-side OS construction.
6. One maintainer must be able to diagnose conflicts and provenance without a
   fleet database or custom control plane.

## Decision

The source of truth for normal fleet intent is a versioned **fleet inventory**
containing machine records and referenced configuration sources. One machine
record assigns exactly one primary role, declares supported platform
constraints, selects machine-scoped configuration sources, and declares its
late-bound and state contracts.

For a selected inventory revision, NeutrinOS composes configuration in the
fixed scope order `common < role < machine`, validates the complete result,
renders upstream-native configuration, and records the exact transformation in
an immutable composition record. The rendered result is placed in release-
owned artifacts or an immutable configuration artifact named by the deployment
manifest. The resulting deployment variant—not the input files in isolation—is
qualified and authorized.

Platform observations, bootstrap hints, provisioning inputs, and late-bound
values may select or satisfy only behavior already declared by the machine
record and deployment manifest. They cannot assign a role, introduce normal
release-owned policy, or produce a different OS deployment on the machine.

## Concrete representation decision

[RES-0005](../../research/comparisons/fleet-intent-representation.md)
records the comparison supporting the ADR-0003 decision: TOML 1.0 authoring
records validated structurally through JSON Schema Draft 2020-12, exact
upstream-native files declared by small source manifests, and canonical JSON
resolved output and evidence. The decision keeps schema validation, reference
resolution, composition, native validation, policy, and qualification as
separate owned boundaries.

[ADR-0003](../../adrs/0003-bounded-fleet-intent-representation.md) accepts
this representation direction. It requires a bounded parser, schema, and
canonicalization spike before production identity depends on concrete
libraries. Operator records remain data, native settings do not wait for a
project schema, defaults are materialized, unknown intent fails, and no
inventory-supplied code implements validation or composition.

## Amendment, proposed 2026-08-11: configuration is delivered as a signed confext

**Status: proposed, drafted by an agent, not accepted.** It amends an accepted
design and requires Jason Tarasovic's acceptance before any part of it is
policy. Until then the accepted text above stands.

DES-0006 C-013, accepted 2026-08-11, made the authenticated release artifact
`/usr` rather than a complete root, and made signed confexts the **only**
mechanism that delivers configuration. That answers this design's own deferred
question -- whether a separately immutable configuration artifact beats
flattened variants -- in the affirmative, but it answers it from outside. The
question named boot-time binding, fallback, and garbage collection, and C-013
adopted the mechanism without settling any of them. SYS-123 now applies in full
to every confext, and this design is its home.

### Several disjoint confexts per deployment variant

A deployment variant resolves to a **set** of configuration extension images.
The deployment manifest names the complete set by digest; a missing, extra, or
substituted member fails the eligibility gate exactly as any other deployment-set
member does.

Owner ruling, 2026-08-11: several confexts rather than one, so that
configuration identical across machines is built, signed, and transferred once
instead of being duplicated inside every machine's image.

**The split is by disjoint path ownership, not by scope.** This is the
constraint that makes several images safe, and it is not a detail. Splitting
along `common`, `role`, and `machine` would fail, because those scopes overlap
by construction -- machine scope exists precisely to override role scope for the
same key -- so resolving them would require precedence at activation time. That
is the "generic role image plus boot-time machine assembly" this design already
rejected, and the rejection stands.

Instead, each confext owns a disjoint set of paths, drawn along consumer or
subsystem lines: network configuration in one, the graphical stack in another.
`common < role < machine` precedence is resolved at build time **within** each
confext, so each one already carries a decided result for the paths it owns.
Two confexts in one deployment writing the same path is a **composition-time
error**, not a runtime conflict to be ordered.

Disjointness buys the property that matters: **merge order cannot change the
effective result.** Activation ordering stops being a semantic question and
becomes a scheduling one. Reuse then comes from two machines legitimately
having byte-identical configuration for a subsystem, which is a fact about the
inventory that the composition record can prove -- not from layering, which
would smuggle precedence back in.

The accepted cost is that the split must be designed. Path ownership is now a
modeling decision with a wrong answer available: a subsystem carved too finely
produces many tiny images, and one carved too coarsely destroys the reuse this
ruling exists to capture. The disjointness rule is mechanically checkable,
which keeps the cost bounded to design effort rather than to correctness.

### Declared failure policy

Owner direction, 2026-08-11: each confext declares the policy for its own
failure to merge. This is what makes the split carry meaning rather than being
only a transport optimization -- a router's network configuration and a
workstation's desktop stack genuinely differ in whether the machine should
continue without them.

A confext is declared either **required**, where failure to merge fails the
trial boot, or **optional**, where failure is reported, marks the deployment
degraded, and allows boot to continue. This replaces the global fail-closed
rule and the per-role rule with a per-subsystem one that follows what the
configuration actually does.

**The declaration is authored in the fleet inventory and carried by the
confext, never authored by it.** An artifact that decides how important it is
would be deciding its own failure handling, which is the shape this project
refuses everywhere else. The inventory declares criticality as reviewed,
identity-bound intent; the composition record records it; the image transports
it. A confext whose declared policy disagrees with the manifest's is a
substituted member and fails the gate.

Two consequences follow and are accepted:

- **Optional is not a soft default.** A deployment in which an optional confext
  failed is degraded, not healthy, and must not be blessed on that boot. It is
  the difference between a router that keeps routing while reporting a broken
  desktop stack and a router that silently becomes healthy with configuration
  missing.
- **Required is the default for anything unclassified.** An unmarked confext
  fails closed. Getting this backwards would let an unreviewed image become
  optional by omission.

### The SYS-123 obligations

Three are already satisfied by the accepted design and are restated rather than
added. **Exact content identity** is the composition record plus the rendered
artifact identities. **Authorization** and **qualification** follow from the
rule that the deployment variant, not the input files in isolation, is what
gets qualified and authorized.

The remaining six are new, and each is new because this design was written
while configuration lived inside the deployment artifact, where the question
could not arise:

- **Base compatibility.** The confext declares a base compatibility level
  through `extension-release.d`, which acts as a **guard** against activating
  against an incompatible `/usr`. It does not carry deployment identity. The
  deployment manifest already binds the literal tuple, which is C-001's answer
  to the hybrid problem, so duplicating that binding in `extension-release.d`
  would add no integrity and would force every machine's confexts to be rebuilt
  and re-signed on every `/usr` release that changed nothing they contain. With
  the guard model, a `/usr` release requires the tuple to be **re-qualified**,
  not the configuration to be **rebuilt**. Reuse across machines depends on
  this: a confext bound to one exact deployment identity could never be shared.
- **Activation ordering.** Inter-extension order is immaterial by construction,
  because the confexts are disjoint -- that is the point of the disjointness
  rule rather than a happy consequence of it. What remains is ordering against
  consumers: each confext must be merged before any unit that reads the paths
  it owns, and the two-stage initrd and sysroot activation named by the C-013
  amendment means "before" has two distinct meanings. Configuration consumed
  before `/usr` is verified is outside the integrity boundary, so which
  confexts must be present in the initrd stage and which may wait for sysroot
  is an integrity boundary, not a convenience. This design states the
  requirement; DES-0006 owns the boot chain that realizes it.
- **Health.** Determined by each confext's declared policy, above. A required
  confext failing to merge fails the trial boot; an optional one failing marks
  the deployment degraded and blocks blessing. Neither case may silently fall
  back to `/usr/lib` release defaults and report success, which would run a
  configuration nobody qualified.
- **Rollback.** Configuration does **not** roll back independently. Because the
  manifest names the complete confext set, rolling back configuration means
  selecting the earlier deployment.
  This follows from the binding above rather than being an additional rule, and
  it is what keeps a rolled-back OS from running forward configuration.
- **Retention.** A confext is retained as long as **any** retained deployment
  names it, and is collected when none does. Sharing makes this a reference
  count rather than a per-deployment lifetime, which is the one place reuse
  adds machinery rather than removing it: collecting a confext because one
  deployment was dropped could strip the retained fallback that still needs it,
  turning garbage collection into the SYS-050 violation C-014 already found in
  the staging path. Otherwise confexts are deployment-set members, so SYS-050's
  current-plus-fallback guarantee covers configuration without a separate
  policy. DES-0006's Configuration artifacts region is its storage home, and
  the bytes count against the capacity formula C-002 produces.
- **Effective-deployment status.** Machine status must report every merged
  confext's identity, its declared failure policy, and whether the merged set
  matches the set the running deployment names. The existing inspection surface asks whether the machine matches its
  expected composition record; that question is now answerable only if the
  active extension is enumerated, not inferred.

### What this amendment does not settle

- Whether the confext is built by the same tooling that renders configuration
  today, or is a separate packaging step with its own identity. It is a
  build-pipeline question, not a semantic one, and belongs with the ADR-0003
  spike.
- Per-machine identity and secrets, which cannot live in `/etc` under C-013 and
  must be projected from state or delivered as credentials. That remains
  `L-003` and is not resolved by having a confext available.
- The bounded path for testing unqualified configuration. C-013 requires it to
  be non-durable by construction, visibly marked, and either unavailable on
  production physical roles or attributable when used. `/run/confexts/` and the
  `ephemeral` modes are the assembly, but it conflicts with
  `image_policy_confext_strict`, so the role distinction must be drawn
  explicitly rather than assumed.
- Whether `Mutable=` remains forbidden in every case. C-013 forbids it for
  release-owned configuration; this amendment does not create an exception and
  does not rule out one being argued later on its own evidence.

## Authoritative intent model

### Fleet inventory

The fleet inventory is authoritative desired intent, not an observation
database. It contains or references:

- the inventory schema and revision;
- common configuration sources;
- role definitions and their configuration sources;
- platform-class definitions;
- machine records;
- state-contract, health-policy, and late-bound-contract references; and
- the policy identifiers needed to validate composition.

Observed firmware versions, current IP addresses, health results, selected
deployment, and similar runtime facts belong in evidence or machine status.
They do not rewrite desired intent merely because they differ.

The inventory may initially live beside the NeutrinOS framework in one
repository. Its interface must permit a future fleet-specific repository
without changing the composition semantics. This design selects a logical
model, not final directory names.

### Machine record

A machine record contains at least:

| Field | Purpose |
| --- | --- |
| Machine name | Stable human-facing inventory key such as `desktop-jason`; not a credential or hardware fact. |
| Enrollment binding | Reference by which an enrolled machine identity is associated with this record; secret material is not present. |
| Role assignment | One authorized primary role. |
| Platform constraints | Accepted architecture, platform classes, required capabilities, and explicitly supported exceptions. |
| Machine configuration sources | Exact machine-scoped inputs and reusable sources selected for this record. |
| Late-bound contracts | Values allowed to arrive after deployment identity is established. |
| State contracts | Persistent state schemas and compatibility rules applicable to the machine. |
| Health policy | Role and machine observations required for qualification and local blessing. |
| Deployment policy reference | Allowed channel, pin, rollout, or other selection policy without naming mutable content as identity. |

A machine name remains stable across OS deployment and ordinary hardware
maintenance. Machine identity may be revoked and re-enrolled without renaming
the record. Reusing a retired machine name for an unrelated machine requires an
explicit inventory history and new enrollment binding rather than silent
replacement.

### Role definition

A role definition binds a role name to:

- role requirements and security objectives;
- role-scoped configuration sources;
- supported platform-class constraints;
- health and qualification policy references;
- required state and late-bound contracts; and
- role-specific deployment contents or artifact policy.

The initial model assigns one primary role per machine. A reusable
configuration source may be referenced by several roles or machines, but that
does not create role inheritance. If a future machine needs several
independently managed system functions, the design must decide whether they are
release-owned services, workloads, or a new composite role rather than growing
an implicit mixin graph.

### Platform class

A platform class declares compatibility constraints and qualification scope.
It is not a fourth configuration scope and does not assign a role. Hardware-
specific normal policy is explicitly referenced by a role or machine
configuration source and becomes identity-bound like any other normal policy.

This separation prevents an observed board model from silently enabling a
service, choosing firewall policy, or converting a workstation into a router.

## Configuration sources and inputs

A configuration source is a named, versioned origin of one or more inputs. Each
input declares:

- its configuration scope;
- owner and consuming upstream component;
- input type and interpretation policy;
- output key, destination, or native attachment point;
- conflict and deletion behavior;
- validation policy where available; and
- whether it contains bounded declarative data or upstream-native
  configuration.

Native configuration is not copied from an untracked catch-all directory. Its
source, consumer, destination, precedence, and digest participate in the same
composition record as convenience-schema inputs. NeutrinOS policy may reject a
supported upstream setting for a specific role, but lack of a project
convenience field is not itself a reason to reject it.

References to shared sources are exact and finite. Recursive discovery,
filesystem traversal order, floating branches, and mutable URLs do not define
composition order or identity.

## Composition algorithm and precedence

For one machine and inventory revision, composition proceeds as follows:

1. Resolve the exact machine record, its one role definition, platform
   constraints, policy references, and all exact configuration-source
   references.
2. Collect common, role, and machine inputs in explicit stable order within
   each scope.
3. Validate source ownership, consumer, type, reference closure, and syntax
   before applying precedence.
4. Resolve conflicts in the fixed order `common < role < machine`.
5. Treat a higher-scope removal as an explicit tombstone; absence alone never
   deletes a lower-scope value.
6. Reject conflicts within one scope unless a named consumer-specific merge
   policy defines and tests their order and semantics.
7. Run policy validation over the complete resolved configuration. Precedence
   decides values; it does not grant permission to violate a security or role
   invariant.
8. Render bounded inputs into upstream-native configuration and retain native
   inputs without lossy translation.
9. Validate the complete rendered output using upstream validators where
   available and project integration checks where required.
10. Emit the composition record, resolved configuration, and rendered
    configuration for the build and qualification stages.

Conditions are allowed only as bounded predicates implemented and tested by
owned tooling over declared inputs such as role, machine name, platform class,
or a finite feature selection. Operator-authored functions, arbitrary
evaluation, dynamic imports, and evaluation of runtime hardware facts to
assemble normal policy are prohibited.

## Composition record

Every resolved configuration produces an immutable composition record that
contains at least:

- inventory revision and machine-record identity;
- role assignment and platform constraints;
- ordered configuration-source and input identities;
- composition and renderer tool identities;
- precedence decisions, explicit tombstones, and overridden input origins;
- policy and validator identities and their results;
- resolved non-secret configuration identity;
- rendered native file and artifact identities;
- declared late-bound and state-contract identities; and
- attributable warnings or accepted exceptions.

The record is release evidence and an input to deployment-manifest creation. It
does not need to be a project-specific format if an upstream immutable object
can express the same information without loss. Secret values and sensitive
custody locations are excluded.

The operator-facing inspection must support both directions:

- given a machine and setting, show the winning value, source, overridden
  values, consumer, and rendered output; and
- given a rendered native file or deployment artifact, show the inputs and
  transformation that produced it.

## Identity-bound and late-bound inputs

Normal non-secret behavior is identity-bound. This includes enabled system
services, kernel and module policy, firewall and routing intent, user and group
policy, mounts after provisioning, graphical-session policy, and the declared
consumption policy for credentials and hardware observations.

A late-bound contract must identify:

- owner and supplying authority or observation source;
- consuming component and exact name;
- schema, constraints, and confidentiality class;
- delivery or observation mechanism;
- availability, invalid-value, and absence behavior;
- rotation or change behavior where applicable;
- effect on health, support, and local-modification status; and
- representative and negative qualification fixtures.

Secret values, machine enrollment identity, hardware observations, dynamic
network data, and independently owned user or workload values may be late-
bound. Their contracts and effects remain identity-bound even when their values
do not.

Systemd credentials are the default delivery mechanism for service-consumed
late-bound values when their semantics fit. This does not reclassify all
hardware facts, protocol state, user data, or provisioning metadata as
credentials, and it does not let credentials carry undeclared normal policy.

## Role assignment and machine identity

Role assignment is desired intent accepted through project change review.
Release authorization binds the resulting deployment identity and role scope,
while enrollment binds one machine identity to one machine record. Normal
selection requires the deployment authorization, current machine-record
binding, role assignment, and observed platform compatibility to agree.

No individual signal is sufficient:

- a machine name is not authentication;
- a machine identity is not role assignment;
- a role assignment is not platform compatibility;
- platform compatibility is not deployment authorization; and
- possession of deployment bytes is not eligibility.

An administrator may deliberately reassign a machine, but the change creates a
new resolved configuration and deployment variant and may require new state,
qualification, enrollment, and recovery decisions. It is not a boot-time
toggle.

## Provisioning and bootstrap boundary

Provisioning prepares blank or reset storage, platform trust, retained
recovery, and machine identity. It may use a bootstrap hint to locate the
intended machine record or provisioning input, but the hint is not authority.

SMBIOS data supplied by a hypervisor or firmware is a platform observation or
bootstrap transport. It may say “attempt enrollment for `router`,” but normal
role assignment becomes effective only after authenticated provisioning binds
the resulting machine identity to the current reviewed machine record and
selects a compatible authorized deployment set.

Ignition is the leading challenger for bounded first-boot or reprovisioning
input because it is conceptually aligned with declarative provisioning.
Cloud-init remains an optional compatibility path for environments that supply
it. Neither becomes the normal NeutrinOS configuration-composition engine, and
neither may continuously overwrite release-owned configuration or assign roles
from mutable instance metadata.

The concrete provisioning authorization, replay protection, install media,
storage operations, and enrollment protocol remain open under L-003 and S-004.
Whatever mechanism is selected must end with:

1. an enrolled machine identity bound to one machine record;
2. platform observations checked against declared constraints;
3. a previously built, qualified, and authorized deployment set selected; and
4. provisioning inputs retired, retained as evidence, or made inert according
   to an explicit lifecycle.

Re-running provisioning is a deliberate reprovision or recovery operation. It
must not silently change role assignment, reset identity, erase state, or
replace the current deployment as a side effect of an ordinary reboot.

## State and compatibility

Fleet inventory and composition records are project or release evidence.
Machine identity, credentials, provisioning completion, persistent
administrator exceptions, and runtime observations retain their DES-0002
owners and state contracts.

Changing identity-bound configuration creates a new deployment identity and
therefore re-enters normal qualification, compatibility, authorization,
staging, and trial-boot policy. Changing a late-bound value follows its own
contract and changes the machine realization or health without pretending that
the deployment bytes changed.

Inventory and composition schemas are versioned. A build must reject an
unsupported schema rather than ignore unknown intent. Migration must preserve
the previous source revision and the ability to reproduce already authorized
deployment identities.

## Security and trust

The protected assets are role assignment, normal privileged behavior,
deployment identity, machine identity, and secret values. Relevant attackers
include a compromised publication or metadata service, a malicious local
network, a workload with access to instance metadata, a mistaken administrator,
and an attacker who can alter SMBIOS or provisioning transport.

The design guarantees that normal release-owned policy is attributable to an
exact inventory revision and deployment identity, and that observation or
bootstrap transport alone cannot authorize another role or deployment. It does
not guarantee that checked-in policy is benign, that an authorized maintainer
cannot make a dangerous change, or that firmware observations are truthful
against compromised firmware.

Secrets remain outside composition records and deployment artifacts. Logs and
diagnostics must name secret references and failure classes without exposing
values. Compromise recovery treats provisioning remnants, administrator
overrides, machine identity, and mutable executable state as potentially
hostile under SYS-035.

## Failure and recovery

| Failure | Required behavior |
| --- | --- |
| Missing or ambiguous machine record | Stop before build or provisioning mutation; report the inventory revision and lookup input. |
| Multiple or missing primary roles | Reject the machine record. |
| Same-scope conflict without merge policy | Reject composition and identify both sources and the output key. |
| Higher scope attempts forbidden policy override | Reject post-composition policy validation; precedence does not bypass the invariant. |
| Unsupported native configuration | Report consumer, source, validator, and rendered destination; do not silently drop it. |
| Unknown platform observation | Mark incompatible or unsupported according to declared policy; do not select another role. |
| SMBIOS or metadata names another machine | Refuse enrollment or require deliberate authenticated reassignment; do not inherit that record's role. |
| Late-bound value absent or invalid | Apply its declared fail-closed, degraded, or unavailable behavior and expose the responsible contract. |
| Renderer changes output unexpectedly | Produce a different composition/output identity and require qualification; do not claim reproduction. |
| Provisioning interruption | Resume, reverse, or enter deliberate recovery under the provisioning state contract; never continue as a partially enrolled normal machine. |
| Provisioning input reappears after completion | Treat it as inert evidence or an explicit reprovision request, never an ordinary boot instruction. |

The prior inventory revision, inputs, composition record, and rendered output
remain available for diagnosis. Reverting source intent creates a new candidate
from the reverted inputs; it does not rewrite the identity or evidence of an
already built deployment.

## Options considered

### Programmable module and overlay language

Rejected for the operator-facing model under SYS-014. It can express arbitrary
composition but recreates the evaluation and debugging burden this design is
meant to bound. Separately owned implementation code may perform deterministic
transformations without becoming operator-authored fleet intent.

### Flat complete configuration per machine

Viable as an escape hatch and diagnostic output, but rejected as the only
authoring model. It duplicates common and role policy and makes cross-machine
review difficult. The resolved configuration provides the same flat view while
retaining attributable sources.

### Generic role image plus boot-time machine assembly

Rejected. It lets mutable metadata or target-side logic create behavior that
was not the literal qualification subject and weakens offline fallback.

### Infer role from SMBIOS or hardware model

Rejected. Hardware observations can establish compatibility or help locate a
bootstrap record, but they are mutable, sometimes non-unique, and not an
authorization to change machine purpose.

### Use Ignition or cloud-init as the normal configuration engine

Rejected as the default architecture. Both may be provisioning transports, but
ongoing target-side mutation of release-owned behavior conflicts with exact
deployment identity, reconstructible `/etc`, and qualified-artifact selection.

### Add platform as a fourth precedence scope

Rejected initially. Platform class answers compatibility, not administrative
intent. Hardware-specific policy can be explicitly referenced by a role or
machine source without giving observed hardware an implicit precedence or
authorization path.

## Operations and diagnostics

The normal inspection surface must answer:

- which machine record and inventory revision produced this deployment;
- which role and platform constraints apply;
- which sources contributed a setting or rendered file;
- which value won and why;
- whether native validation and policy validation passed;
- which late-bound values are satisfied, absent, invalid, or stale without
  exposing secrets;
- whether persistent administrator exceptions changed support status; and
- whether the running machine matches the exact deployment and expected
  composition record.

Raw upstream validation output remains available beside the project-level
attribution. A project status join must not replace native diagnostics or
become another mutable desired-state database.

## Verification

Before accepting the design, paper examples and later implementation tests must
demonstrate:

1. complete reference VM, `desktop-jason`, and `router` machine records;
2. a common value overridden by role and then machine scope with every origin
   visible;
3. an explicit tombstone, a rejected same-scope conflict, and a forbidden
   higher-scope override;
4. an upstream-native setting with no NeutrinOS convenience schema reaching
   rendered output and qualification evidence;
5. identical inputs producing identical resolved and rendered identities;
6. a renderer or input change producing a different attributable identity;
7. secret values excluded while their contracts and qualification fixtures are
   present;
8. wrong or ambiguous SMBIOS data failing to reassign a machine role;
9. provisioning interruption and replay without partial enrollment or silent
   reprovisioning; and
10. one configuration change traced through composition, deployment identity,
    qualification, selection, runtime status, and deliberate rollback.

If the proposed confext amendment is accepted, it adds:

11. two confexts in one deployment claiming the same path failing at
    composition time, not being resolved by activation order;
12. the merged result proving invariant under activation order, exercised by
    merging a deployment's confext set in several orders and comparing the
    effective configuration byte for byte;
13. a confext refusing to activate against an incompatible base, while the same
    confext is legitimately shared by two machines and survives a `/usr` release
    that requires re-qualification but no rebuild;
14. a missing, extra, or substituted set member failing the eligibility gate,
    including a member whose declared failure policy disagrees with the
    manifest;
15. a required confext failing to merge failing the trial boot, and an optional
    one failing marking the deployment degraded and unblessable, with neither
    silently proceeding on `/usr/lib` defaults;
16. an unclassified confext defaulting to required rather than optional;
17. rollback to an earlier deployment carrying its own configuration set, with
    no path by which a rolled-back OS runs forward configuration;
18. a shared confext surviving collection while any retained deployment still
    names it, including the case where the deployment that introduced it was
    dropped and a retained fallback still depends on it; and
19. machine status reporting every merged extension's identity and declared
    policy, and the merged set's agreement with the running deployment,
    enumerated rather than inferred.

[EX-0007](../../research/exercises/0007-native-configuration-and-inspection.md)
now exercises representative native systemd, networkd, sysctl, tmpfiles,
sysusers, nftables, mount, and kernel-command-line inputs; complete-file
replacement, tombstones, and consumer-specific conflicts; and both inspection
directions. It is analysis and sanitized local-experience evidence, not an
implementation result.

## Accepted requirements

The following requirements were accepted through
[PR-0008](../../project/reviews/0008-fleet-intent-and-configuration-requirements.md):

- SYS-042: The authoritative fleet inventory must version machine records,
  role assignments, platform constraints, and exact configuration-source
  references independently of runtime observations.
- SYS-043: Platform observations and bootstrap hints must not assign a role or
  authorize a deployment; normal selection must join an enrolled machine
  identity's current machine-record binding and role assignment with a
  compatible platform and eligible deployment identity.
- SYS-044: Configuration composition must use fixed `common < role < machine`
  precedence, explicit same-scope conflict rules and deletions, and policy
  validation after precedence resolution.
- SYS-045: Every deployment variant must retain an immutable composition record
  identifying its ordered inputs, tools, precedence decisions, validations,
  resolved configuration, rendered outputs, and declared exceptions.
- SYS-046: Every late-bound input must have an identity-bound contract covering
  ownership, source, consumer, schema, constraints, delivery, failure behavior,
  status effect, and qualification fixtures.
- SYS-047: Provisioning and enrollment must remain separate from normal
  configuration and deployment selection, and replay must not silently change
  role, identity, preserved state, or selected deployment.

## Risks and unresolved questions

- Does the accepted TOML, JSON Schema, and canonical JSON split survive a
  parser/validator/canonicalization spike without implementation-specific
  behavior?
- How is inventory change authorization represented before a release
  authorization binds the resulting deployment?
- Should the first implementation co-locate fleet inventory with the framework
  or exercise a separate inventory repository immediately?
- Which native formats have merge semantics that should be preserved instead
  of reduced to file replacement?
- Which security invariants may a machine scope never override?
- Which late-bound values fit systemd credentials, and which belong to network,
  enrollment, platform, user, or workload mechanisms?
- ~~Can a separately immutable configuration artifact satisfy boot-time
  binding, fallback, and garbage collection more simply than flattened
  variants?~~ Answered by DES-0006 C-013 on 2026-08-11: yes, a signed confext,
  and flattened variants are foreclosed rather than merely beaten. The
  proposed amendment above settles the three parts this question named. **The
  answer arrived from outside this design**, which is why it is recorded as a
  proposed amendment awaiting acceptance rather than as a resolved question.
- Is Ignition worth supporting for the reference VM, or should first
  provisioning use a smaller systemd-native path?

## Review disposition

The adversarial review is accepted in [review.md](review.md).
[EX-0006](../../research/exercises/0006-representative-fleet-intent.md)
provides candidate machine records, a field-authority table, non-overridable
invariants, representative late-bound contracts, and scope-composition
fixtures. [EX-0007](../../research/exercises/0007-native-configuration-and-inspection.md)
adds representative native inputs, consumer-specific conflict behavior, and
inspection examples, while
[RES-0005](../../research/comparisons/fleet-intent-representation.md) supports
the bounded representation accepted by ADR-0003. PR-0008 accepts the
configuration and provisioning authority boundaries. DES-0005 is accepted;
concrete provisioning and first-enrollment mechanisms remain open follow-on
work under L-003, and concrete parser/tool selection remains a required spike.
