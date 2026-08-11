---
id: PLN-0002
title: Authenticated `/usr` artifact format comparison
status: proposed
owner: Jason Tarasovic
created: 2026-08-11
last_updated: 2026-08-11
gate: G2
depends_on: [PLN-0001]
---

# Authenticated `/usr` artifact format comparison

## Outcome

Answer DES-0006 C-007 with measurement: build the same package closure as an
EROFS `/usr` artifact and an ext4 `/usr` artifact, authenticate each through
dm-verity and a root hash carried by a signed UKI, boot each in a disposable
VM, and compare them on the criteria verification item 2 names.

The claim this supports is narrow: **one of the two formats is a better
`/usr` artifact for NeutrinOS, and the record says why in measured terms.**
Reaching that measurement requires the `/usr`-only boot path C-013 accepted, so
this plan also produces the first evidence that the path boots at all -- which
is the SYS-049 demonstration PLN-0001 could not make and the owner deferred to
G2 on 2026-08-10.

Nothing here selects a package ecosystem, a partition layout, a state
filesystem, or an updater.

## Non-goals

- **Reproducibility as a selection criterion.** C-013 recorded that release
  reproducibility becomes reachable with a pinned `mkfs.erofs` and that this is
  a consequence of the decision and **never a reason for it**. Reproducibility
  is measured and reported here because it is cheap to measure; it does not
  enter the comparison, and a finding that only one format reproduces does not
  by itself decide C-007.
- A/B slots, staging, finalization ordering, or slot substitution. Those are
  verification items 3 and 4 and belong to a later plan; this plan builds one
  slot per format.
- Encryption, LUKS2, TPM policy, or unlock behavior of any kind.
- Capacity falsification, the minimum viable device, or the C-002 formula.
- The DES-0005 confext lifecycle. Verification items 11-19 -- disjointness,
  order-invariance, required/optional policy, reference-counted retention --
  are a separate plan. One confext appears here only as a boot fixture.
- Any physical-host effect, on `desktop-jason`, `router`, `misc`, or otherwise.
- Production signing, Secure Boot enrollment, or any real trust anchor.
- Performance tuning of either format. Measurement, not optimization.

## Mutation and authority boundary

This plan inherits PLN-0000's boundary unchanged and narrows it as follows. It
does not create new authority.

May read and change:

- repository paths under `src/`, `tools/`, and `docs/`;
- build caches and artifacts in declared locations outside the checkout;
- disposable VM disks, firmware variables, vTPM state, and an isolated test
  network; and
- synthetic signing and credential fixtures generated for this plan and
  destroyed with it.

Must not, and no task may request an exception:

- touch any physical host beyond read-only inspection separately authorized by
  a task;
- use or create production Secure Boot, enrollment, recovery, or credential
  keys;
- enroll any key into physical firmware; or
- publish or roll an artifact to any machine.

The router is specifically out of reach. R-054 records that the development
workstation reaches the network through it, so a mistake there strands the
operator.

## Inputs and dependencies

| Input or dependency | Identity/status | Blocking behavior |
| --- | --- | --- |
| DES-0006 C-013 | Accepted 2026-08-11: authenticated artifact is `/usr` | Fixes the artifact scope this plan measures; a reopening stops the plan |
| DES-0006 C-007 | Open; the question this plan answers | Its criteria define the comparison |
| DES-0006 verification item 2 | Amended 2026-08-11 to carry comparison criteria | Defines done |
| DES-0005 confext amendment | Accepted 2026-08-11 | Constrains the boot fixture; its own verification is out of scope |
| PLN-0001 slice | Complete; declared Fedora 44 closure, `compose.sh`, retention, runner | Reused as the input and harness base; a broken reuse stops for review |
| SYS-049 | Accepted; owner-deferred to G2 on 2026-08-10 | This plan is where it becomes demonstrable |
| `S-004` layout, `C-009` state filesystem | Open | Fixtures only; no task may treat a fixture as a selection |
| mkosi v26, Fedora 44 | Candidate fixtures | Remain candidates; using them accepts nothing |

## Decision and requirement trace

| ID | Applicability | Planned evidence |
| --- | --- | --- |
| SYS-049 | Demonstrated for the authenticated half, both formats | Signed UKI carrying a root hash that authenticates the exact `/usr` and Verity pair; a substituted `/usr` from the other format's build failing the gate |
| SYS-030 | Partial | Boot chain authenticates the artifact from a **synthetic** anchor. No production trust anchor exists, so the requirement's "configured platform trust anchor" is simulated and this stays partial through G2 |
| SYS-018, SYS-041, SYS-059 | Inherited partial from PLN-0001 | Not re-litigated here; the retention and attribution mechanisms are reused unchanged and must keep passing |
| SYS-123 | Not applicable | The single confext is a boot fixture, not a lifecycle demonstration |
| SYS-051 through SYS-056 | Not applicable | No encryption, capacity, or recovery claim in scope |

Candidate mechanisms used here remain candidates unless a separate ADR accepts
them. EROFS winning this comparison does not accept EROFS; it produces the
evidence an ADR would need.

## Work

