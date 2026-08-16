---
id: PR-0031
subject: '`/usr` read-workload comparison plan'
plan: PLN-0003
reviewer: Claude adversarial pass
date: 2026-08-15
last_updated: 2026-08-15
status: accepted
---

# `/usr` read-workload comparison plan review

## Decision scope

This review examines [PLN-0003](../../plans/0003-usr-read-workload-comparison.md):
its outcome, non-goals, boundary, requirement trace, task decomposition,
measurement design, and exit criteria. **It rules on nothing.** Every challenge
below is open for the owner.

## Summary judgment

**Not fit to accept as written.** The plan is aimed at the right target -- threat
1 is the strongest argument against an accepted recommendation and it is an
absence of evidence -- and its no-rebuild boundary, its declaration-before-
measurement discipline, and its written-in null result are all correct. But it
can produce a number that **cannot change the decision it exists to test**: the
C-007 recommendation rests on an accepted weighing rule under which a read
result lands in the two categories the rule discounts, and the plan never says
how new evidence enters that rule. Worse, the one design choice it defers to a
later task -- which guest memory sizes to measure at -- **decides the outcome**,
because the arms' images differ by 111 MiB and any RAM cell between them is a
cell only one arm fits in. Two further gaps matter: no task audits the
declaration against what actually ran, which is the defect PLN-0002-05 was
caught by, and the instrument-sensitivity task proves a weaker property than the
one the comparison needs.

Five challenges are critical or high. None is unfixable, and three are fixed by
saying something in advance rather than by doing more work.

## Challenges

### C-001: The measurement cannot reverse the recommendation, because the accepted rule discounts it

- Severity: critical
- Claim: PLN-0002-13's recommendation was accepted **together with a weighing
  rule**, and that rule is what turns nine rows into an answer. Rule 1 discounts
  any criterion measured at or near the noise floor; rule 3 gives most weight to
  a large magnitude whose cost recurs per machine. A read-workload result is an
  extension of criteria 4 and 5 -- boot behaviour and memory -- which came back
  as ties, and its magnitude would have to be enormous to outweigh 111.4 MiB per
  slot under rule 3. **The plan states no procedure for entering its result into
  the accepted rule**, and defers "what would constitute a reversal" to its own
  task 02, which is after acceptance and inside the plan that wants the answer.
- Failure or cost if true: the plan spends a four-week window measuring
  something that, whatever it shows, gets weighed under a rule that was written
  without it and discounts it by construction. The owner then holds a number and
  no procedure, which is exactly the position C-007 was in before the weighing
  rule was accepted as a separate object.
- Required response or experiment: state the reversal condition **in the plan,
  before acceptance**, in the accepted rule's own terms -- what magnitude, on
  what measure, at what cell, would outweigh 111.4 MiB per slot under rule 3, and
  whether a read cost is a rule-1 noise-floor criterion or a rule-3 recurring
  per-machine cost. That is arguably an amendment to the accepted weighing rule
  and therefore the owner's, not a task's. If the honest answer is "no read
  result could outweigh image size", the plan should say so and be cancelled or
  re-scoped, because then threat 1 is not a threat to the recommendation but a
  caveat on it.

**Ruled 2026-08-15 by Jason Tarasovic: measure first, weigh afterwards.** No
amendment to the accepted weighing rule and no pre-registered reversal
threshold. The exchange rate between a read cost and 111.4 MiB per slot is set
when the figures exist, by the owner. **Two consequences follow and belong in
the plan**: task 02's clause requiring the reversal condition to be declared
before measuring is superseded and comes out; and the disposition must state
that its weighing was performed with the numbers visible, which is the only
mitigation left once pre-registration is declined.

### C-002: The guest memory cells decide the winner, and the plan defers choosing them

- Severity: critical
- Claim: task 02 is to declare RAM cells, "at minimum one where `/usr` fits in
  page cache and one where it cannot". The two images are **171.0 MiB and 282.4
  MiB in use**. Any guest RAM sized between those two figures is a cell where
  the EROFS image fits entirely in cache and the ext4 image cannot -- so the
  comparison at that cell measures the size advantage a second time, in a new
  unit, and reports it as a read result. Cells above both, or below both, bias
  the other way or measure thrashing. **Choosing the cell is choosing the
  outcome**, and the plan hands that choice to the task that runs the
  measurement.
- Failure or cost if true: the plan reproduces PR-0030 C-003 -- the arms are not
  comparable and the plan does not say what makes them equal -- in the one
  dimension it was written to add. A reversal or a confirmation would both be
  attributable to cell selection, and neither would survive review.
