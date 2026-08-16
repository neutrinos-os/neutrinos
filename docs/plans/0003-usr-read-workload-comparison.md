---
id: PLN-0003
title: '`/usr` read-workload comparison'
status: active
owner: Jason Tarasovic
created: 2026-08-15
last_updated: 2026-08-15
gate: G1
depends_on: [PLN-0002]
reviews: [PR-0031]
accepted: 2026-08-15
---

# `/usr` read-workload comparison

**Accepted by Jason Tarasovic on 2026-08-15 and active.** It is the sole active
implementation slice, and it restores the authority PLN-0002 took with it when
it completed the same day: PLN-0000's boundary requires G1 *plus an accepted
follow-on plan*, and this is that plan.

**Revised 2026-08-15 against
[PR-0031](../project/reviews/0031-usr-read-workload-comparison-plan.md)**, which
found the first draft not fit to accept. All ten challenges were ruled by
Jason Tarasovic on 2026-08-15 and the rulings are applied below, each marked
where it lands. Two changed the plan's shape rather than its wording: the
DES-0006 amendment task is **gone**, and building **non-member** artifacts is
now permitted.

## Outcome

Measure the one thing that could reverse PLN-0002-13's C-007 recommendation:
**what a wide read across `/usr` costs on each format.**

The recommendation is EROFS on image size, 1.65x, conditional on the updater.
Its **first and strongest stated threat is an absence** -- no workload was
applied, memory was a tie measured on an idle guest twenty seconds after boot,
and EROFS pays its compression cost on *read*, in decompression time and in
cache holding decompressed pages. That is the case a workstation actually is,
and it is unmeasured.

This plan applies **two declared read workloads** to the **two accepted
primaries, unmodified**, and measures read time, the CPU cost of decompression,
and page-cache footprint, at **declared guest memory cells** whose biases are
named in advance.

The claim it supports is narrow and either sign is a real result: **the C-007
recommendation either survives a read workload or it does not, and the record
says which, in measured terms.**

**No verification item owns this comparison** (ruling, C-007): it is evidence
for C-007's open question and for PLN-0002-13's threat 1, and DES-0006 takes a
disposition at plan end rather than a new item or a clause on item 9.

## Non-goals

- **No rebuild of the accepted set.** The six PLN-0002-06 artifacts are inputs
  here, never outputs. Rebuilding them voids PLN-0002's tally and this plan's
  figures with it.
- **Not DES-0006 verification item 9.** Item 9 is a *workstation representative
  workload across Btrfs, XFS and ext4* -- the state filesystem question under
  `C-009`. This is EROFS against ext4 as the release artifact. Same word,
  different comparison, and under the C-007 ruling neither item owns the other.
- No A/B slots, staging, finalization, updater, encryption, TPM policy, or
  recovery behaviour.
- **No ADR, and no acceptance of a format.** C-007 stays open; this plan
  produces evidence an ADR needs and records no decision.
- **No compression sweep as a result.** Non-member artifacts exist for
  attribution and instrument control (rulings, C-003 and C-005), not to search
  for a faster EROFS. A tuning result is a finding handed on, never a
  recommendation from this plan.
- No workstation role contract. A workload fixture is not a role definition.
- No physical-host effect, no production key, enrolment, or credential.

## Mutation and authority boundary

Inherits PLN-0000's boundary unchanged and narrows it as PLN-0002 did. It
creates no new authority.

May read and change: repository paths under `src/`, `tools/`, and `docs/`;
evidence and cache locations already declared outside the checkout; disposable
VM disks, firmware variables, vTPM state, and an isolated test network.

**May read but must not modify: the six PLN-0002-06 artifacts.** Every boot is
`snapshot=on` against the retained artifact, whose digest is verified **against
the retained value before use** and re-checked after. A task that needs a byte
changed inside one of the six has left this plan's scope.

**May build non-member artifacts** (ruling, C-003). Artifacts built here for
attribution or instrument control are **marked non-member at creation**, are
never cited as members of the accepted set, and never enter PLN-0002's records.
The six are still never rebuilt, re-signed, or modified.

Must not, and no task may request an exception: rebuild or re-sign any member of
the accepted set; touch any physical host; use or create production Secure Boot,
enrolment, recovery, or credential material; enrol any key into physical
firmware; or publish or roll an artifact to any machine. The router is
specifically out of reach (R-054).

## Inputs and dependencies

