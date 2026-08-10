---
id: PR-0028
subject: Continuous-integration evidence for PRE-017
reviewer: Claude implementation pass
date: 2026-08-10
status: accepted
---

# Continuous-integration evidence review

## Decision scope

This review examines the evidence PRE-017 was missing: an executed pinned,
least-privilege CI job running the canonical profiles. It covers the workflow,
the four defects the first runs exposed, and the remote repository settings
that had to change for the job to run at all.

It does not accept NeutrinOS source implementation, does not satisfy PRE-018 or
G1, and accepts no change to the validation execution contract.

## Summary judgment

The workflow runs and both canonical profiles pass on a hosted runner at
`d0a2cc5`, with the checkout unmodified. The remote's history was replaced and
its branch policy migrated from legacy protection to a ruleset.

The evidence is real but thin in one specific way: it is a single green run
preceded by four consecutive failures, every one of which was a defect in this
repository rather than in the runner. That is the honest shape of a first CI
run, and it is also the argument for not treating one green result as proof
that local and remote execution are equivalent.

## Challenges

### C-001: One green run is weak evidence for a job that failed four times

- Severity: medium
- Claim: PRE-017 asks for a passing CI job. It has one, on one commit, after
  four failures. Nothing establishes that the run is repeatable, that it is not
  order- or cache-dependent, or that a second push would pass.
- Response: accurate. The four failures were diagnosed to distinct causes and
  each fix was verified by a subsequent run, so the sequence is evidence of
  convergence rather than of flakiness. But repeatability across independent
  runs has not been measured, and the runner's caches were warm from the same
  job's bootstrap in every case.
- Disposition: accepted as first-run evidence, not as stability evidence.
- Residual risk: the first unrelated push is also the first repeatability test.
  A failure there is a defect in this evidence, not a regression.

### C-002: Local and CI execution were claimed equivalent and were not

- Severity: high
- Claim: PRE-017's design argument was that betterleaks in `mise.lock` gives
  local and CI a single definition of the checks. `T5-VAL-003` then failed only
  in CI because the clean clone's `PATH` was built from git's directory plus
  `/usr/bin` and `/bin`, and resolved mise only because a workstation happens to
  install it into `/usr/bin`. The check passed locally for a reason unrelated to
  what it tests.
- Response: real defect, now fixed by resolving mise the way git already was.
  The equivalence claim was about tool identity, which held: every tool was the
  locked one. What did not hold was environment construction, which no lockfile
  governs.
- Disposition: accepted, with the claim narrowed.
- Residual risk: the same class of defect can exist anywhere a check resolves an
  executable from `PATH` rather than from a declared input. `T5-VAL-002` still
  does exactly this. One accidental dependency was found by running in a second
  environment; there is no reason to believe it was the only one.

### C-003: Failure diagnostics print run-directory contents into a public log

- Severity: medium
- Claim: the repository is public. The new reporting step prints per-check
  stderr into a world-readable CI log, which is a disclosure path that did not
  previously exist.
- Response: the files it reads are the same ones `test_output_paths` submits to
  the output-safety scanner, so unsafe content is quarantined before the
  reporter can see it, and the reporter classifies nothing and reads nothing
  else. It runs only on failure.
- Disposition: accepted.
- Residual risk: output safety detects the synthetic canary and credential
  markers, not arbitrary sensitive content. A check that printed something
  sensitive but unmarked would now publish it. The bound is the scanner's rule
  set, not the reporter.

### C-004: The remote's history was replaced by force

- Severity: medium
- Claim: `main` was force-pushed from `cf88a75` to `ec4e346`, discarding six
  2022 commits, and this is irreversible from the remote's point of view.
- Response: intended and owner-directed. The discarded commits survive in the
  `bak.neutrinos` checkout, which was explicitly preserved, and remain reachable
  on GitHub through `refs/pull/1` to `refs/pull/6`, which cannot be deleted.
- Disposition: accepted.
- Residual risk: those pull-request refs mean the old tree is still fetchable
  from the remote and still scannable by anyone. `T0-SEC-001` scans the local
  clone's reachable history and does not see them.

### C-005: Branch policy was rewritten while the branch was unprotected

- Severity: medium
- Claim: protection was removed entirely to permit the force push, and the
  repository sat with no branch policy for the duration of the CI debugging
  loop, during which five pushes landed on `main` unchecked.
