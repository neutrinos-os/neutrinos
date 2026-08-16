---
id: ADR-0006
title: Mark a slot durably ineligible before overwriting it, and stop selection at an attributable terminal state
status: proposed
date: 2026-08-16
deciders: [Jason Tarasovic]
designs: [DES-0006]
supersedes: []
superseded_by: []
---

# Mark a slot durably ineligible before overwriting it, and stop selection at an attributable terminal state

## Context

Both halves of this decision were raised on 2026-08-11 from
[RES-0014](../research/comparisons/embedded-ab-update-field-evidence.md), a
review of embedded A/B updater field practice, and neither was part of the
2026-08-09 adversarial review. They are recorded together because they are the
two ends of the same failure space: what the update path must guarantee before it
writes, and what the boot path must do when everything it can select has failed.

**[C-014](../designs/0006-storage-layout-and-encryption/review.md)**: the failure
table already required that interrupted staging leave inactive partial bytes
ineligible, but no step in the staging sequence produced that result. The
sequence chose an inactive slot pair and immediately wrote to it. On a first
update the guarantee holds for free, because the slot is empty. On a second
update that slot holds the previous **eligible** deployment — the retained
fallback — and the first byte written destroys it while its eligibility marker
still stands. Between that first byte and the verify, the retained fallback is a
partial image the selection mechanism still treats as a candidate, which
SYS-050 forbids and which reaches C-001's authenticated hybrid through ordinary
operation rather than an exotic interruption. RAUC's documented order is verify
the bundle, **mark the target slots non-bootable**, then write, for exactly this
reason.

**[C-015](../designs/0006-storage-layout-and-encryption/review.md)**: the design
carried only one branch of SYS-038's exhaustion clause. The requirement reads
"select an eligible normal fallback **or stop with an attributable diagnosis**",
and the stop was never designed. Two eligible deployments that both boot and both
fail assessment can alternate indefinitely, each with a fresh attempt counter —
powered, unattended, never converging. On the router that is the difference
between a diagnosable dead machine and one that looks alive over IPMI while
cycling. The loop is not impossible under immutability because **assessment is
not a function of the image**: it evaluates the machine in an environment that
moves, so the causes that matter are the ones *common to both slots* — an expired
certificate, a state schema migrated beyond what the older deployment can read,
PCR values changed by a firmware update, failing hardware, a health check that
depends on reaching something. Fallback only helps when the failure was caused by
the thing being fallen back from.

**Both ruled and accepted 2026-08-11.**

## Decision

### Ineligibility before overwrite

Mark the chosen slot pair **ineligible for selection, durably, before writing any
byte into it**. The previous occupant stops being a retained fallback at that
point rather than when it is overwritten.

**Durability is the load-bearing word**, and its target is ruled rather than left
to implementation. Three levels were put to the owner:

1. survives power loss;
2. survives power loss **plus an unreadable ESP**, which forbids ineligibility
   living solely as a filename on the filesystem holding the artifacts;
3. survives both **plus hostile offline modification**, meaning the marking is
   authenticated rather than merely present.

**Level 3 is the target, level 2 is the accepted fallback, and level 1 is
acceptable only with a recorded reason** for why level 2 was untenable. Ordering
matters: level 1 is the ESP-only marking that C-011 challenges as a shared
failure domain, so landing there must be a stated finding rather than a discovery
that it was easiest.

The mechanism is deferred to the substrate spike, which **owes an answer on level
3's feasibility rather than stopping at the first thing that works**.

### Terminal state for selection

Selection driven by exhaustion is itself durably counted, and a deployment
already selected by exhaustion that then failed assessment is not selected that
way again.

Response depends on whether the failing deployment has **ever passed** assessment.
A deployment that has never passed is unproven, and exhaustion selects an eligible
fallback. A deployment that has passed before **indicts the environment rather
than the image**, so at most one further attempt is made before stopping.

When no eligible normal deployment remains unselected, **automatic selection
stops. The machine does not halt.** The last deployment continues running,
degraded and reachable, and reports an attributable diagnosis naming each
deployment tried and its failure. **Recovery is not entered automatically**, as
SYS-038 requires, and the stop is a terminal state for selection only.

