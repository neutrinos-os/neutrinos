---
id: DES-0001
title: System model and deployment unit
status: in-review
owners: [Jason Tarasovic]
reviewers: [Codex]
created: 2026-08-09
last_updated: 2026-08-09
depends_on: []
decision_backlog: [S-001, S-003, L-004]
related_adrs: []
---

# System model and deployment unit

## Problem

NeutrinOS needs one precise answer to “what gets deployed?” before choosing an
image format, disk layout, updater, or package source. Calling the unit an image
is insufficient: a normal boot may use separately stored firmware-loaded code,
a UKI or equivalent boot artifact, immutable root content, system extensions,
and generated configuration. Treating any one component as the release allows
the others to drift outside qualification, authorization, rollback, and status.

Conversely, treating the entire disk or all persistent state as the release
would make OS replacement rewrite machine identity, credentials, user data, and
workloads. It would also make rollback claims dishonest after mutable state has
advanced.

This design defines the technology-neutral deployment identity and transaction
boundary. Later substrate work must map it to supported systemd/UAPI or bootc
mechanisms without changing its guarantees silently.

## Goals

- Define the independently selectable and replaceable OS deployment unit.
- Bind every release-owned artifact needed for trusted normal operation to one
  immutable identity.
- Keep staging, boot selection, blessing, fallback, and rollback coherent when
  the bytes occupy multiple resources.
- Distinguish build identity, release authorization, machine realization, and
  mutable state.
- Preserve one lifecycle across VM, workstation, and router variants without
  requiring identical artifact shapes.
- Provide falsifiable requirements for substrate and lifecycle spikes.

## Non-goals

- Select EROFS, composefs, SquashFS, OSTree, OCI, GPT partition images, or a
  block-level update format.
- Select `mkosi`, `systemd-sysupdate`, bootc, an installer, or a publication
  service.
- Define the final disk layout, slot count, boot-attempt count, or health timer.
- Make OS rollback revert arbitrary machine, user, or workload state.
- Require a public release to contain an artifact for every possible role or
  machine.
- Treat an artifact digest, signature, or successful health check as proof that
  the source or behavior is benign.

## Accepted constraints

The deployment model is constrained by existing project policy:

- SYS-017 requires deployment to select previously built and qualified bytes
  rather than evaluate or reconstruct an equivalent OS on the machine.
- SYS-019 through SYS-026 and
  [DES-0002](../0002-state-ownership/README.md) keep persistent state, identity,
  migrations, and diagnostics outside undifferentiated OS replacement.
- SYS-030 requires production physical boot to authenticate every release-owned
  boot artifact and the immutable release root from the platform trust anchor.
- SYS-032 and SYS-033 require scoped authorities and independently usable
  recovery.
- [ADR-0001](../../adrs/0001-systemd-first.md) makes the systemd ecosystem the
  default source of lifecycle mechanisms when it can satisfy these
  requirements.
- [ADR-0002](../../adrs/0002-separate-authority-and-recovery.md) separates
  platform signing, release authorization, recovery, enrollment, machine
  identity, and data recovery.

SYS-001 through SYS-003, SYS-005, SYS-008, SYS-010, SYS-012, SYS-013, SYS-028,
SYS-029, SYS-031, and SYS-035 through SYS-041 are accepted lifecycle
constraints through the
[deployment lifecycle requirements review](../../project/reviews/0007-deployment-lifecycle-requirements.md).
That review also records the accepted requirements that supersede the earlier
SYS-004, SYS-006, SYS-007, SYS-009, and SYS-011 statements.

## Terminology

The [project glossary](../../project/glossary.md) is canonical. This table
restates the terms central to this design.

| Term | Meaning |
| --- | --- |
| Artifact | Immutable bytes identified by a cryptographic digest. An artifact may be a boot executable, root image, extension image, configuration artifact, metadata artifact, or another independently transferred object. |
| Deployment manifest | Immutable metadata binding the complete release-owned deployment closure and its role, platform, configuration, and compatibility declarations. |
| Deployment identity | The digest of the deployment manifest. |
| Deployment set | The deployment manifest and its complete deployment closure. This is the independently selectable and replaceable unit. |
| Deployment variant | One deployment set built for a declared role, platform class, and resolved normal configuration. |
| Qualification record | Attributable evidence produced by testing one literal deployment identity under a named policy and environment. |
| Release authorization | A signed authorization joining a deployment identity to its qualification record, allowed authorization scope, compatibility, and policy metadata. |
| Release | A promoted collection of one or more independently identified deployment variants and their authorizations. A human version or release name is not an artifact identity. |
| Machine realization | One deployment set running with the machine's accepted late-bound values, state contracts, policy epoch, identity, and declared local modifications. It is reported as a tuple of evidence, not mislabeled as immutable release bytes. |
| State | Data with a lifecycle that crosses deployment replacement, as governed by DES-0002. |

