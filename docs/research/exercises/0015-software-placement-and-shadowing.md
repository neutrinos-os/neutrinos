---
id: EX-0015
title: Representative software placement, shadowing, and rollback exercise
status: proposed
last_updated: 2026-08-10
supports: [DES-0013, W-003]
---

# Representative software placement, shadowing, and rollback exercise

## Purpose

Determine whether the proposed software placement classes can keep a useful
workstation and router understandable, recoverable, and supportable without
turning the immutable root into a collection of hidden mutable package planes.

This exercise may install only synthetic or disposable test artifacts in the
reference VM/lab. It does not authorize production host changes.

## Required subjects

Choose at least one representative of each applicable class:

| Class | Workstation fixture | Router fixture |
| --- | --- | --- |
| Release | boot/update/recovery diagnostic and session component | network recovery diagnostic and role service |
| User baseline | personal CLI/editor helper | optional administrator CLI only |
| Project | language runtime, compiler/linter, and dev service | router-config validation tool |
| Desktop application | portal-using ordinary GUI app and one broad-access challenger | not applicable |
| Workload | rootless service with bind and named state | network service with explicit state |
| Guest | kernel/OS-sensitive development fixture | optional isolated network-service fixture |
| Local exception | synthetic AppImage/direct binary | synthetic diagnostic download |

## Phase 1: inventory and classification

For each fixture record:

- semantic owner and placement class;
- why the adjacent classes are weaker fits;
- exact source/artifact and verification coverage;
- command/desktop/service activation names;
- execution user, namespaces, permissions, mounts, portals, sockets, devices,
  credentials, network, and kernel boundary;
- configuration, durable state, cache, backup, and removal paths;
- update, rollback, offline, vulnerability, end-of-life, and support owner; and
- expected behavior when its source/update service is absent.

Fail if the class is chosen only from the package format or preferred tool.

## Phase 2: role-critical absence test

Disable user login, user tool sources, project sources, desktop application
remotes, workload registry, and guest publication services.

Verify that:

1. the router provides and diagnoses its promised network role;
2. workstation boot, login recovery, update/fallback, storage, and host
   diagnosis remain possible;
3. no system service resolves commands from a user/project path; and
4. status accurately reports unavailable non-release update domains.

Any missing role/recovery capability is a placement error or an explicit
offline-cache requirement, not an excuse to weaken the test.

## Phase 3: user baseline reconstruction

On a clean disposable account:

1. apply the candidate dotfiles/user manifest;
2. reconstruct the selected tools in locked and offline-cache modes;
3. record exact installed assets and backend verification coverage;
4. interrupt download, install, update, and removal;
5. inject wrong checksum, moved version, unavailable backend, and hostile
   archive/path traversal cases;
6. restore user data without caches and reconstruct again; and
7. prove no host service or recovery command depends on the result.

For mise, test global, project, parent, environment-specific, and local config,
lockfile presence/absence, locked mode, hooks/tasks, shims, and trust decisions.

## Phase 4: project trust and environment comparison

Use one repository revision with reviewed environment inputs and one hostile or
newly changed revision.

Compare direct user tools, mise-managed tools, and a Toolbx/rootless project
container for:

- input identity and reconstruction;
- activation without automatic execution;
- home, source, SSH/GPG agent, credential, socket, device, and network access;
- created-file ownership and cleanup;
- mutable package history versus rebuilt artifact;
- editor/debugger integration;
- concurrent projects requiring conflicting versions; and
- backup size and restoration.

Verify that entering a directory, shell prompt rendering, or editor discovery
does not silently approve an unseen revision's executable configuration.

## Phase 5: desktop application boundary

For the ordinary and broad-access fixtures:

1. install using each candidate system/per-user scope;
2. retain exact remote, ref/commit, runtime, signature/verification, and owner;
3. inventory static permissions, overrides, portal grants, D-Bus, filesystem,
   devices, sockets, network, and host-command access;
4. exercise file chooser, screen/audio, notifications, secrets, and session
   integration as applicable;
5. broaden and reduce a permission and observe approval/status behavior;
6. update, fail update, pin/roll back, remove, reinstall, and restore app data;
7. roll the OS backward across a portal/runtime/driver compatibility change;
8. operate with the remote unavailable; and
9. confirm that release qualification does not imply application qualification.

Compare Flatpak with a native release package and synthetic AppImage/local
binary only where the same capability can be represented honestly.

## Phase 6: workload identity and mutability

Run one workload from an exact OCI digest, then mutate an interactive container
with an internal package manager.

Record and test:

- image/index/platform identity and tag movement;
- runtime configuration and DES-0012 UID/sub-ID mappings;
- binds, volumes, credentials, sockets, devices, and network;
- writable-layer versus application-state ownership;
- health, update, rollback, interrupted activation, and state compatibility;
- export, raw backup, logical backup, restore, and removal; and
- whether native status distinguishes the rebuilt image from mutable history.

Fail any reproducibility claim that depends on unrecorded post-creation changes.

## Phase 7: resolution and shadowing

Create benign fixtures with the same command, desktop/MIME handler, D-Bus name,
interpreter, plugin, and service activation identity in multiple classes.

Verify resolution from:

- interactive shell, `sudo`, administrator shell, system service, user service,
  timer, recovery environment, editor, desktop launcher, and container;
- clean and restored user accounts;
- before and after OS rollback and user/application update; and
- with one realization missing, corrupt, or locally modified.

Privileged and unattended consumers must not inherit mutable interactive
precedence. Status must identify every realization and the effective selection.

## Phase 8: update-domain compatibility

Construct old/new pairs for OS, user tool, desktop runtime/application, OCI
runtime/workload, and guest manager/guest. Exercise supported and incompatible
combinations, including:

- OS rollback while non-release state remains newer;
- application rollback while its data remains newer;
- runtime rollback with newer workload metadata/store;
- offline update in one domain while another is stale; and
- vulnerability withdrawal in one domain without erasing other histories.

Record whether the correct outcome is continue, pin, coordinated update,
quarantine, logical migration, or refusal.

## Phase 9: placement migration

Perform at least two transitions, such as:

- user CLI to release-owned recovery tool;
- native GUI package to Flatpak;
- mutable dev container to exact project/workload artifact; or
- local binary to a reviewed project input.

Inventory state and credentials, back up, detect duplicate activation, stage
the target, interrupt each phase, verify one authoritative realization, and
remove or tombstone the old placement. Reversal must not lose user/workload
state or restore ambiguous command resolution.

## Phase 10: operating-cost comparison

Measure:

- package universes, remotes/registries, trust roots, and credentials;
- background services and privileged helpers;
- disk use, shared runtimes, caches, images, guests, and retained rollbacks;
- update/notification mechanisms and failure modes;
- vulnerability/advisory coverage gaps;
- backup volume and restore time; and
- setup, routine update, diagnosis, migration, and recovery owner time.

## Acceptance evidence

EX-0015 completes only when it produces:

1. a complete representative placement inventory;
2. role-critical absence and recovery results;
3. selected user/project input identities and trust behavior;
4. a desktop application origin/permission/update contract;
5. exact workload and mutable-development distinctions;
6. a resolution/shadowing matrix;
7. cross-domain compatibility and rollback results;
8. interruption-safe migration evidence;
9. explicit rejected mechanisms or exceptions; and
10. measured operating cost.

Only then should W-003 produce mechanism ADRs and concrete role software lists.
