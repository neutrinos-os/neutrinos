---
id: ADR-0001
title: Adopt a systemd-first architectural policy
status: accepted
date: 2026-08-09
deciders: [Jason Tarasovic]
designs: []
supersedes: []
superseded_by: []
---

# Adopt a systemd-first architectural policy

## Context

NeutrinOS needs coherent mechanisms for image building, boot, service and
session management, device and network configuration, resource control,
credentials, updates, recovery, and virtualization. Many of these requirements
are addressed by projects in the systemd ecosystem and by related UAPI
specifications.

Choosing overlapping facilities independently can create additional adapters,
duplicated policy, inconsistent lifecycle semantics, and a wider operational
surface. Conversely, an absolute rule requiring systemd components regardless
of fitness would prevent the project from responding to real gaps or superior
evidence.

## Decision

NeutrinOS adopts a **systemd-first, not systemd-only** architectural policy.

When a project or mechanism in the systemd ecosystem addresses an accepted
requirement, it is the default candidate and must be evaluated first. Choosing
an overlapping alternative requires a documented design showing a strong
justification.

A strong justification must demonstrate at least one material difference:

- the systemd mechanism cannot satisfy an accepted requirement
- it creates an unacceptable security, integrity, or recovery property
- it does not support required hardware or a selected machine role
- its maturity, maintenance, or upstream trajectory creates unacceptable risk
- an alternative produces a measured and meaningful reliability, performance,
  or resource improvement
- it imposes materially greater integration or lifecycle cost than the
  alternative
- an interoperability or compatibility obligation requires another mechanism

The proposal must compare the systemd option and the alternative against the
same requirements, cite evidence, describe integration consequences, and state
when the decision should be revisited.

Familiarity, aesthetic preference, popularity, a marginal feature-count
advantage, or hypothetical portability is not sufficient by itself.

This policy applies to overlapping system and OS-lifecycle facilities. It does
not require every application, workload, desktop component, filesystem, or
development tool to originate in systemd.

## Alternatives considered

### Select every component independently

This maximizes local choice but repeatedly reopens integration decisions and
makes architectural coherence an emergent property of package selection.

### Require systemd mechanisms without exception

This is simpler to state but elevates ecosystem allegiance above accepted
requirements and evidence. It also provides no responsible path around an
upstream gap.

### Use systemd only for service management

This discards much of the intended integration among boot, images, identity,
resource control, credentials, updates, and recovery, and conflicts with the
project's stated direction.

## Consequences

### Benefits

- Component evaluations begin from a coherent default architecture.
- Native integration and shared lifecycle semantics receive explicit weight.
- Review effort focuses on demonstrated gaps rather than unrestricted option
  surveys.
- Exceptions remain possible when supported by requirements and evidence.

### Costs and constraints

- The project inherits systemd ecosystem assumptions and release dependencies.
- Reviewers must guard against treating “systemd-first” as proof that a given
  mechanism meets the requirement.
- Alternatives incur additional documentation and review work.
- Upstream gaps may require contribution, temporary exceptions, or delayed
  features.

### Accepted risks

- Architectural concentration can amplify an upstream defect or unsuitable
  design assumption.
- The burden of proof may discourage a worthwhile alternative unless reviews
  actively seek contrary evidence.

## Validation and review triggers

Compliance is validated by designs identifying applicable systemd mechanisms
and documenting any exception using the criteria above.

Revisit this decision when:

- a selected systemd mechanism repeatedly fails an accepted requirement
- maintaining systemd integration requires substantial downstream divergence
- a non-systemd mechanism becomes a broadly adopted compatibility requirement
- the common lifecycle cannot be expressed for a selected machine role
- concentration risk produces a material security or availability failure