- Required response or experiment: declare the cells in the plan by a **stated
  rule**, not by a number chosen later, and state which way each biases. At
  minimum: one cell generous to both, one cell scaled to each arm's *own* image
  size so neither fits proportionally, and, if an absolute cell between 171 and
  282 MiB is measured at all, it is reported as a size-advantage cell and not as
  a read-cost cell.

**Ruled 2026-08-15 by Jason Tarasovic: declare the cells by rule in the plan,
and name each cell's bias in the record.** One cell generous to both arms; one
scaled to each arm's own image size so neither fits proportionally; and any
absolute cell between 171.0 and 282.4 MiB reported as a **size-advantage cell**
rather than a read-cost cell, because at that size the fits-or-doesn't effect is
criterion 1 counted a second time in a different unit.

### C-003: A loss is unactionable inside this plan's own non-goals

- Severity: high
- Claim: the EROFS arm is `lz4hc` level 12 by declaration. If a read workload
  shows EROFS materially slower, the first question anyone asks is whether a
  cheaper compression setting removes the cost -- and this plan forbids that
  twice, as "no performance tuning" and as "no rebuild of the artifact set".
  Threat 2 of the recommendation already says the deciding number is part
  compression rather than format; this plan inherits that impurity and then
  removes the only response to it.
- Failure or cost if true: a negative result produces no decision and no next
  step. The owner is told EROFS reads slower at one compression setting, cannot
  learn whether that is the format or the setting without voiding the tally, and
  the recommendation is left neither confirmed nor reversed.
- Required response or experiment: decide in advance which comparison this is.
  Either it compares **the two artifacts NeutrinOS would ship**, in which case
  the record must say a loss is a property of the shipped EROFS artifact and a
  compression sweep is a *separate* plan against a *separate* artifact set; or it
  compares the formats, in which case a rebuild is required and PLN-0002's tally
  is knowingly put at risk. The plan currently implies the first and reads like
  the second.

**Ruled 2026-08-15 by Jason Tarasovic: throwaway non-member artifacts are
permitted.** The plan's boundary widens to allow building artifacts that are
**explicitly not members of the accepted six**, for two purposes: splitting a
read-cost loss into format against compression setting, and giving C-005 the
instrument control it needs. **The six are still never rebuilt, re-signed, or
modified**, so PLN-0002's tally is unaffected. Every non-member artifact is
marked as such at creation and is never cited as a member of the set.

### C-004: No task audits the declaration against what actually ran

- Severity: high
- Claim: exit criterion 3 requires the declaration to be "audited against what
  actually ran", and **no task owns that audit**. This is the same shape as
  PLN-0002's exit criteria naming work no task did, and the specific failure it
  guards against is measured history: PLN-0002-05's declaration was audited
  against the built artifacts on 2026-08-14 and took three corrections, one of
  which was a module list describing 21 modules where the artifact shipped 130.
  "A declared parameter can be wrong rather than merely missing" is that plan's
  own finding.
- Failure or cost if true: the plan's central discipline -- declare before
  measuring -- is enforced by nothing. A declared readahead state, cache mode, or
  RAM figure that does not describe the run is undetectable, and every figure
  downstream of it is unattributable.
- Required response or experiment: add a task, or an explicit clause in task 05,
  that reads the parameters back **from the running guest and the host process**
  and compares them to the declaration, failing the run on a mismatch rather
  than recording it afterwards.

**Ruled 2026-08-15 by Jason Tarasovic: a closing audit, not a run-time
abort.** The declaration is audited against the retained runs after measuring,
as PLN-0002-05's audit did, and a mismatch is taken as a correction rather than
preventing the figure. **One implication is load-bearing and belongs in the
harness task**: an audit can only examine what was captured, so every run must
still record the parameters it observed -- readahead state, host cache mode,
guest RAM, accelerator, and the workload as executed -- into the retained
evidence. Without that capture there is nothing to audit against, and a run
parameter that is not read back at the time is unrecoverable afterwards.

### C-005: The sensitivity task proves a weaker property than the comparison needs

- Severity: high
- Claim: task 04 requires cold-cache and warm-cache runs on the same arm to
  differ by a large reproducible margin. That establishes the harness can tell
  **cached from uncached reads**, which is not in doubt and is true on both arms
  regardless of format. It does not establish that the harness can resolve a
  *format* difference of the size at stake. PLN-0002-08 measured a 22ms
  difference inside a run-to-run spread twice that size and correctly called it a
  tie; the same instrument, on the same host, with no CPU pinning and a host page
  cache in the path, may not resolve the effect this plan is looking for.
- Failure or cost if true: a null result is written into the plan as a real
  result -- correctly -- but a null result from an instrument that could not have
  shown the effect is not a result at all, and the plan would report the two as
  the same thing.
