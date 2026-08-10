---
status: informational
source: 2026-08-09-design-session-transcript.md
last_updated: 2026-08-10
---

# Design-session restart brief

## Purpose and authority

This is a compact briefing for resuming NeutrinOS architecture work without
depending on conversational context surviving compaction. It summarizes the
[original design-session transcript](2026-08-09-design-session-transcript.md)
and points to decisions made during later formalization.

This document is **not normative**. Apply this authority order:

1. accepted ADRs and accepted project policy;
2. accepted system requirements;
3. accepted designs;
4. explicit user facts, goals, and preferences recorded here;
5. stated directions and proposals still under review; and
6. exploratory assistant suggestions from the transcript.

An idea's presence in the transcript does not make it a decision. When this
brief conflicts with an accepted record, the accepted record wins and this
brief should be corrected.

## Owner context

These are user-supplied facts and motivations:

- Jason has used Linux for roughly 20 years and wants a technically modern,
  deeply understood system rather than a tutorial distribution exercise.
- The starting workstation environment is minimal Arch Linux with UKIs, TPM
  PCR measurements, i3, greetd, and extensive use of systemd-networkd,
  systemd-boot, systemd-resolved, and systemd-oomd.
- Jason previously tried systemd-homed and left it because Docker/Podman and
  subordinate-identity behavior were practical blockers.
- Jason operated CoreOS professionally for about five years. CoreOS's
  image/update model is valuable prior art, but rebuilding on its historical
  Gentoo-derived stack was experienced as too painful.
- Jason has some direct mkosi familiarity, including upstream interaction as
  GitHub user `JTarasovic`.
- Containers have been a normal tool for more than a decade; increased use of
  microVMs is an explicit goal.
- Version-controlled network and machine configuration is highly valued.
- The desired confidence comes from testing the literal configuration and OS
  artifacts, then deploying and rolling back those exact artifacts.
- The system should span workstation, router, laptop, server, and microVM use
  without forcing every role to have the same package set or artifact shape.
- Jason prefers newer safer or faster replacements for crufty userland tools
  when they are supportable.
- Jason is strongly aligned with the systemd ecosystem and wants an eventual
  Wayland migration that supports real remote-work requirements.

The later
[NixOS configuration and deployment retrospective](../research/experience/nixconfig-retrospective.md)
adds important operating evidence not present in the original transcript:
operator-facing configuration must not become a Turing-complete module
language, and missing convenience-schema support must not block direct use of
upstream-native configuration.

## Project thesis

The durable project idea is not “an Arch derivative” or “Fedora Atomic Sway
with different defaults.” It is a small image-based OS framework with these
distinguishing goals:

- one explicit deployment and configuration model across substantially
  different machine roles;
- build-time composition from pinned package inputs and reviewed native
  configuration;
- VM qualification of the literal artifacts before physical deployment;
- content identity, authorization, boot integrity, health, rollback, and
  recovery that remain distinct and inspectable; and
- mutable state whose ownership and compatibility remain separate from OS
  replacement.

The package distribution is an input to the build, not necessarily the product
identity. Arch familiarity and currency are useful; Fedora's maintained release
branches and systemd/Wayland/container integration are useful. The package
source remains open under
[DES-0007](../designs/0007-package-inputs-and-snapshot-policy/README.md):
Fedora stable is the leading candidate, and a literal Arch snapshot comparison
is required before acceptance. SYS-057 through SYS-064 accept the package-input
and snapshot-policy boundaries without selecting either ecosystem.

Supply-chain evidence, reproducibility, SBOM, vulnerability, and VEX semantics
are now under review in
[DES-0008](../designs/0008-supply-chain-evidence-and-vulnerability/README.md).
No evidence format, scanner, SLSA level, or reproducibility claim is accepted
merely because it appears in that proposal.

## User preferences that must remain visible

### Systemd and UAPI

- Prefer systemd ecosystem components when they satisfy a requirement.
- An overlapping non-systemd component needs a strong, recorded justification.
- Particularly relevant primitives include mkosi, UKIs, systemd-boot,
  systemd-repart, systemd-sysupdate, systemd credentials, systemd-networkd,
  systemd-vmspawn, boot assessment, and UAPI image/partition conventions.
- Systemd-first does not mean systemd-only, nor does a component's presence
  prove that it satisfies NeutrinOS's end-to-end contract.

This preference is now canonical in
[ADR-0001](../adrs/0001-systemd-first.md).

### Filesystems and storage workflows

The transcript contains an explicit user preference, not merely an assistant
idea:

- Jason is partial to Btrfs or ZFS.
- Filesystem features should make container and VM workflows materially easier.
- Btrfs is the leading general mutable-filesystem direction for `/var`,
  `/home`, container storage, VM images, and other mutable state.
- Reflinks are particularly attractive for cheap disposable copies of raw or
  DDI VM images.
- Subvolumes, checksums, compression, quotas, snapshots, and send/receive are
  capabilities worth evaluating and operating deliberately.