The word `deployment` may be used generically in ordinary prose. Where identity
or lifecycle state matters, this design uses `deployment set`, `deployment
identity`, `selected deployment`, `booted deployment`, or `machine
realization` explicitly.

## Proposed decision

The independently replaceable OS unit is a **deployment set**: a content-
identified manifest plus the complete set of exact release-owned artifacts it
names.

The deployment set is the unit of:

- qualification;
- release authorization;
- publication eligibility;
- staging and verification;
- boot selection and attempt accounting;
- blessing;
- retention for normal fallback or deliberate rollback; and
- withdrawal from normal use.

It need not be one file, filesystem, partition, disk image, or OCI object.
Storage and transfer mechanisms may split or deduplicate it, but no subset gains
the identity, qualification, or authorization of the whole. A delta or patch is
only a transport optimization; its reconstructed output must match the exact
artifact identities in the manifest.

## Identity and evidence graph

```text
source revision + pinned inputs + resolved role/machine configuration
                              |
                              v
                 unsigned candidate artifacts
                              |
                 normal-platform signing
                              |
                              v
       exact boot artifacts + root + extensions/config artifacts
                              |
                 immutable deployment manifest
                              |
                  deployment identity D
                              |
              literal qualification record Q
                              |
          release authorization A binds D + Q + scope
                              |
                              v
                  published deployment set
                              |
            stage -> trial boot -> assess -> bless
                              |
                              v
        machine realization reports D plus effective state
```

Platform signing occurs before the manifest and literal qualification because
it changes boot-artifact bytes. The deployment manifest contains artifact and
input identities but not its later qualification result, avoiding a circular
identity. The qualification record binds the manifest and literal artifacts;
release authorization then binds both identities and authorization policy as
required by DES-0004.

Mutable discovery names, tags, filenames, version strings, repository paths,
and URLs may locate a deployment set but never identify or authorize it.

## Deployment-set contents

Every normal deployment manifest identifies, directly or through a closed
content-addressed submanifest:

1. all release-owned code and policy executed before the immutable root is
   authenticated;
2. the exact immutable root content;
3. every release-owned privileged system or configuration extension loaded as
   part of normal OS behavior;
4. separately stored release-owned normal configuration, if any;
5. the resolved non-secret build and configuration inputs that determine those
   bytes;
6. role and platform compatibility declarations;
7. state-contract schema and read/write compatibility requirements;
8. boot, health, and success-policy identifiers; and
9. the manifest schema and interpretation policy needed to reject unsupported
   or ambiguous sets.

An artifact absent from a variant is represented by absence under the manifest
schema, not by an implicit lookup to “latest.” Content may be deduplicated
across deployment sets, but retention and garbage collection must preserve all
objects reachable from every retained normal or recovery identity.

The following are not silently included in the normal deployment identity:

- machine identity, enrollment state, storage-unlock material, and secrets;
- persistent administrator overrides;
- user homes and user-managed applications;
- workload, container, and VM state;
- caches, logs, and other mutable state contracts;
- installation or recovery environments authorized under a different policy;
  and
- mutable publication or fleet-control metadata.

Those items retain separate owners and status. Executable material outside the
deployment set does not inherit the set's qualification merely because the
base OS can load it.

## Configuration boundary

Configuration is classified by when and how it can change behavior:

| Class | Identity treatment | Qualification treatment |
| --- | --- | --- |
| Resolved normal role or machine configuration | Rendered into release-owned artifacts or a separately immutable configuration artifact named by the deployment manifest; any change creates a different deployment identity | The literal resulting deployment variant is qualified |
| Secret reference and delivery policy | Non-secret reference, schema, scope, and expected effect are bound to the deployment; secret value remains machine, user, or workload state | Qualification uses representative values and negative cases; the actual secret is not release identity |
| Hardware-derived value | Accepted source, schema, constraints, and failure behavior are bound to the deployment; observed value is part of effective status | Qualification covers the supported value class and physical targets validate their actual value |
| External runtime data | Owned by the consuming component and excluded from artifact identity unless promoted into declared configuration | Health and contract tests cover failure, invalid data, and loss where relevant |
| Persistent administrator override | Separate administrator state that changes effective status to locally modified or unsupported according to policy | It receives no inherited release qualification; recovery can inspect and disable it |

