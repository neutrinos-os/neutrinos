---
id: RES-0004
status: in-review
last_updated: 2026-08-09
evidence_cutoff: 2026-08-09
decision_gates: [S-001, S-003, L-004]
---

# Deployment-set mapping to systemd/UAPI and bootc

## Question

Can DES-0001's complete deployment set map onto the native identity, transfer,
selection, boot, status, and retention objects of the two substrate candidates,
or would either path require NeutrinOS to build another updater or object store?

This comparison applies the semantic contract and representative variants from
[EX-0005](../exercises/0005-representative-deployment-manifests.md). It does
not select a substrate, disk layout, image format, or project manifest syntax.

## Evidence limit

The mapping is based on current upstream documentation, not a lifecycle spike.
`Native` below means that an upstream project documents the applicable object
or operation. It does not prove power-loss behavior, exact byte identity,
firmware interaction, or suitability on the reference hosts.

The current bootc production backend is OSTree. Its composefs backend is still
explicitly experimental, though upstream now describes it as close to
stabilization and commits to upgrades for systems deployed since bootc 1.16.0.
That movement is relevant but does not change the production-support gate.

The systemd documentation also describes features added across several systemd
releases. The spike must pin versions actually available to the chosen package
source rather than treating current upstream manuals as proof that every target
ships the same surface.

## Candidate object models

### Direct systemd/UAPI composition

The closest native object to one deployment set is a
`systemd-sysupdate` **host target**: several transfer definitions bound by one
common version. The upstream manual explicitly uses a root filesystem, matching
Verity data, and UKI as a combined synchronized update that completes only when
all resources exist for the same version.

The surrounding objects are:

| NeutrinOS responsibility | Candidate native object |
| --- | --- |
| Build output | mkosi-produced UKI, DDI/root image, Verity data, extension/configuration DDI, and metadata |
| Complete transfer group | One `systemd-sysupdate` host target containing every release-owned transfer for the variant |
| Transfer authentication | Signed `SHA256SUMS` plus unconditional payload hash checks for remote URL transfers |
| Inactive acquisition | `systemd-sysupdate acquire VERSION` |
| Offline installation of acquired bytes | `systemd-sysupdate update --offline VERSION` |
| Retained versions | Versioned files/partitions with `InstancesMax=` and `ProtectVersion=` |
| Boot/root discovery | systemd-boot, UKI/systemd-stub, DPS/DDI discovery, dm-verity |
| Boot attempt and blessing | Boot Loader Specification counting plus `systemd-bless-boot.service` |
| Update inspection/API | `systemd-sysupdate list`, `pending`, JSON output, and `org.freedesktop.sysupdate1` |
| Initial layout | `systemd-repart` and image-defined partition policy; installation orchestration remains separate |

`systemd-sysupdate` transfers whole files, directories, subvolumes, or
partitions and keeps at least two resource versions. It syncs newly downloaded
resources before and after finalization by default. Those are strong native
building blocks for inert staging and retained rollback, but the end-to-end
selection boundary still requires fault injection.

Systemd's optional-feature and separately enumerated sysext/confext/component
targets are not automatically members of the host deployment. A release-owned
role extension can satisfy DES-0001 only if it is transferred and selected as
part of the same host target or is otherwise bound to its exact host
deployment. Administrator-optional extensions retain a separate lifecycle and
status under EX-0004.

### bootc

The closest native object is the **OCI image manifest digest** selected by a
bootc host specification. In the production OSTree backend, OCI layers are
mapped into OSTree content and flattened into a deployment; the origin retains
the image reference and bootc exposes booted, staged, and rollback deployments
through its stable JSON/YAML status schema.

The surrounding objects are:

