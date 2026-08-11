---
id: PLN-0002
title: Authenticated `/usr` artifact format comparison
status: accepted
owner: Jason Tarasovic
created: 2026-08-11
last_updated: 2026-08-11
gate: G1
depends_on: [PLN-0001]
reviews: [PR-0030]
accepted: 2026-08-11
---

# Authenticated `/usr` artifact format comparison

Revised 2026-08-11 against [PR-0030](../project/reviews/0030-usr-artifact-format-spike-plan.md),
which found the first draft not fit to accept. Two owner rulings shaped the
revision and are marked where they land.

## Outcome

Answer DES-0006 C-007 by measurement: build the same package closure as an
EROFS `/usr` artifact and an ext4 `/usr` artifact, authenticate each through
dm-verity and a root hash carried by a signed UKI, boot each in a disposable
VM, and measure **all eight** criteria DES-0006 verification item 2 names --
image size, build time, build determinism, boot behavior, memory, update
transfer size, inspectability, corruption behavior -- plus a stated disposition
for recovery behavior.

The claim this supports is narrow: **one of the two formats is a better `/usr`
artifact for NeutrinOS, and the record says why in measured, attributable
terms.** Reaching it requires the `/usr`-only boot path C-013 accepted, so this
plan also produces the first evidence that the path boots at all.

Nothing here selects a package ecosystem, a partition layout, a state
filesystem, or an updater.

## Non-goals

- **No single criterion decides C-007** (owner ruling, 2026-08-11). Build
  determinism is one of eight criteria and is weighed like the rest. The first
  draft excluded it, citing C-013's "reproducibility is never a reason for it";
  that ruling governs the `/usr` **scope** decision, not the format comparison,
  and applying it here deleted a criterion the design named. The surviving
  guard is against any one criterion -- reproducibility included -- carrying the
  recommendation alone.
- A/B slots, staging, or finalization ordering. Those are verification items 3
  and 4 and belong to a later plan. This plan builds a second same-format
  artifact per arm **only** as a substitution source for task 10, never as a
  staging or selection demonstration.
- The DES-0005 confext lifecycle. Verification items 11-19 are a separate plan.
- Encryption, LUKS2, TPM policy, or unlock behavior.
- Capacity falsification, the minimum viable device, or the C-002 formula.
- Any physical-host effect, on `desktop-jason`, `router`, `misc`, or otherwise.
- Production signing, Secure Boot enrollment, or any real trust anchor.
- Performance tuning of either format. Measurement, not optimization.

## Mutation and authority boundary

This plan inherits PLN-0000's boundary unchanged and narrows it as follows. It
creates no new authority.

May read and change: repository paths under `src/`, `tools/`, and `docs/`;
build caches and artifacts in declared locations outside the checkout;
disposable VM disks, firmware variables, vTPM state, and an isolated test
network; and synthetic signing and credential fixtures generated for this plan.

Must not, and no task may request an exception: touch any physical host beyond
separately authorized read-only inspection; use or create production Secure
Boot, enrollment, recovery, or credential keys; enroll any key into physical
firmware; or publish or roll an artifact to any machine.

The router is specifically out of reach. R-054 records that the development
workstation reaches the network through it.

## Inputs and dependencies

| Input or dependency | Identity/status | Blocking behavior |
| --- | --- | --- |
| DES-0006 C-013 | Accepted 2026-08-11: authenticated artifact is `/usr` | Fixes the scope this plan measures; a reopening stops the plan |
| DES-0006 C-007 | Open; the question this plan answers | Its criteria define the comparison |
| DES-0006 verification item 2 | Amended 2026-08-11 | Defines done; all eight criteria are in scope |
| DES-0006 C-008 | **Accepted 2026-08-11**: `/var` belongs to the machine-state volume | Constrains the fixture; see task 04 |
| DES-0005 confext amendment | Accepted 2026-08-11 | Requires a signed confext to boot; its tooling and path carve are **not** provided by it -- see task 03 |
| PLN-0001 slice | Complete; declared Fedora 44 closure, `compose.sh`, retention, runner, five registered tests | Reused; task 11 owns keeping the tests true |
| `S-004` layout, `C-009` state filesystem | Open | Fixtures only; task 04 states fixture status in the register when created |
| mkosi v26, Fedora 44 | Candidate fixtures | Remain candidates; using them accepts nothing |