- Required response or experiment: state the **smallest effect the instrument
  must resolve** and demonstrate it can, before comparing arms. The honest
  control is a same-arm manipulation of known direction and rough magnitude --
  varying readahead, or `cache_strategy`, or the guest's CPU allocation. Note
  that the strongest control, an uncompressed EROFS artifact, requires a build
  the boundary forbids; if a throwaway non-member artifact is acceptable as an
  instrument control, the boundary must say so explicitly, because as written it
  does not.

**Ruled 2026-08-15 by Jason Tarasovic: a non-member control artifact.** Under
the C-003 ruling the plan may build a throwaway EROFS artifact with compression
deliberately different, and the harness must resolve that known difference
**before any arm-to-arm comparison is drawn**. The control is format-scale and
in the result's own units, which is what makes a subsequent null result
meaningful. Cold-versus-warm stays as a cheaper first check; it is not the
sensitivity claim.

### C-006: "Page-cache footprint" is not comparable across the arms as stated

- Severity: high
- Claim: threat 1 names the cost precisely -- "decompression time and **cache
  holding decompressed pages**". On EROFS the cache may hold decompressed pages
  *and* the compressed blocks behind the dm device; on ext4 there is one
  population. `Cached` from `/proc/meminfo`, which is what PLN-0002-08 sampled,
  does not separate them. The plan says "page-cache footprint after the
  workload" and stops there.
- Failure or cost if true: the plan measures a number that means different
  things on the two arms and reports the difference as a format result -- the
  same class of error as reporting partition size instead of bytes in use, which
  overstated EROFS's advantage by 56% until PLN-0002-07 corrected it.
- Required response or experiment: define per-arm what is being counted, and how
  it is read, in task 02's declaration rather than at measurement time. If the
  populations cannot be separated with what the artifact ships, say so and
  report the aggregate with that limit stated.

### C-007: Task 01 asks for a ruling that should precede the plan, not open it

- Severity: medium
- Claim: task 01 drafts a DES-0006 amendment establishing which verification
  item owns this comparison, and the plan's own stop condition says a ruling
  that sends it to `C-009` returns the plan to review. So accepting the plan
  authorizes work whose first act may invalidate the plan's scope. Drafting that
  amendment needs no implementation authority -- it is documentation work, which
  is allowed today with no active plan.
- Failure or cost if true: the owner is asked to accept a scope that the plan
  itself flags as possibly wrong, and the acceptance carries an implementation
  authorization that the first task might immediately suspend.
- Required response or experiment: settle the item-ownership question **before
  acceptance**, as a standalone amendment drafted now, and let PLN-0003 open at
  what is currently task 02.

**Ruled 2026-08-15 by Jason Tarasovic: no verification item owns it.** The
comparison is evidence for C-007's open question and for PLN-0002-13's threat 1,
and DES-0006 takes a **disposition at plan end** rather than a new item or a
clause on item 9. **Task 01 comes out of the plan**, which now opens at the
declaration. One consequence is outside any task's authority: PLN-0002-13's
threat 1 states that "DES-0006 verification item 9 already owns a representative
workload comparison", which this ruling makes false. That record is accepted, so
the correction joins the `fsck.erofs` correction already open for the owner.

### C-008: One workload shape cannot carry the conclusion

- Severity: medium
- Claim: the plan admits the workload is a fixture with no role contract behind
  it and calls its own mitigation weaker than having one. It then measures a
  single shape. A sequential read across all of `/usr` and a sparse
  exec-and-link pattern stress a compressed format in different ways -- one is
  throughput against decompression bandwidth, the other is latency against
  per-cluster decompression of small reads -- and EROFS could plausibly win one
  and lose the other.
- Failure or cost if true: whichever shape is chosen becomes "the workload" by
  being first, which is PR-0029 C-005's failure mode reappearing in the
  measurement rather than in the mechanism.
- Required response or experiment: declare at least two shapes with different
  read profiles, derived from what the artifact actually contains rather than
  invented, and require task 06 to report them separately. A disagreement
  between them is a result, not a problem.

**Ruled 2026-08-15 by Jason Tarasovic: two shapes.** A whole-`/usr` sequential
read for decompression bandwidth, and a sparse exec-and-link pattern for
per-cluster decompression latency on small reads. Both **derived from what the
artifact contains** rather than invented, declared as fixtures, and reported
separately. A disagreement between them is a result and not a problem to be
resolved by picking one.

### C-009: The plan produces C-002-relevant evidence and assigns it nowhere

- Severity: low
- Claim: the trace says no requirement is claimed, which is right, but memory
  behaviour under load at a constrained guest size is exactly the evidence a
  capacity budget needs, and `C-002` is open and named as an input. The plan
  disclaims SYS-056 and then routes the result to no one.
