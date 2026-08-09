---
id: PR-0002
subject: Configuration authoring and deployment boundary
reviewer: Codex adversarial pass
date: 2026-08-09
status: accepted
---

# Configuration authoring boundary review

## Review limitation

This is an AI-assisted adversarial pass informed by the project owner's direct
operating experience and private repository history. It tests whether
SYS-014 through SYS-018 express durable product requirements rather than a
reaction to one tool. It is not a general evaluation of NixOS.

## Summary judgment

The requirements are appropriate for NeutrinOS because they define the
operator contract the owner wants to maintain: bounded inputs, first-class
native configuration, observable composition, qualified-artifact deployment,
and attributable failures. They justify rejecting NixOS as the primary
configuration and deployment framework without implying that NixOS lacks the
technical capability to build or test the target systems.

The requirements are accepted with three interpretation guardrails: data-first
does not mean logic-free; native configuration is not an unchecked bypass; and
late-bound machine data must not be confused with rebuilding the release on the
target.

## Challenges

### C-001: “Bounded data” can be aesthetic rather than testable

- Severity: High
- Claim: YAML, JSON, or TOML can hide just as much indirection as Nix, while a
  small expression language can sometimes be clearer.
- Required response: define the boundary by available authoring powers, not
  file extension. Normal inputs must not provide user-defined functions,
  arbitrary evaluation, or a programmable module system.
- Disposition: Resolved in the interpretation of SYS-014.
- Residual risk: references and overlays can still become difficult to follow;
  representative configuration reviews remain necessary.

### C-002: Moving logic behind the interface can merely hide complexity

- Severity: Critical
- Claim: A generator can recreate Nix's effective behavior while making it
  harder to inspect or override.
- Required response: transformation logic must be separately owned, versioned,
  and tested; precedence, resolved inputs, and generated native outputs must be
  inspectable as release evidence.
- Disposition: Resolved by SYS-016 and its acceptance tests.
- Residual risk: the implementation could technically expose outputs while
  making them too noisy or unstable for useful review.

### C-003: Native configuration can bypass validation and policy

- Severity: Critical
- Claim: An unrestricted escape hatch can defeat cross-role invariants,
  security policy, ownership, and conflict detection.
- Required response: native inputs must declare their owner and target, enter a
  deterministic composition point, and remain subject to applicable policy and
  qualification. “Supported upstream setting” means supported by the selected
  substrate, role, and project policy—not every syntactically valid setting.
- Disposition: Resolved in the interpretation of SYS-015.
- Residual risk: some upstream formats provide weak validation or unclear merge
  behavior, which role designs must address.

### C-004: Artifact-only deployment can exclude necessary late binding

- Severity: High
- Claim: Secrets, enrollment records, network identity, and hardware-derived
  values cannot always be present in a generally qualified artifact.
- Required response: allow separately governed late-bound inputs while
  prohibiting them from evaluating or reconstructing a different OS release on
  the target.
- Disposition: Resolved in the interpretation of SYS-017.
- Residual risk: interactions between a qualified artifact and production-only
  values still require contract and physical-hardware testing.

### C-005: Failure attribution may overpromise control over upstream tools

- Severity: Medium
- Claim: An upstream parser or runtime component may emit incomplete errors,
  so the project cannot guarantee a perfect diagnosis.
- Required response: preserve provenance across project-managed stages and
  identify the responsible stage and inputs even when the upstream root cause
  remains opaque. Exercise known failures at each lifecycle boundary.
- Disposition: Accepted as a design obligation under SYS-018, not a promise to
  explain every upstream defect.
- Residual risk: diagnostics can regress as upstream components change.

### C-006: Rejecting NixOS can discard mature composition and test machinery

- Severity: High
- Claim: Replacing NixOS may require the project to rebuild capabilities with a
  smaller maintainer base and worse correctness.
- Required response: reject the conflicting operator-facing framework, not its
  lessons. Reuse existing image, update, validation, and test substrates; do
  not treat “not NixOS” as permission for a greenfield stack.
- Disposition: Mitigated by CH-001, ADR-0001, and the existing-system research.
- Residual risk: the eventual substrate may still cost more to integrate and
  operate; bounded lifecycle spikes remain mandatory before selection.

## Decision

Accepted by Jason Tarasovic on 2026-08-09. SYS-014 through SYS-018 are
normative project requirements with the interpretations above. NixOS is
rejected as NeutrinOS's primary configuration and deployment framework because
its normal operator-facing authoring model conflicts with those requirements.

This decision does not select systemd-sysupdate, bootc, a package source, or a
configuration file format. It does not prohibit borrowing NixOS testing ideas
or considering Nix as a hidden build implementation if later evidence shows
that doing so adds value without leaking into the operator contract.
