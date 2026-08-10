---
id: DES-0013
title: Software placement and execution boundaries
status: in-review
owners: [Jason Tarasovic]
reviewers: [Codex adversarial pass]
created: 2026-08-10
last_updated: 2026-08-10
depends_on: [DES-0001, DES-0002, DES-0005, DES-0007, DES-0008, DES-0011, DES-0012]
decision_backlog: [W-003]
related_adrs: []
---

# Software placement and execution boundaries

## Problem

An image-based OS does not answer where every piece of software belongs. The
same executable might be shipped in the OS, installed for one user, selected by
a project, packaged as a desktop application, run as an OCI workload, or placed
in a guest. Those choices change who owns updates, which state is durable, what
can access the host, what rollback means, and which evidence supports it.

Without an explicit placement policy, an immutable root merely moves mutation
into `$HOME`, containers, application stores, extensions, and VM disks. The
machine then accumulates overlapping package universes and ambiguous commands
whose provenance, permissions, currentness, and recovery behavior are harder to
understand than a conventional mutable host.

## Goals

- Define placement classes by owner and lifecycle rather than package format.
- Keep role-critical and recovery-critical capability inside the qualified
  deployment boundary.
- Give user and project software useful autonomy without making it hidden OS
  configuration.
- Make application and workload confinement claims depend on effective access.
- Keep update, rollback, backup, vulnerability, and support status truthful
  across independently updated software.
- Provide a small decision procedure that works across workstation, server,
  router, and future laptop roles.

## Non-goals

- Select every application, editor, shell tool, runtime, or language version.
- Accept Flatpak, mise, Toolbx, Distrobox, AppImage, Podman, Docker, or a
  microVM implementation merely because it is a candidate.
- Define the detailed microVM lifecycle owned by W-002.
- Require all software on a machine to update or roll back atomically.
- Treat every personal executable as a NeutrinOS-supported component.
- Prevent an administrator or user from running arbitrary code they control.
- Make sysext a general-purpose personal package manager.

## Inputs and constraints

The transcript established a direction, not a decision:

```text
host-critical capability -> OS artifact
personal CLI baseline     -> user-owned configuration/tooling
project toolchain         -> project environment
desktop application       -> sandboxed application mechanism when suitable
service/dev workload      -> OCI image and separate writable state
different kernel/OS       -> microVM or VM artifact
```

The accepted scope rejects arbitrary host package-manager mutation and support
for every packaging ecosystem. DES-0002 requires explicit state owners.
DES-0007 and DES-0008 require exact intake, provenance, maintenance, and
vulnerability evidence for release-owned software. DES-0011 owns credentials,
and DES-0012 owns Unix identity and rootless mappings.

## Decision drivers

1. A role must boot, recover, and provide its promised capability without a
   user logging in or a mutable user/project package source being available.
2. User and project iteration should not force a whole-OS rebuild when the
   software is not part of the role contract.
3. Placement must not turn source checkout, shell activation, desktop launch,
   or container start into an invisible privilege escalation.
4. One maintainer cannot securely operate an unbounded number of package,
   update, advisory, and rollback systems.
5. The current machine must explain which executable will run and who owns it.
6. OS rollback must not be advertised as rolling back independently owned
   applications, tools, containers, or guests.

## Proposed terminology

### Software component

Executable code or executable-adjacent content installed or made available on
a managed machine, including binaries, libraries, scripts, plugins, runtimes,
kernel modules, firmware, desktop applications, container images, and guests.

### Software placement class

The owner and lifecycle boundary through which a component is made available.
The initial classes are:

| Class | Owner | Typical content | Identity and update boundary |
| --- | --- | --- | --- |
| Release | NeutrinOS release | boot, recovery, host policy, drivers, system services, role-required tools | deployment identity and rollout |
| User baseline | human/user environment | personal interactive CLI and editor helpers | user-managed manifest and realization |
| Project | project/repository | compilers, SDKs, linters, generators, test dependencies | reviewed project input and lock/environment identity |
| Desktop application | user or administrator | interactive GUI applications and runtimes | application ref/artifact, permissions, and application update policy |
| Workload | workload owner | services, jobs, dev services, containerized tools | exact workload artifact plus runtime/configuration contract |
| Guest | guest owner | distinct kernel or operating environment | guest deployment and guest state lifecycle |
| Local exception | administrator or user | temporary or unsupported executable | attributable override with explicit support effect |

These classes are semantic. Flatpak normally realizes a desktop application;
an OCI image normally realizes a workload; neither format determines the owner
or safety of a particular instance.

