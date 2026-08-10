---
id: RES-0003
status: in-review
last_updated: 2026-08-10
evidence_cutoff: 2026-08-09
decision_gates: [P-001, S-001, L-004]
review: reviews/0002-bootc-vs-systemd-sysupdate.md
---

# bootc versus systemd-sysupdate

## Question

Does an accepted NeutrinOS requirement justify assembling the host lifecycle
directly from `systemd-sysupdate` and adjacent systemd/UAPI components, or
should bootc be the default substrate candidate?

This comparison treats the candidates at their actual product boundaries.
bootc is an opinionated installation and host-update system. `systemd-sysupdate`
is a generic atomic resource-transfer mechanism that must be combined with an
image builder, partition layout, installer, boot policy, state model, release
publisher, and fleet policy.

## Summary judgment

Accepted SYS-030 now gives a direct systemd/UAPI composition a decisive current
advantage: normal physical boot must authenticate the complete release-owned
boot and immutable-root chain. The documented bootc production path does not
currently demonstrate that claim; its systemd-boot and sealed UKI/composefs
path remains experimental.

A direct systemd/UAPI and mkosi composition therefore becomes the **default
substrate candidate**, not an accepted architecture. bootc remains the strongest
challenger because its stable CLI and API, OCI distribution, installation,
staged updates, machine-readable status, switching, and rollback would
materially reduce NeutrinOS-owned lifecycle integration if a production-
supported path can satisfy SYS-030.

The selection cannot be finalized from documentation. The systemd composition
must prove that its stronger trust fit does not create an unreliable,
project-owned lifecycle product. NeutrinOS will not adopt bootc's experimental
backend merely to satisfy the requirement. Production-supported, symmetric
lifecycle spikes remain gates for the substrate ADR.

The follow-up
[deployment-set mapping](deployment-set-substrate-mapping.md) now maps every
DES-0001 identity and lifecycle field onto both candidates. It rejects a custom
updater or object store, but finds that both paths still need a bounded detached
release-evidence envelope and a read-only status/gate join.

## Requirements applied

Accepted requirements may disqualify a candidate. Candidate requirements guide
the comparison but cannot decide it until ratified.

| Requirement | Status | Consequence for this comparison |
| --- | --- | --- |
| SYS-002 | Accepted | The release process must pin and qualify the literal OCI digest or systemd resource set eventually offered to a machine. |
| SYS-003, SYS-019–SYS-026 | Accepted | A rollback command is insufficient; interrupted staging, failed boot, state compatibility, preservation, diagnostics, and recovery must be exercised. |
| SYS-005 | Accepted | Workstation and router must share lifecycle semantics even if their image contents or storage layouts differ. |
| SYS-008, SYS-031 | Accepted | The running system needs exact deployment identity and machine-readable, independently meaningful release and support properties. |
| SYS-014–SYS-016 | Accepted | Neither Containerfiles nor transfer definitions may become an open-ended operator-facing machine language; resolved inputs and generated configuration must remain inspectable. |
| SYS-017 | Accepted | Deployment must name the already qualified OCI digest or complete resource-set identity, not merely a mutable tag or version string. |
| SYS-018 | Accepted | Configuration and deployment failures must identify the responsible input, scope, output, and lifecycle stage on either substrate. |
| SYS-028–SYS-041 | Accepted | Authorization, staging, boot integrity, status, recovery, trial boot, blessing, retention, and offline lifecycle behavior apply to the complete substrate mapping. |
| SYS-057–SYS-064 | Accepted | Package input resolution, retained closure, source boundaries, currentness, executable build inputs, and upstream transitions remain independent of the deployed substrate. |

## Upstream facts

### bootc