| Input or dependency | Identity/status | Blocking behavior |
| --- | --- | --- |
| The two primaries of the PLN-0002-06 set | Accepted 2026-08-14, digests retained in the [artifact set](../project/usr-artifact-set.md) | **Verify against the retained digest before every run.** A mismatch stops the plan rather than being measured |
| [PLN-0002-13 recommendation](../project/artifact-format-recommendation.md) and its accepted weighing rule | Accepted 2026-08-15 | Defines what this plan tests. **Its threat 1 misnames item 9 as the owner of this comparison**; the C-007 ruling makes that false, and correcting an accepted record is the owner's |
| [PLN-0002-05 declaration](../project/artifact-parameter-declaration.md) | Accepted, audited against the built artifacts | The arms' parameters, including the mount-option asymmetry task 01 must declare |
| `tools/validation/vm.py`, `src/slice/measure-boot.py` | Working harness: SMBIOS credential delivery, QMP accelerator assertion, digest check | Reused. A workload that cannot be delivered as a credential is a stop condition, not a reason to modify a member artifact |
| `src/slice/compose.sh` | Working and deterministic; PLN-0002-07 measured builds at 46.65s and 52.87s median | What produces the non-member artifacts. A control build is about a minute, which is why it is affordable |
| Synthetic signing material | **Expires 2026-09-11** | Hard schedule bound, and it binds the non-member artifacts too. Measurements after it are against expired enrolment material and must say so |
| The ParticleOS command-line ruling | Open since 2026-08-12 | If settled in its own favour the accepted set rebuilds and **every figure in PLN-0002 and in this plan voids**. Not a reason to wait; a reason to state the dependency |
| `C-002` capacity budget, workstation role contract | Open | Fixtures only. Task 06 routes figures to `C-002` with their limits attached (ruling, C-009); no capacity claim follows |

## Decision and requirement trace

**No requirement is claimed, demonstrated, or advanced by this plan**, and that
is deliberate rather than an omission. It measures a property of two candidate
formats; requirement satisfaction is not what is under test.

| ID | Applicability | Planned evidence |
| --- | --- | --- |
| SYS-049 | **Unchanged, and not re-claimed** | Nothing is substituted, signed, or verified here. PLN-0002's trace stands, including its measured gap in the signature clause |
| SYS-030 | **Not applicable** | A VM with a synthetic anchor, as in PLN-0001 and PLN-0002 |
| SYS-056 | **Not claimed, and routed anyway** | Layout capacity and margins are `C-002`'s. Task 06 hands it the memory-under-load figures with their scope limits inline -- one CPU class, synthetic workload, no role contract -- so they cannot be cited as budget input without them |
| SYS-018, SYS-041, SYS-059 | Inherited partial, untouched | No check is registered against them and no mechanism they trace to changes |

Candidate mechanisms remain candidates. EROFS winning or losing a read workload
accepts nothing.

## Work

Ordered so the declaration precedes every measurement and the instrument is
proven before any comparison is drawn from it.