| Task | Status | Depends on | Output/evidence | Next action |
| --- | --- | --- | --- | --- |
| PLN-0002-01 | pending | — | `/usr`-only composition: the PLN-0001 closure split into a `/usr` artifact plus release-owned defaults in `/usr/lib`, with the declaration and retention mechanisms intact | Extend `compose.sh` to emit a `/usr` tree and record what moved out of the flattened root |
| PLN-0002-02 | pending | 01 | Two authenticated artifacts: EROFS+dm-verity and ext4+dm-verity, each with its Verity pair and a synthetically signed UKI carrying its root hash | Build both from the identical closure; retain digests for all four objects |
| PLN-0002-03 | pending | 02 | Offline measurements: image size, build wall time, build determinism, update transfer size, inspectability of each format without booting | Measure and record; report reproducibility separately from the comparison |
| PLN-0002-04 | pending | 02 | Disposable VM layout: ESP, one `/usr` slot, one Verity slot, a writable root partition, one confext | Build the layout with `systemd-repart` definitions; declare the root-partition filesystem a fixture, not a C-009 selection |
| PLN-0002-05 | pending | 04 | Boot record for both formats: `/etc` regenerated by `systemd-tmpfiles` and `systemd-sysusers`, `/usr` mounted read-only and verity-authenticated, no failed units | Boot each artifact; capture whether anything durable appears in `/etc` |
| PLN-0002-06 | pending | 05 | Early-boot evidence: what is consumed before `/usr` is verified, and whether `systemd-confext-initrd`/`systemd-confext-sysroot` behave as C-013 assumed | Exercise the initrd stage deliberately; this is C-013's stated residual risk and the most likely place the design is wrong |
| PLN-0002-07 | pending | 05 | Negative evidence: a substituted `/usr`, a substituted Verity tree, and a mismatched root hash each failing closed with an attributable diagnostic | Inject each; record verbatim diagnostics as PLN-0001-06 did |
| PLN-0002-08 | pending | 03, 05, 06, 07 | Boot-behavior and memory measurements completing verification item 2's criteria, and a C-007 recommendation with its evidence | Draft the recommendation; **the drafter does not accept it** |
| PLN-0002-09 | pending | 08 | Retained evidence bundle, updated requirement trace, work register, and DES-0006 disposition | Assemble as PLN-0001-08 did |

## Failure, interruption, and cleanup

Stop and return to review if: the `/usr`-only split cannot preserve PLN-0001's
declaration and attribution guarantees; either format cannot be authenticated
through a signed UKI with available tooling; early boot requires content that
cannot be brought inside the integrity boundary; or a task finds itself needing
a mechanism selection that `S-004` or `C-009` has not made.

A failed boot is a result, not an interruption. Both formats failing is a
publishable outcome that sends C-007 back to DES-0006 with evidence rather than
an answer.

All VM disks, firmware variables, vTPM state, and synthetic keys are destroyed
at task end. Synthetic signing material never leaves the plan's scratch
location and is never enrolled anywhere. Evidence is retained outside the
repository with one SHA-256 per file, as PLN-0001-08 established, and scanned
for unsafe output before retention.

Partial artifacts are discarded rather than reused: a half-built `/usr` from an
interrupted task is exactly the hybrid C-001 warns about, and no measurement may
be taken from one.

## Risks and unknowns

| Risk or unknown | Effect | Disposition |
| --- | --- | --- |
| mkosi may not support a `/usr`-only artifact with Verity as directly as the flattened root it built in PLN-0001 | Task 01/02 cost, possibly a different composition path | Test early; if the fixture cannot express it, stop for review rather than hand-rolling a second composition path |
| EROFS tooling determinism is unproven here | Reproducibility measurement may be inconclusive | Non-blocking by construction: reproducibility is explicitly outside the comparison |
| The root-partition filesystem is unselected (`C-009` deferred, three-way) | A fixture choice could look like a selection | Declared a fixture in task 04 and in the register; C-008's ruling puts `/var` in the machine-state volume, but this plan builds no state volume and holds `/var` in the fixture |
| Early boot is C-013's stated weak point | Task 06 may falsify part of the accepted amendment | That is the point of running it. A falsification returns to DES-0006 review, it does not get worked around |
| Synthetic anchor keeps SYS-030 partial | G2 cannot claim the full boot-integrity requirement | Accepted and recorded in the trace, not hidden |
| The comparison could be decided by an implementation accident rather than by the formats | Wrong answer to C-007, which is the failure C-007 itself predicts | Both artifacts come from one identical closure and one harness; any asymmetry in handling is recorded as a threat to the finding |

## Exit criteria

1. Every task is satisfied, cancelled with rationale, or moved to a linked plan.
2. Verification item 2's criteria each have a measured value for both formats,
   or a recorded reason the measurement could not be made.
3. SYS-049's authenticated half has retained positive and negative evidence.
4. Early-boot behavior is recorded as observed, including anything consumed
   before `/usr` is verified.
5. A C-007 recommendation exists with its evidence, and is **open for owner
   decision rather than accepted by the plan**.
6. Native diagnostics and failure evidence are retained.
7. The work register, DES-0006, and affected records are updated together.
8. Remaining unknowns are linked and assigned to a later gate or plan.

## Decision

Open for owner review.

Accepting this plan would authorize NeutrinOS source work again, bounded to the
scope above, on the same basis PLN-0001 had: G1 is satisfied and PLN-0000's
mutation boundary requires G1 plus an accepted follow-on plan. No new gate is
required, and none is claimed.

It would **not** authorize: G2, any physical-host effect, any production key or
enrollment, an ADR accepting EROFS or ext4, a partition layout, a state
filesystem, or a package ecosystem. It would not settle `S-004`, `C-009`, or
`C-002`, and completing it would not by itself satisfy SYS-030.
