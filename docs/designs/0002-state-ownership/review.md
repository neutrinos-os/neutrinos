---
design: DES-0002
reviewer: Codex adversarial pass
perspective: failure, operations, security, maintainability
date: 2026-08-09
status: open
---

# State ownership and rollback contract review

## Summary judgment

The proposal gives “rollback” an honest and testable meaning and prevents
`/etc` or `/var` from becoming undifferentiated mutable escape hatches. Its
strongest reason for rejection is operational cost: a detailed state contract
for every component can become a second packaging database that one person
cannot maintain.

## Challenges

### C-001: Reconstructed `/etc` may break ordinary Linux software

- Severity: critical
- Claim: packages and administrative tools routinely expect durable writable
  files in `/etc`, sometimes without an alternative location.
- Failure or cost if true: normal upgrades lose configuration or require a
  growing set of fragile projections and exceptions.
- Required response or experiment: inventory writes to `/etc` on both reference
  roles, test a transient view, and establish a simple persistent-exception
  mechanism before accepting the default.
- Author response: persistent exceptions are permitted but must be individually
  owned and tested; the substrate spike must exercise them.
- Disposition: open.
- Residual risk: upstream behavior can change and add new writes after an
  apparently complete inventory.

### C-002: The state inventory can recreate configuration-module complexity

- Severity: critical
- Claim: schema, compatibility, backup, reset, sensitivity, and health metadata
  for every state item could become an enormous custom DSL and maintenance
  burden.
- Failure or cost if true: NeutrinOS repeats the Nix failure one layer lower,
  spending more time describing metadata than operating machines.
- Required response or experiment: begin with lifecycle-significant namespaces,
  allow direct native contracts, measure required metadata for workstation and
  router, and reject fields that do not drive a gate or operation.
- Author response: the proposed fields are obligations, not necessarily one
  universal schema. The representation remains open.
- Disposition: open.
- Residual risk: enforcement may be inconsistent if contracts are distributed
  across native formats.

### C-003: Backward-compatible state can block necessary updates

- Severity: critical
- Claim: databases and security-sensitive formats sometimes require
  forward-only migrations. Requiring the previous release to remain healthy can
  indefinitely delay urgent fixes.
- Failure or cost if true: rollback policy competes with security response and
  produces stale deployments.
- Required response or experiment: define an explicit maintenance release path
  with backup, commit barrier, recovery objective, and minimum emergency gates.
- Author response: forward-only migration is allowed only when the normal
  rollback claim is withdrawn visibly; its relationship to the accepted
  emergency policy remains to be designed.
- Disposition: open.
- Residual risk: “maintenance operation” can become a routine loophole.

### C-004: A locally-modified status does not control dangerous drift

- Severity: high
- Claim: an administrator can acknowledge or ignore the marker while the
  override continues to invalidate qualification and security assumptions.
- Failure or cost if true: fleet status is accurate but operational safety is
  not improved.
- Required response or experiment: define which overrides block automatic
  rollout, which merely warn, how they expire, and how recovery can disable
  them.
- Author response: retained as an open policy decision under C-002 and L-006.
- Disposition: open.
- Residual risk: overly strict blocking may prevent emergency remediation.

### C-005: Ownership categories overlap in real systems

- Severity: high
- Claim: UID allocation, Wi-Fi credentials, container storage, TPM state, and
  service accounts can span release, machine, user, and workload lifecycles.
- Failure or cost if true: forcing one owner hides shared invariants or creates
  contradictory contracts.
- Required response or experiment: require one accountable primary owner while
  recording dependent contracts and compatibility edges; test identity as a
  cross-cutting case.
- Author response: accepted as a needed refinement; path and Unix ownership are
  already explicitly non-authoritative.
- Disposition: mitigated; dependency representation remains open.
- Residual risk: cross-owner upgrade ordering can still form cycles.

### C-006: Preserving state can preserve compromise

- Severity: critical
- Claim: OS repair or rollback that preserves credentials, executable local
  configuration, user state, and workload data can reintroduce an attacker's
  persistence.
- Failure or cost if true: the recovery procedure restores availability without
  restoring trustworthiness.
- Required response or experiment: the threat model must distinguish
  availability recovery from compromise recovery and define when identity,
  overrides, secrets, or all mutable state must be destroyed.
- Author response: factory reset and re-enrollment scopes are separated. EX-0003
  now makes no automatic mount, execution, or restoration the compromise-
  recovery default and requires owner-aware quarantine, selective restore,
  regeneration, re-enrollment, or destruction. The concrete state-contract
  inventory and hostile-state procedure remain open under S-005 and S-006.
- Disposition: mitigated at the policy level; state mechanisms and exercises
  remain open.
- Residual risk: operators may choose preservation before knowing whether state
  is trustworthy.

### C-007: Diagnostics can leak secrets or exhaust constrained storage

- Severity: high
- Claim: retaining logs across failed deployments can preserve credentials,
  personal data, or attacker-controlled volume and fill a router's disk.
- Failure or cost if true: recovery evidence becomes a confidentiality or
  availability failure.
- Required response or experiment: define redaction, access, rotation, quota,
  and export behavior per role; failure injection must include full storage.
- Author response: operational evidence is explicitly governed by retention and
  sensitivity policy; concrete limits remain role decisions.
- Disposition: open.
- Residual risk: useful failure evidence may be lost under strict limits.

## Missing alternatives or evidence

- An empirical `/etc` write inventory for the initial workstation and router
  package sets.
- Representative state contracts for one database, rootless container storage,
  network identity, and a user home.
- A comparison of bootc transient `/etc`, persistent three-way merge, and a
  systemd-confext-style rendered view.
- Measured operator work for backup verification and forward-only migration.

## Required changes before acceptance

1. Decide whether reconstructed `/etc` is the accepted default or a hypothesis
   for the substrate spike.
2. Define the minimum viable state-contract fields using real role examples.
3. Reconcile forward-only migrations with emergency release policy.
4. Add compromise-recovery requirements after the threat model begins.
5. Obtain independent human review and dispose of every critical challenge.

## Owner direction

Jason Tarasovic accepted the policy direction and SYS-019 through SYS-026 on
2026-08-09 through
[PR-0003](../../project/reviews/0003-state-ownership-requirements.md). This
review remains open because accepting the requirements does not establish that
the proposed `/etc`, inventory, migration, and recovery mechanisms are yet
operable.
