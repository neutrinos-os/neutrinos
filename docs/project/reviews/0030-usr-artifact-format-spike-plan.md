---
id: PR-0030
subject: Authenticated `/usr` artifact format comparison plan
plan: PLN-0002
reviewer: Claude adversarial pass
date: 2026-08-11
status: open
---

# Authenticated `/usr` artifact format comparison plan review

## Decision scope

This review examines [PLN-0002](../../plans/0002-usr-artifact-format-spike.md):
its outcome, non-goals, boundary, requirement trace, task decomposition,
comparison method, and exit criteria. It rules on nothing. Every challenge
below is open for the owner.

## Summary judgment

**Not fit to accept as written.** The plan's stated purpose is to answer
DES-0006 C-007, and its method cannot: two of verification item 2's eight named
criteria have no task at all, a third is unilaterally removed from the
comparison, and the free parameters that actually decide image size, memory,
and update transfer size between EROFS and ext4 are nowhere declared, so
whoever runs task 02 picks the winner. Separately, task 04 makes a partition
layout, a persistence decision DES-0006 records as open, and a `/var` placement
that contradicts the accepted C-008 ruling, all under the word "fixture", and
SYS-049 is marked demonstrated on a substitution test that is not the one
SYS-049 asks for. The bones are good — the boundary, the failure-is-a-result
stance, and the refusal to accept its own recommendation are right — but the
measurement design and the trace both need work before this authorizes source.

## Challenges

### C-001: Two of the eight criteria that define "done" have no task

- Severity: critical
- Claim: DES-0006 verification item 2 names the comparison criteria as image
  size, build time and determinism, boot behavior, memory, update transfer
  size, inspectability, **corruption behavior, and recovery behavior**. Task 03
  covers size, build time, determinism, update transfer, inspectability; task
  08 covers boot behavior and memory. **No task measures corruption behavior
  and no task measures recovery behavior.** Task 07 injects substitution, which
  is an authorization test, not a corruption test: a substituted `/usr` fails
  the root-hash gate at mount, while an in-place bit flip inside an already
  authenticated artifact fails at read time, and the blast radius differs by
  format — EROFS's compressed clusters versus ext4's blocks are exactly where
  the two formats are expected to diverge. Item 2's early-boot element also
  names `fstab` and `crypttab`, and the plan excludes encryption "of any kind",
  so no `crypttab` exists to exercise.
- Failure or cost if true: exit criterion 2 is unreachable by construction, the
  plan completes with six of eight criteria and hands the owner a
  recommendation that C-007 does not license, and EROFS is selected by having
  been measured on the criteria that favor it — the precise failure C-007 was
  written to prevent.
- Required response or experiment: add a task that injects single-bit
  corruption into an authenticated region of each artifact and records
  detection point, diagnostic, and failure blast radius per format; add a task
  or an explicit deferral with rationale for recovery behavior; state what is
  done about `crypttab` given the encryption non-goal. If a criterion is
  deliberately deferred, that is a proposed amendment to verification item 2
  and belongs to the owner, not to a task list.

### C-002: The plan deletes an accepted criterion by calling it a non-goal

- Severity: critical
- Claim: verification item 2 names "build time **and determinism**" as a
  comparison criterion. PLN-0002's first non-goal removes determinism from the
  comparison and demotes it to a side report. The citation supporting this is
  misapplied: C-013 said release reproducibility is a consequence of the
  `/usr` **scope** decision and never a reason **for that decision**. It said
  nothing about the format comparison, where determinism is a directly relevant
  property of the two `mkfs` tools and is a criterion the owner accepted.
- Failure or cost if true: a plan has narrowed a design's accepted definition of
  done. If EROFS reproduces and ext4 does not — plausible, given PLN-0001
  measured `mkfs.btrfs` unreproducible for reasons unreachable from
  configuration — the plan is committed in advance to not counting the one
  criterion the difference showed up on. That is the mirror image of the bias
  the non-goal claims to prevent.
- Required response or experiment: restore determinism as a comparison
  criterion, or take the removal to the owner as an explicit amendment to
  verification item 2 with the reason stated. Note the asymmetry either way:
  excluding a criterion that one arm wins is not neutral.

### C-003: The two arms are not comparable, and the plan does not say what makes them equal