- Failure or cost if true: the measurement is taken once, filed under C-007, and
  re-taken later by whoever works `C-002`.
- Required response or experiment: name `C-002` as a recipient in task 06's
  disposition, without claiming a requirement or a budget.

**Ruled 2026-08-15 by Jason Tarasovic: route it to `C-002`, with the caveat
attached.** The disposition names `C-002` as a recipient of the
memory-under-load figures, and the pointer carries its scope limits inline --
one CPU class, a synthetic workload, no role contract -- so it cannot be cited
as budget input without them. No requirement, budget, or role is claimed.

### C-010: Exit criterion 7 is a tautology

- Severity: low
- Claim: "the artifacts are byte-unchanged at plan end, verified" is guaranteed
  by `snapshot=on`, which the boundary already mandates. It cannot fail in a way
  that indicates anything, and it reads as a safeguard.
- Failure or cost if true: a criterion that cannot fail crowds out the one that
  could -- that every boot verified the digest **before** use, which is what
  catches a corrupted or substituted retained artifact.
- Required response or experiment: restate it as pre-run verification against
  the retained digests, which is the check with content.

## What the plan gets right

- **It aims at the strongest argument against the accepted recommendation**
  rather than at something easier, and says so.
- **The no-rebuild boundary is correct and load-bearing.** Making the six
  artifacts inputs that are never outputs is what keeps PLN-0002's tally valid,
  and it is stated as a boundary rather than as an intention.
- **A null result is written in as a result**, with the explicit instruction not
  to search for a workload that separates the arms. That is the discipline this
  project has repeatedly needed.
- **The mount-option asymmetry is caught before measuring.** Noticing that
  `cache_strategy=readaround` is EROFS-only, and that a read comparison sits
  directly on top of it, is the kind of thing PLN-0002 found only after the
  first pass.
- **The declaration-before-measurement gate is inherited deliberately**, with
  the readahead and host-cache traps named from PLN-0002's own corrections.
- **It refuses to accept its own disposition**, and states that either sign is a
  real outcome.

## Revision verification, 2026-08-15

**All ten challenges were ruled by Jason Tarasovic on 2026-08-15**, each ruling
recorded inline above, and the plan was revised the same day to apply them.
Verified against the revision:

- **Two rulings changed the plan's shape**, not its wording. Task 01 -- the
  DES-0006 amendment -- is **gone** under C-007, and the plan now opens at the
  declaration; the boundary now permits **non-member artifacts** under C-003,
  with marking and destruction rules, while the six members stay untouched.
- **Two rulings were taken against this review's recommendation**, and both are
  recorded as accepted risk rather than as resolved. C-001 declines
  pre-registration: the plan's largest carried risk is now stated as such in its
  own risk table, and task 06 must say its weighing was done with the figures
  visible. C-004 declines a run-time abort in favour of a closing audit, which
  is only possible because task 02 now carries the obligation to **capture**
  observed parameters into the evidence.
- Task renumbering was checked. The old 02-07 are now 01-06, a new task 05
  carries the declaration audit, and no cross-reference points at a task number
  that moved -- the defect PR-0030's own revision introduced and had to fix.
- Exit criteria grew from nine to ten and now include the instrument-control
  gate, the audit, the pre-run digest verification C-010 asked for, and a
  criterion that no non-member artifact is retained or cited as a member.

**One challenge is not closed by any ruling and is not the plan's to close.**
PLN-0002-13's threat 1 states that DES-0006 verification item 9 owns this
comparison. The C-007 ruling makes that false, and the recommendation is an
accepted record, so the correction is the owner's -- alongside the `fsck.erofs`
correction PLN-0002-12 raised and PLN-0002-14 did not take.

## Disposition

**PLN-0003 accepted by Jason Tarasovic on 2026-08-15** with the revision above.
All ten challenges are dispositioned by that acceptance: eight by the revision,
and C-001 and C-004 by the owner rulings the revision records as accepted risk
rather than as resolved. The review is closed.

Two concerns are **not** closed by acceptance and carry forward as standing
risks on the plan:

- **C-001.** No reversal threshold is pre-registered, so the weighing happens
  with the figures visible. The plan's risk table carries it and task 06 must
  say so in the record.
- **C-008's residue.** Two workload shapes are better than one and neither has a
  role contract behind it. They become the reference by being first, which is
  PR-0029 C-005's failure mode in the measurement rather than the mechanism.

One item is outside the plan's authority entirely: PLN-0002-13's threat 1
misnames verification item 9 as owning this comparison, and correcting an
accepted record is the owner's.
