---
id: RES-0012
title: Unix identity, homed, and rootless-container comparison
status: draft
date: 2026-08-10
source_checked: 2026-08-10
related_designs: [DES-0012]
---

# Unix identity, homed, and rootless-container comparison

## Question

Which current Linux and systemd identity mechanisms can keep user and workload
file ownership predictable across rootless containers, reinstall, backup,
restore, and selected host movement without imposing one unnecessary global UID
namespace?

## Current fleet evidence

Read-only inspection on 2026-08-10 found:

| Source | Human UID/GID | Subordinate UID/GID | Evidence limit |
| --- | --- | --- | --- |
| `desktop-jason` current local account | 60503:60503 | 165536:65536 in both `/etc/subuid` and `/etc/subgid` | Locally observed NSS/passwd and sub-ID files |
| `nixconfig` common declaration for `router` and `misc` | 5001:5001 | No declaration found | Desired checked-in configuration, not a fresh live-host observation |

The workstation account is present in classic `/etc/passwd`. Jason confirmed
that the machine used systemd-homed roughly five years ago and that he converted
away from it because rootless Docker and Podman issues blocked his workflow.
UID 60503 is therefore retained homed-era identity state, not a coincidental
allocation in systemd's documented 60001…60513 homed range. Numeric location in
that range does not make the current account homed-managed.

## Classic fixed accounts

Classic user/group records provide a direct stable name-to-number binding. They
are broadly compatible with NSS, rootless engines, recovery tools, backups, and
filesystems. NeutrinOS can generate or materialize them from identity-bound
fleet configuration rather than mutate them manually on each host.

### Fit

- Predictable ownership for bind-mounted source and raw restores.
- No login-time ownership remap or home activation lifecycle.
- Works with explicit `/etc/subuid` and `/etc/subgid` delegation.
- Straightforward recovery when the normal user manager is unavailable.

### Gaps and risks

- Numeric allocation and collision prevention become project responsibilities.
- Moving a user into another independently administered domain can conflict.
- UID changes require explicit ownership migration.
- Classic account files alone do not express portable identity, credential,
  state, or recovery policy.

### Disposition

Leading initial human-account baseline, combined with an authoritative allocation
record and separate user-state/credential contracts.

## systemd-homed and JSON user records

### Current upstream behavior

Systemd-homed associates a human user record with its home area and can manage
LUKS, directory, Btrfs subvolume, fscrypt, and CIFS storage. User records are
available through the systemd user/group record API and NSS. JSON user records
include a stable UUID and distinguish portable record fields from per-machine
bindings.

`homectl --uid=` describes a preferred UID. If a portable home reaches another
machine where that number is occupied, homed may assign a different local UID.
Current systemd UID documentation also says homed's default idmapped home mounts
map selected ranges: 0…60000, the user's UID, 60514…65534, and systemd's
524288…1879048191 container range. Arbitrary subordinate-owned files outside
those mappings cannot simply be created in the home.

Homed activates the home on login and deactivates it after the final session,
subject to explicit activation and session behavior. User services, lingering
container engines, suspend, remote login, and recovery therefore participate in
the home lifecycle.

### Fit

- Rich systemd-native identity and home metadata with signed records.
- Explicit portable/local record sections and stable non-numeric UUID.
- Idmapped home mounts can avoid broad recursive ownership changes in supported
  cases.
- Integrated storage, authentication, quota, resource, and session semantics.

### Gaps and risks

- Portable collision handling conflicts with a simple stable-numeric invariant.
- Current workstation sub-IDs 165536…231071 lie outside homed's documented
  default mapped ranges.
- Moving the rootless graph root outside home does not by itself prove source-
  tree and created-file behavior.
- Per-user LUKS may duplicate the planned whole-volume custody boundary.
- Session deactivation interacts with lingering user services and container
  engines.
- Prior real-world Docker/Podman failure means paper compatibility is
  insufficient.

### Disposition

Mandatory systemd challenger. Do not select until the literal EX-0014 workflow
passes and is no more operationally fragile than the classic baseline.

Sources:

- <https://systemd.io/USER_RECORD/>
- <https://systemd.io/HOME_DIRECTORY/>
- <https://systemd.io/UIDS-GIDS/>
- <https://www.freedesktop.org/software/systemd/man/latest/homectl.html>
- <https://www.freedesktop.org/software/systemd/man/latest/pam_systemd_home.html>

## systemd service users

`sysusers.d` is the native declarative interface for creating system users and
groups. `DynamicUser=` provides activation-time service identities from
systemd's dynamic range; systemd-managed `StateDirectory=`, `CacheDirectory=`,
`LogsDirectory=`, and related paths can mediate their storage.

### Fit

- `sysusers.d` makes fixed service identity part of exact image configuration.
- Dynamic users avoid permanent allocations for services without externally
  meaningful raw ownership.
- Manager-owned directories align lifecycle, sandbox, and identity setup.

### Gaps and risks

- A raw backup or recovery tool sees numbers, not the activation that allocated
  them.
- Fixed package IDs can differ between package universes.
- External shares, bind mounts, protocols, or manual paths can escape systemd's
  managed-directory behavior.
- A fixed name is not proof that two package baselines assign the same number.

### Disposition

Use native systemd primitives. Prefer dynamic service identity only when all
durable ownership remains safely mediated; otherwise register a fixed ID in the
allocation record.

Sources:

- <https://www.freedesktop.org/software/systemd/man/latest/sysusers.d.html>
- <https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html>
- <https://systemd.io/UIDS-GIDS/>

## Subordinate UID/GID delegation