- Response: accurate. The window was deliberate and the pushes were the ones
  being debugged. Policy is now stricter than before: the two required contexts
  it enforced had not existed since 2022 and could never report, so the previous
  configuration blocked every push while proving nothing.
- Disposition: accepted as a bounded and closed window.
- Residual risk: the replacement is a ruleset with an empty bypass list rather
  than a legacy `enforce_admins` flag. Adding any bypass actor later reopens
  admin bypass with no separate toggle to notice.

### C-006: CI still cannot exercise the cold-cache path

- Severity: low
- Claim: PR-0026 C-004 recorded that CI's bootstrap warms the uv cache, so the
  declared-cache failure path is never taken. Executing the job confirms this
  rather than resolving it.
- Response: unchanged and carried forward.
- Disposition: deferred to the same owner decision as PR-0026 C-003 and C-005.
- Residual risk: unchanged.

## Probe observations

- Run `31418770417` at `d0a2cc5`: `canonical profiles` succeeded, fast and
  complete both `passing=6 failing=0`, checkout asserted unmodified.
- The four preceding runs failed for distinct causes: uv unresolved in
  bootstrap; no per-check reason escaping the runner; two failure messages
  carrying no evidence; the clean clone's `PATH`.
- The second of those is the reason the others were diagnosable at all. Before
  it, a failing profile reported only `passing=5 failing=1`.
- betterleaks bootstrap reported `✓ Cosign verified` on the runner, and uv
  reported verified GitHub artifact attestations.
- The effective ruleset on `main` is `deletion`, `non_fast_forward`,
  `required_linear_history`, `required_signatures`, and
  `required_status_checks` against `canonical profiles`.

## Required confirmations

- One green run is first-run evidence. Repeatability is untested.
- Tool identity is locked; environment construction is not, and C-002 is a
  class of defect rather than a single fixed instance.
- The public CI log is a new disclosure surface bounded by the scanner's rules.
- The six discarded commits remain reachable on the remote through pull-request
  refs and are outside `T0-SEC-001`'s reach.

## Owner decision

Accepted by Jason Tarasovic on 2026-08-10. PRE-017 is satisfied. C-002's
residual class, C-003, and C-006 remain open; C-006 joins the deferred set
already carried by PR-0026 C-003 and C-005.

## Post-acceptance evidence

Recorded 2026-08-10 after acceptance. This section adds observations; it does
not revise any challenge or disposition above, which stand as accepted.

- **C-001 is closed.** Repeatability was measured at `6ec625a`, a different
  commit on a cold runner. Run `31420905770` (`workflow_dispatch`) and run
  `31421167463` (`pull_request`) both passed on the first attempt with no
  intervening fix, fast `passing=5 failing=0` and complete `passing=6
  failing=0`, betterleaks `✓ Cosign verified`, checkout unmodified. Two
  independent green runs at a second revision satisfy what C-001 asked for.
- **C-002's declared-`PATH` fix was exercised in CI**, since `T5-VAL-002` and
  `T5-VAL-003` pass at `6ec625a` under the per-executable construction. The
  residual class remains open: the fix covers the two known instances, not the
  general rule that a check must resolve executables from declared inputs.
- **New finding: the required status check deadlocks direct pushes to `main`.**
  `canonical profiles` triggers only on `push` to `main` and `pull_request`
  targeting `main`. A direct push is rejected with `GH013` because the check
  cannot report on a commit that has not landed, and the commit cannot land
  until it reports. The ruleset therefore made `main` pull-request-only in
  effect, which no record stated and which contradicts this review's probe
  observation that no pull-request requirement existed. Recorded as `P-008`.
- **New finding: merging through GitHub changes signature provenance.** Every
  commit on `main` through `d0a2cc5` carries the owner's SSH signature because
  it was pushed directly. The repository permits only squash merges, which
  replace the pushed commits with one commit signed by GitHub's `web-flow` key.
  That satisfies `required_signatures` while weakening what the rule proves:
  the signature attests that a change passed through GitHub, not that the owner
  authored it. Carried into `P-008`.
- Pull request 7 remains open and green; nothing was merged. Local `main` at
  `6ec625a` is three commits ahead of the remote by owner decision to continue
  working locally.
