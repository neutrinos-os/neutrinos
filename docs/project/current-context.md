---
status: informative
last_updated: 2026-08-16
source_snapshot_revision: 7c60742
current_gate: G1
target_gate: G2
active_plan: PLN-0003 (accepted 2026-08-15; PLN-0000, PLN-0001, PLN-0002 complete)
---

# Current project context

> Maintained, non-normative cold-context artifact. For a read-only status task,
> rely on this file and open no path it cites; exception, one authority the user
> names. Before an edit or a high-risk claim, verify the governing source, which
> wins.
>
> A pointer index, never the sole home of a decision, ruling, measurement or next
> action. **Keep it under 1,100 words**, enforced by `T0-DOC-004`; a measurement
> or a narrative belongs in the owning record.

## Position

- **G1 approved** 2026-08-10 (PR-0029). A readiness gate, not a capability gate:
  it authorizes disposable VM and lab work only. Seven review challenges carried
  open.
- **PLN-0000, PLN-0001 and PLN-0002 are complete and accepted**, the last on
  2026-08-15 with two qualifications in its exit-criteria assessment.
- **PLN-0003 is accepted** 2026-08-15 (PR-0031): the `/usr` read-workload
  comparison, the one measurement that could reverse the C-007 recommendation
  (`docs/plans/0003-usr-read-workload-comparison.md`).
- **SYS-018, SYS-041, SYS-059 and SYS-049 are accepted at `Partial`**
  (2026-08-11). SYS-049's substitution clause holds for the image and Verity tree
  and **is falsified for the signature**, carried by two deferred checks.

## Next action

**The owner directed a build sequence on 2026-08-16**, ahead of PLN-0003, which
is not retired: (1) the workstation capability declaration — landed, 21 entries,
`T2-ROLE-001`; (2) machine-state and home volumes — landed as the `state`
composition variant, `/var` and `/home` measured mounted from Btrfs partitions;
(3) boot that composition to a graphical session in a disposable VM; (4) measure
C-009 on the container and microVM workload the declaration names. **Step 3 is
next.**

## Standing findings

One line each; the owning record is the authority.

- **This slice's mechanisms fail open silently — eight instances**, so a
  successful boot says nothing about the artifact. Worst: a valid signature over
  a root hash the image does not carry boots to `running` with zero failed units
  ([substitution](artifact-substitution-records.md)).
- `systemd.image_policy=usr=signed` is a structural predicate, not an enforcement
  mechanism ([declaration](artifact-parameter-declaration.md)).
- Upstream's `/usr` signature enforcement point is the TPM unseal, not the mount
  (`S-005`, [backlog](decision-backlog.md)). Confext enforcement is closed
  (`T4-CONFEXT-001`).
- Build determinism is closed; **any determinism claim must state whether the
  confext was rebuilt** ([artifact set](usr-artifact-set.md)).
- **Any blast-radius claim must state whether readahead was disabled**; size
  claims use bytes in use — partition size overstates EROFS by 56%
  ([corruption](artifact-corruption-records.md),
  [measurements](artifact-format-measurements.md)).
- A declared parameter can be wrong rather than merely missing; the 2026-08-14
  audit read the built artifacts and took three corrections.
- **`systemd-gpt-auto-generator` mounts nothing under `root=tmpfs`** (2026-08-16):
  it finds partitions through the device behind `/`. Explicit `.mount` units in
  `/usr` work and are what ships; the derived `/var` UUID is correct but reads
  nothing until a writable root partition exists.

## Open and the owner's

- **Two corrections to accepted records**: the `fsck.erofs --extract` finding
  ([disposition](artifact-recovery-disposition.md)), and PLN-0002-13's threat 1
  naming item 9 as owning the workload comparison.
- **The ruled command line is not the implemented one** (2026-08-12, against
  `usr=signed` with `usrhash=` retained). Settling it rebuilds the six artifacts
  and voids what was measured against them
  ([declaration](artifact-parameter-declaration.md)).