## Decision and requirement trace

| ID | Applicability | Planned evidence |
| --- | --- | --- |
| SYS-049 | **Partial**, with covered cells named | Root hash in a signed UKI authenticating the exact `/usr` and Verity pair; substitution of a *same-format* valid `/usr`, its Verity tree, the confext, and the manifest. Covered cells of C-001's cross product are enumerated in task 10; uncovered cells carry forward, including every cell needing A/B slots or a physical role |
| SYS-030 | **Not applicable** | Restored from the first draft's "partial" per PR-0030 C-010. The requirement binds normal boot on a production physical role; a VM with a synthetic anchor is a different thing, not a partial instance of it. PLN-0001 classified it the same way |
| SYS-020 | Partial | Task 07 records `/etc` regenerated by `systemd-tmpfiles`/`systemd-sysusers` and whether anything durable appears there. C-013 claims to satisfy SYS-020 by construction; this plan measures that claim |
| SYS-048 | Partial | Task 04's regions are declared with owner and lifecycle purpose; the fixture's deviations from DES-0006's region table are recorded |
| SYS-051 | **Applicable, not satisfied** | Split out of the group per PR-0030 C-010. The fixture writes an unencrypted `/var` and journal to tmpfs; nothing persists, so no plaintext spill survives power-off, and that is the whole of the claim. No encryption boundary is designed or demonstrated |
| SYS-052 through SYS-056 | Not applicable | No encryption, capacity, snapshot, or recovery claim in scope |
| SYS-123 | **Partial** | Reclassified from "not applicable" per PR-0030 C-006. The plan builds a real signed confext under `image_policy_confext_strict`; content identity, authorization, and base compatibility are exercised in fact. Task 03 names what it produces and hands it back as candidate |
| SYS-018, SYS-041, SYS-059 | Inherited partial from PLN-0001 | Task 11 keeps the mechanisms and their checks true across the `/usr` split; "must keep passing" is a check, not an assertion |

Candidate mechanisms remain candidates unless a separate ADR accepts them.
EROFS winning does not accept EROFS; it produces the evidence an ADR needs.

## Work

Ordered so the plan's most likely falsification runs first (PR-0030 C-007).