### Software placement record

The authoritative statement that joins a component to its placement class,
owner, exact source/artifact identity, consumers, execution boundary, granted
host interfaces, configuration and credentials, state owner, update and
rollback policy, backup/recovery, maintenance, evidence, and support effect.

### Execution boundary

The effective isolation and host-integration contract under which a component
runs. It is described by actual users, namespaces, mounts, portals, sockets,
devices, capabilities, system calls, credentials, and kernel boundary—not by a
format label such as sandbox, container, or VM.

### Update domain

A set of components advanced and recovered by one owner under one update
protocol. Different update domains may have compatibility relationships, but
success or rollback in one does not imply success or rollback in another.

## Placement rules

### Rule 1: role promises live in the release

Software belongs in the release placement class when a role needs it for any
of the following:

- boot, storage unlock, networking needed for normal role availability;
- installation, update, health assessment, fallback, maintenance, or recovery;
- enforcement or diagnosis of host security and configuration policy;
- a system service or hardware integration promised by the role;
- an operator command required to repair the host while user software is absent;
- a library, runtime, portal, driver, firmware, or helper required to qualify
  another release-owned capability.

This is not a minimal-size contest. A diagnostic tool needed to recover a router
can be more appropriately release-owned than a large user application used
daily on the workstation.

Release software is resolved from declared package/project inputs, appears in
the deployment SBOM and vulnerability process, and changes only through a new
deployment. The on-host distribution package manager is diagnostic, not an
authorized mutation interface.

### Rule 2: sysext is an artifact shape, not another owner

A system extension may carry release-owned, host-integrated functionality when
separate delivery materially reduces build, storage, or role-variant cost. It
must still be compatibility-bound to the base deployment, authorized,
qualified, included in effective deployment status, and advanced or withdrawn
under an explicit transaction.

Activating a sysext changes the effective `/usr` or `/opt` view. Therefore a
mutable personal extension directory would be hidden host mutation, not a user
software plane. No random personal-software installation through sysext is
proposed.

### Rule 3: the user baseline is personal, non-critical, and reconstructible

The user baseline may contain interactive CLI tools and editor helpers that are
useful across projects but are not required for host operation, recovery,
policy enforcement, or unattended services. It must have:

- a user-owned declarative manifest and, where supported, locked artifact
  identity/checksums;
- an explicit source/backend allowlist and executable trust policy;
- separated configuration, cache, and durable user data;
- reconstruction and removal behavior on a clean account;
- an update/currentness policy independent of OS rollback; and
- diagnosable command resolution.

Dotfiles may configure tools but do not become an unrestricted software supply
chain. mise is the leading small mechanism because it supports per-user and
per-project selection and now has lockfiles, but backend verification coverage,
configuration trust, hooks, shims, and offline reconstruction require literal
evaluation. Nix profiles and Linuxbrew introduce broader independent package
universes and are not leading defaults given project goals and operating
experience; they remain possible explicit exceptions or challengers.

### Rule 4: project tools are owned by the project

A compiler, language runtime, generator, linter, or test service belongs to the
project placement class when its version and behavior are part of building or
testing that repository rather than a promise of the host role.

The reviewed repository pins or content-identifies the environment inputs and
declares whether they run directly as the user, in a rootless container, or in
a guest. Entering a checkout or opening it in an editor must not silently trust
and execute newly encountered environment files, hooks, tasks, or plugins.
Local consent/trust state is user-owned and must distinguish reviewed revisions.

Direct user execution is appropriate for small tools whose host access is
intended. A project container is appropriate for a mutable distribution
userspace or large/conflicting dependency set, but Toolbx-style home and host
integration means it is an ergonomic boundary, not a strong sandbox. A guest is
appropriate when the project requires another kernel/OS or a stronger boundary.

### Rule 5: desktop applications use an application boundary when it fits

Flatpak is the leading desktop-application challenger because it supplies
application/runtime identity, isolation, portals, permissions, and independent
updates without mutating the OS image. It is not accepted as a universal or
inherently safe default.

Each supported desktop application must record:

- exact application identity, origin, branch/ref or artifact, and update owner;
- whether installation is system-wide or per-user and who may change it;
- effective static permissions, portal grants, overrides, and privileged host
  interfaces such as filesystem, D-Bus, devices, sockets, and host execution;
- application-owned configuration, data, cache, secrets, backup, and removal;
- compatibility with the selected desktop/session/portal stack; and
- vulnerability, maintenance, rollback, and offline behavior.