| Task | Status | Depends on | Output/evidence | Next action |
| --- | --- | --- | --- | --- |
| PLN-0003-01 | pending | — | **Workload and measurement declaration**, held to PLN-0002-05's standard: **an undeclared parameter invalidates the comparison.** Declares both workload shapes; the memory cells and each cell's direction of bias; host cache mode; readahead state; accelerator; repetition count; the cold-cache protocol; and **what is counted as page-cache footprint on each arm** | Declare before measuring. **Two shapes** (ruling, C-008): a whole-`/usr` sequential read for decompression bandwidth, and a sparse exec-and-link pattern for per-cluster latency on small reads, both derived from what the artifact contains rather than invented, reported separately. **Cells by rule** (ruling, C-002): one generous to both arms; one scaled to each arm's *own* image size so neither fits proportionally; and any absolute cell between **171.0 and 282.4 MiB** declared a **size-advantage cell** and reported as such, because there the fits-or-doesn't effect is criterion 1 counted again in a new unit. **Page cache per arm** (ruling, C-006): establish what this kernel exposes for EROFS, separate decompressed pages from compressed blocks where it can, and where it cannot report the aggregate with the limit stated in the record. Four traps carry over from PLN-0002 and each must be declared or neutralised: the arms' **mount options differ** (`user_xattr,acl,cache_strategy=readaround` against plain `ro,relatime`), **dm readahead is 8 MiB**, the host page cache can serve the guest's reads, and at 1948.6 MiB both images fit entirely in cache. **No reversal threshold is pre-registered** (ruling, C-001) |
| PLN-0003-02 | pending | 01 | **Harness**: `src/slice/measure-workload.py`, reusing `vm.py` and the `measure-boot.py` pattern. Workload delivered **only** as SMBIOS Type 11 credentials; member digests verified against the retained values before use and re-checked after; accelerator asserted per run over QMP; serial console and per-run JSON retained | Build it. **Every run records the parameters it observed** -- readahead state, host cache mode, guest RAM, accelerator, and the workload as executed -- into the retained evidence, because the audit in task 05 can only examine what was captured and a run parameter not read back at the time is unrecoverable (ruling, C-004). A workload that cannot be expressed in what the artifact already ships is a **stop condition**: no member artifact is modified to make a measurement possible |
| PLN-0003-03 | pending | 02 | **Instrument control**: a **non-member** EROFS artifact built with compression deliberately different, and the demonstration that the harness resolves that known difference | Build and measure it **before any arm-to-arm comparison is drawn** (ruling, C-005). The control is format-scale and in the result's own units, which is what makes a subsequent null result mean anything. Cold-versus-warm stays as a cheaper first check and is **not** the sensitivity claim. If the harness cannot resolve the control, the comparison stops here |
| PLN-0003-04 | pending | 03 | **Measure both arms**, identically, both shapes, at every declared cell, with the declared repetitions. Read wall time, CPU time attributable to decompression, page-cache footprint as declared, and any failed units | Measure; retain verbatim. The two primaries only; the four variants answer nothing here. Where a result is plausibly attributable to `lz4hc:12` rather than to EROFS, a **non-member** artifact at a different compression setting splits the two (ruling, C-003) -- attribution, not a sweep |
| PLN-0003-05 | pending | 04 | **Declaration audit**: the task-01 declaration read back against the retained runs, with every correction recorded | Audit after measuring, as PLN-0002-05's audit did (ruling, C-004). Its finding there was that **a declared parameter can be wrong rather than merely missing** -- 130 modules shipped against 21 declared -- and a mismatch here is a correction taken in the open, not a figure quietly dropped |
| PLN-0003-06 | pending | 05 | **Disposition: does the C-007 recommendation survive?** With magnitude and sign, per shape and per cell, and what the workloads do not cover | Draft; **the drafter does not accept it.** **The weighing is performed with the figures visible and the record must say so** (ruling, C-001): no reversal condition was pre-registered, so the exchange rate between a read cost and 111.4 MiB per slot is set by the owner after the fact, and that is the weaker position honestly stated. Routes the memory-under-load figures to `C-002` with their limits inline (ruling, C-009). Either sign is a result: a reversal is new evidence against an accepted recommendation, a confirmation discharges threat 1 and removes the last measurement blocking a C-007 ADR |
| PLN-0003-07 | pending | 06 | Retained evidence bundle, work register, current context, and the **DES-0006 disposition** | Assemble as PLN-0002-14 did, with `collect-evidence.py --task-evidence`. DES-0006 receives a disposition rather than a new verification item (ruling, C-007) |

## Failure, interruption, and cleanup

Stop and return to review if: the workload cannot be delivered without modifying
a member artifact; any member digest fails verification before a run; the
harness cannot resolve the task-03 control; or a task needs a mechanism `S-004`
or `C-009` has not selected.

**A null result is a result** -- but only once task 03 has shown the instrument
could have seen the effect. If both arms measure the same under workloads that
demonstrably exercise reads, on an instrument that resolved the control, threat
1 is discharged and task 06 says so rather than searching for a workload that
separates them. Searching until the arms differ is how a measurement becomes an
argument.

Every VM disk, firmware variable, and vTPM state is destroyed at task end.
**Non-member artifacts are destroyed with them** and are never retained beside
the accepted set, where a later reader could mistake one for a member. Evidence
is retained outside the repository with one SHA-256 per file and scanned for
unsafe output, as PLN-0001-08 and PLN-0002-14 established.

**The signing material expires 2026-09-11.** Work after that date measures
expired enrolment material and every affected record must say so.

## Risks and unknowns

