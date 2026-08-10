---
id: PR-0021
subject: Failed validation invocation result contract
reviewer: Codex adversarial pass
date: 2026-08-10
status: accepted
---

# Failed validation invocation result review

## Decision scope

This review challenges the PRE-015 result path before registered test
execution: command-line parsing, runner preflight, and test selection. It
closes C-006 from [PR-0020](0020-validation-runner-hostile-probes.md) if
accepted. It does not close output-safety C-007, satisfy PRE-015, or authorize
NeutrinOS product implementation.

## Summary judgment

The runner now allocates bounded result storage before source inspection or
preflight. Rejected execution invocations produce `run.json`, a present and
empty `results.jsonl`, empty artifact/log directories, a failure stage, source
identity when obtainable, and verified checkout-cleanup state. Thirteen hostile
runner probes pass.

The boundary is materially safer but incomplete. Retained output is not yet
scanned or quarantined, the root refusal has unit rather than privileged
end-to-end coverage, and an inability to allocate or write the run directory
cannot be represented inside that unavailable directory.

## Challenges

### C-001: Preflight can fail before evidence storage exists

- Severity: high
- Claim: refusing root or an undeclared environment before allocating the run
  directory violates the result contract and leaves only terminal text.
- Response: allocation and empty `results.jsonl` creation precede source
  snapshot, preflight, selection, and execution. All handled failure stages
  converge on the same manifest and terminal summary.
- Disposition: resolved in implementation
- Residual risk: failure to allocate the run directory itself remains
  terminal-only and must be made explicit in future runner recovery policy.

### C-002: Rejected secrets can leak while being diagnosed

- Severity: critical
- Claim: omitting an environment value from `run.json` is insufficient if
  source-identification subprocesses inherit it or terminal diagnostics echo
  arbitrary rejected values.
- Response: Git receives an exact non-secret environment; preflight records
  rejected variable names only; malformed argument values are not echoed; a
  synthetic environment-value probe finds the canary in no retained or
  terminal output.
- Disposition: resolved for pre-execution failures
- Residual risk: C-007 still requires scanning every stream and artifact
  produced during test execution.

### C-003: Failure diagnostics are an unbounded artifact

- Severity: high
- Claim: an adversarial argument or exception could make `run.json` or terminal
  output grow without the normal per-test output limit.
- Response: runner-level error text is UTF-8 normalized and bounded to 16 KiB;
  invalid identifier syntax is summarized without its value.
- Disposition: resolved for the current runner error field
- Residual risk: the aggregate manifest and future omission/registration fields
  need explicit schema and size limits under PRE-016.

### C-004: An empty result stream can masquerade as success

- Severity: high
- Claim: an empty `results.jsonl` is ambiguous without a durable explanation.
- Response: `run.json` records `final_result=failing`, one of `invocation`,
  `preflight`, or `selection` as `failure_stage`, no selected IDs, zero counts,
  and checkout cleanup. The process exits 2.
- Disposition: resolved in implementation
- Residual risk: a future schema must constrain stage and exit-code semantics.

### C-005: Queries and private child execution create nested noise

- Severity: medium
- Claim: interpreting “every invocation” literally would make `check:list`
  mutate external state and make each runner-private child create a nested run.
- Response: the contract now distinguishes profile/exact-test execution from
  the read-only registration query. Private child results belong to their
  parent registered-test record.
- Disposition: proposed clarification
- Residual risk: CI and operator guidance must continue to treat `check:list`
  as information, never gate evidence.

## Probe observations

Working tree based on `f776586`, Python 3.14.7, uv 0.12.3:

- `T5-VAL-001`: thirteen probes passed in 0.83 seconds;
- preflight, selection, and argument-parse failures each emitted a run
  directory and exited 2;
- each pre-execution failure preserved the exact dirty checkout identity and
  retained an empty `results.jsonl`;
- a synthetic rejected environment value appeared in neither retained files
  nor terminal output; and
- a 20,000-character invalid identifier was summarized without echoing its
  value.

These are development observations from a dirty checkout, not qualification or
gate evidence.

## Required confirmations

1. C-006 from PR-0020 is closed for profile and exact-test execution failures.
2. Empty `results.jsonl` is valid only with a failing manifest that names the
   pre-execution failure stage.
3. `check:list` is a read-only query and not an evidence-producing execution.
4. Runner-private child execution is represented by its parent result rather
   than a nested run directory.
5. C-007, root end-to-end coverage, and run-storage failure policy remain open.
6. PRE-015 and G1 remain active and unsatisfied.

## Owner decision

Accepted by Jason Tarasovic on 2026-08-10. Acceptance approves this bounded
implementation increment, the C-006 closure, and the six confirmations above.
It does not accept PRE-015 or G1.