An application needing broad home, device, socket, bus, or host-command access
may still be useful, but the project must not advertise a confinement property
that those grants defeat. A native release package is justified when the role
requires tight host integration or recovery availability. AppImage or an
unmanaged binary is a local exception unless its source, updates, state, and
support are onboarded into another class.

### Rule 6: OCI packages workloads, not trust conclusions

An OCI placement must bind a digest-resolved image and platform, runtime
configuration, workload identity, namespace mapping, mounts, network, devices,
sockets, credentials, writable state, update transaction, health, backup,
restore, and retirement.

Mutable interactive containers are valid development environments, but their
post-creation package history is not a reproducible workload artifact. A
production or role-required service cannot depend on an unrecorded mutable
container. Rootless narrows host privilege; DES-0012 still governs the exact
mapping and attachments.

### Rule 7: use a guest for a real guest requirement

A microVM or VM is justified when the workload needs a distinct kernel, another
OS, kernel-level isolation from an untrusted workload, device mediation, or a
separate failure/recovery domain that simpler placement cannot provide. It is
not the automatic destination for every dependency conflict.

The guest has its own exact artifact, configuration, credentials, state,
update, health, backup, and compromise lifecycle. W-002 will define how those
objects integrate with host networking, storage, and rollout.

### Rule 8: one name must resolve predictably

The effective executable selected by a shell, desktop entry, MIME handler,
systemd unit, D-Bus activation, interpreter directive, plugin loader, or
container/guest launcher must be inspectable. A lower-authority mutable class
must not silently shadow a release-owned command in privileged or unattended
contexts.

Where the same component intentionally exists in multiple classes, status must
show each realization and the selection rule. Unattributed downloads,
curl-to-shell installation, implicit latest tags, unreviewed plugin
auto-installation, and mutable aliases do not establish usable artifact
identity.

### Rule 9: updates and rollback stop at ownership boundaries

Release, user, project, desktop-application, workload, and guest updates are
separate transactions unless an explicit compatibility and coordination record
joins them. Status must expose their current, stale, vulnerable, locally
modified, or unsupported state independently.

Rolling the OS back does not roll back a Flatpak, user tool, project cache,
container volume, or guest disk. Conversely, updating one of those must not
silently change the deployment identity. A compatibility failure may require
pinning, coordinated change, quarantine, or a new deployment, but never a false
whole-machine rollback claim.

### Rule 10: changing placement is a migration

Promoting a user tool into the release, moving a native app to Flatpak, or
converting a mutable container into a workload image changes owner, authority,
state paths, update protocol, and support. The transition inventories state and
credentials, checks collisions and duplicate activations, verifies backup,
qualifies the target boundary, cuts over, verifies behavior, and defines
rollback/removal of the old realization.

## Placement decision procedure

Apply the first matching obligation, then validate the resulting boundary:

1. Required for boot, unattended role service, host policy, health, update, or
   recovery? Place in the release.
2. Host-integrated release capability that demonstrably benefits from separate
   delivery? Evaluate a deployment-bound sysext.
3. Requires another kernel/OS or a stronger kernel boundary? Place in a guest.
4. Long-running service or reproducible isolated workload? Place in an exact
   OCI/workload artifact when its host attachments qualify.
5. Interactive desktop application with an acceptable application permission
   contract? Evaluate Flatpak first.
6. Version belongs to one repository? Place in the project environment, using
   direct tools, a project container, or a guest according to access needs.
7. Personal interactive CLI used across projects? Place in the user baseline.
8. Otherwise classify it as a local exception until deliberately onboarded.

Convenience can choose among mechanisms that satisfy the obligations; it
cannot move a role requirement into an owner that cannot recover or support it.

## Representative examples

| Capability | Leading placement | Reason and caveat |
| --- | --- | --- |
| `systemd`, boot/update/recovery tools | Release | Defines or recovers the host lifecycle |
| Router packet filtering and diagnostics | Release | Unattended role promise and recovery requirement |
| Sway/session plumbing selected by workstation role | Release | Login/session capability under role qualification |
| `ripgrep` used during emergency host repair | Release | Recovery availability outweighs minimal image size |
| Personal prompt/theme/editor helper | User baseline | User preference; not a role dependency |
| Project Node/Python/Rust version | Project | Repository owns the build/test version |
| Mutable distro shell for development | Project container | Useful Toolbx/Distrobox shape; not a security boundary by default |
| Ordinary GUI application | Desktop application | Flatpak leads if origin and permissions are acceptable |
| GUI hardware/debug tool with broad host access | Case-specific | Broad permission may justify release or explicit exception |
| Long-running application service | Workload | Exact image plus declared state, credentials, health, and maps |
| Untrusted kernel experiment | Guest | Requires a distinct kernel and stronger failure boundary |
| Random AppImage/downloaded binary | Local exception | No inferred update, confinement, or support contract |

