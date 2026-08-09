---
id: RES-0001
status: in-review
last_updated: 2026-08-09
evidence_cutoff: 2026-08-09
decision_gate: CH-001
review: reviews/0001-existing-systems.md
---

# Existing-system adopt/build/borrow comparison

## Question

Can an existing system reasonably provide the provisional NeutrinOS invariant,
and if not, which existing work should NeutrinOS adopt instead of recreating?

The invariant requires one version-controlled, test-gated machine model across
heterogeneous roles. The literal release artifacts and applicable declarative
configuration must pass role tests before deployment. Transactional
replacement, rollback, and recovery are part of the release contract.

## Summary judgment

There is no justification for building a new image, update, boot, or rollback
substrate.

The project boundary remains a thin NeutrinOS role, configuration,
qualification, release, and fleet-policy layer over existing lifecycle
components. The follow-up
[bootc versus systemd-sysupdate comparison](bootc-vs-systemd-sysupdate.md)
makes a direct systemd/UAPI and mkosi composition the default substrate
candidate under accepted SYS-030. bootc remains the lifecycle and maintenance
challenger if a production-supported path can authenticate the complete
release-owned boot and immutable-root chain.
[ParticleOS](https://github.com/systemd/particleos) is the closest executable
reference for the default candidate and should be studied and reused
selectively, not silently forked or treated as a stable dependency.

This does **not** yet satisfy CH-001. NixOS was a credible adopt-instead
candidate on technical capabilities, but the
[owner's operating retrospective](../experience/nixconfig-retrospective.md)
identifies a material conflict with the desired authoring and deployment
model. The derived data-first configuration requirements are now
[accepted](../../project/reviews/0002-configuration-authoring-boundary.md), so
NixOS is rejected as the primary framework rather than hidden behind a new
project DSL.

bootc is not rejected as a lifecycle product, but it is no longer the default
substrate candidate. Its documented production backend does not currently
demonstrate SYS-030, while the sealed systemd-boot/UKI/composefs path is
experimental. The later substrate ADR must compare production-supported paths
through the same trust, state, and lifecycle scenarios.

The unresolved objections and acceptance gates are tracked in the
[adversarial review](reviews/0001-existing-systems.md).

## How candidates are judged

This is not a feature-count comparison. Each candidate is tested against the
same six obligations.

| Obligation | Pass condition |
| --- | --- |
| Release identity | A deployment names an immutable or content-addressed whole-system artifact, not merely a desired package set. |
| Literal-artifact qualification | The artifact offered to machines can be the artifact that passed boot and role acceptance tests. |
| Common multi-role model | Workstation and router roles can share source, lifecycle semantics, and evidence while retaining explicit differences. |
| Transaction and recovery | Staging, activation, health assessment, rollback, and offline recovery have explicit mechanisms. |
| State and configuration | OS, machine configuration, secrets, user data, and workload state have separable ownership and update semantics. |
| Sustainable adoption | The project can consume the system without inheriting an unjustified packaging fork or an unbounded compatibility surface. |

Security, provenance, key management, and fleet rollout are also important,
but none of the candidates supplies the complete accepted NeutrinOS contract
without project-specific policy and evidence.

## Outcome matrix

Ratings are judgments from the cited upstream capabilities, not results from
hands-on spikes. `Strong` does not mean complete.

| Candidate | Release identity | Literal artifact testing | Multi-role model | Transaction/recovery | State/configuration | Conclusion |
| --- | --- | --- | --- | --- | --- | --- |
| NixOS | Strong | Strong | Strong | Mixed | Strong mechanics; poor operator fit | **Reject as the primary framework** |
| bootc / rpm-ostree | Strong | Strong | Moderate | Strong | Moderate | **Lifecycle challenger; production trust gap** |
| ParticleOS | Strong | Promising | Moderate | Promising | Promising | **Borrow as executable reference** |
| GNOME OS | Strong | Promising | Weak | Promising | Promising | Borrow mechanisms and operating lessons |
| Flatcar | Strong | Moderate | Weak | Strong | Moderate | Borrow provisioning and fleet patterns |
| Conventional Arch | Weak | Project-supplied | Moderate | Project-supplied | Project-supplied | Use only as a possible package input |

## Candidate findings

### NixOS

#### Upstream facts

The [NixOS manual](https://nixos.org/manual/nixos/stable/) documents a
declarative system configuration, named generations, rollback, image building,
and a QEMU-based multi-machine test framework. It also documents
`systemd-repart` image definitions and an image-appliance profile that disables
on-machine configuration switching when images are updated externally.

Nix derivations and sandboxed builds provide a strong basis for traceability,
but the [NixOS reproducibility project](https://reproducible.nixos.org/) makes
clear that this does not by itself guarantee bit-for-bit reproducibility.
Standard NixOS also ordinarily retains `/nix` and `/boot`, and its familiar
operating model is generation switching backed by an on-machine Nix store,
rather than signed discoverable disk images promoted through
`systemd-sysupdate`.

#### Assessment

NixOS has the strongest version-controlled role composition and test story in
this set. Its appliance facilities may be enough to make the exact output
artifact externally qualified and promoted. The question is not whether NixOS
can build a workstation and router; it can.

The [NixOS configuration and deployment retrospective](../experience/nixconfig-retrospective.md)
adds evidence that a capability comparison alone misses. The owner spent
substantial effort on Nix evaluation, local module abstractions, flake
composition, deployment integration, and escape hatches for upstream settings.
The desired source of truth is bounded machine data plus first-class native
configuration, not a Turing-complete operator-facing module program.

Constraining NixOS to an externally updated appliance could improve deployment
identity, but it does not remove Nix and the NixOS module system from
configuration authorship. Hiding them behind a new data schema would require
NeutrinOS to maintain another mediation layer and repeat the same capability-
lag problem.

#### Conclusion

**Reject as the primary configuration and deployment framework.** The reason
is an operator-model conflict documented from actual use and formalized in
accepted SYS-014 through SYS-018, not preference for systemd-native machinery.
NixOS remains useful prior art for composition and testing; adopting Nix as a
hidden image builder would need separate evidence.

### Fedora Atomic, rpm-ostree, and bootc

#### Upstream facts

[bootc](https://bootc.dev/bootc/) provides transactional, in-place OS updates
using OCI images and describes its API as stable. The broader
[bootable-container model](https://containers.github.io/bootable/) explicitly
targets version-controlled system definitions, atomic updates, rollback, and
preservation of `/etc` and `/var`. Its current implementation uses rpm-ostree.

The [rpm-ostree administrator handbook](https://coreos.github.io/rpm-ostree/administrator-handbook/)
documents immutable deployments, rollback, package layering and overrides, a
read-only `/usr`, and persistent `/etc` and `/var`. The
[bootc image specification](https://bootc.dev/bootc/bootc-images.html) covers
kernel and initramfs placement and optional composefs/UKI integration. The
[bootloader documentation](https://bootc.dev/bootc/bootloaders.html) also
records current boundaries: bootloader updates are separate, and systemd-boot
support is tied to the composefs backend.

Fedora CoreOS tooling demonstrates artifact-level VM testing:
[coreos-assembler](https://coreos.github.io/coreos-assembler/) builds images
and its [kola external tests](https://coreos.github.io/coreos-assembler/kola/external-tests/)
exercise built systems in provisioned machines. The same project now directs
custom immutable OS builders toward bootc.

#### Assessment

bootc already meets much of the release-identity, transactional update, and
rollback requirement with a stable interface and a familiar container
distribution path. It does not inherently provide NeutrinOS's role schema,
literal-artifact evidence join, state-owner contracts, or fleet policy—but
those are layers the project would also need on a systemd-native substrate.

Choosing a direct `systemd-sysupdate` composition instead of bootc requires more
than ADR-0001. Accepted SYS-030 now supplies that reason: the production bootc
path does not currently demonstrate authentication of the complete
release-owned boot and immutable root, while its sealed path is experimental.
The systemd composition must still prove that it can supply the lifecycle
reliability and operability bootc already integrates.

#### Conclusion

**Lifecycle and maintenance challenger; not selected.** Keep bootc as the
benchmark that a direct systemd design must beat on complexity, recovery, and
maintenance, and reevaluate a production-supported bootc path that satisfies
SYS-030. The Fedora Atomic desktop products themselves are not a multi-role
framework, but that does not reject bootc's reusable lifecycle mechanisms.

### ParticleOS and the systemd/UAPI image stack

#### Upstream facts

[ParticleOS](https://github.com/systemd/particleos) is an in-development,
customizable immutable distribution assembled with mkosi. It supports multiple
package bases and desktop profiles, uses `systemd-sysupdate`, and demonstrates
signed UKIs, dm-verity, user-owned Secure Boot keys, system extensions, and
installation with `systemd-sysinstall`. Its README explicitly provides no
backward-compatibility guarantee.

The surrounding specifications and documentation form a coherent substrate:

- [Discoverable Disk Images](https://uapi-group.org/specifications/specs/discoverable_disk_image/)
  define composable GPT images and signed dm-verity relationships.
- [systemd's image-building guidance](https://systemd.io/BUILDING_IMAGES/)
  describes image identity, first-boot population, repartitioning, and
  encryption behavior.
- [automatic boot assessment](https://systemd.io/AUTOMATIC_BOOT_ASSESSMENT/)
  connects boot counting, completion, blessing, and fallback.
- [root filesystem discovery](https://systemd.io/ROOTFS_DISCOVERY/) connects
  systemd-boot, UKIs, root images, system extensions, and configuration
  extensions.

#### Assessment

ParticleOS is close to the architecture NeutrinOS was independently describing.
That is evidence to narrow this project, not evidence to reproduce ParticleOS
under another name. The plausible NeutrinOS contribution is the layer it does
not claim to be: heterogeneous role definitions, configuration/state
contracts, qualification evidence, release promotion, and fleet policy for
this project's requirements.

ParticleOS is not yet a safe unqualified dependency. Its stated instability
means NeutrinOS should reuse upstream interfaces and selected configuration,
contribute generally useful fixes upstream, and keep any project-specific
policy visibly separate. A wholesale fork would create exactly the maintenance
burden CH-001 is intended to prevent.

#### Conclusion

**Borrow as the executable reference for the preferred substrate.** Do not
design a competing image layout, installer, boot assessment, or update engine.
Define an explicit upstream/dependency boundary before implementation.

### GNOME OS

#### Upstream facts

[GNOME OS](https://os.gnome.org/) is a pre-release system for virtual machines
and selected real hardware. GNOME's engineering reports document its move from
OSTree to `systemd-sysupdate`, use of system extensions, Secure Boot and
encryption work, and planned openQA coverage
([2024 report](https://blogs.gnome.org/tbernard/2025/04/11/gnome-stf-2024/)).

As of February 2026, its developers still described the system as unstable,
warned that early adopters might need to reinstall, and reported ongoing work
around `systemd-homed`, configuration extensions, and a mkosi/BuildStream DDI
prototype
([2026 report](https://blogs.gnome.org/adrianvovk/2026/02/18/gnome-os-hackfest-fosdem-2026/)).
GNOME also uses the OS as a
[VM-based application and platform test target](https://handbook.gnome.org/testing.html).

#### Assessment

GNOME OS is valuable evidence that the systemd-native path can support a real
desktop, configuration extensions, developer extensions, recovery, and CI. It
is not a reasonable base for the project because its product boundary is GNOME
development and desktop hardware, not heterogeneous workstation/router roles.
Adapting that boundary would effectively create a new distribution anyway.

#### Conclusion

**Borrow mechanisms and lessons.** Track its confext/sysext, installer,
recovery, vulnerability-reporting, and openQA work. Do not adopt the product or
its GNOME-specific policy as the multi-role base.

### Flatcar Container Linux

#### Upstream facts

[Flatcar](https://www.flatcar.org/docs/latest/) is a minimal, immutable
container-host OS with read-only images and atomic updates. Its provisioning
model translates [Butane into Ignition](https://www.flatcar.org/docs/latest/getting-started/);
[Ignition](https://www.flatcar.org/docs/latest/provisioning/ignition/) applies a
versioned machine configuration once during first boot. Its documented update
model uses A/B USR partitions and configurable reboot strategies
([updates and rollback](https://www.flatcar.org/docs/latest/getting-started/learning-series/immutability-updates-rollbacks/)).

[Nebraska](https://www.flatcar.org/docs/latest/updates-releases/nebraska/)
provides an Omaha-compatible service for fleet groups, channels, rollout, and
update metadata, including custom and air-gapped payload arrangements.

#### Assessment

Flatcar has strong operational patterns for immutable hosts, failure-safe
updates, first-boot provisioning, and fleet rollout. Its deliberate
container-host specialization and one-shot configuration model are poor fits
for a general workstation/router framework. Expanding it would fight the
product boundary rather than reuse it.

#### Conclusion

**Borrow patterns, not the product.** In particular, study Ignition's versioned
schema and deterministic first boot, A/B failure behavior, and Nebraska's
separation of rollout metadata from update payloads.

### Conventional Arch Linux

#### Upstream facts

Arch is a rolling package distribution. Its official repositories move forward
as a coherent set and normally remove superseded versions
([official repositories](https://wiki.archlinux.org/title/Official_repositories)).
Arch documents mkosi support for raw images, UKIs, Secure Boot, encryption, and
QEMU testing ([mkosi](https://wiki.archlinux.org/title/Mkosi)), while its
[reproducible-build effort](https://wiki.archlinux.org/title/Reproducible_builds)
remains ongoing.

#### Assessment

A conventionally mutated Arch host supplies neither whole-system release
identity nor transactional deployment. Project-specific image CI could add
those properties, but that means the lifecycle comes from mkosi/systemd or
another substrate rather than Arch itself. Arch remains attractive as a
package source and for custom kernel inputs, subject to the later maintenance
and snapshot decision.

#### Conclusion

**Do not adopt conventional Arch as the system lifecycle.** Keep Arch open as
a package-input candidate; do not create a downstream Arch packaging fork.

## Proposed architecture boundary

If the remaining challenges are resolved in favor of the systemd-native path,
the boundary should be:

| Layer | Default owner |
| --- | --- |
| DDI/UKI layout, boot discovery, boot assessment, extension format, update and install mechanisms | systemd and UAPI specifications/implementations |
| Image assembly and VM boot tooling | mkosi |
| Executable integration reference and reusable configuration | ParticleOS, selected explicitly |
| Package payloads and security fixes | chosen upstream distribution; undecided |
| Role schemas, composition policy, state contracts, qualification gates, evidence manifest, promotion and fleet policy | NeutrinOS |
| Applications and workload data | their declared owners, outside the OS rollback promise |

This boundary is a proposal, not an ADR. Any NeutrinOS component that moves
upward into the substrate must explain why the upstream interface is
insufficient and what long-term maintenance obligation the project accepts.

## Evidence limitations

- This pass is based on current primary documentation and source repositories,
  not hands-on prototypes or recovery drills.
- Project documentation tends to describe intended behavior more completely
  than failure modes and operational cost.
- The candidates evolve quickly; facts and conclusions should be revalidated
  when the substrate ADR is proposed.
- No security architecture has yet been accepted, so cryptographic feature
  presence is not treated as proof that the later threat model is satisfied.
- No package-input maintenance model has yet been chosen.

## Gates before CH-001 can close

1. Accept or revise the RES-0003 burden-of-proof result after the relevant
   trust and state requirements and symmetric lifecycle spikes exist.
2. Define the intended ParticleOS relationship: documentation reference,
   selected configuration reuse, upstream collaboration, or dependency.
3. Subject the result to an independent human review before accepting the
   distinguishing invariant.

## Proposed CH-001 disposition

**Keep open.** The research supports abandoning a greenfield substrate,
narrows the possible project contribution, and documents why NixOS's operator
model is a poor fit. It does not yet demonstrate that the proposed
systemd-native NeutrinOS layer is preferable to a bootc solution.
