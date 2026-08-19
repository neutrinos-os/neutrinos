---
status: informative
last_updated: 2026-08-18
source_snapshot_revision: 423a23c
---

# Current project context

> Non-normative pointer index. Never the sole home of a result.
> **Keep it under 1,100 words**, enforced by `T0-DOC-004`.

## Runs today

```sh
python3 src/slice/slice.py build --arm erofs --variant session --role workstation
```

- `--arm`: `/usr` format, `erofs` or `ext4` → `composition/mkosi.repart.<arm>/`.
- Output: `out-<arm>-<variant>`. Interactive boot: `slice.py compose … vm`.
- Every variant: signed UKI, verity-sealed `/usr`, `/etc` from a factory tree.
- Packages and asserts come from the workstation
  [capability declaration](../../src/roles/workstation/capabilities.toml),
  21 entries.

Variants that matter:

- `state` — `/var` and `/home` mounted from their partitions.
- `session` — greetd, sway, `graphical-session.target` active, Wayland socket,
  `foot` executing (`T4-SESSION-001`).
- `workload` — rootless container with a writable bind mount; nested VM to PID 1
  under forced KVM from a reflink copy (`T4-WORKLOAD-001`).

## Missing to ship

Verified in the composition, not inferred:

- `mkosi.repart/` = ESP + `usr` + `usr-verity` + `usr-verity-sig`. **One slot.**
- `sysupdate`: nowhere but a list of mkosi verbs.
- No boot counting, no bless, no installer.
- Every boot ever: `snapshot=on`. **Nothing has persisted, updated or rolled
  back.**

In dependency order:

0. **Boot the same disk twice.** Drop `snapshot=on`. Nearly free; tests the one
   property never tested.
1. **Writable root partition.** One repart file. Makes partition discovery
   native, reverses the `root=tmpfs` ruling of 2026-08-11. Everything below
   rides on it.
2. **Second `/usr` slot + `sysupdate.d`.** Two repart definitions, one transfer
   config. The whole content of "update"; CH-002 and CH-003 wait on it.
3. **Boot counting + bless.** `systemd-boot` tries counters, a health check that
   blesses, fallback when it does not. CH-004 has no evidence.
4. **Install to a disk.** repart against a real block device on first boot.
   Spare disk or new machine; `desktop-jason` untouched until 0–3 work.

0–3 are VM work. A deleted build directory is the undo.

## Traps already paid for

Owning record is the authority.

- **Nine silent fail-opens** — a successful boot says nothing about the
  artifact. Worst: valid signature over a root hash the image does not carry,
  boots to `running`, zero failed units
  ([substitution](artifact-substitution-records.md)). Newest: `greetd` active,
  no login possible.
- `systemd.image_policy=usr=signed` — structural predicate, not enforcement
  ([declaration](artifact-parameter-declaration.md)). Upstream's `/usr`
  enforcement point is the TPM unseal, not the mount.
- **`systemd-gpt-auto-generator` mounts nothing under `root=tmpfs`** — finds
  partitions through the device behind `/`. Explicit `.mount` units in `/usr`
  ship instead. Closed by step 1.
- **Blast-radius claims: state whether readahead was disabled.** Size claims use
  bytes in use — partition size overstates EROFS by 56%
  ([corruption](artifact-corruption-records.md),
  [measurements](artifact-format-measurements.md)).
- **Ruled command line ≠ implemented one** (2026-08-12). Settling it rebuilds
  artifacts and voids measurements taken against them. A declared parameter can
  be wrong, not just missing.
- **`/etc` model works; three PAM diagnoses were wrong.** `/etc/authselect` is
  `L`, not `C` — read-only inside verity. `nullok` open.
- **Btrfs, EROFS, mkosi, the Fedora snapshot: surviving fixtures, not
  decisions.** Write the ADR or replace them.

## Checks

- `mise run check:fast` after edits. `check:complete` when editing
  `tools/validation/`.
- `mise run check:list` — authoritative for what is registered and in which
  profile.
- Artifact-dependent checks: `check:complete -- --artifact KIND=DIR`, absolute
  paths. `sandbox.deny_env` blocks the environment route.
- No single artifact satisfies every check declaring `slice`; `complete` cannot
  pass in full. Details: [validation](validation.md).
- **CI red on `main`, stays red** (`P-008`). Not tracked, not reported.
- `T4-SESSION-001` refuses `graphics` (no GPU in the VM) and `login` (needs
  driven authentication).

## Safety

- VMs and spare disks only. No mutation of `desktop-jason`, `router`, `misc`.
- Synthetic signing/credential fixtures only. **Expire 2026-09-11.**
- No push, merge or publication without a request.
- Six PLN-0002-06 artifacts: read-only inputs. Rebuilding one voids its
  measurements. `state`/`session`/`workload` are separate and touch none.

## Open, blocking nothing

- **C-007** — EROFS recommended, 1.65x, 111.4 MiB per slot, conditional on the
  updater not being whole-image-only. An ADR settles it
  ([recommendation](artifact-format-recommendation.md)).
- **C-009** — state filesystem. Workload axis a draw, accepted 2026-08-18
  ([A-007](assumptions.md)); Btrfs incumbent. Failure, repair, quota, encryption,
  operational unmeasured; volumes are plaintext, so encryption has nothing to
  compare.
- **C-010** PAM policy. **C-011** unsupplied packages
  ([backlog](decision-backlog.md)).

## This file

Update with the source when it stops being true. Questions:
[decision backlog](decision-backlog.md). Risks:
[risk register](risk-register.md). Assume a dirty worktree.
