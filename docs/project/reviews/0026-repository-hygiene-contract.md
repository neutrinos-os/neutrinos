---
id: PR-0026
subject: Repository hygiene contract and clean-clone check
reviewer: Claude implementation pass
date: 2026-08-10
status: accepted
---

# Repository hygiene contract review

## Decision scope

This review examines the [repository hygiene contract](../repository-hygiene.md)
and the `T5-VAL-003` clean-clone check that PRE-016 requires. It does not
accept documentation structure, which the [docs README](../../README.md) owns,
and does not authorize NeutrinOS source implementation.

## Summary judgment

The contract closes PRE-016's eight subjects: layout, generated content,
ignored state, artifact bounds, identifiers, formatting, dependencies, and
supersession. `T5-VAL-003` gives the clean-clone requirement a check rather
than a claim.

Two things it does not do, both stated in the document rather than implied:
the size and binary bounds are reviewer-applied policy with no check behind
them, and mise task dispatch in a clean clone remains uncovered.

## Challenges

### C-001: A closed top-level table will be bypassed rather than amended

- Severity: medium
- Claim: a table requiring a named owner and lifecycle for every top-level
  entry is friction, and the likely outcome is that files appear anyway and
  the table silently falls out of date, leaving a document that describes a
  repository that no longer exists.
- Response: the table was amended four times during PRE-017 as `README.md`,
  `LICENSE`, `.gitignore`, `.editorconfig`, `.betterleaks.toml`, `.githooks/`,
  and the adapter directories landed. That is the only evidence available that
  the mechanism is used rather than bypassed, and it is one plan's worth.
- Disposition: accepted as a known maintenance cost.
- Residual risk: no check enforces the table. A top-level addition that skips
  it is invisible until someone reads the contract. A `T0` check comparing the
  tracked top level against the table would close this and is not written.

### C-002: The size and binary bounds bind nothing and are unenforced

- Severity: medium
- Claim: bounds that no check enforces and that nothing currently violates are
  decoration. The largest tracked file is 69 KB against a 1 MiB bound.
- Response: correct, and the document now says so explicitly rather than
  implying enforcement. The bounds exist to be cited when the first image, VM
  disk, or evidence bundle is proposed, which is a review argument rather than
  a runtime condition. PLN-0001 introduces exactly those artifacts.
- Disposition: accepted as policy without a check.
- Residual risk: a large or binary artifact can be committed today with no
  mechanical objection. The first VM-artifact increment should either add the
  check or record why a reviewer suffices.

### C-003: The clean-clone check does not cover mise task dispatch

- Severity: high
- Claim: PRE-016 asks whether a clean clone can run the documented fast
  validation. Operators run `mise run check:fast`, not the runner directly, so
  a check that bypasses mise does not answer the question asked.
- Response: accurate and not fully resolved. The clone is driven through its
  committed runner because the runner's strict environment allowlist rejects
  the mise configuration-isolation variables the probe requires, and widening
  that allowlist would weaken the boundary PR-0020 established. Weakening a
  reviewed boundary to make a test pass was rejected. `T5-VAL-002` covers
  dispatch under isolation, so the two checks together cover dispatch and
  clean-clone execution, but no single check covers both at once.
- Disposition: accepted as a bounded limitation, recorded in the contract.
- Residual risk: a defect that only appears when mise dispatches tasks inside a
  fresh clone would not be caught. Closing it requires an owner decision on the
  allowlist, which was not taken.

### C-004: A warm uv cache is an undeclared local-state dependency

- Severity: medium
- Claim: a check for "no undeclared local state" that itself depends on the
  operator's populated uv cache is self-contradictory.
- Response: canonical validation is offline by accepted contract, so a test
  cannot acquire packages. The dependency is declared rather than hidden: the
  cache is an explicit `NEUTRINOS_VALIDATION_UV_CACHE` input the dispatcher
  resolves and the runner validates, and a cold cache fails the check with that
  stated reason rather than passing or reaching the network.
- Disposition: accepted; the dependency is declared and fails closed.
- Residual risk: CI's first run populates the cache during bootstrap, so CI
  never exercises the cold-cache failure path.

### C-005: `blocked` would represent the cold-cache case better than `failing`

- Severity: low
- Claim: a cold cache is a missing capability, not a defect, and reporting it
  as `failing` conflates the two.
- Response: agreed in principle. The runner counts `blocked` but has no
  producer for it, and introducing one changes result semantics defined in the
  accepted validation contract.
- Disposition: deferred; not taken as a drive-by change to accepted policy.
- Residual risk: a cold-cache CI failure will read as a defect and cost a
  diagnosis cycle.

## Probe observations

- `T5-VAL-003` was verified non-vacuous: pointed at an empty uv cache it fails
  with the stated reason rather than passing or downloading.
- Adding the check's declared environment variable broke two existing hostile
  probes, which is the probes working: they caught an unreviewed change to the
  runner environment allowlist.
- The check reads committed `HEAD`, so it cannot validate uncommitted work.
  Each increment that changes the runner requires a commit before the check
  reflects it.

## Required confirmations

- The contract is policy, and later work cites it rather than restating it.
- The uncovered mise-dispatch case is a known gap, not an oversight, and
  closing it is an allowlist decision the owner has not taken.
- The size and binary bounds carry no check.

## Owner decision

Accepted by Jason Tarasovic on 2026-08-10. PRE-016 is satisfied. C-003 and
C-005 remain open and carry forward; C-002 is expected to bind first in
PLN-0001.