| Task | Status | Depends on | Output/evidence | Next action |
| --- | --- | --- | --- | --- |
| PLN-0002-01 | **complete** | — | **Early-boot spike, one format, throwaway.** What is consumed before `/usr` is verified; whether `systemd-confext-initrd`/`systemd-confext-sysroot` behave as C-013 assumed; the named failure-capture path for every later task | Complete 2026-08-11. **The assumption holds and the gate is not triggered**: the `/usr`-only path boots on a tmpfs root, and `systemd-confext-sysroot.service` merges a confext into `/sysroot/etc` before switch-root. See the [early-boot record](../project/spike-early-boot-record.md). Owner ruling 2026-08-11: systemd 261 arrives as a local package overlay from OBS `system:systemd`, because Fedora 44 stays on 259.x and the unit is new in 261. Three findings are handed back and taken nowhere: a tmpfs root leaves a separately delivered confext with nowhere to live, read-only `/etc` breaks first-boot presets so runtime unit enablement is unavailable, and `/etc/machine-id` has no home |
| PLN-0002-02 | pending | 01 | `/usr`-only composition from the PLN-0001 closure, release defaults in `/usr/lib`, declaration and retention mechanisms intact | Extend `compose.sh`; record what moved out of the flattened root |
| PLN-0002-03 | pending | 01 | Confext build path and a minimal path carve, both **marked candidate and handed back** to DES-0005 and the ADR-0003 spike | Produce the signed confext the boot needs; record the carve as the first drawn, not the reference |
| PLN-0002-04 | pending | 01 | Disposable layout: ESP, one `/usr` slot, one Verity slot, **tmpfs root partition**, one confext. Fixture status recorded in the work register at creation | Build `systemd-repart` definitions. **Owner ruling 2026-08-11: tmpfs, which is the preferred direction and avoids the first draft's contradiction of the accepted C-008 ruling.** `/var` is tmpfs-backed and nothing persists; no machine-state volume is built, so C-008 is respected by not implementing the thing it governs |
| PLN-0002-05 | pending | 02, 04 | **Declared parameter set for both arms** and the pairing rule that justifies it: `mkfs.erofs` compression algorithm and level, EROFS cluster size, ext4 block size, inode ratio, reserved-block percentage and feature set, dm-verity hash block size and salt, and the initrd contents per arm with the asymmetry stated and its direction of advantage named | Declare before building. An undeclared parameter invalidates the comparison |
| PLN-0002-06 | pending | 05 | Two authenticated artifacts per arm: EROFS+dm-verity and ext4+dm-verity, each with Verity pair and synthetically signed UKI. Second same-format artifact per arm exists only as a task 10 substitution source. Signing key lifetime stated across the task graph | Build all four; retain digests |
| PLN-0002-07 | pending | 06 | Offline measurements: image size, build wall time, **build determinism**, update transfer size, inspectability. Repetition count and accelerator state recorded for every timed measurement | Measure both arms identically |
| PLN-0002-08 | pending | 06 | Boot records both arms: `/usr` read-only and verity-authenticated, `/etc` regenerated, no failed units, boot behavior and memory with repetition count and accelerator state | Boot each; PLN-0001 measured the same boot at 72s TCG and 18s KVM, so accelerator state is recorded per run |
| PLN-0002-09 | pending | 06 | **Corruption behavior**: single-bit corruption injected into an authenticated region of each artifact, recording detection point, diagnostic, and blast radius per format. Compressed EROFS clusters versus ext4 blocks is where the formats are expected to diverge | Inject and record verbatim |
| PLN-0002-10 | pending | 06 | **Negative evidence**: same-format `/usr` substitution, Verity substitution, confext substitution, manifest substitution, and a wrong-but-valid signing key, each failing closed with a diagnostic that discriminates root-hash mismatch from signature failure from mount failure. Covered cells of C-001's cross product enumerated | Inject each; record which mechanism rejected it and how that was determined |
| PLN-0002-11 | pending | 02, 03, 04 | The five registered slice tests updated for the `/usr` artifact, plus new checks for root-hash-to-UKI binding, read-only `/usr`, and nothing durable in `/etc`. Each verified failure-sensitive as PLN-0001-05 did | Update `T2`/`T3`/`T4-SLICE-*` and register the new checks |
| PLN-0002-12 | pending | 07, 08, 09, 10 | Recovery-behavior disposition: measured, or deferred with rationale naming where it goes. The `crypttab` element of item 2's early-boot clause is addressed against the encryption non-goal | Decide and record; a deferral is a proposed amendment to item 2 and is **the owner's**, not a task's |
| PLN-0002-13 | pending | 11, 12 | C-007 recommendation with its evidence, stating which criteria decided it and which were inconclusive. **If task 08 produced no values, this task says so and recommends nothing** | Draft; **the drafter does not accept it** |
| PLN-0002-14 | pending | 13 | Retained evidence bundle, updated requirement trace, work register, and DES-0006 disposition | Assemble as PLN-0001-08 did |

## Failure, interruption, and cleanup

Stop and return to review if: task 01 falsifies C-013's early-boot assumption;
the `/usr` split cannot preserve PLN-0001's declaration and attribution
guarantees; either format cannot be authenticated through a signed UKI with
available tooling; or a task needs a mechanism selection `S-004` or `C-009` has
not made.

**Failure capture is named before it is needed** (PR-0030 C-009). Task 01
established it on 2026-08-11 by inducing three failures; see the
[early-boot record](../project/spike-early-boot-record.md). Every later task
uses: how the journal is recovered when the
machine never reaches userspace, which PLN-0001 had to do offline from a disk
copy; the console path, given PLN-0001's composition amendments were reverted;
whether notify-vsock readiness applies to a pre-`/usr` failure, which it does
not; and the diagnostics that distinguish a missing filesystem driver from a
root-hash mismatch from a refused confext. A failure that cannot be attributed
to one of those is itself a finding.