Normal checked-in non-secret machine configuration therefore does not float
beside a generic OS image. It either determines the built variant or becomes an
exact immutable artifact named by that variant. Late binding is reserved for
values whose lifecycle genuinely belongs to the machine, user, workload, or
environment; it is not an escape hatch for reconstructing a different OS on the
machine.

## Variants, roles, and releases

A release may contain multiple deployment variants. Each variant has its own
deployment identity and qualification record. Variants may differ in kernel,
package set, root image, extension set, platform policy, configuration, and
physical storage representation while following the same lifecycle contract.

A shared release name means only that the project promoted those variants as a
declared collection. It does not mean:

- their bytes are interchangeable;
- one variant's tests qualify another;
- every role must ship at the same moment;
- all machines update atomically; or
- an absent role variant may be reconstructed on the machine.

If two variants must interoperate—for example, workstation administration of a
router—the release records the interface or fleet compatibility being claimed
and the evidence for it. A role with no authorized variant remains on its last
supported deployment or becomes stale according to policy; a shared version
label does not fabricate support.

Machine-specific variants are allowed for the initial fleet because exact
checked-in machine configuration is part of the qualification subject. Shared
role and platform inputs must still be visibly factored so that per-machine
builds do not become unrelated hand-maintained operating systems. Variant count
and qualification cost are explicit lifecycle metrics and review triggers.

## Transactional staging and selection

`Atomic` means atomic **eligibility and selection**, not that all bytes are
written in one storage operation.

1. Discovery yields an immutable deployment identity and release authorization.
2. The machine verifies authorization scope, platform compatibility, supported
   manifest schema, and required policy before the candidate can affect
   selection.
3. Every artifact is fetched into inactive storage. Partial or corrupt content
   remains an ineligible staging object.
4. The machine verifies the complete artifact closure and applicable state-
   compatibility preconditions.
5. Only then may one selection operation make the complete deployment identity
   a trial boot candidate. The previously selected deployment remains intact.
6. Early boot independently verifies that the artifacts it actually uses match
   the selected identity and satisfy the platform trust policy.
7. The booted deployment reports its identity and remains unblessed while role-
   specific health is evaluated.
8. Success blesses that deployment on that machine. It does not qualify a new
   release globally.
9. Failure may reselect a retained normal deployment only when its authorization,
   freshness, and state-compatibility policy permit it. Recovery-only artifacts
   require deliberate recovery activation.

An interrupted fetch, verification, selection write, or boot must yield the
old selection, one complete trial selection, or an explicit diagnosable stop.
It must not assemble a bootable hybrid from old and new release-owned artifacts.

## Lifecycle and status dimensions

Lifecycle state and trust claims are reported separately:

| Dimension | Example values |
| --- | --- |
| Presence | discoverable, partially staged, complete, retained, absent |
| Authorization | normal, recovery-only, withdrawn, unknown |
| Qualification | passed policy identity, failed, incomplete, unavailable |
| Selection | inactive, next trial, booted, fallback, manually selected |
| Boot assessment | unattempted, pending, failed, blessed |
| Freshness/currentness | current, stale, pinned, expired, unknown |
| Compatibility | applicable, incompatible, migration required, unknown |
| Effective modification | exact, declared late-bound values, locally modified, quarantined |
| Support | supported, degraded, unsupported, unknown |

No single `healthy`, `signed`, `current`, or `green` value substitutes for this
evidence. In particular:

- signed does not mean qualified;
- booted does not mean blessed;
- blessed does not mean current or uncompromised;
- retained does not mean eligible for automatic fallback; and
- the base deployment may remain exact while mutable executable state makes the
  machine realization locally modified or unsupported.

## State, rollback, and recovery

Deployment rollback means reselecting an already retained immutable deployment
set. It does not roll back persistent state. DES-0002's compatibility and
migration contracts decide whether automatic reselection is safe.

Before a candidate becomes selectable, the machine verifies that it can
consume the machine's state and that every advertised automatic fallback can
consume the state expected after the candidate runs. A forward-only commit
barrier removes incompatible deployments from automatic fallback eligibility
even if their bytes remain mechanically retained.