| NeutrinOS responsibility | Candidate native object |
| --- | --- |
| Build output and main content identity | Bootc-compatible OCI image and immutable OCI manifest digest |
| Kernel/initrd source | Content inside the OCI image, copied transactionally to the boot location during deployment |
| Transfer authentication | Container signature policy or OSTree remote signature policy plus OCI digests |
| Inactive acquisition | `bootc upgrade --download-only` and the staged deployment |
| Selection | Apply staged deployment, `bootc switch`, and bootloader ordering |
| Retained rollback | Booted/rollback OSTree deployments and `bootc rollback` |
| Related system images | Logically bound images pulled and retained with their owning host deployments |
| Update inspection/API | Stable `bootc status` YAML/JSON schema |
| Initial installation | `bootc install`, installation configuration, external installer integration, and `.bootc-aleph.json` provenance |

For NeutrinOS, a production bootc variant would initially need to flatten all
release-owned base-role code and exact normal configuration into the main OCI
image. Default persistent `/etc` three-way merge is incompatible with the
normal configuration contract; bootc's documented transient-`/etc` mode is the
appropriate starting point.

Logically bound images are useful for system-owned application containers:
bootc pulls them with an upgrade and retains those needed by rollback
deployments. They are not an initial answer for release-owned privileged base
behavior under SYS-030. Their store is separate, bootc currently honors only
the image-reference field, and the documented root fs-verity setting does not
cover that store. Base-role content remains in the host image unless a later
trusted-closure spike proves an equivalent binding.

## Field-by-field mapping

Ratings mean:

- `native`: the candidate directly provides the semantic object or operation;
- `composed`: adjacent upstream mechanisms can express it, with project-owned
  configuration and tests;
- `thin join`: NeutrinOS needs bounded metadata or status logic, but not an
  updater or content store;
- `gap`: no production-supported mapping currently satisfies the contract; and
- `test`: documentation is promising but only a spike can establish the claim.

