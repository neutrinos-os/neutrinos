---
design: DES-0009
reviewer: Codex adversarial pass
perspective: security, operations, failure, maintainability, alternatives
date: 2026-08-10
status: open
---

# Fleet release promotion and rollout control review

## Summary judgment

The proposal correctly prevents a rollout server from becoming a second release
authority or updater. Its strongest feature is the separation among exact
authorization, rollout grants, local eligibility, and availability scheduling.

The strongest reason to reject it is proportionality. Eleven new requirements
and several evidence objects could bury a three-machine fleet under ceremony.
The design is acceptable only if one simple representation supports both an
attended initial procedure and later automation without inventing a distributed
control plane.

## Challenges

### C-001: The design is a fleet manager disguised as static metadata

- Severity: critical
- Claim: plans, revisions, grants, observations, indexes, and status joins are
  enough machinery to recreate a bespoke fleet service.
- Evidence: the proposal requires coordination across machines and time even
  when no live controller exists.
- Failure or cost if true: implementation and maintenance exceed the value for
  three machines.
- Required response or experiment: EX-0011 must encode and execute a complete
  rollout with ordinary files and a small bounded procedure, then measure owner
  time and irreducible fields.
- Author response: each object is a semantic authority boundary; formats may be
  collapsed when independent verification remains possible.
- Disposition: open.
- Residual risk: a future UI may quietly make its database authoritative.

### C-002: A rollout grant duplicates release authorization

- Severity: high
- Claim: two signed permissions over the same deployment add ceremony without
  an independent security boundary.
- Evidence: both records can contain deployment and scope identities.
- Failure or cost if true: operators cannot explain which signer is needed and
  clients implement conflicting precedence.
- Required response or experiment: compare a separately signed grant with a
  deterministic derivation from signed plan revisions; document exact authority
  each option adds.
- Author response: release authorization answers whether use is permitted;
  rollout grants bound timing, cohort, transition, and action. They need not use
  distinct signatures if those claims remain separable.
- Disposition: mitigated, pending mechanism exercise.
- Residual risk: combined envelopes can still blur the distinction in tooling.

### C-003: Tiny cohorts provide no statistical safety

- Severity: high
- Claim: one canary success says little about another platform or role, while
  one failure can stop every release.
- Evidence: the initial fleet is heterogeneous and includes singleton roles.
- Failure or cost if true: rollout adds delay without reducing the relevant
  failure probability.
- Required response or experiment: every cohort must state what behavior it
  covers and cannot cover; use role-specific VMs and stricter attended gates for
  unrepresented physical targets.
- Author response: cohorts are ordered evidence scopes, not statistical claims.
- Disposition: mitigated.
- Residual risk: physical-only firmware and peripheral failures remain first-
  occurrence risks.

### C-004: Missing telemetry can freeze the fleet indefinitely

- Severity: high
- Claim: counting unreachable machines as neither success nor failure prevents
  advancement during ordinary travel, shutdown, or network loss.
- Evidence: personal machines are not continuously online.
- Failure or cost if true: routine releases require manual cleanup of every
  absent member.
- Required response or experiment: plans need observation deadlines and an
  explicit disposition for missing members: exclude before start, defer with an
  owner and expiry, or accept risk through a new decision.
- Author response: missing cannot silently become success, but it need not block
  forever.
- Disposition: resolved in the gate and deferral model.
- Residual risk: careless exclusions can hide chronically stale machines.

### C-005: Cached activation grants create an offline vulnerability window

- Severity: critical
- Claim: a target may activate a now-withdrawn deployment while unable to learn
  about withdrawal.
- Evidence: offline operation and revocation are inherently in tension.
- Failure or cost if true: compromise or severe vulnerability continues after a
  fleet-wide stop decision.
- Required response or experiment: bind cached grants to exact action and short
  declared knowledge windows; distinguish safe boot continuity from permission
  to begin a new trial; report knowledge time.
- Author response: offline exposure cannot be eliminated without an online boot
  dependency. Policy bounds and exposes it.
- Disposition: accepted-risk subject to role-specific freshness exercises.
- Residual risk: the router may need a longer offline window than desired.

### C-006: A compromised target can graduate its cohort

- Severity: critical
- Claim: malware in the candidate can report health and cause expansion.
- Evidence: the target produces many local observations after it boots.
- Failure or cost if true: one compromised canary becomes a fleet-wide release
  oracle.
- Required response or experiment: scope local blessing to that machine, use
  independent checks for externally observable role behavior, authenticate
  observations, and require more than candidate-controlled self-report for
  consequential gates.
- Author response: SYS-039 already prevents local blessing from becoming global
  qualification; this design carries the same limit into rollout.
- Disposition: mitigated.
- Residual risk: workstation correctness includes user-visible behavior that is
  difficult to assess externally.