- Whether G1's approval should be revisited against the corrected trace.
- **C-007 is open.** PLN-0002-13 recommends EROFS, conditional on the updater not
  being whole-image-only, on image size at 1.65x and 111.4 MiB per slot. **That
  acceptance does not accept EROFS** — an ADR does
  ([recommendation](artifact-format-recommendation.md)).
- **C-009 is open** and now has both a workload — the container and microVM
  entries of the capability declaration — and volumes to measure on.
- **A writable root partition** would make partition discovery native, and
  reverses the `root=tmpfs` ruling of 2026-08-11.

## Mutation boundary

Allowed: PLN-0003's named tasks on disposable VM disks, firmware variables,
virtual TPM state and test networks; **non-member artifacts**, marked at creation
and destroyed at task end; synthetic signing and credential fixtures; build
caches in declared locations; documentation and validation work.

**The six PLN-0002-06 artifacts are read-only inputs**, every boot `snapshot=on`.
Rebuilding or modifying a member would void PLN-0002's tally; the `state` variant
is a separate artifact and touches none of them.

Also allowed, owner authorization 2026-08-16, outside PLN-0003's scope:
**corpus-integrity checks under `tools/validation/`**; **role declaration and VM
composition work under `src/roles/` and `src/slice/`** for the build sequence
above, disposable VMs only. `AGENTS.md`'s pre-implementation clause is suspended
for that sequence by the sole acceptance authority.

Prohibited: implementation outside those two scopes; G2 qualification claims;
mutation of `desktop-jason`, `router`, `misc` or another physical host;
production credentials, keys, enrollment state, recovery material or machine
authority; treating a candidate fixture, probe or agent summary as an accepted
decision; autonomous push, merge, release or publication.

The synthetic signing material expires **2026-09-11**.

## Accepted decisions bounding current work

Pointers, not authority. **[ADR index](../adrs/README.md)** is the list; ADR-0004
through ADR-0009, **accepted 2026-08-16**, record the DES-0006 and DES-0005
rulings, so storage and configuration are bound there rather than in a design
review. Also: naming; Apache-2.0 and public (`scope.md`, `P-007`); system policy
(`docs/requirements/system.md`); test taxonomy; validation contract; PLN-0000's
readiness model.

## Fixtures, not architecture

mkosi composition (challenger: bootc); a declared Fedora snapshot (challenger:
Arch); EROFS and ext4; Btrfs on `/var` and `/home`; `systemd-sysinstall`; a
distribution kernel; a disposable VM as harness; every component named in a role
capability declaration. **PR-0029 C-005 is the standing risk**: repeated success
is how a candidate becomes a decision without an ADR. PR-0030 C-006 is the same
in PLN-0002's confext carve. W-002 and W-004 are open.

## Validation

`check:fast` runs 12 and `check:complete` 21, 2 deferred of 23 registered;
`mise run check:list` is authoritative. `T2-ROLE-001` and `T2-STATE-001` each
reject eight constructed violations, verified detected; `T4-STATE-001` asserts
both state volumes are block-device-backed, verified to fail without them.
`mise.toml` sets `sandbox.deny_env`, so **no artifact-dependent check is
reachable through `mise run`** — all eight block. Editing `tools/validation/`
requires `complete`. Details: [validation](validation.md). **CI is red on `main` and
stays red** (`P-008`); not tracked or reported. `P-009` is open and blocks
nothing.

**`T0-DOC-003` and `T0-DOC-004` are `P-010`'s first step** (2026-08-16),
RES-0016's recommended validator and not an answer to the question, which stays
open. They bind the ADR and comparison indexes to the files they describe, hold
this file to its declared word bound, and stop a routing document linking to
anything frozen. Six failure modes verified detected.

## Context path

Root `AGENTS.md`'s Read section governs it and is not restated here. Questions:
`decision-backlog.md`; risks: `risk-register.md`; history:
`docs/background/design-session-summary.md`.

Update this file when the gate, the active plan, a relevant accepted decision or
leading fixture, the mutation boundary, the canonical validation commands, or the
one next action changes. Assume a dirty worktree; preserve unrelated work.
