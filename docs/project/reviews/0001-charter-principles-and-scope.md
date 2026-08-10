---
id: PR-0001
subject: Charter, principles, and scope ratification
reviewer: Codex adversarial pass
date: 2026-08-09
status: accepted
---

# Charter, principles, and scope review

## Review limitation

This is an AI-assisted adversarial pass, not independent human review. Its
purpose is to make objections and their dispositions durable before the
project owner ratifies the documents.

## Summary judgment

The project documents are coherent enough to ratify after the proposed edits.
Their strongest property is that artifact identity, literal-artifact testing,
state ownership, and recovery form a connected contract. Their strongest risk
is that “one lifecycle” and “systemd-first” could become conclusions that
override contrary role requirements instead of hypotheses repeatedly tested by
the workstation and router.

## Challenges

### C-001: Exact configuration cannot always be booted unchanged

- Severity: High
- Claim: Machine secrets, hardware-derived values, enrollment records, and
  other late-bound data make a literal reading of “exact OS/configuration pair
  has booted” either impossible or likely to leak sensitive inputs into CI.
- Required response: Separate applicable declarative inputs from late-bound
  values and specify what qualification covers for each.
- Disposition: Mitigated in the invariant and Principle 2. Later designs must
  define configuration scopes, composition, and their tests.
- Residual risk: Untested interactions can still occur only on physical
  hardware.

### C-002: One lifecycle can become a harmful abstraction

- Severity: High
- Claim: A workstation and router have materially different availability,
  storage, network, and recovery needs. Requiring sameness can hide divergence
  or weaken both designs.
- Required response: Define common lifecycle semantics without demanding
  identical artifacts or implementations.
- Disposition: Mitigated in Principle 5, success criterion CH-006, and the
  proposed non-goals.
- Residual risk: The actual boundary cannot be validated until both roles run
  through a complete lifecycle.

### C-003: Rollback language overpromises application-state recovery

- Severity: Critical
- Claim: Replacing an OS artifact does not transactionally revert databases,
  container volumes, home directories, credentials, or other mutable state.
- Required response: Make state-owner compatibility and recovery contracts a
  success criterion; explicitly reject transparent rollback of arbitrary
  workload state.
- Disposition: Resolved in CH-005 and the proposed non-goals. Detailed state
  design remains a gate for DES-0001.
- Residual risk: An OS rollback may remain unsafe until individual schemas are
  inventoried and tested.

### C-004: “Not a derivative” was ambiguous

- Severity: Medium
- Claim: The original wording could be read as rejecting Arch or Fedora
  packages even though their use as build inputs remains an open decision.
- Required response: Reject maintenance of a downstream packaging fork, not
  package reuse.
- Disposition: Resolved by revised non-goal wording.

### C-005: Cryptographic identity may be mistaken for complete provenance

- Severity: Medium
- Claim: A hash identifies bytes but does not establish trustworthy source,
  builder identity, input completeness, or qualification.
- Required response: Keep artifact identity, provenance, and test evidence as
  separate linked properties.
- Disposition: Resolved in CH-002 and CH-003; later trust designs must not
  collapse these properties into one signature.

### C-006: Systemd-first can create confirmation bias

- Severity: High
- Claim: Starting every evaluation with a preferred ecosystem can suppress
  evidence of architectural gaps.
- Required response: Require comparison against accepted requirements and
  preserve an exception path.
- Disposition: Accepted risk governed by ADR-0001. Principle 7 requires current
  evidence and Principle 5 permits role-driven divergence.

### C-007: Minimalism can become an unmeasured goal

- Severity: Medium
- Claim: Removing Perl, initrds, modules, or generic kernel support can increase
  build and recovery cost without meaningful runtime benefit.
- Required response: Require measurements and preserve a general recovery path
  while specialization is being justified.
- Disposition: Resolved by new Principle 11 and an explicit non-goal.

### C-008: The success criteria were not verifiable

- Severity: High
- Claim: The original bullets described good properties but did not identify
  evidence that would demonstrate project success.
- Required response: Assign stable identifiers and observable evidence.
- Disposition: Resolved by criteria CH-001 through CH-007.

## Recommendation

Ratify the proposed success criteria, eleven principles, and proposed
non-goals as a coherent initial policy set. Keep the distinguishing invariant
provisional until the existing-system comparison satisfies CH-001. Reopen the
policy set if the workstation/router comparison invalidates the common
lifecycle or if a state owner cannot meet the rollback contract.

## Decision

Accepted by Jason Tarasovic on 2026-08-09. The charter, principles, scope,
success criteria, and non-goals are ratified as the initial project policy set.
The distinguishing invariant remains provisional pending CH-001.
