---
id: PR-0018
subject: Validation execution contract
reviewer: Codex adversarial pass
date: 2026-08-10
status: accepted
---

# Validation execution contract review

## Decision scope

This review asks whether the proposed
[validation execution contract](../validation-contract.md) is a safe, small,
and reproducible interface for PRE-015. It reviews the contract, not an
implementation or CI result.

## Summary judgment

The proposal is suitable for implementation if `./check` remains a dispatcher
and evidence boundary rather than growing into a custom test framework. Its
strongest property is that the same profile semantics govern local and CI use
while secrets, privilege, network, and physical mutation are denied by
default.

The strongest reason to reject it is bootstrap friction. An offline,
secret-free, unprivileged complete suite requires deliberate retained inputs
and user-owned isolation. If acquisition and validation are not separated
cleanly, users will bypass the entry point or CI will quietly regain ambient
network and credentials.

## Challenges

### C-001: “Complete” overstates what ran

- Severity: critical
- Claim: a green complete run may omit physical trials, undefined roles, or
  deferred requirements while readers assume total project qualification.
- Required response: define complete as the applicable authorized registered
  suite and emit every omission with its trace reason.
- Author response: the contract does so and excludes T7 categorically.
- Disposition: resolved in proposal
- Residual risk: summaries and CI names must retain “applicable suite” scope.

### C-002: The dispatcher becomes a second test framework

- Severity: high
- Claim: selection, registration, output, and cleanup logic may grow custom
  assertion APIs and hide native runner behavior.
- Required response: keep `./check` thin, delegate assertions, retain native
  diagnostics, and standardize only cross-runner policy and result joins.
- Author response: the stable interface explicitly permits purpose-built
  runners and requires native logs.
- Disposition: mitigated
- Residual risk: implementation review must reject framework features without
  a demonstrated cross-runner need.

### C-003: Offline validation merely assumes cached inputs are correct

- Severity: critical
- Claim: separating acquisition can leave mutable or substituted cached bytes
  outside the tested identity boundary.
- Required response: acquisition must be attributable and every test must bind
  retained input identities before use.
- Author response: the contract requires pinned separate acquisition and exact
  fixture identities; SYS-057/SYS-058 testing remains independently required.
- Disposition: mitigated
- Residual risk: PLN-0001 must define acquisition and cache verification.

### C-004: Environment scrubbing breaks tools and invites exceptions

- Severity: high
- Claim: build and VM tools often depend on home directories, agents, proxy
  variables, runtime sockets, and system configuration.
- Required response: supply a temporary home and explicit allowlist; treat each
  new host dependency as a reviewed capability rather than inheriting ambient
  state.
- Author response: included.
- Disposition: resolved in proposal
- Residual risk: initial hostile preflight must prove credential-like values
  are absent from child processes.

### C-005: Dirty-checkout support makes results irreproducible

- Severity: high
- Claim: local fast results can be misattributed to HEAD while testing unstaged
  changes.
- Required response: record a diff identity, preserve exact state, and forbid
  dirty qualification and CI results.
- Author response: included.
- Disposition: resolved in proposal
- Residual risk: the result schema must distinguish untracked content without
  retaining sensitive bytes.

### C-006: Strict no-retry policy makes CI noisy

- Severity: medium
- Claim: transient infrastructure faults will fail gates even when assertions
  are sound.
- Required response: preserve the first result, classify infrastructure versus
  assertion failure, and permit an explicit new run without rewriting history.
- Author response: included; required flaky tests remain blocking.
- Disposition: accepted risk
- Residual risk: CI availability may justify a narrowly scoped infrastructure
  retry later, but never assertion retries within one result.

### C-007: Cleanup code is more dangerous than leaked test state

- Severity: critical
- Claim: signal handlers using broad paths, globs, mounts, or shared network
  names can delete user data or disrupt unrelated work.
- Required response: use per-run identifiers, exact resource inventories,
  idempotent cleanup, and no broad destructive target.
- Author response: included.
- Disposition: resolved in proposal
- Residual risk: destructive cleanup paths require dedicated hostile probes.

### C-008: CI infrastructure reintroduces a mutable supply chain

- Severity: critical
- Claim: floating actions, broad token permissions, and automatic dependency
  downloads undermine the validation boundary.
- Required response: immutable action commits, a versioned runner label with
  recorded resolved image identity, least privilege, no secrets, and an
  explicit boundary before offline `./check` execution.
- Author response: included.
- Disposition: mitigated
- Residual risk: runner-image identity and action update ownership remain
  PRE-016/PRE-017 housekeeping work.

### C-009: Fixed time budgets may be arbitrary

- Severity: medium
- Claim: image and VM checks vary by hardware and cold-cache state; a fixed
  timeout can punish slow but correct environments or hide deadlocks behind a
  generous global limit.
- Required response: enforce per-test timeouts, separate default from maximum,
  and require plan-level justification for exceptions.
- Author response: included with initial budgets.
- Disposition: mitigated
- Residual risk: replace estimates with measured distributions after the first
  implementation slice.

### C-010: CI retention is not durable evidence

- Severity: high
- Claim: a 14-day workflow artifact may expire before a release or decision is
  audited.
- Required response: classify CI output as ephemeral and require qualification
  results to enter a separately governed evidence set before reliance.
- Author response: included.
- Disposition: resolved in proposal
- Residual risk: the durable evidence store remains PLN-0001/PRE-016 work.

## Required changes before acceptance

No textual blocker is currently known. Owner review should confirm:

1. `./check fast|complete|list|run` as the stable interface;
2. offline, unprivileged, secret-free execution as the default;
3. the initial timeout and 14-day ephemeral CI-retention budgets;
4. no automatic assertion retry and blocking treatment of required flaky tests;
5. initial CI limited to `fast`, with `complete` local and manual until its
   infrastructure is deterministic; and
6. implementation plus passing local/CI and hostile-probe evidence remains
   necessary after policy acceptance.

## Decision

Accepted by Jason Tarasovic on 2026-08-10. All six review confirmations are
approved. The implementation risks and hostile probes remain active PRE-015
work; policy acceptance is not implementation evidence.