If task 08 yields no boot values, task 13 recommends nothing and exit criterion
2 is met by recorded reasons rather than measurements. That is a real outcome,
not a formality.

Synthetic signing keys live for the whole task graph, not per task, because
task 10 must distinguish a substitution failure from a signature failure and
needs a second wrong-but-valid key to prove the gate discriminates. Their
lifetime is stated per artifact in task 06. They never leave the plan's scratch
location, are never enrolled anywhere, and are destroyed at plan end.

All VM disks, firmware variables, and vTPM state are destroyed at task end.
Evidence is retained outside the repository with one SHA-256 per file, scanned
for unsafe output, as PLN-0001-08 established. Partial artifacts are discarded
rather than measured: a half-built `/usr` is the hybrid C-001 warns about.

## Risks and unknowns

| Risk or unknown | Effect | Disposition |
| --- | --- | --- |
| C-013's early boot is its own stated residual risk | Task 01 may falsify part of an accepted amendment | Scheduled first for exactly that reason. A falsification returns to DES-0006 review; it is not worked around |
| The initrd cannot be identical across arms, since each needs its own filesystem driver | Boot and memory partly measure the initrd, not the format | Task 05 declares the asymmetry and which arm it advantages; task 13 names it as a threat to the finding |
| mkosi may not express a `/usr`-only artifact with Verity as directly as PLN-0001's flattened root | Task 02 cost, possibly a different composition path | **Closed by task 01, 2026-08-11.** It expresses it directly through `mkosi.repart` definitions, and parses the root hash out of repart's JSON to inject `usrhash=` into the UKI itself. No second composition path is needed |
| Task 03 draws the first confext path carve and builds the first confext tooling | Both become the reference by being first -- the implementation-accident failure mode | Marked candidate at creation and handed back to DES-0005 and ADR-0003. The plan states it does not own them |
| The tmpfs root partition is a fixture, and the persistence question DES-0006 records as open stays open | A fixture could look like a decision | Task 04 records fixture status in the register at creation. tmpfs is the cheaper and less committal of the two, which is why the owner chose it |
| The comparison could be decided by `mkfs` flags rather than by the formats | Wrong answer to C-007 -- the failure C-007 predicts | Task 05 declares every parameter before task 06 builds; an undeclared parameter invalidates the comparison |
| Second same-format artifacts could be read as A/B staging | Scope creep into verification items 3 and 4 | Built only as substitution sources; no selection, staging, or finalization is exercised or claimed |

## Exit criteria

1. Every task is satisfied, cancelled with rationale, or moved to a linked plan.
2. Each of verification item 2's eight criteria has a measured value for both
   formats or a recorded reason it could not be measured, and recovery
   behavior has a stated disposition.
3. SYS-049 has retained positive and negative evidence, with covered and
   uncovered cells of C-001's cross product enumerated.
4. Early-boot behavior is recorded as observed, including everything consumed
   before `/usr` is verified.
5. Every claim this plan makes is behind a registered check, and each check is
   verified failure-sensitive.
6. A C-007 recommendation exists with its evidence and its stated threats, and
   is **open for owner decision rather than accepted by the plan**.
7. Native diagnostics and failure evidence are retained.
8. The work register, DES-0006, and affected records are updated together.
9. Remaining unknowns are linked and assigned to a later gate or plan.

## Decision

Open for owner review.

Accepting this plan would authorize NeutrinOS source work again, bounded to the
scope above, on the basis PLN-0001 had: G1 is satisfied and PLN-0000's mutation
boundary requires G1 plus an accepted follow-on plan. The frontmatter carries
`gate: G1` -- the gate this plan executes under, per PR-0030 C-012 -- not G2.

It would **not** authorize: G2 or any G2 qualification claim, any physical-host
effect, any production key or enrollment, an ADR accepting EROFS or ext4, a
partition layout, a state filesystem, a confext path carve, or a package
ecosystem. It would not settle `S-004`, `C-009`, or `C-002`, and completing it
would not satisfy SYS-030, which is not applicable to a VM with a synthetic
anchor.
