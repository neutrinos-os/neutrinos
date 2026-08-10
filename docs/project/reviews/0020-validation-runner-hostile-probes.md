---
id: PR-0020
subject: Initial validation runner and hostile probes
reviewer: Codex adversarial pass
date: 2026-08-10
status: proposed
---

# Initial validation runner hostile-probe review

## Decision scope

This review challenges the initial Linux-x64 implementation of PRE-015: the
mise dispatch boundary, Python 3.14 runner, T0 documentation checks, and
`T5-VAL-001` hostile runner probes. It does not satisfy PRE-015, select a
NeutrinOS product mechanism, or authorize source implementation.

## Summary judgment

The implementation is a useful, bounded increment. It found and closed three
fail-open paths during its own review: pytest checkout mutation, network access
by mise before the task sandbox started, and ambient PATH substitution for
repository tools. The registered hostile suite now passes eight synthetic
environment, cache-boundary, network, timeout, interruption, output, and
cleanup probes.

It is not yet a complete validation contract. In particular, errors before
normal test execution do not all create `run.json` and `results.jsonl`, output
canaries are not scanned, the empty-cache acquisition check is not retained as
a repeatable test, and no clean CI result exists.

## Challenges

### C-001: The task sandbox starts too late to stop mise resolution

- Severity: critical
- Observation: an isolated empty mise cache gained remote-version metadata
  from unrelated global `latest` tools before the task began.
- Response: repository mise context is now fully offline; bootstrap alone sets
  `MISE_OFFLINE=0`. A repeat with an empty cache wrote only local bin-path
  metadata and acquired no remote-version records.
- Disposition: resolved in implementation
- Residual risk: retain this as an automated or otherwise reproducible probe.

### C-002: Ambient PATH can impersonate a missing locked tool

- Severity: critical
- Observation: with project mise data redirected, plain `uv` and `python`
  command names could still resolve through ambient shims or PATH.
- Response: every task resolves both tools with `mise which`; uv receives the
  resolved Python interpreter and runs locked, offline, and without syncing.
- Disposition: resolved in implementation
- Residual risk: CI must prove missing tool and stale lock failures explicitly.

### C-003: The test framework dirties the checkout

- Severity: high
- Observation: the first hostile run created `.pytest_cache`; repository-state
  preservation correctly failed the invocation.
- Response: mise resolves an explicit XDG validation-cache root outside the
  checkout; pytest writes only reconstructible metadata below it, canonical
  profiles do not use cache-dependent selection, and bytecode writes remain
  disabled. The runner rejects missing, relative, or in-repository cache roots
  and records the resolved path and non-evidence semantics in `run.json`.
- Disposition: resolved in implementation
- Residual risk: PRE-016 must set aggregate cache-capacity and housekeeping
  policy; future test plugins and native tools need the same audit.

### C-004: Timeout cleanup only kills the direct child

- Severity: critical
- Claim: a timed-out, interrupted, or apparently successful test could leave a
  descendant holding pipes or host resources.
- Response: execution uses a new process group, bounded nonblocking output,
  signal-safe termination, descendant cleanup after leader exit, and absence
  verification. Timeout, interruption, and descendant-leak probes pass.
- Disposition: resolved for processes
- Residual risk: mounts, VMs, devices, sockets, and other later capabilities
  require resource-specific owners and probes.

### C-005: Output limits are detected only after disk exhaustion

- Severity: high
- Claim: post-exit file-size checks do not bound a hostile writer.
- Response: the parent drains nonblocking pipes, writes at most the registered
  limit, terminates on overflow, and records overflow as failure.
- Disposition: resolved in implementation
- Residual risk: declared artifacts need separate per-file and aggregate caps.

### C-006: Preflight failures violate the result contract

- Severity: high
- Observation: root, undeclared-environment, and invalid-ID failures currently
  exit before the full run directory and manifest are written.
- Required response: make all invocations produce a bounded result with the
  failure stage and cleanup state, without exposing environment values.
- Disposition: open; blocks PRE-015

### C-007: Secret absence is not output safety

- Severity: high
- Observation: mise strips a synthetic ambient canary and the runner rejects
  undeclared environment names, but retained output is not yet scanned for
  synthetic canaries or credential-shaped material.
- Required response: implement declared synthetic canaries, scan every retained
  stream/artifact, quarantine unsafe raw output, and fail the run.
- Disposition: open; blocks PRE-015

### C-008: The implementation is Linux-specific

- Severity: medium
- Observation: process groups, selectors, interval signals, and mise's network
  sandbox are exercised only on the currently locked Linux-x64 platform.
- Response: describe this as the supported validation platform for G1 rather
  than implying portability from Python alone.
- Disposition: accepted boundary for this increment
- Residual risk: adding another supported platform requires its own lock and
  equivalent hostile probes.

## Probe observations

Working tree based on `7556ba6`, Python 3.14.7, uv 0.12.3:

- all four mise tasks validated;
- `T5-VAL-001`: eight probes passed in 0.31 seconds;
- an ambient `NEUTRINOS_VALIDATION_SECRET_CANARY` did not reach the runner;
- pytest metadata persisted under the declared external XDG cache while the
  exact ignored and non-ignored checkout identity remained unchanged;
- network socket creation failed with `EPERM` inside the canonical task;
- timeout, interruption, output overflow, and descendant-leak fixtures left no
  owned process group;
- the registered run preserved tracked, staged, untracked, and ignored checkout
  identity; and
- after enabling mise offline mode, a canonical list run with an empty isolated
  mise cache acquired no remote-version metadata.

These are development observations from a dirty checkout, not qualification or
gate evidence.

## Required confirmations

1. Mise offline mode applies before task launch; bootstrap explicitly opts in
   to acquisition.
2. Canonical tasks resolve Python and uv through `mise which`, not ambient PATH.
3. `T5-VAL-001` joins the fast and complete profiles as validation-infrastructure
   failure coverage.
4. Pytest metadata uses the declared external XDG cache, never controls
   canonical selection, and is neither checkout state nor retained evidence.
5. Linux x64 is the only implemented validation platform in this increment.
6. C-006 and C-007 remain open and PRE-015 remains active.

## Owner decision

Pending. Acceptance approves this bounded implementation increment and the six
confirmations above; it does not accept PRE-015 or G1.