### C-007: Pause races with an already issued reboot

- Severity: critical
- Claim: a machine can pass its last server check immediately before a pause and
  reboot into the bad candidate.
- Evidence: distributed decisions cannot revoke a consumed grant instantly.
- Failure or cost if true: blast radius exceeds the operator's apparent pause
  point.
- Required response or experiment: define the point of no return, action-
  specific short-lived grants, local recheck immediately before selection, and
  status that reports grants already consumed or in flight.
- Author response: pause is bounded, not instantaneous; the UI must show the
  maximum in-flight set.
- Disposition: open pending EX-0011.
- Residual risk: network partitions preserve an unavoidable race window.

### C-008: Reboot locking harms availability after coordinator failure

- Severity: high
- Claim: leaked locks can block all future maintenance, while expiring leases
  can allow overlapping reboots after a partition.
- Evidence: FleetLock-like coordination is a distributed lease problem.
- Failure or cost if true: either the release stalls or dependent services go
  down together.
- Required response or experiment: use reboot coordination only for real shared
  failure domains, bound leases, reconcile ownership after boot, and test both
  leaked and duplicate slots.
- Author response: the initial fleet probably needs attended windows rather than
  a lock service.
- Disposition: mitigated.
- Residual risk: any future clustered role needs a stronger availability model.

### C-009: Percentage rollouts silently reshuffle membership

- Severity: high
- Claim: changing fleet size, hashes, or backend state moves machines between
  phases and destroys reconstruction.
- Evidence: common phased systems calculate offers dynamically.
- Failure or cost if true: the actual blast radius cannot be proven later.
- Required response or experiment: freeze the inventory snapshot and cohort
  algorithm/version; materialize membership for small fleets.
- Author response: the proposal requires exact members or a deterministic
  selector over a frozen snapshot.
- Disposition: resolved.
- Residual risk: large future fleets may resist materialized membership.

### C-010: A stale pin becomes accidental long-term support

- Severity: high
- Claim: a healthy pinned machine may remain vulnerable while operators assume
  retained means supported.
- Evidence: retained, healthy, current, and supported are independent states.
- Failure or cost if true: known exposure persists without a remediation owner.
- Required response or experiment: pins require reason, expiry/review,
  consequence, and remediation; withdrawal outranks normal pins.
- Author response: status remains explicitly stale or unsupported.
- Disposition: resolved.
- Residual risk: a single maintainer can still repeatedly renew accepted risk.

### C-011: Emergency rollout normalizes bypasses

- Severity: critical
- Claim: every inconvenient release can be labeled urgent and skip cohorts.
- Evidence: expedited paths tend to become the easiest path.
- Failure or cost if true: normal qualification and blast-radius controls become
  ceremonial.
- Required response or experiment: bind emergency use to the maintenance-policy
  incident classification, record skipped gates and reduced claims, impose a
  follow-up obligation, and report its frequency.
- Author response: emergency changes timing, not identity or minimum evidence.
- Disposition: mitigated.
- Residual risk: governance remains mostly self-discipline in the personal phase.

### C-012: Omaha or Cincinnati semantics are mistaken for NeutrinOS authority

- Severity: high
- Claim: a valid server response, group, channel, version, or graph edge is
  treated as sufficient permission to select a deployment.
- Evidence: upstream protocols have their own identity and trust assumptions.
- Failure or cost if true: the chosen service bypasses exact deployment and
  local eligibility policy.
- Required response or experiment: map every upstream field to the canonical
  dictionary, preserve raw responses, and inject a valid response naming an
  unauthorized or incompatible payload.
- Author response: upstream systems may supply discovery and rollout decisions;
  targets still enforce NeutrinOS authorization and eligibility.
- Disposition: open pending comparison and exercise.
- Residual risk: a large adapter could negate the value of adoption.

## Missing alternatives or evidence

- A literal minimal signed-record representation.
- Omaha/Nebraska field and trust-boundary mapping for a non-Flatcar payload.
- Cincinnati graph mapping to NeutrinOS release and deployment identities.
- A systemd-native host execution sketch that does not become a second updater.
- Measured normal and emergency operator time.
- A representative external router health observer and alternate-access path.
- A concrete clock, epoch, and replay policy for offline machines.
- An explicit decision on whether rollout observations enter permanent release
  evidence or a shorter-lived private operations class.

## Required changes before design acceptance

1. Decide whether rollout grants are signed records or derived decisions.
2. Execute EX-0011 with the actual reference fleet inventory.
3. Demonstrate pause and withdrawal races with bounded in-flight actions.
4. Demonstrate offline, stale-clock, replay, and controller-restore behavior.
5. Compare minimal records with Nebraska and Cincinnati-derived approaches.
6. Define role-specific observation and maintenance-window contracts.
7. Quantify record count, private telemetry, infrastructure, and owner time.