| DES-0001 field or guarantee | Direct systemd/UAPI | bootc production OSTree | Consequence |
| --- | --- | --- | --- |
| Complete immutable deployment identity | `thin join`: one version synchronizes resource transfers, while signed checksum manifests identify bytes; the common version itself is not a content identity | `native` for the flattened host image via OCI manifest digest; installed boot artifacts and separately owned bootloader state still need closure evidence | Neither candidate natively exposes the complete NeutrinOS evidence tuple as one status identity |
| Exact boot artifact | `native/composed`: signed UKI is an explicit versioned transfer | `composed`: kernel/initrd are sourced from the image and transactionally installed; bootloader content is managed separately | Record final installed boot identities, not only build-source identity |
| Authenticated immutable root | `native/composed`: DDI/root plus signed dm-verity and UKI root binding fit SYS-030 | `gap` on the production path for the accepted platform-to-root claim | Direct path retains the current trust advantage |
| Sealed bootc root challenger | Not applicable | `native but experimental`: sealed UKI embeds the composefs digest and requires it at boot | Reevaluate only when the backend and full lifecycle are production-supported |
| Release-owned extensions | `composed/test`: DDIs, sysext/confext, and sysupdate transfers exist, but exact host membership and discovery must be proven | Flatten into host OCI image initially; logically bound images are inadequate for privileged trusted-base closure today | Do not treat compatible or co-retained content as exact set membership |
| Exact normal configuration | Preferred immutable confext is `composed/test`; safest first mapping is config flattened into the root | Flatten into derived OCI image and use transient `/etc`; separately signed configuration remains future-facing | EX-0005's shared-config target is conditional, not yet a substrate fact |
| Resolved build/config inputs | mkosi manifests, checksums, and project build evidence; `thin join` | OCI configuration/labels and project build evidence; `thin join` | Neither substrate replaces provenance or resolved-config evidence |
| Role authorization scope and platform compatibility | Transfer paths/patterns and image metadata can encode variants; `thin join` for authorization scope | OCI references/labels can encode variants; `thin join` for authorization scope | Mutable paths and labels remain discovery, never authority |
| State-contract identifiers | `thin join` in release evidence and image content | `thin join` in OCI content/metadata | Both need NeutrinOS state gates before selection and blessing |
| Health-policy identifier | `thin join`; systemd supplies boot counting and blessing mechanics | `thin join`; bootc has backend-specific failure detection but no complete NeutrinOS role-health join | Role health and evidence remain project policy |
| Manifest interpretation/schema | Transfer definitions and upstream versioned APIs are native; deployment evidence schema is project-owned | OCI and bootc status schemas are native; deployment evidence schema is project-owned | Prefer a detached bounded envelope over a second update manifest |
| Literal-artifact qualification join | `thin join` keyed by complete deployment identity | `thin join` keyed by OCI digest plus final boot closure | Neither tool owns qualification policy |
| Detached release authorization | Signed checksum manifests authenticate transfer but do not natively bind qualification, authorization scope, compatibility, or freshness; `thin join` | Container signature policy authenticates images but does not natively bind all NeutrinOS promotion claims; `thin join` | One small signed release-evidence envelope is justified on both paths |
| Inert partial staging | `native/test`: incomplete versions/resources are recognized and `acquire` separates fetch from installation | `native/test`: download-only and staged deployments isolate the running root | Fault injection remains mandatory |
| Complete-set selection | `native/test` for one sysupdate target with common version; external extension discovery is the hard case | `native/test` for flattened OCI deployment | Prove one old/new/stop outcome at every boundary |
| Boot-time binding of actual bytes | UKI-to-Verity root is strong; exact external config/extension tuple is a `gap/test` | Production boot path is a `gap` for SYS-030; sealed composefs is experimental | This is the critical discriminator for multi-artifact composition |
| Per-machine boot attempt accounting | `native` through BLS counting | Backend-dependent; OSTree integration is available but must be configured and exercised, composefs does not currently configure counting | No common bootc guarantee can be assumed from the CLI alone |
| Role-specific assessment and blessing | `composed`: systemd blessing supplies mechanism, NeutrinOS supplies health gate | `composed/gap`: project health plus backend mechanisms; automatic failed-boot behavior needs proof | A local successful service is not global qualification |
| Normal rollback selection | `composed/test`: retained version resources plus bootloader selection | `native/test`: rollback deployment and bootloader ordering | DES-0002 compatibility gates remain outside both tools |
| Recovery-only separation | Separate target/media/authorization by NeutrinOS policy | Separate image/media/authorization by NeutrinOS policy | Neither ordinary failed-boot path may select recovery automatically |
| Offline retained boot/fallback | `composed/test`; installed resources and boot entries need no update source | `native/test`; deployed OSTree content and boot entries need no registry | Router data-plane-loss test remains required |
| Complete-closure retention/GC | `composed/test`: instance retention and protected versions apply to resources; closure reachability must align | `native` for bootc deployments and logically bound image retention; project recovery/state artifacts remain separate | Exercise shared objects and retained recovery explicitly |
| Machine-readable deployment status | Native version/resource JSON and sysupdate D-Bus; `thin join` for all DES status dimensions | Native stable booted/staged/rollback JSON/YAML; `thin join` for all DES status dimensions | One read-only NeutrinOS status aggregator is justified |
| Installation/provisioning | `composed`: repart/image policy plus an installer or image wrapper | `native` for simple install; external installer required for richer storage; provenance file is useful | Installation remains separate from long-term deployment identity |

## The two justified NeutrinOS-owned joins

Neither mapping justifies a custom updater, object store, bootloader, image
format, or rollback engine. Both do justify two narrow project-owned surfaces.

### 1. Detached release-evidence envelope

The envelope joins existing immutable identities. It minimally identifies:

- the substrate-native deployment identity and complete artifact closure;
- qualification-record identity;
- role, platform, and machine-class scope;
- state and peer compatibility declarations;
- authorization class and signer;
- freshness, withdrawal, and offline policy; and
- schema/interpreter identity.

It does not carry artifact bytes, select storage slots, download content, or
replace OCI and `SHA256SUMS` transport verification. On a direct path it binds
the exact hashes behind one sysupdate version. On bootc it binds the OCI digest
plus any final boot artifact or platform-state identities not closed by that
digest.

If an upstream object later contains the complete fields and signatures, that
object replaces the envelope. `Deployment manifest` remains a semantic role,
not a commitment to permanent custom syntax.

### 2. Read-only status and gate join