Failed normal boot automation may choose only another eligible normal
deployment. It may stop and request recovery, but it never selects a recovery-
only deployment automatically. Recovery uses the independently authorized and
capability-staged policy in DES-0004.

Normal update and rollback do not require the discovery service, package
repository, normal signing environment, WAN, DNS, or routed data plane once the
applicable sets and policy are retained locally. Role-specific remote
coordination may affect rollout timing but is not a boot dependency.

## Installation and storage

An installer, full-disk image, VM disk, or factory image is a transport and
initialization vehicle, not automatically the long-term deployment identity.
It may contain:

- one or more normal deployment sets;
- an independently authorized recovery set;
- storage-layout declarations;
- boot and selection metadata; and
- initial empty or provisioned state containers.

After installation, mutable state diverges while the contained deployment
identity remains the identity of its release-owned artifact closure. Replacing
or migrating the disk layout is a separately planned storage operation. It must
not reclassify mutable disk contents as release artifacts or claim that a disk
snapshot is an OS release.

The physical substrate may use A/B partitions, content-addressed objects,
versioned files, filesystem images, or another mechanism. Conformance depends
on complete-set identity, inert staging, transactional selection, boot-time
binding, and recoverability rather than the shape alone.

## Role traces

### Reference VM

- The VM qualifies each literal final deployment set before physical rollout.
- A VM disk wrapper does not replace the identities of the boot, root, and
  extension artifacts it contains.
- Controlled UEFI and vTPM state exercise applicable boot and unlock policies.
- Failure injection covers every staging and selection boundary.

### Workstation

- The normal deployment set includes the generic kernel and exact privileged OS
  and desktop artifacts selected for the machine.
- `/home`, user applications, development containers, and VM disks remain user
  or workload state and do not roll back with the OS.
- A failed graphical session can prevent blessing even when basic boot succeeds;
  diagnostics survive fallback under their state contract.
- Local developer or administrator extensions remain explicit and cannot inherit
  normal release qualification silently.

### Router

- The router may use a smaller or differently shaped deployment variant without
  changing discovery, staging, selection, assessment, rollback, and recovery
  semantics.
- Exact non-secret network and service policy is resolved into or named by the
  deployment set; long-lived credentials remain machine state.
- Health includes externally observed forwarding and critical network services,
  not merely reaching a local service state.
- Retained boot, fallback, and deliberate recovery remain usable without WAN,
  DNS, registry, or the normal routed data plane.

## Failure analysis

| Failure | Required behavior |
| --- | --- |
| Mutable tag or URL resolves to different bytes | Content and authorization verification reject the substitution; discovery location has no identity authority. |
| One artifact is missing, corrupt, or from another deployment | The set remains ineligible; current selection is unchanged. |
| Power fails during staging | Partial objects remain inert and can be resumed or discarded without affecting current boot. |
| Power fails while recording the next selection | Boot resolves either the previous complete selection or the new complete selection, or stops with attributable diagnostics; it never constructs a hybrid. |
| Boot loads a mismatched kernel, root, extension, or configuration artifact | Normal trust verification fails before the set is treated as the selected qualified deployment. |
| Candidate boots but health fails | Do not bless; fall back only to a compatible, authorized normal set and preserve diagnostics. |
| Candidate crosses a forward-only state barrier | Remove incompatible old sets from automatic fallback eligibility while retaining their bytes only under declared recovery or forensic policy. |
| Machine-specific late-bound value is missing or invalid | Fail at its declared lifecycle stage and report the input class; do not synthesize a different configuration or rebuild the OS. |
| Local executable override persists across OS rollback | Report the base deployment and effective modification separately; use compromise recovery when trust is in doubt. |
| Publication and normal network disappear | Continue booting and assessing retained sets under offline policy; updates wait. |
| All retained normal sets fail | Stop in a diagnosable state and require deliberate recovery; do not silently promote recovery to normal. |
| Garbage collection removes a shared object | Treat every affected deployment set as incomplete and ineligible; retention accounting must operate on transitive manifest reachability. |

## Alternatives considered

### Complete disk image as the deployment unit

Rejected. It confuses mutable machine and user state with release identity and
makes post-install disk divergence unavoidable. Disk images remain useful
installation and VM transport artifacts.

### Root filesystem image alone

Rejected. Separately stored boot artifacts, privileged extensions, and normal
configuration could drift outside the qualified and authorized identity,
violating SYS-030 and literal-artifact qualification.

### Kernel or UKI plus a mutable traditional root

