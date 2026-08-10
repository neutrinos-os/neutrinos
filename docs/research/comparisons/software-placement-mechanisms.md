---
title: Software placement mechanism comparison
status: research-note
last_updated: 2026-08-10
supports: [DES-0013, EX-0015]
---

# Software placement mechanism comparison

## Question

Which current upstream mechanisms can realize NeutrinOS release, user, project,
desktop-application, workload, and guest placement classes, and which properties
must the project not infer from their names?

This note records upstream semantics. It does not accept a mechanism.

## Comparison axes

- lifecycle owner and mutation authority;
- artifact/input identity and verification;
- host integration and effective isolation;
- configuration, credential, and state ownership;
- update, rollback, offline, and removal behavior;
- native inspection and cross-plane ambiguity; and
- additional package universe, service, and maintenance cost.

## Native release packages

Packages resolved during the image build naturally participate in the existing
DES-0007 package closure, DES-0008 evidence, deployment identity, literal-boot
qualification, and fleet rollout. They are the strongest fit for role-required
host capability.

Their cost is coupling: any version change requires another deployment build
and applicable qualification. Installing them with a mutable package manager on
the target would bypass that lifecycle and is already outside project scope.

## systemd system extensions

The current `systemd-sysext` documentation says extensions merge additional
`/usr` and `/opt` content into the host using an overlay and are particularly
useful with immutable system images. The files resemble a normal OS tree and
extensions can carry release metadata used for compatibility matching.

Implications:

- sysext is host integration, not application sandboxing;
- activation changes the effective host software view even without changing
  backing root bytes;
- compatibility matching is necessary but not sufficient for NeutrinOS
  authorization, qualification, transaction, and rollback; and
- it is a plausible separately delivered release artifact, not a personal
  software installation plane.

Sources checked 2026-08-10:

- [systemd-sysext](https://www.freedesktop.org/software/systemd/man/devel/systemd-sysext.html)
- [System and service credentials](https://systemd.io/CREDENTIALS/) for the
  separate credential boundary

## Flatpak

Flatpak provides application/runtime identities, repositories, per-user and
system installations, independent updates, and a sandbox with static and
dynamic permissions. Upstream documents a restrictive default environment,
then enumerates permissions for network, display/audio, IPC, D-Bus,
filesystems, devices, and other host resources. Portals provide mediated access
for supported interactions.

Important limits:

- an application's effective permissions include its manifest, administrator
  and user overrides, dynamic portal grants, and host/runtime capability;
- broad filesystem, bus, device, or host-command access can dominate the
  default sandbox;
- per-user versus system installation changes the mutation owner and inventory,
  not the application code's intrinsic trustworthiness;
- an application update does not share the OS deployment transaction; and
- application data and permissions need their own backup/restore behavior.

Flatpak is therefore a strong desktop-application candidate, not evidence that
an arbitrary application is confined, maintained, current, or recoverable.

Sources checked 2026-08-10:

- [Flatpak basic concepts](https://docs.flatpak.org/en/latest/basic-concepts.html)
- [Flatpak sandbox permissions](https://docs.flatpak.org/en/latest/sandbox-permissions.html)
- [Using Flatpak](https://docs.flatpak.org/en/latest/using-flatpak.html)
- [Flatpak command reference](https://docs.flatpak.org/en/latest/flatpak-command-reference.html)

## mise

Current mise documentation describes per-user and per-project tool selection,
environment variables, tasks, configuration discovery, and lockfiles. A
`mise.lock` can pin exact versions and, depending on backend, URLs, checksums,
sizes, and provenance. Locked mode can reject missing pre-resolved URLs.

Important limits:

- backend support ranges from full artifact metadata to version-only;
- config can affect environments and run tasks/hooks, so trusting a checkout is
  an executable-input decision;
- global, parent, environment-specific, and local configuration introduce
  precedence that must be diagnosed;
- a lockfile is not created automatically in every workflow and its presence
  does not make unsupported backends equally verifiable; and
- fetched tools remain user-executed host code, not sandboxed applications.

This makes mise a plausible narrow user/project tool selector. It should not
own system services, host policy, recovery capability, or every dependency in
the machine.

Sources checked 2026-08-10:

- [mise overview](https://mise.jdx.dev/)
- [mise lockfiles](https://mise.jdx.dev/dev-tools/mise-lock.html)
- [mise settings](https://mise.jdx.dev/configuration/settings.html)
- [mise configuration](https://mise.jdx.dev/configuration.html)

## Toolbx and Distrobox-shaped development containers

Toolbx describes itself as a fully mutable container for development and
troubleshooting tools, editors, and SDKs. Its goals emphasize restoring a
familiar command-line environment on an immutable host. It integrates with the
user environment and exposes home/project files by design.

Consequences:

- it is well suited to mutable project exploration and dependency conflicts;
- its ergonomic host integration means it should not be described as a strong
  security sandbox without an exact access analysis;
- package installation after container creation is mutable history unless
  separately captured; and
- source ownership, credentials, agents, sockets, devices, and container-store
  backup remain explicit contracts.

Distrobox is a related candidate but requires its own literal evaluation; no
property is inherited merely because the interaction model is similar.

Sources checked 2026-08-10:

- [Toolbx documentation](https://containertoolbx.org/doc/)
- [Toolbx goals](https://containertoolbx.org/goals/)

## OCI images and rootless runtimes

The OCI image specification gives descriptors content digests and defines image
manifests, indexes, configuration, and filesystem layers. A digest can identify
exact image content; a mutable tag cannot.

OCI identity does not define runtime security, state, credentials, health,
networking, update ordering, or backup. DES-0012 separately requires exact
rootless namespace maps and attachment semantics. An image becomes a supported
workload only when joined to those contracts.

Sources checked 2026-08-10:

- [OCI Image Specification](https://specs.opencontainers.org/image-spec/)
- [OCI descriptor digests](https://specs.opencontainers.org/image-spec/descriptor/)

## AppImage and direct local binaries

A self-contained binary or filesystem image is a convenient transport. On its
own it does not give NeutrinOS a standard origin policy, confinement contract,
permission inventory, coordinated update/currentness record, state boundary,
or recovery path. A downloaded artifact can be content-identified and onboarded,
but the format alone supplies too little lifecycle integration to lead.

Default classification: local exception, not forbidden software.

Source checked 2026-08-10:

- [AppImage concepts](https://docs.appimage.org/introduction/concepts.html)

## Nix profiles and Linuxbrew

Both can provide broad user-level package universes. That breadth is also the
cost: another resolver, trust root, advisory/currentness process, cache/store,
garbage-collection model, configuration surface, and command-precedence layer.

Nix profiles do not remove the project's recorded Nix language and deployment
experience merely because their scope is per-user. Linuxbrew similarly remains
useful as a gap-filler rather than a presumed baseline. Either could be an
explicit user/project exception if a concrete need exceeds the operating cost.

Sources checked 2026-08-10:

- [Nix profiles](https://nix.dev/manual/nix/latest/package-management/profiles)
- [Homebrew on Linux](https://docs.brew.sh/Homebrew-on-Linux)

## Guests

A VM or microVM supplies a separate kernel boundary and can run another OS, but
creates another complete artifact, patch, identity, networking, storage,
credential, observability, and recovery lifecycle. W-002 must define the
NeutrinOS guest model before this class selects a mechanism.

## Comparative summary

| Mechanism | Best initial class | Main strength | Main false inference to reject |
| --- | --- | --- | --- |
| Image-built native package | Release | Exact deployment and qualification | Every useful tool must be in the image |
| sysext | Release extension | Separate host-integrated artifact | Safe mutable package layering |
| mise | User/project | Narrow tool/version selection | Lockfile means uniform provenance or sandboxing |
| Flatpak | Desktop application | App identity plus permissions/portals | Flatpak label means safely confined |
| Toolbx/Distrobox | Project development | Mutable familiar userspace | Container means reproducible or strongly isolated |
| OCI image | Workload | Content-addressed packaged filesystem | Digest defines safe runtime/state lifecycle |
| AppImage/local binary | Local exception | Simple portable delivery | Format defines origin, updates, or confinement |
| Nix profile/Linuxbrew | User/project exception | Broad package availability | More package coverage has low lifecycle cost |
| VM/microVM | Guest | Separate kernel/OS boundary | Stronger boundary is operationally free |

## Research conclusion

No mechanism spans all placement classes honestly. The decision should accept
the owner/lifecycle taxonomy first, then use EX-0015 to select a deliberately
small mechanism set. Native release packages, mise, Flatpak, exact OCI images,
and guests form the leading shapes; sysext, Toolbx/Distrobox, AppImage, Nix
profiles, and Linuxbrew remain bounded challengers or exceptions.