Examples illustrate the procedure and do not accept the named components.

## Failure and recovery behavior

| Failure | Required behavior |
| --- | --- |
| User/project source unavailable | Host role and recovery continue; cached use follows declared verification policy |
| Desktop app update breaks | Roll back/pin or remove that application without claiming OS rollback |
| Application permission broadens | Block, require attributable acceptance, or mark changed support/security status |
| Project checkout is untrusted | Do not activate hooks/tasks/environment automatically |
| Workload tag moves | Reject unresolved identity; retain prior digest and state compatibility decision |
| User tool shadows host command | Privileged/unattended path remains fixed; status identifies interactive resolution |
| OS rolls back across runtime/portal ABI change | Compatibility gate blocks or coordinates the transition |
| Placement migration fails | Keep one authoritative active realization and a defined return path; diagnose duplicates |
| Application/workload state is hostile | Restore/recovery policy may quarantine or reject it independently of OS health |

## Security and supply-chain consequences

NeutrinOS release qualification covers release-owned components. It does not
silently endorse every user, project, application, workload, or guest artifact.
Those classes still need inventory sufficient to identify known exposure,
source/origin, effective privilege, stale state, and the owner responsible for
action. Unknown or opaque content is a visible coverage gap.

The most dangerous boundary is often an attachment rather than a package:
whole-home access, host command execution, Docker/Podman sockets, D-Bus names,
SSH agents, browser profiles, device nodes, project credentials, and writable
source trees can dominate the nominal container or application sandbox.

## Mechanism posture

| Mechanism | Current posture | Evidence needed |
| --- | --- | --- |
| Native package in OS image | Accepted placement shape, exact selection open | Package closure, role need, qualification, update cost |
| systemd-sysext | Release-owned challenger only | Compatibility/identity, activation transaction, boot/status/rollback |
| Dotfiles | Leading user configuration source | Clean reconstruction, secret separation, failure behavior |
| mise | Leading user/project tool challenger | Locked/offline resolution, backend coverage, trust/hooks/shims, updates |
| Flatpak | Leading desktop-app challenger | Origin/ref, permissions/overrides/portals, state, rollback, advisories |
| Toolbx/Distrobox | Project-dev challenger | Host integration, source ownership, mutable history, cleanup |
| OCI image/runtime | Leading workload artifact family | Digest, maps, attachments, state, health, update/rollback |
| AppImage/local binary | Explicit exception by default | Origin, integrity, updates, state, confinement, support |
| Nix profile/Linuxbrew | Non-leading challengers | Second-universe cost, trust, closure, updates, user experience |
| microVM/VM | Guest boundary challenger | W-002 artifact, networking, storage, identity, lifecycle evidence |

## Evidence plan

EX-0015 should use representative workstation, router, and development
capabilities to compare:

1. release inclusion and recovery availability;
2. user baseline reconstruction with offline and hostile-source cases;
3. project direct-tool versus Toolbx/container environments;
4. Flatpak identity, permission drift, portal, update, rollback, and backup;
5. OCI digest, mutable history, mapping, state, and credential behavior;
6. command/desktop/activation shadowing across classes;
7. OS rollback across newer application/runtime/workload state;
8. promotion/demotion between placement classes; and
9. source, update service, storage, vulnerability, and owner-time cost.

## Open questions

- Which exact personal CLI tools belong in the workstation release for recovery
  rather than in the user baseline?
- Should ordinary workstation Flatpaks be system or per-user installations, and
  who owns remote and permission policy in either model?
- Which Flatpak remotes and verification/currentness policies are supportable?
- Can mise's supported backends provide the locked and offline evidence needed
  for the chosen tools without becoming another fragile supply chain?
- When does a project container's broad home/session integration outweigh its
  convenience?
- Which cross-domain compatibility gates are required for desktop portals,
  GPU drivers, container runtimes, and guest managers?
- Does a separately delivered sysext reduce real fleet cost enough to justify
  another activation/compatibility object?

## Proposed requirements

SYS-121 through SYS-132 capture the accepted policy in this design. PR-0016 is
the accepted adversarial requirements review.

## Review disposition

The placement taxonomy and policy boundaries are accepted. Exact default
mechanisms, application inventories, Flatpak installation scope/remotes,
user/project tool backends, and guest/workload selections remain in review
pending EX-0015 and W-002.