- Severity: critical
- Claim: "both artifacts come from one identical closure and one harness" is
  not sufficient and is not even achievable. Every number in task 03 and task
  08 is dominated by parameters the plan never declares: `mkfs.erofs`
  compression algorithm and level (`-z lz4hc:12` versus none changes image size
  and update transfer size by a large multiple and changes memory materially),
  EROFS cluster size, ext4 block size, inode ratio, reserved-block percentage
  and feature set, and the dm-verity hash block size and salt on both arms.
  Worse, the arms cannot share an initrd: each needs its own filesystem driver
  and the EROFS arm needs `erofs-utils` on the build side, so either the UKIs
  differ — and boot time and memory then measure the initrd as much as the
  format — or both drivers ship in both arms and neither artifact is the one
  that would ship.
- Failure or cost if true: task 08 produces a number that reads as an answer and
  is actually a record of one engineer's `mkfs` flags. C-007's residual risk
  ("measurements may be platform- and package-set-specific") understates it:
  the result is not even configuration-specific, it is unattributable.
- Required response or experiment: before task 02, declare the full parameter
  set for both arms and the rule that justifies each pairing (default-versus-
  default? tuned-versus-tuned? at what compression?), declare how the initrd
  asymmetry is handled and which arm it advantages, and state the repetition
  count and accelerator state for every timed and memory measurement — PLN-0001
  measured the same boot at 72s under TCG and 18s under KVM.

### C-004: SYS-049 is marked demonstrated on a substitution that SYS-049 does not ask for

- Severity: critical
- Claim: SYS-049 requires that "independently valid substituted release-owned
  members must fail the boot-integrity gate", with an evidence column naming a
  "UKI, root, Verity, configuration, manifest, and slot-substitution matrix on
  VM and physical roles", and C-001 binds this to a cross product rather than a
  sample. The plan's evidence is "a substituted `/usr` from the other format's
  build failing the gate". That substitute is not an independently valid
  release-owned member of the same kind: it is a different filesystem format,
  and it can fail for mount reasons before the root hash is ever consulted, so
  a pass proves nothing about the binding. The plan builds **one slot per
  format**, so no same-format second deployment exists to substitute from. The
  confext — now a release-owned deployment-set member under C-013 — is never
  substituted, and neither is the manifest.
- Failure or cost if true: SYS-049 is recorded as demonstrated on a test that
  cannot distinguish "the binding worked" from "the kernel could not mount an
  ext4 superblock as EROFS". PLN-0001 already produced one fault that "passed"
  for a reason it never stated (F-RES-01); this repeats that shape on the
  requirement PLN-0001 explicitly deferred here.
- Required response or experiment: build a second same-format deployment per
  arm so a genuinely valid member can be substituted, add confext and manifest
  substitution, and state which cells of C-001's cross product this plan covers
  and which carry forward. Alternatively mark SYS-049 **partial** with the
  covered cells named — but do not mark it demonstrated on the current test.

### C-005: Task 04 decides `S-004`, decides an open partition-count question, and contradicts an accepted ruling

- Severity: critical
- Claim: task 04 builds "ESP, one `/usr` slot, one Verity slot, a writable root
  partition, one confext" from `systemd-repart` definitions and calls it a
  fixture. Three problems. (a) That is a partition layout: it is DES-0006
  verification item 1 performed without being claimed, and it will be the only
  executed layout in the repository, which is how `S-004` gets settled by
  repetition — PR-0029 C-005's named failure mode. (b) DES-0006 records as
  **open** whether the root partition needs to persist at all, and explicitly
  says deciding it "changes the partition count, so it is a decision, not a
  detail". Task 04 decides it, in the direction of persistence, as a fixture.
  (c) The plan says it "holds `/var` in the fixture" on the root partition.
  C-008 was **accepted on 2026-08-11**: `/var` belongs to the machine-state
  volume. The fixture contradicts an accepted ruling, and every boot-behavior
  and memory number in task 08 is then measured against a layout the design has
  already ruled out.
- Failure or cost if true: the comparison's substrate is wrong, the numbers do
  not transfer to the layout that will actually ship, and two open decisions
  acquire a de facto answer with an artifact and no ADR behind it.
- Required response or experiment: either build the tmpfs root-partition
  variant as the fixture — which is closer to the accepted rulings and cheaper
  — or record explicitly that the fixture violates the accepted C-008
  disposition, why that is acceptable for a format comparison, and what
  measurement it invalidates. Add a task that states the layout's fixture
  status in the register at the moment it is created, not afterwards.

