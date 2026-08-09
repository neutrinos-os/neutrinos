---
status: accepted
last_updated: 2026-08-09
---

# Maintenance and security policy

## Scope

This policy defines a realistic operating commitment for the personal-fleet
phase. It is an internal standard for deciding whether a machine can be called
current and supported. It is not a service-level agreement or promise to
external users.

## Commitment

NeutrinOS maintains one current release line. Development moves forward from
current upstream inputs; the project does not initially maintain long-term
branches or routinely backport fixes to older releases.

Previous deployments and artifacts may be retained as known-good rollback or
recovery choices, but their presence does not make them security-maintained
releases. A machine running an older deployment must be identifiable as stale
or intentionally pinned rather than silently reported as current.

The project provides best-effort security response appropriate to a
single-maintainer personal fleet. It promises prioritization and a defined
process, not continuous monitoring or clock-based response times.

## Software ownership boundary

The maintenance commitment applies to:

- OS artifacts produced and signed by the project
- project-owned role and machine configuration
- project-produced extensions that participate in the trusted system
- build and release infrastructure whose compromise could affect an artifact

User-managed tools, project environments, graphical application stores,
containers, microVM workloads, firmware, and third-party services require
separate ownership and update policies. Their boundaries must remain visible;
installing them must not imply that the base OS maintains them.

## Release maintenance model

- A release is current only after its exact artifacts and relevant role
  configuration pass the required qualification gates.
- Normal maintenance consumes new upstream package and source inputs, rebuilds
  the release artifacts, and qualifies them as a unit.
- Runtime mutation by a package manager is not the normal security-update
  mechanism for OS-owned files.
- Downstream patches are exceptional. They must be linked to their source,
  reason, affected versions, upstream status, and removal condition.
- Normal release cadence remains open until the package-input and build models
  are selected. Security work may create an out-of-band release.
- At least one usable recovery path must survive release replacement, but a
  vulnerable rollback artifact may require restricted use, replacement, or
  removal after recovery confidence is restored.

## Vulnerability and incident process

For each reported issue affecting a deployed or releasable component:

1. Determine whether the component and vulnerable code are present in an
   artifact or trusted build path.
2. Determine exploitability in the actual role and configuration rather than
   relying only on a generic severity score.
3. Record affected releases, machines, configuration, and trust boundaries.
4. Select containment, update, withdrawal, credential rotation, or recovery
   actions.
5. Build and run the required qualification gates on the resulting artifacts.
6. Deploy, verify machine health, and record closure or residual risk.

### Emergency

Emergency work takes precedence over unrelated project work when an issue has
credible active exploitation or enables material remote compromise, signing or
build-chain compromise, loss of persistent data, or bypass of a relied-upon
trust boundary.

Response is immediate best effort after discovery. Containment may include
pausing rollout, withdrawing an artifact, disabling an exposed feature,
isolating a machine, rotating credentials, or producing an expedited release.

### Expedited

An issue is expedited when it materially affects confidentiality, integrity,
availability, privilege boundaries, or a reachable service but does not meet
the emergency criteria. It is handled ahead of normal feature work and included
in the next qualified release or an earlier release when exposure warrants it.

### Routine

Issues with low applicability or impact are addressed through normal input
refresh and release qualification. Deferral and residual exposure must remain
visible rather than disappearing into an untracked backlog.

## Minimum emergency release gate

Urgency may reduce broad regression coverage, but it must not eliminate the
minimum evidence that makes deployment safer than inaction. An emergency
release must, at minimum:

- have attributable and pinned inputs
- produce identifiable artifacts
- verify artifact integrity and signing
- boot the literal artifact on the reference qualification platform
- exercise the changed security or containment behavior
- demonstrate the intended boot-success and rollback path
- receive role-specific checks proportionate to the affected machines

Any skipped normal checks must be recorded and completed after containment.

## Unsupported and stale states

A machine is not current when it:

- runs something other than the current qualified release without a recorded
  exception
- uses project-owned configuration that has not passed the applicable gate
- cannot be correlated to release and configuration provenance
- has missed a security action known to apply to it
- has local OS mutation that invalidates the qualified artifact identity

An unsupported state may be operationally necessary, especially during
recovery. It must be explicit, observable, and accompanied by a remediation or
accepted-risk record.

## Required capabilities before claiming the policy is operational

- release manifests precise enough for vulnerability applicability analysis
- an inventory mapping machines to artifact and configuration identities
- defined upstream advisory and vulnerability information sources
- automated or repeatable input refresh and rebuild
- minimum qualification and failure-injection gates
- release withdrawal, rollout pause, and rollback mechanisms
- signing-key compromise and credential-rotation procedures
- a way to surface stale, pinned, locally modified, and unsupported machines

Until these exist, this document is a design target rather than an operational
security claim.

## Review triggers

Review this policy when:

- the project gains supported external users
- maintenance is shared by multiple people
- a public release cadence or response promise is considered
- a long-term or multiple-channel release model is proposed
- machines cannot update regularly or require extended offline operation
- the package ecosystem requires downstream security backports
- a security incident shows the qualification gate or response classification
  to be inadequate