The [bootc introduction](https://bootc.dev/bootc/) describes transactional host
updates using OCI images and states that its CLI and API are stable. The
[upgrade documentation](https://bootc.dev/bootc/upgrades.html) provides
download-only staging, explicit application, image switching, status, and
rollback. The [installer documentation](https://bootc.dev/bootc/bootc-install.html)
covers disk installation, provisioning hooks, TPM2-bound LUKS, and installation
provenance containing the source image reference and digest.

The production backend is OSTree. OCI layers are imported into a content-
addressed OSTree store and flattened into deployments, as described by the
[storage documentation](https://bootc.dev/bootc/filesystem-storage.html).
`bootc status` exposes structured YAML or JSON intended for programmatic use,
including booted and staged deployments, according to the
[status manual](https://bootc.dev/bootc/man/bootc-status.8.html).

The state model is materially opinionated. The
[filesystem documentation](https://bootc.dev/bootc/filesystem.html) defines a
read-only image root, persistent `/var`, and either a persistent three-way-
merged `/etc` or recommended transient `/etc`. This is useful prior art, but
its rollback behavior still has to satisfy the NeutrinOS state-owner contract.

Important current limitations are documented upstream:

- [bootloader documentation](https://bootc.dev/bootc/bootloaders.html) says
  bootloader updates are not automatic and systemd-boot is supported only by
  the composefs backend, not the production OSTree backend;
- the [composefs backend](https://bootc.dev/bootc/experimental-composefs.html),
  which supplies the sealed UKI path, remains explicitly experimental despite
  now being described upstream as close to stabilization; and
- [boot-failure detection](https://bootc.dev/bootc/boot-failure-detection.html)
  differs by backend, with composefs boot counting and an equivalent
  boot-complete check still incomplete.

bootc does not require a particular role-authoring interface, but its normal
image derivation examples use Containerfiles and shell commands. That build
implementation is compatible with SYS-014 only if NeutrinOS keeps normal role
and machine intent in bounded data or native files and exposes the resulting
OCI filesystem and metadata for review.

### systemd-sysupdate and adjacent components

The upstream
[systemd-sysupdate manual source](https://github.com/systemd/systemd/blob/main/man/systemd-sysupdate.xml)
defines atomic updates for files, directories, subvolumes, partitions, and
combinations such as a root filesystem, verity data, and kernel image. It can
retain two or more versions, recognizes incomplete downloads, operates on
running systems or offline disk images, and separates periodic acquisition
from reboot scheduling.

The
[transfer-definition manual source](https://github.com/systemd/systemd/blob/main/man/sysupdate.d.xml)
defines declarative source/target matching, instance retention, and signature
verification of SHA256 manifests. Multiple transfers in one component can
coordinate resources that must advance together; separate components and
optional features can have independent lifecycles.

`systemd-sysupdate` does not create the target partitions it updates. Its own
documentation directs image authors to `systemd-repart`. Installation, image
construction, release publication, state layout, and fleet orchestration
therefore remain integration responsibilities. The surrounding systemd stack
does provide strong building blocks: the
[automatic boot assessment model](https://systemd.io/AUTOMATIC_BOOT_ASSESSMENT/)
connects boot counting, health gates, blessing, and fallback, while
[mkosi](https://github.com/systemd/mkosi) builds package-based disk images,
UKIs, verity data, and related artifacts.

This composability is valuable when the disk layout and trust chain are product
requirements. It is also the main cost: NeutrinOS would own the glue and stable
operational interface that bootc already supplies.

## Comparison

| Dimension | bootc production path | systemd-sysupdate composition |
| --- | --- | --- |
| Release transport | OCI registry and digest; established container distribution and policy ecosystem | HTTP or local resource sets with signed checksum manifests; publication convention is project-owned |
| Install/update surface | Integrated install, fetch, stage, apply, switch, status, and rollback | Atomic acquire/update primitive; install and lifecycle orchestration are composed from adjacent tools |
| On-machine identity | Structured booted/staged image status and install provenance | Versioned resources are inspectable; NeutrinOS must define a joined release identity and status contract |
| Production maturity | Stable surface over production OSTree backend | Shipped systemd component, but the complete distro lifecycle is a project integration rather than one promised product surface |
| Boot recovery | Explicit rollback; automatic failure handling varies by backend and is incomplete for composefs | Native boot counting and extensible health/blessing model, but correct end-to-end integration is the image author's responsibility |
| Trust path | OCI signature policy available; fully sealed systemd-boot/UKI/composefs path is experimental | Natural fit for signed UKIs, verity partitions, DDIs, and user-owned keys; complete policy and key lifecycle remain project work |
| State semantics | Defined `/etc` and `/var` behavior, including a transient-`/etc` option | Deliberately unspecified; NeutrinOS must design all state ownership and migration behavior |
| Independent components | Host OCI image is the main release unit; bound images add related payloads | Multiple synchronized resources plus independently updated components and optional features are first-class |
| Role authoring risk | Containerfile/shell derivation can become the machine language if left unchecked | Transfer and mkosi layering can become a bespoke module system if left unchecked |
| Maintenance burden | Additional bootc/OSTree/container stack, but an upstream lifecycle product owns major integration | Smaller conceptual runtime stack, but NeutrinOS owns substantially more integration, compatibility, and operational UX |

## ADR-0001 exception analysis

ADR-0001 creates a preference, not an automatic selection. bootc still has a
strong material lifecycle justification:

1. it exposes one stable product surface for install through rollback;
2. it reuses OCI registries, digests, authentication, mirroring, and signature
   policy rather than requiring a NeutrinOS publication protocol;
3. it supplies a concrete state and deployment model to test; and
4. it reduces the amount of lifecycle integration NeutrinOS must own.

That justification cannot waive an accepted requirement. SYS-030 now requires
the directly authenticated immutable root that bootc's documented sealed path
provides only through an experimental backend. bootc can regain default status
if a production-supported configuration demonstrates the claim or if later
evidence shows the current assessment is incomplete.

## Proposed disposition

1. Treat the direct systemd/UAPI and mkosi composition as the default substrate
   candidate under accepted SYS-030.
2. Keep bootc as the lifecycle and maintenance challenger; reevaluate any
   production-supported path that can demonstrate SYS-030.
3. Do not accept a substrate ADR until the remaining trust model and concrete
   state ownership are specified enough to expose disqualifying constraints.
4. Before that ADR, run the same bounded lifecycle scenarios against both final
   candidates. A paper comparison cannot establish failure behavior or owner
   effort.
5. Reject either approach if ordinary role or machine changes require an
   operator-authored Containerfile, shell program, template language, or
   programmable module system in violation of SYS-014.

This resolves the present burden-of-proof challenge without circular reliance
on ADR-0001: the direct systemd composition leads because an independently
accepted trust requirement distinguishes it. It is not yet an accepted
architecture.

## Required lifecycle evidence

The later spikes must use pinned literal artifacts and record operator effort:

- construct and identify workstation and router artifacts from the same model;
- install to a blank UEFI QEMU disk and inspect provisioning provenance;
- stage a specific qualified release without following a mutable reference;
- interrupt acquisition and staging at representative boundaries;
- boot a deliberately unhealthy release and observe assessment and fallback;
- roll back after `/etc` defaults and mutable state have changed;
- recover when neither normal boot entry succeeds;
- rotate or revoke the update-signing authority used by the candidate;
- inspect the exact resolved configuration and release identity on the target;
  and
- estimate ongoing integration surfaces, upstream tracking, and fleet
  automation owned by NeutrinOS.