- ZFS is most attractive for a future dedicated storage or hypervisor role,
  where datasets, clones, zvols, and replication may justify its out-of-tree
  kernel integration.
- Filesystem features serve mutable state. Filesystem snapshots are not the
  primary OS deployment identity or rollback mechanism.

The current storage mechanism proposal is
[DES-0006](../designs/0006-storage-layout-and-encryption/README.md), which is
still in review. SYS-048 through SYS-056 accept its policy boundaries. The
mechanism design must preserve this stated direction while retaining ext4 as
an evidence-based challenger where a role does not benefit from Btrfs.

### Configuration

- Normal machine and network configuration belongs in version control.
- Prefer bounded declarative records and upstream-native files to a custom
  programming language.
- A project schema must not gate access to a supported upstream setting.
- Common, role, and machine intent should compose deterministically and remain
  inspectable in its fully resolved native form.
- Runtime machine observation may establish compatibility; it must not silently
  assign purpose or role.

The canonical result is
[ADR-0003](../adrs/0003-bounded-fleet-intent-representation.md) and
[DES-0005](../designs/0005-fleet-intent-and-configuration/README.md).

### Testing and rollback

- `mkosi build` and VM boot should exercise the literal artifact eventually
  offered to a physical machine.
- Router tests should model representative WAN/LAN topology and cover network
  services, failed updates, and loss of the router's own data plane.
- OS rollback should reselect a retained immutable deployment rather than
  rewind arbitrary mutable data through a whole-filesystem snapshot.
- A successful local boot does not substitute for qualification, authorization,
  state compatibility, or role-health evidence.

The canonical lifecycle requirements are in
[SYS-028 through SYS-041](../requirements/system.md) and
[DES-0001](../designs/0001-system-model/README.md).

### User, application, container, and VM ownership

The transcript explored a useful separation:

- host-critical tools and policy belong to the OS artifact;
- personal CLI baselines may use dotfiles and mise;
- project toolchains belong to their project environment;
- GUI applications may use an appropriate user-owned packaging or sandboxing
  mechanism;
- containers and microVMs are workload artifacts with separate writable state;
  and
- sysext should not become a random personal-software installation mechanism.

This is a useful direction, not a final software-placement decision. Flatpak,
AppImage, Nix profiles, Toolbx/Distrobox, and other mechanisms were compared but
none was accepted merely by appearing in the transcript.

### Rootless containers and identity

- Moving a container engine's internal store outside `$HOME` does not solve
  bind-mounted source-tree ownership and mapping problems.
- Stable user IDs, stable subordinate UID/GID ranges, idmapped mounts, and
  `keep-id` behavior deserve explicit tests.
- systemd-homed must not be reintroduced until rootless container storage,
  bind-mounted project trees, session behavior, backup, and recovery are
  demonstrably boring.
- A normal Btrfs home remains the leading simple baseline from the transcript.

This remains open under W-001 in the
[decision backlog](../project/decision-backlog.md).

### Desktop

User-stated context:

- Wayland migration is desired, but remote work was a blocker around 2020 and
  must be tested against current real workflows.
- greetd is already familiar and used.
- uwsm was appealing because systemd-owned session and application cgroups fit
  the desired process and systemd-oomd model.
- Using focused GTK/GNOME applications is acceptable; accidentally adopting a
  full desktop's session and settings machinery is not the same decision.
- Visual consistency matters even without a full desktop environment.

Sway, uwsm, mako, fuzzel, Waybar, particular portals, polkit agents, secret
services, remote-desktop tools, and GTK/Adwaita were candidate components in an
assistant-proposed capability matrix. They remain role-design inputs, not
accepted selections.

### Kernels and runtime minimization

- Custom kernels are desired for size, speed, and potentially no-initrd roles.
- Kernel source, configuration, modules, and resulting UKI must remain built,
  identified, and qualified artifacts.
- A generic kernel is the initial physical fallback; role-specific kernels need
  measured value and their own qualification.
- No-initrd is most plausible for tightly controlled microVMs and perhaps a
  router, but encryption, dm-verity, TPM, discovery, and recovery can justify a
  small systemd initrd.
- Perl and other build-time scripting dependencies need not be present in the
  runtime image. A “no runtime scripting language” router or microVM profile was
  suggested, not accepted.

Kernel specialization remains open under W-004.

## Provisional architecture carried by the transcript

The transcript motivates this candidate flow:

```text
pinned package and source inputs
        + reviewed role/machine configuration
        -> mkosi build
        -> signed UKI + immutable root artifact
        -> dm-verity/content binding
        -> boot the literal deployment in a VM
        -> role-specific qualification
        -> release authorization and publication
        -> inert staging on a machine
        -> trial boot, assessment, and blessing
        -> deliberate rollback or independently authorized recovery
```

Important ownership boundaries:

```text
release-owned: kernel, initrd, UKI, immutable root, exact normal configuration
machine-owned: enrollment, host identity, machine credentials, machine state
admin-owned: explicit attributable local overrides
user-owned: home, desktop settings, user credentials and applications
workload-owned: containers, VM disks, databases, queues, service data
operational: journals, health results, update and failure evidence
```