A small status surface correlates substrate state with release authorization,
qualification, boot integrity, health, freshness, compatibility, platform
state, and local modifications. It reads upstream APIs and evaluates gates. A
thin coordinator may invoke the native operation after those gates pass; the
status surface must not become another mutable desired-state engine or
duplicate artifact storage.

The same join can answer why a candidate is ineligible before calling the
native install/select operation. Policy may coordinate an updater; it does not
reimplement its transaction.

## Configuration-artifact finding

EX-0005 preferred shared release artifacts plus a separately immutable bound
configuration artifact when the substrate can enforce the whole tuple.

The direct path has the more plausible native representation:

- confext DDIs provide immutable `/etc` content;
- sysupdate can transfer several resources under one host version; and
- UAPI defines UKI-specific auxiliary locations for confext and sysext DDIs.

This is still not enough on paper. Systemd extension compatibility normally
matches OS identity/version or extension level, and installed compatible
extensions can be activated automatically. Compatibility is weaker than exact
membership. The spike must show that a boot selects only the literal config DDI
authorized for that UKI/deployment and rejects another validly signed,
compatible DDI. If it cannot, normal configuration is flattened into the root
or its digest is bound into an authenticated early-boot object.

The bootc production path does not currently offer an equally natural
separately immutable config member with complete host-deployment semantics.
NeutrinOS should use derived OCI variants with exact config in the image and
transient `/etc` for the initial challenger. A future sealed/config-map or
equivalent mechanism may be reevaluated; ordinary first-boot provisioning is
not a substitute.

## Mapping the reference variants

| Variant | Direct systemd/UAPI paper mapping | bootc production paper mapping |
| --- | --- | --- |
| VM fixture | Signed UKI + root DDI + Verity + flattened fixture config in one host target | One fixture OCI digest with kernel/initrd and transient `/etc` |
| `desktop-jason` | Signed workstation UKI + root/Verity; initially flatten exact config, then challenge with a UKI-specific config DDI | One derived workstation OCI digest containing exact normal config; platform boot artifacts inventoried separately |
| `router` | Signed router UKI + root/Verity; exact network config flattened until external config binding passes; all transfers acquirable before offline install | One derived router OCI digest containing exact network policy; no privileged base-role logically bound images initially |

The direct path can still share build inputs, identical root or extension
objects, and static HTTP storage even when the first qualified variants flatten
configuration. The bootc path naturally shares OCI layers across derived images.
Neither physical representation changes the complete deployment identity or
qualification boundary.

## Adversarial findings

### Version coordination is not content identity

Systemd-sysupdate's common `@v` is an excellent synchronization key, but a
version string does not become the NeutrinOS deployment identity merely because
all filenames contain it. The detached envelope must bind the literal hashes,
and boot/runtime status must correlate the selected version to that content
identity.

### OCI identity does not automatically close over platform boot state

An OCI digest strongly identifies the bootc source image. The production path
extracts or copies kernel/initrd material and manages bootloader installation
separately; bootloader updates are not automatic. The spike must prove which
final bytes are derived deterministically from the digest and how any separate
release-owned boot artifact and bootloader state are identified and updated.

### Signature policy is not release promotion

Systemd's signed checksum manifest and bootc's container signature policy can
authenticate fetched bytes. Neither alone proves that those bytes passed the
named qualification, apply to this role, remain fresh, or are state-compatible.
Using the same key and a mutable discovery path would collapse authentication
and promotion in conflict with DES-0004.

### Native status is necessary but not sufficient

Both candidates now expose machine-readable update state. Neither natively
reports every independent DES-0001 dimension. The project should join, not
replace, those schemas and retain their raw evidence for diagnosis.

### The preferred composition may lose to the flattened fallback

A separately bound configuration DDI is elegant only if its complete-set
binding survives substitution, interrupted transfer, boot selection, rollback,
and garbage collection. Flattening exact configuration into the root is
acceptable and safer when that proof fails, even if it costs more build and
transfer work.

## Disposition

The mapping supports these conclusions:

