---
id: PR-0017
subject: Test and evidence strategy
reviewer: Codex adversarial pass
date: 2026-08-10
status: accepted
---

# Test and evidence strategy review

## Decision scope

This review asks whether the proposed
[test and evidence strategy](../test-strategy.md) is sufficient to satisfy
PRE-014 before NeutrinOS chooses test frameworks, commands, CI, or evidence
storage under PRE-015.

Acceptance would establish a test taxonomy and trace policy. It would not
authorize source implementation, a physical-host trial, or any product
mechanism.

## Summary judgment

The proposal is suitable for acceptance if its claim boundaries remain
mandatory in implementation plans. Its strongest property is that tests attach
to exact claims and subjects rather than accumulating into an undifferentiated
“green” result.

The strongest reason to reject it is process cost. Eight levels and detailed
trace rows could become paperwork copied after implementation instead of a
tool for selecting the smallest sufficient evidence. PRE-015 and PLN-0001 must
therefore prove that the contract can be maintained from executable metadata
without creating a second test-management system.

## Challenges

### C-001: The numbered taxonomy will be mistaken for a confidence ladder

- Severity: high
- Claim: T7 may be treated as stronger than all preceding evidence even when a
  physical boot says nothing about deterministic composition or input identity.
- Failure or cost if true: broad physical success launders gaps in precise
  lower-level claims.
- Required response: require per-claim levels and explicit non-claims; state
  that higher levels do not subsume lower observability.
- Author response: the strategy makes the taxonomy non-ordinal and gives the
  physical-boot counterexample explicitly.
- Disposition: resolved in proposal
- Residual risk: reports and CI presentation must preserve the distinction.

### C-002: Failure injection is not actually one level

- Severity: high
- Claim: corruption of a parser fixture, interruption of a VM transition, and
  power loss on a physical machine have different subjects and authority.
- Failure or cost if true: a generic T5 mark hides where the invariant was
  exercised.
- Required response: pair T5 with its execution level and exact transition.
- Author response: the strategy uses forms such as `T5@T2` and `T5@T4` and
  requires transition-specific post-failure invariants.
- Disposition: resolved in proposal
- Residual risk: the executable result schema remains PRE-015 work.

### C-003: Golden outputs can freeze an incorrect implementation

- Severity: high
- Claim: regenerating and committing a golden result can bless drift without
  checking semantics.
- Failure or cost if true: tests confirm self-consistency instead of policy.
- Required response: identify an independent oracle, review semantic diffs,
  and retain generation inputs and tool identity.
- Author response: the strategy requires a predeclared oracle and retained
  exact inputs; PRE-015/PRE-016 must define golden regeneration and review.
- Disposition: mitigated
- Residual risk: the first golden workflow must demonstrate independent review.

### C-004: VM success will silently become a hardware-support claim

- Severity: critical
- Claim: boot and recovery in a VM omit firmware, TPM, storage, device, power,
  and platform-specific failure behavior.
- Failure or cost if true: G1 evidence is overstated and physical deployment
  begins without a safe trial plan.
- Required response: make T4's non-claims explicit and require T7 plus separate
  mutation authority for hardware-dependent claims.
- Author response: T4, T7, and the SYS-030 trace row establish that boundary.
- Disposition: resolved in proposal
- Residual risk: later role plans must not collapse T6 and T7.

### C-005: Failure tests may prove only that an error was noticed

- Severity: critical
- Claim: an injected failure can return a useful message while still damaging
  the selected deployment, evidence, retained fallback, or mutable state.
- Failure or cost if true: apparent negative coverage masks loss of the actual
  safety invariant.
- Required response: assert the post-failure state, prior valid selection or
  deliberate recovery path, retained evidence, and retry/cleanup behavior.
- Author response: the selection rules require the invariant and recovery path,
  not merely an error code.
- Disposition: resolved in proposal
- Residual risk: PLN-0001 must enumerate transition boundaries rather than use
  a representative single interruption.

### C-006: Exhaustive matrices can make the project immobile

- Severity: high
- Claim: cross-products of artifact, role, platform, transition, fault, and
  state versions are unbounded.
- Failure or cost if true: the suite becomes too slow to run and too costly to
  interpret, encouraging skipped gates.
- Required response: decompose claims, use pairwise or model-derived cases only
  with a recorded coverage argument, and reserve full cross-products for
  boundaries whose interaction is itself the claim.
- Author response: the strategy requires smallest independent properties and
  explicit gaps, but the reduction method remains plan-specific.
- Disposition: mitigated
- Residual risk: PLN-0001 must justify its selected failure matrix.

### C-007: Fixture success can settle open architecture by inertia

- Severity: high
- Claim: tests written around mkosi, Fedora, EROFS, or a particular VM layout
  can make replacement look prohibitively expensive and later be cited as
  architecture acceptance.
- Failure or cost if true: G1 experimental fixtures become permanent without
  comparative evidence or an ADR.
- Required response: keep substrate-independent assertions separate from
  adapters, label fixtures in traces, and state their non-claims.
- Author response: the strategy bars experimental results from accepting
  architecture and the representative trace labels the package and deployment
  mechanisms as candidates.
- Disposition: mitigated
- Residual risk: PLN-0001 file and fixture layout must preserve replaceable
  boundaries.

### C-008: Detailed evidence retention can leak secrets or overwhelm storage

- Severity: critical
- Claim: raw logs, VM state, crash artifacts, and hostile-input results may
  contain credentials, topology, personal data, or unbounded output.
- Failure or cost if true: the test system becomes a confidentiality or
  capacity hazard.
- Required response: use synthetic authority, make sensitivity and redaction
  explicit, bound output, and define cleanup and retention before execution.
- Author response: the strategy requires synthetic-authority boundaries and
  result redaction/cleanup metadata; concrete enforcement is a PRE-015 exit
  condition.
- Disposition: mitigated; blocking for PRE-015
- Residual risk: no executable test should handle credentials before that
  enforcement exists.

## Required changes before acceptance

No textual blocker is currently known. Owner review should confirm:

1. the eight-level taxonomy is useful rather than too granular;
2. `T5@Tn` is acceptable notation for cross-cutting failure injection;
3. the representative G1 trace has the right reduced claims and deferrals; and
4. PRE-015, not this policy, should own commands, runners, CI, retention,
   redaction, timeouts, and flaky-test behavior.

## Decision

Accepted by Jason Tarasovic on 2026-08-10. The eight test levels, cross-cutting
`T5@Tn` notation, representative G1 trace, and PRE-015 boundary are approved.
The mitigated residual risks remain required review inputs for PLN-0001 and
PRE-015; acceptance is not evidence that they have been implemented.
