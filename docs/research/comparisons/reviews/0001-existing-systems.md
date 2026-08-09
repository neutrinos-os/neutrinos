---
id: RR-0001
subject: RES-0001 existing-system comparison
reviewer: Codex adversarial pass
date: 2026-08-09
status: open
---

# Existing-system comparison review

## Review limitation

This is an AI-assisted adversarial pass, not independent human review. It tests
the comparison for motivated reasoning and unsupported rejection. It cannot
replace hands-on evaluation or an operator's account of the existing NixOS
deployment.

## Summary judgment

The comparison is strong enough to reject a greenfield NeutrinOS substrate and
to narrow the proposed project boundary. It is not strong enough to establish
that NeutrinOS should exist as a distinct framework. Its largest weakness is
selection bias: the accepted systemd-first posture makes ParticleOS feel
architecturally natural even though bootc is more mature in key areas. NixOS
also remains technically stronger in composition and testing, although the
owner's documented experience now establishes a material authoring-model
conflict.

## Challenges

### C-001: The preferred conclusion may be encoded in the premise

- Severity: Critical
- Claim: ADR-0001 can make native systemd composition appear preferable before
  lifecycle cost and reliability have been compared.
- Evidence: bootc describes a stable transactional API, while ParticleOS
  explicitly disclaims backward compatibility.
- Failure or cost if true: NeutrinOS inherits integration and maintenance work
  merely to preserve an ecosystem preference.
- Required response: identify a material accepted requirement that bootc
  cannot reasonably meet, or select bootc.
- Author response: RES-0003 makes bootc the default substrate candidate under
  current accepted requirements and requires symmetric lifecycle spikes before
  an ADR. No systemd-native selection is proposed.
- Disposition: Mitigated at the documentation stage; final selection remains
  open pending trust and state requirements and operating evidence.
- Residual risk: later requirements could be written to rationalize the
  preferred substrate.

### C-002: NixOS may already satisfy the claimed distinction

- Severity: Critical
- Claim: Declarative multi-role configuration, image construction, generation
  rollback, and VM tests already cover most of the invariant. External image
  appliance support may close the remaining lifecycle gap.
- Evidence: the NixOS manual documents each mechanism. The owner's
  `nixconfig` retrospective now documents a different kind of gap: Nix
  language, module, deployment, and abstraction costs in actual operation.
- Failure or cost if true: NeutrinOS duplicates a mature module and test
  ecosystem with fewer maintainers.
- Required response: translate actual NixOS operating pain into requirements
  and determine whether appliance mode changes the relevant authoring model,
  not only artifact delivery.
- Author response: RES-0002 records the repository evidence and derives
  SYS-014 through SYS-018. Appliance mode does not remove Nix evaluation or
  the NixOS module system from machine authorship.
- Disposition: Resolved for candidate selection. SYS-014 through SYS-018 were
  accepted through PR-0002, so NixOS is rejected as the primary configuration
  and deployment framework.
- Residual risk: a data-first requirement could be aesthetic discomfort in
  architectural language, or could cause NeutrinOS to invent a worse module
  system. The bounded/native-input distinction must be enforced.

### C-003: ParticleOS resemblance is not proof of a sustainable base

- Severity: High
- Claim: Similarity to the desired architecture demonstrates feasibility, not
  stability, support, or an appropriate dependency boundary.
- Evidence: ParticleOS states that it is in development and makes no backward-
  compatibility guarantee.
- Failure or cost if true: a fork or tight dependency makes NeutrinOS absorb
  upstream churn and effectively maintain another distribution.
- Required response: define exactly what is reused and prefer stable systemd,
  UAPI, and mkosi interfaces over private ParticleOS structure.
- Author response: the comparison proposes ParticleOS as an executable
  reference only, pending an explicit relationship decision.
- Disposition: Mitigated; dependency boundary remains open.
- Residual risk: copying configuration can create a de facto fork even without
  repository history.

### C-004: Exact-artifact qualification is not a unique substrate feature

- Severity: High
- Claim: Any candidate can attach CI results to immutable artifact digests if
  project policy is added around it.
- Evidence: bootc/OCI images, Nix store closures or appliance images, OSTree
  commits, and DDIs can all be assigned stable identities.
- Failure or cost if true: the provisional invariant does not justify a new
  named framework; it describes a release discipline.
- Required response: explicitly identify the reusable policy artifact the
  project will produce, or accept that NeutrinOS may remain a repository for a
  personal deployment rather than a distinct architecture.
- Author response: the proposed project layer is narrowed to role schemas,
  state contracts, evidence, qualification, and fleet policy. Whether that
  deserves a reusable framework remains open.
- Disposition: Open.
- Residual risk: branding can outpace substantive differentiation.

### C-005: Product specialization is being treated asymmetrically

- Severity: Medium
- Claim: GNOME OS and Flatcar are rejected for narrow product boundaries, but
  ParticleOS's desktop-oriented assumptions may receive more accommodation.
- Evidence: ParticleOS includes desktop profiles and systemd-homed policy;
  multi-role router evidence has not been shown.
- Failure or cost if true: supposedly reusable upstream policy leaks into the
  common model and makes the router an exception.
- Required response: use the router to test every borrowed assumption and keep
  integration examples distinct from project policy.
- Author response: the proposed boundary reuses mechanisms and selected
  configuration, not ParticleOS product policy.
- Disposition: Mitigated.
- Residual risk: the boundary is theoretical until role designs exist.

### C-006: Documentation review underweights operations

- Severity: High
- Claim: Documentation cannot establish interrupted-update behavior, recovery
  ergonomics, artifact promotion integrity, or day-two maintenance cost.
- Evidence: no candidate has been installed, updated, broken, and recovered as
  part of this review.
- Failure or cost if true: the selection optimizes an architecture diagram and
  discovers operational defects only after implementation is committed.
- Required response: after requirements are accepted and before the substrate
  ADR, run bounded lifecycle spikes for the final candidates.
- Author response: recorded as a gate for a later implementation phase; the
  project is intentionally still in documentation and requirements work.
- Disposition: Open, correctly deferred.
- Residual risk: implementation momentum can make the spike ceremonial.

### C-007: Upstream security maintenance remains unowned

- Severity: High
- Claim: An image pipeline does not answer who notices, supplies, rebuilds,
  qualifies, and deploys a security fix.
- Evidence: the package ecosystem and snapshot policy remain undecided.
- Failure or cost if true: exact artifacts improve identity but remain stale or
  vulnerable without an operable response loop.
- Required response: keep package-source maintenance as a separate gating
  decision and include it in substrate total cost.
- Author response: explicitly excluded from closure and retained as L-001 and
  L-002.
- Disposition: Open.
- Residual risk: the personal-fleet boundary can obscure accumulated response
  burden.

## Required changes before acceptance

1. Obtain an independent human review of RES-0001.
2. Accept or revise RES-0003 after its prerequisite requirements and symmetric
   lifecycle spikes are complete.
3. Define the ParticleOS relationship without creating an implicit fork.
4. Keep CH-001 open until those dispositions are recorded.

## Recommendation

Accept RES-0001 as an **in-review research result** and use it to constrain the
next requirements work. Do not yet accept the distinguishing invariant, select
a substrate, or create an implementation plan.
