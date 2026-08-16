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
> wins. A pointer index, never the sole home of a decision, ruling, measurement
> or next action. **Keep it under 1,100 words**, enforced by `T0-DOC-004`.

## Position

- **G1 approved** 2026-08-10 (PR-0029). A readiness gate, not a capability gate:
  disposable VM and lab work only. Seven review challenges carried open.
- **PLN-0000, PLN-0001 and PLN-0002 are complete and accepted**, the last
  2026-08-15 with two qualifications in its exit-criteria assessment.
- **PLN-0003 is accepted** 2026-08-15 (PR-0031): the `/usr` read-workload
  comparison, the one measurement that could reverse C-007
  (`docs/plans/0003-usr-read-workload-comparison.md`).
- **SYS-018, SYS-041, SYS-059 and SYS-049 are accepted at `Partial`**
  (2026-08-11). SYS-049's substitution clause holds for the image and Verity tree
  and **is falsified for the signature**, carried by two deferred checks.

## Next action

**The owner directed a build sequence on 2026-08-16**, ahead of PLN-0003, which
is not retired. Landed: (1) the workstation capability declaration, 21 entries,
`T2-ROLE-001`, which now selects packages and names what checks assert;
(2) machine-state and home volumes, the `state` variant, `/var` and `/home`
measured mounted from Btrfs partitions; (3) a graphical session, the `session`
variant — greetd, sway and `graphical-session.target` active, Wayland socket
present, `foot` executing (`T4-SESSION-001`). **Next: (4) measure C-009 on the
container and microVM workload the declaration names.**

## Standing findings

One line each; the owning record is the authority.

- **Mechanisms fail open silently — nine instances**, so a successful boot says
  nothing about the artifact. Worst: a valid signature over a root hash the
  image does not carry boots to `running`, zero failed units
  ([substitution](artifact-substitution-records.md)). Newest: `greetd` active
  while no login could work.
- `systemd.image_policy=usr=signed` is a structural predicate, not an enforcement
  mechanism ([declaration](artifact-parameter-declaration.md)).
- Upstream's `/usr` signature enforcement point is the TPM unseal, not the mount
  (`S-005`, [backlog](decision-backlog.md)). Confext enforcement is closed
  (`T4-CONFEXT-001`). Determinism is closed; **state whether the confext was
  rebuilt** ([artifact set](usr-artifact-set.md)).
- **Blast-radius claims must state whether readahead was disabled**; size claims
  use bytes in use — partition size overstates EROFS by 56%
  ([corruption](artifact-corruption-records.md),
  [measurements](artifact-format-measurements.md)).
- A declared parameter can be wrong rather than merely missing (2026-08-14
  audit, three corrections).
- **`systemd-gpt-auto-generator` mounts nothing under `root=tmpfs`** (2026-08-16):
  it finds partitions through the device behind `/`. Explicit `.mount` units in
  `/usr` work and are what ships; the derived `/var` UUID is correct but reads
  nothing until a writable root partition exists.
- **An `/etc`-less image cannot authenticate anyone** (2026-08-16, `C-010`).
  Fedora keeps the PAM stack in `/etc/pam.d`, which ADR-0004 empties. A
  **fixture-grade** stack now ships in `/usr/lib/pam.d`; not reviewed policy,
  not for a physical host.

## Open and the owner's

- **Two corrections to accepted records**: the `fsck.erofs --extract` finding
  ([disposition](artifact-recovery-disposition.md)), and PLN-0002-13's threat 1
  naming item 9 as owning the comparison.
- **The ruled command line is not the implemented one** (2026-08-12). Settling
  it rebuilds the six artifacts and voids what was measured against them
  ([declaration](artifact-parameter-declaration.md)).
- Whether G1's approval should be revisited against the corrected trace.
- **C-007 is open.** PLN-0002-13 recommends EROFS, conditional on the updater
  not being whole-image-only, at 1.65x and 111.4 MiB per slot. **That acceptance
  does not accept EROFS** — an ADR does
  ([recommendation](artifact-format-recommendation.md)).