### C-006: The confext is not a fixture, and building one needs work DES-0005 left unowned

- Severity: high
- Claim: the trace marks SYS-123 "not applicable" because "the single confext is
  a boot fixture, not a lifecycle demonstration". C-013 ruled the opposite:
  every confext is a release-owned artifact inheriting SYS-123 in full, and the
  plan itself must produce a dm-verity-signed confext verified under
  `image_policy_confext_strict` with `Mutable=disabled`, with a valid
  `extension-release.d` base level, in order to boot at all. Building it
  requires two things DES-0005's amendment explicitly left unsettled and
  assigned elsewhere: **confext build tooling** (handed to the ADR-0003 spike)
  and **the actual path carve** (which the amendment says "nobody has drawn").
- Failure or cost if true: the plan invents the confext build path and the first
  path carve as a side effect of getting a VM to boot, and the first executed
  instance of both becomes the reference. SYS-123's content-identity,
  authorization, base-compatibility and activation-ordering obligations are
  exercised in fact while recorded as not applicable, so a failure in them has
  nowhere to be attributed.
- Required response or experiment: reclassify SYS-123 as partial with the
  obligations this plan actually touches named, and either state that confext
  tooling and the path carve are inputs this plan does not have — making the
  plan blocked on DES-0005 — or add an explicit task that produces them, marks
  them candidate, and hands them back to DES-0005/ADR-0003.

### C-007: Task 06 is a precondition of task 05, not its successor

- Severity: high
- Claim: task 06 examines "what is consumed before `/usr` is verified" and
  whether `systemd-confext-initrd`/`systemd-confext-sysroot` behave as C-013
  assumed, and depends on 05. But the initrd stage runs **before** the boot
  task 05 records. You cannot have a clean boot record from 05 unless the early
  stage 06 investigates already worked. The dependency is inverted. Compounding
  this, the plan itself names 06 as "the most likely place the design is
  wrong", and its blocking input C-013 lists early boot as its sole residual
  risk — yet 06 is scheduled sixth, after the composition split, both builds,
  all offline measurements, and the layout.
- Failure or cost if true: if 06 falsifies C-013's early-boot assumption, the
  fix changes the initrd or the composition, which invalidates every task 03
  measurement and both task 05 boot records; the plan pays for tasks 01-05
  twice. If instead 06 is merely a write-up of what 05 already had to make
  work, it is not an experiment at all.
- Required response or experiment: move the early-boot exercise to the front as
  a minimal spike on one format only, before the comparison is built, and
  reorder the dependency so 05 depends on it. Say explicitly what task 06 does
  that task 05 did not already have to do.

### C-008: No task registers a check, and the `/usr` split breaks the five existing ones

- Severity: high
- Claim: PLN-0001 spent a whole task (05) registering `T2/T3/T4-SLICE-*` in the
  canonical runner precisely because hand-made claims are not evidence, and the
  validation contract requires slice tests to register there. PLN-0002 has no
  such task. Every artefact it produces — digests of four objects, the boot
  record, the negative results, the measurements — is a hand-made claim.
  Worse, task 01 changes the artifact shape underneath tests that assume the
  flattened disk image: `T3-SLICE-001` binds the UKI on the ESP of a composed
  disk image, `T3-SLICE-002` attributes NEVRAs in the shipped closure,
  `T4-SLICE-001` boots the literal artifact. Nothing in the plan updates them,
  and the trace simultaneously asserts that the inherited SYS-018/041/059
  mechanisms "must keep passing".
- Failure or cost if true: `check:fast`/`check:complete` go red or, worse, keep
  passing against an artifact they no longer describe — F-RES-01's shape again.
  The trace's "must keep passing" claim has no check behind it.
- Required response or experiment: add a task that updates the five registered
  tests for the `/usr` artifact and registers new checks for the claims this
  plan makes (root-hash-to-UKI binding, read-only `/usr`, nothing durable in
  `/etc`), and verifies each is failure-sensitive as PLN-0001-05 did.

### C-009: "A failed boot is a result" is asserted, not engineered

