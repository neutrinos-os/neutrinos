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
> names. Before edits or a high-risk claim, verify the governing source. A
> conflicting source wins; correct this summary.
>
> A pointer index, never the sole home of a decision, ruling, measurement or next
> action. **Keep it under 1,100 words**, enforced by `T0-DOC-004`; a measurement,
> or a narrative of how a result was reached, belongs in the owning record.

## Position

- **G1 approved** 2026-08-10 (PR-0029). A readiness gate, not a capability gate:
  it authorizes disposable VM and lab work under an accepted follow-on plan and
  nothing else. Seven review challenges are carried open, not closed.
- **PLN-0000, PLN-0001 and PLN-0002 are complete and accepted**, the last on
  2026-08-15 with two qualifications in its exit-criteria assessment. Their
  results live in the plans and records; they are not restated here.
- **PLN-0003 is accepted** 2026-08-15 (PR-0031), the active plan and sole active
  implementation slice: the `/usr` read-workload comparison, the one measurement
  that could reverse the C-007 recommendation
  (`docs/plans/0003-usr-read-workload-comparison.md`).
- **SYS-018, SYS-041 and SYS-059 are accepted at `Partial`** (2026-08-11), as is
  SYS-049, whose substitution clause holds for the image and the Verity tree and
  **is falsified for the signature** — a measured gap carried by two deferred
  checks.

## Next action

**PLN-0003-01: the workload and measurement declaration.** Nothing precedes it —
declare before measuring, on PLN-0002-05's standard, where an undeclared
parameter invalidates the comparison. It must fix the two workload shapes, the
memory cells and each cell's direction of bias, host cache mode, readahead state,
accelerator, repetition count, the cold-cache protocol, and what counts as
page-cache footprint on each arm.

## Standing findings

One line each; the owning record is the authority.

- **This slice's mechanisms fail open silently — eight instances**, so a
  successful boot is not a statement about the artifact. Worst and latest: a
  valid signature over a root hash the image does not carry boots to `running`
  with zero failed units ([substitution](artifact-substitution-records.md)).
- `systemd.image_policy=usr=signed` is a structural predicate, not an enforcement
  mechanism ([declaration](artifact-parameter-declaration.md)).
- Upstream's `/usr` signature enforcement point is the TPM unseal, not the mount
  (`S-005`, [backlog](decision-backlog.md)).
- Confext signature enforcement is closed and registered (`T4-CONFEXT-001`).
- Build determinism is closed; **any determinism claim must state whether the
  confext was rebuilt** ([artifact set](usr-artifact-set.md)).
- **Any blast-radius claim must state whether readahead was disabled**, and any
  size claim must use bytes in use — partition size overstates EROFS's advantage
  by 56% ([corruption](artifact-corruption-records.md),
  [measurements](artifact-format-measurements.md)).
- A declared parameter can be wrong rather than merely missing; the 2026-08-14
  audit read the built artifacts and took three corrections.
- Retention of inputs is what has repeatedly made work possible.

## Open and the owner's

- **Two corrections to accepted records**: the `fsck.erofs --extract` finding
  ([disposition](artifact-recovery-disposition.md)), and PLN-0002-13's threat 1
  naming verification item 9 as owning the workload comparison.
- **The ruled command line is not the implemented one** (ruling 2026-08-12
  against `usr=signed` with `usrhash=` retained). Settling it in the ruling's
  favour rebuilds the six artifacts and voids what was measured against them
  ([declaration](artifact-parameter-declaration.md)).
- Whether G1's approval should be revisited against the corrected requirement
  trace.
- **C-007 is open.** PLN-0002-13 recommends EROFS, conditional on the update
  mechanism not being whole-image-only, on image size at 1.65x and 111.4 MiB per
  slot. **That acceptance does not accept EROFS** — an ADR does
  ([recommendation](artifact-format-recommendation.md)).

## Mutation boundary

Allowed: PLN-0003's named tasks on disposable VM disks, firmware variables,
virtual TPM state and test networks; **non-member artifacts**, marked at creation
and destroyed at task end; synthetic signing, enrollment and credential fixtures;
build caches in declared locations; documentation, ADR, design and validation
work; read-only inspection the task authorizes.

**The six PLN-0002-06 artifacts are read-only inputs**, every boot `snapshot=on`
with the digest verified first. Rebuilding, re-signing or modifying a member is
prohibited and would void PLN-0002's tally.

Also allowed, owner authorization 2026-08-16 and outside PLN-0003's task scope:
**corpus-integrity checks under `tools/validation/`**. No artifact, VM or
measurement work.

Prohibited: implementation outside PLN-0003's task scope; a compression sweep as
a result; G2 qualification claims; mutation of `desktop-jason`, `router`, `misc`
or another physical host; production credentials, keys, enrollment state,
recovery material or machine authority; treating a candidate fixture, probe or
agent summary as an accepted decision; autonomous push, merge, release or
publication.

The synthetic signing material expires **2026-09-11**.

## Accepted decisions bounding current work

Pointers, not authority. **[ADR index](../adrs/README.md)** is the list; ADR-0004
through ADR-0009 were **accepted 2026-08-16** and record the DES-0006 and
DES-0005 rulings of 2026-08-11, so storage and configuration are bound there
rather than in a design review. Also: naming (`naming.md`); Apache-2.0 and public
(`scope.md`, `P-007`); system policy (`docs/requirements/system.md`); test
taxonomy (`test-strategy.md`); validation contract (`validation-contract.md`);
PLN-0000's readiness model.

## Fixtures, not architecture

mkosi composition (challenger: bootc); a declared Fedora snapshot (challenger:
Arch); EROFS and ext4; `systemd-sysinstall`; a distribution kernel with a normal
initrd; a disposable VM as harness. **PR-0029 C-005 is the standing risk**:
repeated success is how a candidate becomes a decision without an ADR, and the
test is whether the challengers are ever run. PR-0030 C-006 is the same risk in
PLN-0002's confext carve. W-002, W-004 and the role contracts are open; do not
encode their fixture shapes as architecture.

## Validation

`check:fast` runs 10 checks and `check:complete` 18, with 2 deferred of 20
registered; `mise run check:list` is authoritative. `complete` needs a composed
artifact and the declared fixture directories, and editing `tools/validation/`
requires it. Details: [validation](validation.md). **CI is red on `main` and
stays red** (`P-008`); not tracked or reported. `P-009` is open and blocks
nothing.

**`T0-DOC-003` and `T0-DOC-004` are `P-010`'s first step** (2026-08-16),
RES-0016's recommended validator and not an answer to the question, which stays
open. They bind the ADR and comparison indexes to the files they describe, hold
this file to the word bound it declares, and stop a routing document linking to
anything frozen. Six failure modes verified detected.

## Context path

1. Root `AGENTS.md`. 2. This file. 3. Read-only status: hard stop — cite paths
without opening them. 4. Execution or edit: the active plan's sections and only
the sources governing the exact change. 5. Questions: `decision-backlog.md`
(`work-register.md` is frozen — do not read or cite it). 6. History:
`docs/background/design-session-summary.md`.

Update this file when the gate, the active plan, a relevant accepted decision or
leading fixture, the mutation boundary, the canonical validation commands, or the
one next action changes. Assume a dirty worktree; preserve unrelated work.