- **C-009 is open**, with a workload (the declaration's container and microVM
  entries) and volumes to measure on.
- **A writable root partition** would make partition discovery native, and
  reverses the `root=tmpfs` ruling of 2026-08-11.
- **`C-010`** PAM policy: `/usr` release content or signed confext.
  **`C-011`** role packages the declared closure cannot supply — `uwsm`,
  `polkit-gnome`, an `oo7` daemon. Both opened 2026-08-16
  ([backlog](decision-backlog.md)).

## Mutation boundary

Allowed: PLN-0003's named tasks on disposable VM disks, firmware variables,
virtual TPM state and test networks; **non-member artifacts**, destroyed at task
end; synthetic signing and credential fixtures; documentation and validation
work.

**The six PLN-0002-06 artifacts are read-only inputs**, every boot `snapshot=on`.
Rebuilding a member would void PLN-0002's tally; the `state` and `session`
variants are separate artifacts and touch none of them.

Also allowed, owner authorization 2026-08-16, outside PLN-0003's scope:
**corpus-integrity checks under `tools/validation/`**; **role declaration and VM
composition work under `src/roles/` and `src/slice/`** for the build sequence
above, disposable VMs only. `AGENTS.md`'s pre-implementation clause is suspended
for that sequence by the sole acceptance authority.

Prohibited: implementation outside those two scopes; G2 qualification claims;
mutation of `desktop-jason`, `router`, `misc` or another physical host;
production credentials, keys, enrollment or recovery material; treating a
fixture, probe or agent summary as an accepted decision; autonomous push, merge,
release or publication.

The synthetic signing material expires **2026-09-11**.

## Accepted decisions bounding current work

Pointers, not authority. **[ADR index](../adrs/README.md)** is the list;
ADR-0004..0009 (2026-08-16) record the DES-0006 and DES-0005 rulings. Also:
naming; Apache-2.0 and public (`scope.md`, `P-007`); system policy
(`docs/requirements/system.md`); test taxonomy; validation contract.

## Fixtures, not architecture

mkosi composition (challenger: bootc); a declared Fedora snapshot (challenger:
Arch); EROFS and ext4; Btrfs on `/var` and `/home`; a disposable VM as harness;
every component named in a role capability declaration. **PR-0029 C-005 is the
standing risk**: repeated success is how a candidate becomes a decision without
an ADR. W-002 and W-004 are open.

## Validation

`check:fast` runs 12 and `check:complete` 22, 2 deferred of 24 registered;
`mise run check:list` is authoritative. Editing `tools/validation/` requires
`complete`. `T2-ROLE-001` and `T2-STATE-001` each reject eight constructed
violations; `T4-STATE-001` asserts both state volumes are block-device-backed.
All verified failing when they should.
`T4-SESSION-001` asserts nine observations and **records the two capabilities it
refuses to assert**: `graphics` needs a GPU the VM lacks, `login` needs a driven
authentication. `mise.toml` sets `sandbox.deny_env`, so **no artifact-dependent
check is reachable through `mise run`** — all nine block. Details: [validation](validation.md). **CI is red on `main` and
stays red** (`P-008`); not tracked or reported. `P-009` is open and blocks
nothing.

**`T0-DOC-003` and `T0-DOC-004` are `P-010`'s first step** (2026-08-16),
RES-0016's recommended validator and not an answer to the question, which stays
open. They bind the ADR and comparison indexes to the files they describe, hold
this file to its declared word bound, and stop a routing document linking to
anything frozen. Six failure modes verified detected.

## Context path

Root `AGENTS.md`'s Read section governs it. Questions: `decision-backlog.md`;
risks: `risk-register.md`; history: `docs/background/design-session-summary.md`.

Update it when the gate, the active plan, an accepted decision or leading
fixture, the mutation boundary, the validation commands, or the next action
changes. Assume a dirty worktree; preserve unrelated work.
