---
id: RR-0002
subject: RES-0003 bootc versus systemd-sysupdate
reviewer: Codex adversarial pass
date: 2026-08-09
status: open
---

# bootc versus systemd-sysupdate review

## Review limitation

This is an AI-assisted adversarial pass over primary upstream documentation.
Neither candidate has been operated for NeutrinOS, so maturity, recovery, and
maintenance judgments remain hypotheses.

## Summary judgment

SYS-030 resolves the paper-stage burden of proof in favor of the direct
systemd/UAPI composition. bootc remains operationally stronger as an integrated
lifecycle product, but its documented production path does not currently
demonstrate the accepted boot-to-root claim. This is not substrate selection:
the systemd path can still fail on reliability, recovery, or owner effort.

## Challenges

### C-001: “Complete lifecycle product” may import an unwanted ecosystem

- Severity: Critical
- Claim: bootc brings OSTree, container image libraries, registry policy,
  backend transitions, and distribution-specific base-image conventions.
- Failure or cost if true: NeutrinOS trades visible integration code for a
  larger transitive stack whose roadmap it does not control.
- Required response: count dependencies and owned compatibility surfaces in
  the spike; compare day-two debugging and upgrade work, not command count.
- Disposition: Open.

### C-002: The production bootc path does not match the desired trust sketch

- Severity: Critical
- Claim: systemd-boot and sealed UKI/composefs behavior currently require the
  experimental backend, while the stable production path is OSTree-based.
- Failure or cost if true: NeutrinOS either abandons its intended trust model,
  adopts experimental storage, or plans a disruptive backend migration.
- Required response: accept the threat and trust requirements before substrate
  selection, then evaluate only production-supported paths against them.
- Disposition: Resolved at the current documentation boundary. SYS-030 is
  accepted, so the proposed preference is reversed; a production-supported
  bootc path may reopen the finding.

### C-003: OCI convenience can violate the data-first authoring boundary

- Severity: High
- Claim: a collection of layered Containerfiles and `RUN` scripts is another
  Turing-complete machine configuration repository.
- Failure or cost if true: the project recreates the Nix experience with shell
  and container layers while claiming compliance because the output is OCI.
- Required response: make the role and machine source of truth satisfy
  SYS-014–SYS-016 and classify any Containerfile as generated output or
  separately owned build implementation.
- Disposition: Guardrail accepted; concrete proof remains open.

### C-004: systemd-first is being relaxed exactly when it becomes costly

- Severity: High
- Claim: calling bootc “more complete” may excuse bypassing the accepted
  ecosystem preference whenever integration work appears.
- Failure or cost if true: ADR-0001 has no practical effect on major choices.
- Required response: record the missing systemd product-level capabilities and
  the measurable ownership they transfer to NeutrinOS. Revisit the exception if
  systemd gains an equivalent supported lifecycle surface.
- Disposition: Mitigated in the explicit ADR-0001 exception analysis.

### C-005: sysupdate's composability may be a feature, not missing product

- Severity: High
- Claim: NeutrinOS wants explicit state, trust, qualification, and fleet
  contracts. Owning their composition may be the project rather than wasteful
  glue.
- Failure or cost if true: bootc's existing opinions become constraints, and
  NeutrinOS builds adapters around them anyway.
- Required response: identify the project-specific layer after state and trust
  designs; compare its size and clarity on both candidates.
- Disposition: Open.

### C-006: Documentation maturity is not operational reliability

- Severity: Critical
- Claim: neither stable APIs nor elegant component boundaries prove safe
  interrupted updates, rollback, recovery, or comprehensible failures.
- Failure or cost if true: the substrate decision becomes expensive to reverse
  after role configuration and release infrastructure depend on it.
- Required response: execute the symmetric lifecycle scenarios in RES-0003
  before the substrate ADR and preserve the raw evidence.
- Disposition: Open, correctly deferred until implementation spikes are
  authorized.

## Required changes before acceptance

1. Complete the remaining trust and concrete state requirements relevant to the
   substrate.
2. Specify exact, symmetric spike procedures and pass/fail thresholds.
3. Obtain independent human review of the candidate weighting.
4. Run the spikes before accepting a substrate ADR.

## Recommendation

Accept RES-0003 only as an **in-review burden-of-proof result**. Let bootc be
the default candidate while the missing requirements are formalized. Do not
convert that default into an architectural dependency or implementation plan.
