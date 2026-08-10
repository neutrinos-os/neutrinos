---
design: DES-0011
reviewer: Codex adversarial pass
perspective: security, operations, failure, maintainability, alternatives
date: 2026-08-10
status: open
---

# Secret custody and credential delivery review

## Summary judgment

The design correctly demotes “secret store” from an architectural answer to one
component in a scoped flow. Systemd credentials are a convincing last-mile
default, but the proposal is not ready to choose an online issuer, envelope
format, PKI, or host encryption mode.

The strongest objection is operational proportionality. Per-consumer grants,
versions, epochs, offline envelopes, compromise graphs, and restart coordination
could become a private Vault-like platform for three machines. The design is
acceptable only if EX-0013 demonstrates a boring attended baseline whose record
model can later admit automation without requiring it now.

## Challenges

### C-001: systemd credentials are being mistaken for a secret manager

- Severity: critical
- Claim: activation-scoped files do not issue, authorize, distribute, renew,
  revoke, back up, or recover secrets.
- Failure or cost if true: the project invents these semantics accidentally in
  unit files and scripts.
- Required response or experiment: map every baseline step to a named owner,
  record, and upstream primitive; leave systemd responsible only for final
  service delivery.
- Author response: the proposed model explicitly separates contract, grant,
  custody, transport, and delivery.
- Disposition: resolved in design; mechanism open.

### C-002: the contract is a custom configuration schema in disguise

- Severity: critical
- Claim: a large project schema may recreate the NixOS-style abstraction that
  the project rejected.
- Failure or cost if true: new upstream credential features are blocked until
  NeutrinOS exposes them.
- Required response or experiment: keep the contract an authorization and
  lifecycle boundary, preserve literal native unit configuration, and allow a
  reviewed upstream-native path whose effects remain classified.
- Author response: contracts describe ownership and effects rather than
  reproduce every systemd or application option.
- Disposition: mitigated; EX-0013 must show the literal representation.

### C-003: root or the target service can simply steal the plaintext

- Severity: critical
- Claim: namespacing and ramfs do not protect a credential from privileged host
  compromise or from the process legitimately consuming it.
- Failure or cost if true: documentation overstates the runtime security
  boundary and delays necessary rotation.
- Required response or experiment: state the boundary honestly, minimize scope
  and lifetime, prefer non-exportable/application-native operations where
  justified, and make machine compromise drive dependent credential rotation.
- Author response: accepted as a threat-model limit, not treated as solved by
  systemd credentials.
- Disposition: accepted limitation with bounded blast radius.

### C-004: host-bound encryption makes recovery impossible

- Severity: critical
- Claim: combining TPM state and a key under `/var` can make a restored disk or
  replacement board unable to decrypt its credential store.
- Failure or cost if true: machine or service restoration fails precisely
  during hardware loss.
- Required response or experiment: classify values as replaceable, reissuable,
  or independently recoverable; exercise TPM clear, lost `/var`, disk and board
  replacement; never claim backup from copied ciphertext alone.
- Author response: systemd-creds host binding is a candidate local store, not a
  universal backup format.
- Disposition: open pending EX-0013.

### C-005: a separate machine encryption key expands identity ceremony

- Severity: high
- Claim: remotely or offline encrypting to a machine may require another key,
  certificate, attestation, rotation, and recovery path.
- Failure or cost if true: enrollment complexity doubles and keys are reused
  unsafely to avoid it.
- Required response or experiment: compare authenticated ephemeral transfer,
  dedicated key agreement, and locally re-sealed administrative envelopes;
  reuse an identity key only if its algorithm and policy explicitly permit it.
- Author response: exact envelope recipient remains open.
- Disposition: open.

### C-006: a credential can smuggle arbitrary privileged policy

- Severity: critical
- Claim: an issuer can place a script, unit, firewall fragment, or template in a
  signed and correctly delivered credential.
- Failure or cost if true: late-bound input replaces qualified configuration.
- Required response or experiment: use per-contract schemas and semantic
  allowlists; inject executable and policy-shaped payloads at every adapter.