| Risk or unknown | Effect | Disposition |
| --- | --- | --- |
| **The result arrives with no procedure to weigh it** | The accepted weighing rule was written without a read criterion, and its rules 1 and 3 pull in opposite directions on one. The exchange rate against 111.4 MiB per slot has no common unit | **Accepted by owner ruling (C-001): measure first, weigh afterwards.** No pre-registered threshold. Task 06 states that its weighing was done with the numbers visible. This is the plan's largest carried risk and it is deliberate |
| **The workloads are fixtures and become "the" workloads by being first** | PR-0029 C-005's failure mode, relocated to the measurement | Two shapes with different read profiles, derived from artifact contents, declared as fixtures, reported separately. Task 06 must state what workload class the result does not cover. Weaker than a role contract, and there is none |
| Cell selection decides the outcome | Any RAM between 171.0 and 282.4 MiB is a cell only EROFS fits in | Cells declared by rule in task 01 with each bias named; a size-advantage cell is reported as one |
| The arms' mount options differ, `cache_strategy=readaround` among them | A read comparison could measure an EROFS read strategy rather than EROFS | Declared in task 01 and carried into task 06's caveats. It cannot be silently inherited from PLN-0002-05 |
| Host page cache serves the guest's reads | Both arms look identical for a reason inside neither | Cache mode declared in task 01; task 03's control is what would catch it |
| The constrained cell measures RAM sizing rather than format | A difference that is about thrashing on a small guest | Both arms at every cell, reported per cell rather than pooled |
| A loss is attributable to `lz4hc:12` rather than to EROFS | The recommendation's threat 2 impurity, inherited | Non-member artifacts split format from setting (C-003). The split is attribution; a tuning result is handed on, not recommended |
| **The measurement is on one CPU class** | lz4hc decompression is CPU work; a developer workstation is not a router or a laptop | Stated as scope, and carried inline on the `C-002` pointer. No result transfers to a role budget |
| The command-line ruling settles in its own favour | The accepted set rebuilds and this plan's figures void with PLN-0002's | Named as an input dependency; the record carries the caveat |
| The signing material expires mid-plan | Later runs, and any non-member artifact, use expired enrolment material | Schedule bound stated; affected records say so |

## Exit criteria

1. Every task is satisfied, cancelled with rationale, or moved to a linked plan.
2. The workload shapes, memory cells, and every measurement parameter are
   declared **before** the first measurement, with each cell's bias named.
3. The instrument is shown to resolve a known format-scale difference before any
   arm-to-arm comparison is drawn from it.
4. Both arms are measured identically, on both shapes, at every declared cell,
   with repetition count and accelerator state recorded per run, or a recorded
   reason a cell could not be measured.
5. The declaration is audited against the retained runs, and every correction is
   recorded rather than absorbed.
6. A disposition on PLN-0002-13's threat 1 exists with its evidence and its
   stated threats, states that its weighing was performed with the figures
   visible, and is **open for owner decision rather than accepted by the plan**.
7. Every run verified its member artifact against the PLN-0002-06 retained
   digest **before** use, and a mismatch stopped the plan.
8. No non-member artifact is retained, cited as a member, or recorded in
   PLN-0002's records.
9. Native diagnostics and failure evidence are retained outside the repository.
10. The work register, DES-0006, and affected records are updated together, and
    remaining unknowns are linked and assigned to a later gate or plan.

## Decision

**Accepted 2026-08-15 by Jason Tarasovic**, with the revision above and with two
residual risks accepted as part of it: the C-001 weighing gap, by the same day's
ruling, and the workload fixtures, which have no role contract behind them and
become the reference by being first.

Accepting this plan authorizes NeutrinOS reference-VM work again, bounded
to the scope above, on the basis PLN-0001 and PLN-0002 had: G1 is satisfied and
PLN-0000's mutation boundary requires G1 plus an accepted follow-on plan. The
frontmatter carries `gate: G1`, the gate this plan executes under, not G2.

It would authorize one thing the previous plans did not: **building artifacts
that are not members of the accepted set**, for attribution and instrument
control, under the marking and destruction rules above.

It does **not** authorize: rebuilding, re-signing, or modifying any member of
the PLN-0002-06 set; a compression sweep as a result; an ADR accepting EROFS or
ext4; G2 or any qualification claim; any physical-host effect; any production
key or enrolment; a state filesystem comparison, a partition layout, an updater,
or a workstation role contract. It would not settle `S-004`, `C-009`, or
`C-002`, and completing it would not close C-007 -- it would remove the last
measurement standing between the recommendation and an ADR, in whichever
direction the measurement points.