1. **No custom updater or object store is justified.** Static HTTP plus signed
   checksum manifests and sysupdate targets are sufficient transport objects
   for the direct path; OCI/OSTree already own them for bootc.
2. **A detached release-evidence envelope is justified.** Neither native
   signature object carries qualification, scope, compatibility, freshness, and
   authorization class together.
3. **A read-only status/gate join is justified.** It correlates project evidence
   with native machine state without becoming another deployment engine.
4. **Direct systemd/UAPI remains the default candidate.** Its production
   building blocks map naturally to the accepted platform-to-root trust claim
   and a synchronized multi-resource host target.
5. **bootc remains the lifecycle challenger.** Its flattened OCI identity,
   integrated staging/rollback, status schema, installation, and content reuse
   are materially stronger product surfaces; its production trust closure is
   still disqualifying under SYS-030.
6. **Flattened normal configuration is the initial safe mapping on both paths.**
   The direct candidate may graduate to a separately immutable config DDI only
   after exact boot binding and fault-injection tests.

This completes DES-0001's substrate mapping at the documentation level and
mitigates review C-008. It does not resolve C-001 or A-014: only symmetric
production-supported spikes can show that native transaction and boot behavior
enforce the paper model without expanding the two thin joins into a custom
lifecycle product.

## Symmetric spike contract

Each candidate must use the same source/configuration change and record literal
objects, commands, failures, and operator-owned glue.

1. Build a VM fixture plus one workstation and router candidate.
2. Identify every source artifact, installed boot artifact, root, config input,
   native deployment object, and detached evidence join.
3. Acquire a pinned identity without making it boot-selectable.
4. Interrupt each download, finalization, selection, and sync boundary.
5. Substitute one valid artifact from another deployment and attempt boot.
6. Boot, report identity, fail health, exhaust attempt count, and return to an
   eligible compatible normal deployment.
7. Cross a state-compatibility barrier and verify automatic fallback is removed.
8. Remove the network/registry/publication source and repeat retained boot,
   fallback, status, and deliberate recovery.
9. Retain two deployments sharing content, garbage-collect another, and verify
   both closures.
10. Record build time, bytes built/transferred/retained, qualification duration,
    project code/config surface, and upstream-specific maintenance obligations.

## Upstream sources

### systemd/UAPI

- [systemd-sysupdate manual source](https://github.com/systemd/systemd/blob/main/man/systemd-sysupdate.xml)
- [sysupdate transfer-definition manual source](https://github.com/systemd/systemd/blob/main/man/sysupdate.d.xml)
- [sysupdate D-Bus API manual source](https://github.com/systemd/systemd/blob/main/man/org.freedesktop.sysupdate1.xml)
- [automatic boot assessment](https://systemd.io/AUTOMATIC_BOOT_ASSESSMENT/)
- [boot and root discovery](https://systemd.io/ROOTFS_DISCOVERY/)
- [Discoverable Disk Images](https://uapi-group.org/specifications/specs/discoverable_disk_image/)
- [Extension Images](https://uapi-group.org/specifications/specs/extension_image/)
- [Unified Kernel Images](https://uapi-group.org/specifications/specs/unified_kernel_image/)
- [mkosi](https://github.com/systemd/mkosi)

### bootc

- [bootc introduction](https://bootc.dev/bootc/)
- [upgrade and rollback](https://bootc.dev/bootc/upgrades.html)
- [status API](https://bootc.dev/bootc/man/bootc-status.8.html)
- [image layout](https://bootc.dev/bootc/bootc-images.html)
- [filesystem and transient `/etc`](https://bootc.dev/bootc/filesystem.html)
- [container storage](https://bootc.dev/bootc/filesystem-storage.html)
- [logically bound images](https://bootc.dev/bootc/logically-bound-images.html)
- [bootloader integration](https://bootc.dev/bootc/bootloaders.html)
- [boot-failure detection](https://bootc.dev/bootc/boot-failure-detection.html)
- [installation](https://bootc.dev/bootc/bootc-install.html)
- [experimental composefs backend](https://bootc.dev/bootc/experimental-composefs.html)