- Author response: encryption and issuer authentication do not reclassify
  policy as data.
- Disposition: mitigated; test required.

### C-007: unit scoping is illusory when a shared fetcher has all secrets

- Severity: critical
- Claim: a privileged agent or AF_UNIX broker that can fetch every secret
  becomes the fleet-wide local compromise point.
- Failure or cost if true: compromise of one adapter exposes unrelated users,
  workloads, and services.
- Required response or experiment: authenticate the local consumer, enforce
  grant scope before retrieval, minimize cached plaintext, and test hostile
  sibling units and workloads.
- Author response: the systemd delivery directory is only the final boundary;
  brokers need their own exact authorization model.
- Disposition: open until an adapter exists.

### C-008: rotation is not atomic for a running service

- Severity: high
- Claim: systemd credentials are immutable during an activation, while remote
  peers and local services may switch keys at different times.
- Failure or cost if true: outage, authentication split brain, or indefinite
  retention of the old key.
- Required response or experiment: model prepare, overlap, activate, verify,
  retire, and rollback; test both native renewal and restart/drain paths.
- Author response: file replacement is not treated as successful rotation.
- Disposition: open pending EX-0013.

### C-009: offline availability defeats rapid revocation

- Severity: critical
- Claim: a router using a cached key while disconnected cannot learn that it
  was revoked.
- Failure or cost if true: a compromised credential remains usable longer than
  status implies.
- Required response or experiment: declare maximum offline validity and clock
  policy per contract, distinguish local expiry from observed revocation, and
  expose authority knowledge time.
- Author response: this is an explicit per-role tradeoff.
- Disposition: accepted tradeoff; numeric bounds open.

### C-010: backup and diagnostics leak everything anyway

- Severity: critical
- Claim: plaintext or decryptable envelopes enter journals, command history,
  coredumps, support bundles, backups, swap, or returned seed media.
- Failure or cost if true: narrow runtime delivery provides false confidence.
- Required response or experiment: inspect each path with recognizable canary
  values; verify redaction, dump policy, non-swappable storage, media cleanup,
  and backup classification.
- Author response: remanence testing is required evidence.
- Disposition: open pending EX-0013.

### C-011: enrollment becomes automatic secret entitlement

- Severity: critical
- Claim: any key bound to a machine record may receive all role secrets,
  including after quarantine or on an unsupported deployment.
- Failure or cost if true: one mistaken enrollment becomes immediate privilege
  escalation.
- Required response or experiment: require an exact credential grant distinct
  from enrollment and bind optional lifecycle/health prerequisites.
- Author response: enrollment identifies the subject; grants authorize
  delivery.
- Disposition: resolved in design.

### C-012: the design is too elaborate for the initial fleet

- Severity: critical
- Claim: operating a bespoke issuer and protocol will cost more and be less
  secure than manual placement of a few root-owned files.
- Failure or cost if true: the project stalls or runs unreviewed shortcuts.
- Required response or experiment: implement the tabletop first with signed
  static records, attended transfer, local sealing, and systemd delivery;
  measure steps and only add a service for demonstrated rotation or scale.
- Author response: no permanent secret service is required by the policy.
- Disposition: mitigated; owner-cost gate remains.

## Acceptance blockers

Before accepting a concrete mechanism, the project needs:

1. a literal credential-contract example for one workstation and one router
   service;
2. an online and offline flow producing equivalent authorization semantics;
3. recovery results for host-bound storage;
4. a successful service rotation and a failed rotation recovery;
5. boot-mode isolation and hostile-consumer results;
6. remanence inspection; and
7. measured owner steps, dependencies, and recurring maintenance.

## Recommendation

Accept the proposed policy requirements if their language remains substrate-
neutral. Do not yet accept a secret backend, envelope format, PKI, credential
encryption mode, or new daemon. Preserve systemd credentials as the default
service interface and require evidence for exceptions.
