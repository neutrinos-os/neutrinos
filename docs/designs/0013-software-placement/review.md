---
design: DES-0013
reviewer: Codex adversarial pass
date: 2026-08-10
status: open
---

# Adversarial review: software placement and execution boundaries

## Summary

The proposed classes are useful only if they prevent two common failures:
moving an unqualified role dependency out of the image to preserve a cosmetic
claim of minimalism, and calling independently mutable user/application state
safe merely because the root is immutable.

The design should advance at the policy level. Mechanism selection should wait
for a literal mixed-environment exercise.

## Strongest challenges

### This creates bureaucracy for ordinary software installation

It can. A placement record should be generated from native inventories and use
defaults for low-consequence personal tools. The full contract matters when
software is role-required, privileged, persistent, remotely exposed, or
claimed as supported. The alternative is not zero process; it is hidden update
and recovery policy discovered during failure.

### Everything could just go in the image

That maximizes literal-system qualification but couples personal and project
iteration to OS rollout, expands variants and rebuild pressure, and tempts
users to bypass the image for urgent work. Release placement is correct for
role promises, not every executable a person might run.

### Everything outside the image could just use containers

Containers do not define origin, update, state, privilege, source-tree access,
desktop integration, or recovery. Toolbx intentionally exposes much of the
host for development; rootless OCI still shares the host kernel and may expose
powerful mounts and sockets. A single format would conceal distinct owners.

### Flatpak should simply be the desktop default

Flatpak is the leading challenger, but effective permissions range from narrow
portal access to broad home/device/bus/host-command access. Application origin,
permission drift, updates, state, backup, and portal compatibility still need
qualification. Some host-integrated applications will not fit honestly.

### Per-user installs conflict with centrally understood machines

They do if status cannot inventory them. Central awareness does not require
central ownership: user-owned applications may update independently while the
host reports origin, identity, privilege, state, currentness, and support. The
system must not silently convert awareness into fleet authorization.

### mise repeats the Nix problem

It could repeat part of it if used as an unbounded configuration/task language
or universal package manager. The proposed scope is narrower: interactive user
and project tools, explicit trust, locked inputs where supported, and no host
policy or service ownership. EX-0015 must reject it if backend variability,
hooks, or reconstruction costs recreate the operational pain.

### A software bill of materials should cover the whole machine

One joined inventory is useful; one undifferentiated assurance claim is not.
The release SBOM can strongly bind built artifacts. User tools, Flatpaks,
containers, mutable project environments, and guests have different identities
and evidence. Status should join them while retaining coverage and authority.

### Sysext can provide convenient package layering

That is precisely the risk. Because it changes the effective host hierarchy,
its content must behave like release-owned host software. Separate delivery
does not turn it into a safe user package plane.

### Strong isolation always means a VM

A guest may provide the required kernel boundary, but it adds another OS,
update, storage, networking, observability, and recovery domain. Use it when the
threat or compatibility requirement pays that cost, not as ritual isolation.

## Required clarifications retained in the design

- Placement class is semantic, not synonymous with a packaging technology.
- Host role/recovery requirements cannot depend on user or project state.
- Execution boundary means effective access, including attachments.
- Mutable dev containers are not reproducible workload artifacts.
- Project configuration is executable input and requires revision-aware trust.
- Command and activation precedence is part of the contract.
- Updates, rollback, and support status stop at owner boundaries.
- Placement changes are explicit migrations.

## Evidence required before mechanism selection

1. One real workstation inventory classified by owner and placement.
2. One router recovery run with user/application sources absent.
3. mise reconstruction and hostile/untrusted project configuration tests.
4. Flatpak permission, override, portal, update, rollback, and backup tests.
5. Toolbx/project-container host exposure and source ownership comparison.
6. OCI mutable-versus-digest workload comparison.
7. PATH, desktop, D-Bus, interpreter, plugin, and unit shadowing cases.
8. Cross-domain OS rollback and compatibility cases.
9. At least one failed/interrupted placement migration.
10. Measured services, stores, credentials, storage, and owner time.

## Recommendation

The owner accepted the mechanism-neutral placement requirements. Keep Flatpak,
mise, Toolbx/Distrobox, sysext, OCI runtime details, installation scope,
remotes, and the exact user/application inventory open through EX-0015.
