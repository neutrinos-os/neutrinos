---
status: accepted
last_updated: 2026-08-09
---

# Project charter

## Purpose

NeutrinOS explores a systemd-native, image-based Linux operating system model
that can support several machine roles from a common build, configuration,
testing, and release process.

The project is motivated by a desire to make machine configuration reviewable,
reproducible, testable before deployment, and recoverable after a failed
change. It is not motivated merely by assembling a preferred package list.

## Provisional distinguishing invariant

NeutrinOS provides one version-controlled, test-gated machine model across
heterogeneous personal-fleet roles. A change is deployable only when the exact
release artifacts and applicable declarative configuration inputs have passed
role-specific boot and acceptance tests. Machine secrets and hardware-specific
values may be injected later, but their schemas, policies, and observable
effects must be covered by qualification. Transactional replacement, rollback,
and recovery are part of the release contract.

This invariant is provisional until the existing-system comparison determines
whether an established system already provides it without unreasonable
adaptation. If it does, the project should adopt or extend that system rather
than preserve novelty for its own sake.

## Architectural posture

NeutrinOS is systemd-first. When the systemd ecosystem provides a mechanism
for an accepted requirement, that mechanism is the default choice. Selecting a
different implementation requires documented evidence that the systemd option
cannot adequately satisfy the requirement or would impose materially greater
risk or lifecycle cost.

This is not a prohibition on non-systemd software. It is a burden-of-proof rule
for overlapping system facilities and OS lifecycle mechanisms. The complete
decision and exception criteria are recorded in
[ADR-0001](../adrs/0001-systemd-first.md).

## Intended outcome

A source revision and pinned inputs should produce identifiable release
artifacts that can be booted and tested unchanged, deployed transactionally,
and either blessed or rolled back. Role-specific behavior should be expressed
without giving up a common system lifecycle.

Potential roles include:

- workstation
- laptop
- router
- server or storage host
- microVM guest

This list describes the intended design envelope, not an initial support
commitment.

The initial qualification platform is an x86-64 QEMU/KVM virtual machine using
UEFI and virtio devices, with vTPM support available for trust-path tests. The
first physical role is the current workstation. The router is the second,
deliberately contrasting role used to test whether the shared system model is
genuinely role-independent.

## Initial audience and commitment

NeutrinOS initially serves Jason's personal fleet. The architecture should be
developed as a reusable multi-role OS framework, but the project is not
initially a public distribution and makes no external compatibility, hardware
support, release-cadence, or security-response commitment.

This boundary permits the project to test whether the framework is genuinely
reusable without prematurely converting internal design goals into promises to
outside users.

## Project-level success criteria

| ID | Criterion | Evidence |
| --- | --- | --- |
| CH-001 | The project either demonstrates that its distinguishing invariant cannot be met by reasonably adapting an existing system, or adopts that system instead of duplicating it. | Completed adopt/build/borrow comparison with a documented conclusion. |
| CH-002 | Every release can be traced to source revision, pinned inputs, build configuration, produced artifacts, and qualification results. | Verifiable deployment manifest, release authorization, and provenance record. |
| CH-003 | The literal artifact offered for deployment passes the reference-platform gate and all applicable role-specific gates. | Artifact identities joined to test records. |
| CH-004 | Interrupted staging, failed boot, failed health checks, and an unusable new deployment each have exercised recovery paths. | Failure-injection results and recovery records. |
| CH-005 | OS, machine, administrator, user, and workload state have explicit ownership, migration, backup, rollback, and reset semantics. | Accepted state model traced to tests. |
| CH-006 | Workstation and router deployments use the same release lifecycle; necessary role divergence is explicit rather than hidden behind accidental abstraction. | Both roles qualify through the common lifecycle with documented exceptions. |
| CH-007 | A running machine exposes whether it is current, stale, pinned, locally modified, or unsupported, and the accepted maintenance policy is operational. | Fleet inventory and a completed release/security-response exercise. |

## Charter review status

The foundational audience, target, naming, architectural-posture, and
maintenance questions have been resolved. The success criteria, design
principles, scope, and non-goals were ratified after
[adversarial review](reviews/0001-charter-principles-and-scope.md). The
distinguishing invariant remains provisional until success criterion CH-001 is
satisfied.