- Severity: high
- Claim: the plan says both formats failing is a publishable outcome, but
  nothing is structured to produce attributable evidence from a failure. No
  task names the instrumentation: how the journal is recovered when the machine
  never reaches userspace (PLN-0001 had to pull it offline from a disk copy),
  what serial/console path exists given the composition amendments were
  reverted, whether notify-vsock readiness applies when the failure is
  pre-`/usr`, or what distinguishes "EROFS driver missing" from "root hash
  mismatch" from "confext refused" in the captured record. Task 08 additionally
  depends on 03, 05, 06 and 07 all producing values; if 05 yields nothing, task
  08 has no boot-behavior or memory numbers, exit criterion 2 falls to "a
  recorded reason", and exit criterion 5 still demands a recommendation.
- Failure or cost if true: the plan's most likely outcome — an early-boot
  failure — produces a note saying it did not boot, which sends C-007 back to
  DES-0006 with no more information than it started with.
- Required response or experiment: name the failure-capture path per task
  before starting, as PLN-0001-06 did for injected faults, and state what task
  08 produces when 05 has no values.

### C-010: The requirement trace is not honest in three places

- Severity: medium
- Claim: (a) SYS-030 is listed **partial** here, having been "Not applicable to
  G1" in PLN-0001 for the correct reason: the requirement binds "normal boot on
  a production physical role", and a VM with a synthetic anchor is not a
  partial instance of that, it is a different thing. Upgrading the
  classification without new evidence is drift toward a G2 claim. (b) SYS-020 is
  absent from the trace, yet task 05 measures its exact subject — `/etc`
  regenerated from identified inputs and nothing durable found there — and
  C-013 claims to satisfy SYS-020 "by construction"; a plan that measures a
  requirement's claim should trace it. SYS-048 is likewise engaged by task
  04's region ownership and absent. (c) "SYS-051 through SYS-056: not
  applicable — no encryption, capacity, or recovery claim in scope" collapses
  six requirements into one dismissal while the plan builds an unencrypted
  writable root partition holding `/var` and a journal, which is precisely the
  plaintext-spill mapping SYS-051 governs.
- Failure or cost if true: the trace understates what the plan touches and
  overstates what it demonstrates, which is the defect PLN-0001's downgrades
  were accepted to correct.
- Required response or experiment: restore SYS-030 to not-applicable or justify
  partial with evidence; add SYS-020 and SYS-048 rows; split SYS-051 out of the
  group with a stated reason.

### C-011: Synthetic key lifecycle makes the negative tests ambiguous

- Severity: medium
- Claim: the cleanup section says synthetic keys are "destroyed at task end",
  but the UKI signing key created in task 02 must still exist in task 07 to
  distinguish a substitution failure from a signature failure, and the negative
  tests need a *second*, wrong key to prove the gate discriminates. The plan
  names neither the key's lifetime across tasks nor the wrong-key case.
- Failure or cost if true: task 07's diagnostics cannot separate "root hash did
  not match" from "UKI signature did not verify" from "key was regenerated
  between tasks", and a fail-closed result gets attributed to the wrong
  mechanism.
- Required response or experiment: state key lifetime per artifact across the
  task graph, add a wrong-but-valid-signature case to task 07, and record the
  discriminating diagnostic for each injected fault.

### C-012: The frontmatter claims G2 while the decision section disclaims it

- Severity: low
- Claim: `gate: G2` sits above a Decision section stating "No new gate is
  required, and none is claimed" and that acceptance "would not authorize G2".
  Current context prohibits "any work reaching for G2 qualification claims"
  and the current gate is G1. PLN-0001 carried `gate: G1`, the gate it executed
  under.
- Failure or cost if true: a reader scanning frontmatter records the plan as G2
  work, which is what the prose spends a paragraph denying.
- Required response or experiment: set the field to the gate the work executes
  under, or define what the field means when a plan produces evidence *for* a
  later gate.

## What the plan gets right

- The mutation boundary inherits rather than restates PLN-0000's, keeps one
  authority, and adds the R-054 router reasoning explicitly.
- Task 08's "**the drafter does not accept it**" and exit criterion 5 keep the
  C-007 recommendation with the owner, which is the rule most easily lost in a
  plan whose output is a recommendation.
- Treating a falsification of C-013 as the point of task 06 — "it does not get
  worked around" — is the correct disposition for an accepted amendment's
  stated residual risk.
- Discarding partial artifacts as "exactly the hybrid C-001 warns about" is a
  precise reuse of a design challenge as an operational rule.
- The risk table names the implementation-accident risk against itself rather
  than only against fixtures, which is the right instinct even though C-003
  argues the stated mitigation does not achieve it.