### Requirement effect

**None, for either half, and this must not be misread.** SYS-050 already forbids
C-014's outcome; the defect was the surviving eligibility marker, not the
overwrite, and SYS-050 permits overwriting a previous fallback with a new
candidate.

For C-015, **SYS-038 is read narrowly**: "every trial boot" governs each
deployment's own attempt accounting, and the cross-deployment loop falls outside
it. The terminal-state ladder is therefore a **design commitment beyond the
requirement floor**, adopted because the owner directed that the system be
designed for the broader behaviour. **It must not be cited as evidence of
satisfying SYS-038.**

## Alternatives considered

### Write first and rely on the verify step

Rejected. It is the behaviour C-014 found, and it leaves a window in which a
partial image carries a standing eligibility marker. The window is entered by
ordinary operation, not by an exotic interruption, so its probability is the
update rate rather than the fault rate.

### Ineligibility marking held only in memory

Rejected. It leaves the window unchanged across power loss, which is the failure
the marking exists to close.

### Automatic recovery entry when every deployment fails

Rejected. ChromeOS alone among the surveyed implementations enters recovery
automatically; SYS-038 forbids it, and an unattended router makes it untenable.
RES-0014 records five implementations converging on the same terminal state —
stop selecting, keep running, be loud — and **none of them halts the machine**.
greenboot stops rebooting and reports through logs, MOTD and `red.d` operator
scripts in the still-running system; MicroOS branches on whether the snapshot was
ever known-good; Android prompts rather than resetting unattended.

### A minimal notification image in the ESP

Raised by the owner as an aside and **not adopted**. It needs a credential to
notify, which puts authority in the least protected failure domain on the
machine.

## Consequences

### Benefits

- The retained fallback has a defined lifetime that ends at a marked point rather
  than at an ambiguous one during a write.
- An interrupted stage can no longer produce a slot marked eligible with foreign
  bytes in it.
- A machine that cannot converge becomes diagnosable rather than cycling, and
  stays reachable while it reports.
- The environment-versus-image distinction is designed in, so the system stops
  retrying a fallback that shares the cause.

### Costs and constraints

- Staging gains a durable write before the first data byte, which costs a
  synchronous operation on every update.
- Exhaustion-driven selection now needs its own durable counter, separate from
  per-deployment attempt counters.
- The design must carry two failure-table rows it did not have: interrupted
  ineligibility marking, and every eligible deployment failing assessment.
- Level 3 durability likely requires an authenticated marking mechanism that does
  not exist yet.

### Accepted risks

- **The mechanism for durable ineligibility is not chosen here**, and it
  interacts with the ESP failure domain raised in C-011 and RES-0014, since
  systemd-boot's counters live as filenames on the same FAT filesystem as the
  artifacts they select.
- Level 3 additionally interacts with whether the bootloader's own attempt
  counters are trustworthy, which is a larger question than staging order and is
  deliberately not opened here.
- A terminal state that keeps running degraded is a state an operator can ignore
  for a long time; loudness is a design obligation, not a side effect.
- The "has ever passed" test requires durable per-deployment assessment history,
  which is additional state in the machine-state volume
  ([ADR-0005](0005-volume-boundaries-by-policy-difference.md)).

## Validation and review triggers

The substrate spike owes a measured answer on level 3 feasibility, not a
first-thing-that-works result. RES-0014 proposed five failure-matrix cells that
DES-0006's verification list did not cover; the two most directly owned by this
ADR are interrupting a write to the inactive slot **after** the previous
deployment has been partially overwritten, and forcing both slots to boot and
fail assessment to confirm a bounded, attributable dead end.

Revisit this decision when:

- level 3 durability proves infeasible and the recorded reason for landing at
  level 2 or level 1 must be stated;
- the bootloader's own attempt counters are shown untrustworthy, which would
  widen this beyond staging order;
- a measured terminal state is reached in operation and the diagnosis proves not
  to be attributable in practice; or
- SYS-038 is ever re-read broadly, which would convert the ladder from a design
  commitment into a requirement obligation and change what evidence it owes.
