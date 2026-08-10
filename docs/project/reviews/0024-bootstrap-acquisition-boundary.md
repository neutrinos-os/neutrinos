---
id: PR-0024
subject: Bootstrap acquisition boundary and unenforceable endpoint restriction
reviewer: Claude implementation pass
date: 2026-08-10
status: accepted
---

# Bootstrap acquisition boundary review

## Decision scope

This review corrects a PRE-015 boundary claim that the pinned mechanism cannot
enforce: the accepted contract restricted locked uv synchronization to its
declared package endpoints, and pinned mise cannot do so on the only locked
platform. It amends the accepted
[validation execution contract](../validation-contract.md) and the operator
[validation page](../validation.md). It does not satisfy PRE-015, constitute
clean-checkout, CI, qualification, or G1 evidence, or authorize NeutrinOS
product implementation.

## Summary judgment

The documented bootstrap could not run on any supported platform. Pinned mise
2026.7.17 rejects `--allow-net=<host>` with `per-host network filtering is not
supported on Linux`, and `lockfile_platforms = ["linux-x64"]` declares no other
platform. The endpoint restriction the contract asserted was therefore never
enforced by any executed command.

The defect was masked by operator-checkout state: a populated `.venv` already
carried the dev group, so `T5-VAL-001` passed locally. A first clean checkout
fails it with `No module named pytest`.

The amendment removes the unenforceable claim and states the boundary that the
mechanism does hold: bootstrap is an unfiltered acquisition phase bounded by
pinned inputs — `mise.lock` fixing tool versions, `uv.lock` with `--locked`
fixing package versions and recorded SHA-256 hashes, failing closed on
mismatch. This is a weaker network claim and an accurate one.

## Challenges

### C-001: Removing the restriction weakens the acquisition boundary

- Severity: high
- Claim: dropping per-host filtering permits bootstrap to reach any host and
  loses a defense the contract previously promised.
- Response: the defense did not exist. Every prior bootstrap either failed at
  the mise argument parser or ran unfiltered. The amendment removes a false
  assurance rather than an operating control, and records the real one.
- Disposition: resolved by correction
- Residual risk: unfiltered acquisition remains a genuine exposure; only lock
  integrity, not host reachability, bounds it.

### C-002: Pinned locks are not equivalent to endpoint restriction

- Severity: high
- Claim: locks constrain what is installed, not what is contacted; a
  compromised or substituted index could still be reached.
- Response: accepted and stated rather than argued away. `--locked` fails on
  any lock mismatch and uv verifies recorded hashes, so a substituted artifact
  fails closed even when the host is reachable. Reachability itself is
  unbounded, and the contract now says so instead of implying otherwise.
- Disposition: accepted limitation, recorded
- Residual risk: index availability, metadata exposure, and traffic analysis
  during bootstrap are unaddressed. A network-level control belongs to the
  execution environment or CI, not to this contract.

### C-003: A dirty checkout masked the failure

- Severity: medium
- Claim: local passing runs were treated as adequate while a first clean
  checkout was broken, so the evidence practice, not just the command, failed.
- Response: confirmed. The clean-clone run at `9b58781` is what exposed it.
  Clean-checkout profile evidence is already a required, still-open PRE-015
  item; this is a concrete instance of why.
- Disposition: resolved by correction; evidence item remains open
- Residual risk: other operator-state-dependent claims may remain masked until
  clean profiles and CI run routinely.

### C-004: A future mise could silently re-tighten or re-loosen the boundary

- Severity: medium
- Claim: a later mise that supports per-host filtering on Linux would leave the
  contract describing a weaker boundary than the mechanism offers, and the
  amendment could be read as permanently renouncing endpoint restriction.
- Response: the contract requires review before reinstating an endpoint
  restriction, so a future tightening is a recorded decision rather than a
  silent change. Releases 2026.7.18 through 2026.8.3 were reviewed and none
  restores per-host filtering on Linux; this is not a version-bump defect.
- Disposition: resolved in wording
- Residual risk: the review burden depends on someone noticing the capability
  change; no automated check asserts it.

### C-005: `lockfile = true` auto-creation changes fail-closed behavior

- Severity: medium
- Claim: mise 2026.8.3 creates missing project lockfiles during `mise install`
  when `lockfile = true`, so a checkout without `mise.lock` could have one
  written during bootstrap instead of failing.
- Response: out of scope for this amendment and not currently reachable —
  `mise.lock` is committed and the pinned mise predates the change. Recorded
  here so a future bump is evaluated against the acquisition boundary rather
  than adopted incidentally.
- Disposition: deferred, recorded
- Residual risk: a mise bump without this evaluation could weaken fail-closed
  bootstrap behavior.

## Probe observations

Working tree at `9b58781`, mise 2026.7.17, Python 3.14.7, uv 0.12.3:

- the documented `mise exec --allow-net pypi.org --allow-net
  files.pythonhosted.org` bootstrap exits non-zero on Linux without attempting
  acquisition;
- a fresh `git clone` at `9b58781`, bootstrapped with plain
  `uv sync --locked`, installed five dev packages and then passed both
  `check:fast` and `check:complete` at `passing=4 failing=0`, exit 0, leaving
  the checkout clean;
- without that bootstrap the same clean checkout fails `T5-VAL-001` with
  `No module named pytest`, three passing and one failing; and
- `uv.lock` records SHA-256 hashes for sdists and wheels.

These are development observations from a clean clone of a committed revision,
not qualification or gate evidence.

## Required confirmations

1. The endpoint-restriction clause is removed because the pinned mechanism
   cannot enforce it on the only locked platform, not because the restriction
   was judged unnecessary.
2. Bootstrap is an unfiltered acquisition phase bounded by pinned, hash-checked
   locks that fail closed on mismatch.
3. Reinstating an endpoint restriction requires review rather than a silent
   tightening.
4. Network-level control of bootstrap, if wanted, belongs to the execution
   environment or CI and remains unspecified.
5. Clean local profiles, pinned least-privilege CI, PRE-015, and G1 remain
   open.

## Owner decision

Accepted by Jason Tarasovic on 2026-08-10. Acceptance amends the validation
execution contract and the operator validation page, and confirms the five
items above. It does not accept PRE-015 or G1.