`/etc/subuid` and `/etc/subgid` authorize users to construct mappings through
`newuidmap` and `newgidmap`. The shadow-utils interface permits multiple ranges
per user and can use files or an NSS subid provider.

Rootless Docker currently documents at least 65,536 subordinate UIDs/GIDs as a
prerequisite. Rootless Podman also requires subordinate ranges for multi-ID
operation and normally derives its rootless user namespace from them.

### Fit

- Widely supported across current rootless engines.
- Matching 65,536 ranges provide full 16-bit container identities.
- Explicit files are easy to inspect and reconstruct for the initial fleet.

### Gaps and risks

- Allocation files do not inherently coordinate with every other allocator.
- On-disk subordinate ownership becomes dangerous after range reuse.
- Multiple ranges and engine-specific consumption complicate portability.
- Matching ranges on different hosts help raw movement but are unnecessary for
  many logical exports.

### Disposition

Leading initial delegation interface. Generate it from one allocation record;
never allocate on the target opportunistically.

Sources:

- <https://man7.org/linux/man-pages/man5/subuid.5.html>
- <https://man7.org/linux/man-pages/man5/subgid.5.html>
- <https://docs.docker.com/engine/security/rootless/>
- <https://docs.podman.io/en/latest/markdown/podman.1.html>

## Podman namespace modes

Podman exposes `keep-id`, `auto`, `nomap`, and explicit mapping controls.
`keep-id` maps the invoking user into the namespace, which is attractive for
host source trees. Current documentation warns that it uses all of the user's
subuids/subgids, and `auto` cannot be used while `keep-id` or `nomap`
containers exist. `auto` instead allocates unique slices from a subordinate
range assigned to the special `containers` name.

Podman volume syntax also supports idmapped mounts with an explicit map. That
can change the view of a source without recursive ownership changes, subject to
the backing filesystem and kernel/runtime implementation.

### Fit

- Directly covers the development source-bind use case.
- Explicit maps and idmapped volumes can express more exact ownership.
- Rootless operation avoids a privileged daemon for ordinary user workloads.

### Gaps and risks

- Namespace modes have concurrency and allocation interactions.
- Rootless store defaults under `$HOME`, where homed/network filesystem
  behavior matters.
- Supplementary groups and access granted only through host group membership
  can surprise rootless binds.
- Rootless does not make attached devices, sockets, secrets, or source trees
  unprivileged relative to the user.

### Disposition

Primary semantic fixture because it matches the stated workflow, not yet the
accepted OCI runtime. Mapping must be per workload.

Sources:

- <https://docs.podman.io/en/latest/markdown/options/userns.container.html>
- <https://docs.podman.io/en/latest/markdown/options/volume.html>
- <https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html>

## Docker rootless

Docker rootless runs both daemon and containers in a user namespace and uses
`newuidmap`/`newgidmap` plus subordinate ranges. It provides useful compatibility
evidence because Docker was part of the original blocker and remains present on
the current workstation.

### Fit

- Real compatibility requirement for existing development workflows.
- Independent implementation tests whether policy is Podman-specific.

### Gaps and risks

- Long-running user daemon and storage have their own session/linger lifecycle.
- Namespace behavior and bind semantics differ from Podman controls.
- Supporting two engines' raw stores or exact behavior may be unnecessary.

### Disposition

Mandatory compatibility fixture for W-001. Runtime selection belongs to W-003
or role design.

Source:

- <https://docs.docker.com/engine/security/rootless/>

## Idmapped mounts

The Linux VFS idmapped-mount API attaches a user-namespace mapping to a mount.
The same underlying inodes can appear with different ownership at different
mounts without changing their on-disk UID/GID, and the mapping lifetime follows
the mount.

### Fit

- Avoids recursive `chown` for container and portable-home views.
- Makes backing ownership and consumer-visible ownership separable.
- Can allow several namespaces to access the same tree through different views.

### Gaps and risks

- Requires literal filesystem, kernel, mount, overlay, runtime, and backup-tool
  support.
- A mapped view can hide surprising backing ownership from operators.
- It does not allocate identities, authenticate users, or migrate backups.
- Stacked namespace/filesystem/mount mappings are easy to misdiagnose.

### Disposition

Preferred mapping primitive where the exact path is qualified, with explicit
backing and visible maps in status.

Source:

- <https://docs.kernel.org/filesystems/idmappings.html>

## systemd container ranges and nspawn

Systemd documents distinct special UID ranges for homed, dynamic service users,
nspawn container allocations, and foreign OS images. `systemd-nspawn -U` can
pick a 65,536-ID range and makes running container users visible through
machined/NSS.

These ranges are useful allocation prior art, but they do not automatically
coordinate with shadow-utils sub-ID files or OCI engines. Reserving a range in
`/etc/subuid` does not prove every systemd allocator will see it as an NSS user
collision.

### Disposition

Respect systemd special ranges and test coexistence. Do not force development
OCI containers into nspawn's allocator merely to stay systemd-native.

Sources:

- <https://systemd.io/UIDS-GIDS/>
- <https://www.freedesktop.org/software/systemd/man/latest/systemd-nspawn.html>

## Comparative conclusion

The smallest credible initial combination is:

```text
fleet allocation record
    -> classic fixed human UID/GID
    -> explicit matching subordinate UID/GID range
    -> per-workload rootless namespace contract
    -> idmapped bind/volume where qualified
    -> fixed sysusers or DynamicUser per service-state need
```

Systemd-homed must be tested against that baseline rather than dismissed from
historical experience or accepted from current feature lists. Exact UID/sub-ID
numbers and container runtime remain design outputs, not research conclusions.