Rejected for trusted normal production. Authenticating only early boot leaves
privileged userspace substitutable and conflicts with accepted SYS-030.

### Desired package or configuration set

Rejected as the deployment identity. Re-evaluating or converging packages on
the machine can produce bytes different from qualification and conflicts with
SYS-017. Package metadata and configuration remain build inputs.

### One universal artifact for every role and machine

Rejected. It hides role requirements behind runtime conditionals, expands each
machine's attack and update surface, and contradicts the accepted permission
for role-specific kernels, packages, layouts, and artifacts.

### Independently updated boot, root, and extension resources

Rejected as independent normal release units. A transfer mechanism may update
them separately, but a complete deployment manifest must bind the compatible
combination before selection.

### Substrate-native identity only

Deferred as an implementation mapping, not accepted as the architecture. An OCI
digest, OSTree commit, GPT resource version, or image hash is sufficient only
if it identifies the complete NeutrinOS deployment set and preserves its
qualification and authorization joins. Otherwise a project-level manifest is
still required.

## Verification

The design is viable when tests demonstrate:

1. any change or substitution in a release-owned artifact changes or invalidates
   the complete deployment identity;
2. the literal platform-signed deployment set is the set named by qualification
   and release authorization;
3. interruption at every transfer, verification, and selection boundary cannot
   make a partial or hybrid set boot-eligible;
4. a boot verifies the complete selected set rather than trusting staging-time
   verification alone;
5. the running system reports deployment identity separately from authorization,
   qualification, selection, assessment, freshness, compatibility, local
   modification, and support;
6. exact checked-in workstation and router configuration changes produce a new
   deployment identity, whether by changing another release artifact or a
   separately stored immutable configuration artifact named by the manifest;
7. secrets and actual hardware values remain late-bound without permitting the
   machine to reconstruct a different OS;
8. workstation and router variants use the same lifecycle states and evidence
   while retaining their required artifact and health differences;
9. rollback reselects only a complete, authorized, state-compatible normal set;
10. losing publication and normal networking does not prevent retained boot,
    fallback, status, or deliberate recovery;
11. recovery-only authorization cannot become normal through failed-boot logic;
    and
12. garbage collection preserves the complete transitive closure of every
    retained normal and recovery identity.

## Risks and unresolved questions

- Which exact artifact classes must the initial normal deployment set contain
  on the direct systemd/UAPI substrate and on the bootc challenger?
- Can the selected boot and update mechanisms commit one complete selection
  across separately stored resources without a project-owned update engine?
- Which executable extensions belong to the base deployment, and which remain
  administrator, user, or workload state with separate support status?
- Is an immutable per-machine configuration artifact operationally better than
  rebuilding otherwise shared deployment artifacts for each machine?
- How should a release group variants when one role is delayed, withdrawn, or
  incompatible with a cross-machine protocol?
- What minimum externally observable health and boot-attempt policy applies to
  each role?
- Which status and manifest fields must survive schema evolution across every
  retained rollback and recovery set?
- What freshness and offline-revocation rule determines whether a mechanically
  retained normal set remains selectable?
- At what variant count or qualification duration does exact per-machine build
  identity become unsustainable for the personal fleet?

## Evidence and review disposition

The [existing-system comparison](../../research/comparisons/existing-systems.md)
supports a thin NeutrinOS policy and evidence surface over upstream lifecycle
components rather than a new image or update engine. The
[bootc comparison](../../research/comparisons/bootc-vs-systemd-sysupdate.md)
keeps both substrate candidates accountable to the same complete-set identity
and failure boundaries. The
[executable-input tabletop](../../research/exercises/0004-executable-input-inventory.md)
assigns inputs outside the immutable root explicit owners and status effects
without extending release qualification to mutable code. The
[representative-manifest tabletop](../../research/exercises/0005-representative-deployment-manifests.md)
shows how VM, workstation, and router tuples can bind exact configuration while
sharing unchanged content and evidence only at justified boundaries. The
[substrate mapping](../../research/comparisons/deployment-set-substrate-mapping.md)
maps those semantics to one sysupdate host target or a flattened bootc OCI
deployment, rejecting a custom updater while identifying two narrow evidence
and status joins. DES-0002, DES-0003, and DES-0004 provide state, trust, and
authority constraints incorporated here.

The proposal is now in adversarial review. No artifact format, manifest schema,
disk topology, updater, installer, or health implementation is selected, and no
candidate lifecycle requirement is ratified by this document alone.