The accepted definitions of deployment set, deployment identity, qualification,
authorization, state, fallback, rollback, and recovery live in the
[project glossary](../project/glossary.md). Use those terms instead of copying
the looser language of the original chat.

## Existing systems and lessons to retain

- **Fedora Atomic Desktops:** a strong warning against claiming novelty for
  “immutable host + Sway + Flatpak + containers + rollback.” NeutrinOS needs a
  cross-role, exact-artifact invariant that those words alone do not provide.
- **CoreOS and Flatcar:** valuable image, rollback, and fleet-update experience.
  Omaha/Nebraska may inform rollout policy—who updates and when—without becoming
  the artifact installer or content identity.
- **GNOME OS:** close prior art for systemd-sysupdate, UAPI disk images,
  confext, mkosi migration, booting literal artifacts in CI, installer work,
  and debuginfod-style debug separation. Its use of BuildStream, Flatpak, or
  homed is not automatically applicable.
- **bootc/Fedora bootable containers:** the strongest lifecycle challenger to
  direct systemd/UAPI composition; production boot-to-root integrity remains a
  decisive comparison gate.
- **NixOS:** demonstrates powerful version-controlled composition, while local
  operating experience rejects its programmable DSL and deployment ergonomics
  as the primary operator interface for this project.
- **Amutable/ParticleOS:** useful inspiration for joining source, pinned inputs,
  build evidence, root hash, UKI identity, Secure Boot, measurement, and runtime
  reporting without assuming its implementation choices.

## Do not infer decisions from these transcript mentions

- A video title or research link is not project direction.
- composefs appeared in recommended videos; the original transcript did not
  select it as a NeutrinOS host-root mechanism.
- EROFS and XBOOTLDR were not selected in the original transcript.
- Flatpak was a candidate GUI boundary, not an accepted default.
- systemd-homed was explicitly associated with unresolved container blockers,
  not chosen for reuse.
- Omaha/Nebraska was proposed for rollout policy, not accepted as the updater.
- Arch and Fedora were compared; neither package source was selected.
- AUR content was proposed to require review, pinning, vendoring, and CI rather
  than entering an image directly; the repository policy remains open.
- Sway, uwsm, greetd, mako, fuzzel, portals, PipeWire, WirePlumber, polkit
  agents, and GNOME/GTK applications remain a capability shortlist until the
  workstation role accepts them.
- sysext/confext are mechanisms to evaluate at defined ownership boundaries,
  not generic package/profile abstractions.
- Custom kernels and no-initrd variants remain evidence-gated optimizations.
- Btrfs snapshots do not define OS identity, qualify state rollback, or replace
  independent backups.
- ZFS was a future storage/hypervisor direction, not the common root or mutable
  filesystem choice.

## Canonical decisions made after the transcript

Do not reconstruct these from the transcript; read their records:

- Project name and identifier: [NeutrinOS and `neutrinos`](../project/naming.md).
- Initial scope and target order: [personal fleet/reusable framework; VM,
  `desktop-jason`, then `router`](../project/scope.md).
- Project constraints and non-goals: [charter](../project/charter.md) and
  [principles](../project/principles.md).
- Systemd preference: [ADR-0001](../adrs/0001-systemd-first.md).
- Authority and recovery separation:
  [ADR-0002](../adrs/0002-separate-authority-and-recovery.md).
- Fleet-intent representation:
  [ADR-0003](../adrs/0003-bounded-fleet-intent-representation.md).
- Normative behavior: [system requirements](../requirements/system.md), using
  each requirement's individual status.
- Current unresolved work: [decision backlog](../project/decision-backlog.md).
- Actual platform evidence:
  [reference host inventory](../research/hardware/reference-host-inventory.md).

DES-0001 through DES-0004 contain accepted policy boundaries but still have
implementation-level review work. DES-0005 and ADR-0003 are accepted. The
policy boundaries in SYS-048 through SYS-056 are accepted; DES-0006 remains in
review while its concrete storage mechanisms await evidence. SYS-057 through
SYS-064 accept package-input policy; DES-0007 and the Fedora-versus-Arch
selection remain in review pending EX-0009. SYS-065 through SYS-074 accept the
supply-chain evidence and vulnerability policy boundaries; DES-0008 remains in
review for concrete formats, mechanisms, and costs.

## Restart checklist

Before continuing architecture work after compaction or in a new session:

1. Read this brief.
2. Inspect `git status` and recent commits; preserve uncommitted user work.
3. Read the [ADR index](../adrs/README.md),
   [system requirements](../requirements/system.md), and
   [decision backlog](../project/decision-backlog.md).
4. Read the complete current design and adversarial review for the active
   backlog question.
5. Use the [glossary](../project/glossary.md) rather than inventing synonyms.
6. Consult the full transcript for provenance when this brief says a direction
   came from it.
7. Never upgrade a preference, candidate, research mention, or assistant
   suggestion into an accepted decision without the normal review and ADR
   workflow.
