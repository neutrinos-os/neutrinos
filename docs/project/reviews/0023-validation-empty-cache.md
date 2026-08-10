---
id: PR-0023
subject: Retained empty-mise-cache validation probe
reviewer: Codex adversarial pass
date: 2026-08-10
status: accepted
---

# Retained empty-mise-cache validation review

## Decision scope

This review challenges the PRE-015 boundary between validation and tool/input
acquisition. It closes the repeatability residual from C-001 in
[PR-0020](0020-validation-runner-hostile-probes.md) if accepted. It does not
constitute clean-checkout, CI, qualification, or G1 evidence and does not
authorize NeutrinOS product implementation.

## Summary judgment

`T5-VAL-002` is a registered fast/complete-profile test that creates isolated
mise cache, config, data, state, trust, system-config, XDG, and HOME roots. It
starts with an empty cache, exposes only the locally installed tool families
selected by the repository lock, and runs nested `check:list` under the
repository's offline and no-auto-install policy. The retained log names the
resolved executables and complete post-run cache inventory. Only mise's local
per-version binary-path record is permitted.

The probe is suitable for this pinned Linux-x64 slice. Its narrow cache-file
allowlist intentionally fails on a mise cache-layout change so the acquisition
claim must be reviewed rather than silently weakened.

## Challenges

### C-001: Deleting the operator cache is unsafe and irreproducible

- Severity: high
- Claim: proving an empty-cache path by clearing the user's cache races other
  processes, destroys useful state, and cannot be retained as a normal test.
- Response: the test creates a private temporary cache and never reads,
  modifies, renames, or deletes the operator cache. Its ordinary parent result
  and bounded log retain the observation.
- Disposition: resolved in implementation
- Residual risk: reconstructible operator-cache capacity and cleanup remain
  PRE-016 housekeeping.

### C-002: Empty cache plus empty tool storage only proves failure

- Severity: high
- Claim: a test with neither cache nor installed locked tools cannot separate
  prohibited acquisition from missing bootstrap inputs.
- Response: the dispatcher declares exact Python and uv installation roots.
  The probe links their read-only mise tool families into isolated data,
  verifies nested `mise which` resolves beneath the declared exact versions,
  and permits no other tool family.
- Disposition: resolved in implementation
- Residual risk: bootstrap correctness itself remains a separate acquisition
  responsibility.

### C-003: User or parent configuration can contaminate the probe

- Severity: critical
- Claim: changing HOME or XDG paths alone does not prevent mise from finding a
  `.config/mise/config.toml` while walking repository ancestors.
- Response: hostile development runs reproduced that leak. The final probe
  sets isolated global and system config paths and stops config discovery at
  the repository parent. It explicitly trusts only this checkout in isolated
  state. No user-global tool or setting enters resolution.
- Disposition: resolved in implementation
- Residual risk: the ceiling assumes the repository root remains the sole
  project-config scope; a future intentional parent config requires review.

### C-004: The nested task sandbox can discard its own isolation

- Severity: critical
- Claim: `sandbox.deny_env` removes the probe's mise/XDG controls before task
  scripts invoke `mise where` and `mise which`, causing fallback to ambient
  state.
- Response: the nested invocation permits only `MISE_*` and `XDG_*` from an
  exact environment constructed by the test. That environment contains no
  inherited credentials or production authority. Normal canonical invocations
  retain the stricter default deny-environment behavior.
- Disposition: resolved for the nested probe
- Residual risk: adding another allowed namespace requires a new hostile
  review.

### C-005: “No download” is not proven by a successful exit

- Severity: high
- Claim: mise could populate remote version metadata from an ambient cache or
  perform resolution before the inner task reports success.
- Response: the isolated cache is asserted empty immediately before nested
  execution. The enclosing canonical mise sandbox denies network syscalls, the
  project sets offline mode and disables task auto-install, and the post-run
  inventory permits only `TOOL/VERSION/bin_paths-*.msgpack.z`. Any other file
  fails the test.
- Disposition: resolved in implementation
- Residual risk: a future mise version may rename a harmless local record; the
  probe will fail closed until the allowlist and claim are reviewed.

### C-006: `check:list` is not evidence-producing

- Severity: medium
- Claim: using the list query conflicts with PR-0021's decision that it does
  not create validation evidence.
- Response: nested `check:list` remains a read-only subject. The registered
  parent `T5-VAL-002` execution produces the result, diagnostics, timeout,
  cleanup, output-safety scan, and exit semantics.
- Disposition: resolved by parent-child semantics
- Residual risk: the nested query must never be presented independently as a
  passing gate result.

## Probe observations

Working tree based on `ecf8f98`, mise 2026.7.17, Python 3.14.7, uv 0.12.3:

- all four mise tasks validated after adding declared install roots;
- `T5-VAL-001`: seventeen hostile probes passed in 0.89 seconds;
- `T5-VAL-002`: passed in 0.30 seconds from an empty private mise cache;
- nested resolution selected `bin/python3.14` and
  `uv-x86_64-unknown-linux-musl/uv` beneath the declared locked installs;
- the sole cache output was
  `uv/0.12.3/bin_paths-833b7.msgpack.z`, classified as local executable-path
  metadata; and
- the retained result reported zero remote-metadata files and preserved the
  dirty checkout identity.

The final dirty-checkout `check:fast` and `check:complete` development reruns
were initially not obtained: the reviewing execution environment rejected
further approved mise commands after its tool-usage limit was reached. A
later session obtained both on the same working tree, `ecf8f98`, mise 2026.7.17,
Python 3.14.7, uv 0.12.3:

- `mise run check:fast`: `passing=4 failing=0 blocked=0 skipped=0
  not_applicable=0 deferred=0`, terminal exit 0; and
- `mise run check:complete`: identical counts, terminal exit 0.

These are development observations from a dirty checkout, not qualification or
gate evidence.

## Required confirmations

1. The PR-0020 empty-cache repeatability residual is closed by registered
   `T5-VAL-002` for the current Linux-x64 validation slice.
2. The probe may read the already-bootstrapped locked Python and uv tool
   families but may not populate or rely on the operator cache.
3. Only exact constructed mise/XDG isolation variables cross the nested task
   sandbox; user-global and ancestor configuration are excluded.
4. The post-run cache allowlist covers only local executable-path metadata; a
   new cache class fails closed pending review.
5. Nested `check:list` is the probe subject, not independent evidence; the
   registered parent result carries the claim.
6. Clean local profiles, pinned least-privilege CI, PRE-015, and G1 remain open.

## Owner decision

Accepted by Jason Tarasovic on 2026-08-10. Acceptance approves this bounded
implementation increment, closes the stated PR-0020 C-001 repeatability
residual, and confirms the six items above. It does not accept PRE-015 or G1.
