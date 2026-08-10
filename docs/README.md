# NeutrinOS documentation

This directory is the design record for NeutrinOS. The project is currently in
the discovery and architecture phase; documents marked `draft`, `sketch`, or
`proposed` are not commitments.

Architecture sessions should begin with the
[design-session restart brief](background/design-session-summary.md), then
verify its summary against the current ADRs, requirements, and active design.

## Start here

1. [Project charter](project/charter.md)
2. [Scope](project/scope.md)
3. [Design principles](project/principles.md)
4. [Naming](project/naming.md)
5. [Project glossary](project/glossary.md)
6. [Maintenance and security policy](project/maintenance-policy.md)
7. [Decision backlog](project/decision-backlog.md)
8. [Current project context](project/current-context.md)
9. [Aggregate work register](project/work-register.md)
10. [Pre-implementation readiness plan](plans/0000-pre-implementation-readiness.md)
11. [Reference-VM evidence slice plan](plans/0001-reference-vm-slice.md)
12. [Test and evidence strategy](project/test-strategy.md)
13. [Validation execution contract](project/validation-contract.md)
14. [Repository hygiene contract](project/repository-hygiene.md)
15. [Existing-system adopt/build/borrow comparison](research/comparisons/existing-systems.md)
16. [System requirements](requirements/system.md)
17. [First system-model design](designs/0001-system-model/README.md)
18. [State ownership and rollback design](designs/0002-state-ownership/README.md)
19. [Initial threat and trust model](designs/0003-threat-and-trust-model/README.md)
20. [Minimum viable authority and recovery model](designs/0004-authority-and-recovery/README.md)
21. [Fleet intent and configuration composition](designs/0005-fleet-intent-and-configuration/README.md)
22. [Storage layout, immutable root, and encryption](designs/0006-storage-layout-and-encryption/README.md)
23. [Package inputs and snapshot policy](designs/0007-package-inputs-and-snapshot-policy/README.md)
24. [Supply-chain evidence, reproducibility, and vulnerability assessment](designs/0008-supply-chain-evidence-and-vulnerability/README.md)
25. [Fleet release promotion and rollout control](designs/0009-fleet-release-rollout/README.md)
26. [Installation, provisioning, and machine enrollment](designs/0010-installation-and-enrollment/README.md)
27. [Secret custody and credential delivery](designs/0011-secret-and-credential-delivery/README.md)
28. [Unix identity and rootless-container ownership](designs/0012-unix-identity-and-rootless-containers/README.md)
29. [Software placement and execution boundaries](designs/0013-software-placement/README.md)

The original conversation is preserved as [background material](background/2026-08-09-design-session-transcript.md).

## Document types

| Location | Purpose | Authority |
| --- | --- | --- |
| `project/` | Charter, scope, assumptions, risks, and decision inventory | Project policy |
| `requirements/` | Candidate and accepted testable statements of what the system must accomplish | Per-requirement status |
| `designs/` | Proposals, alternatives, experiments, and review responses | Mutable while under review |
| `adrs/` | Architectural decisions and their rationale | Historical decision record |
| `architecture/` | Description of the currently accepted system | Derived from accepted ADRs |
| `plans/` | Bounded execution plans, phase gates, sequencing, and exit criteria | Mutable execution intent; cannot accept architecture |
| `research/` | Evidence, comparisons, and investigation notes | Informational |
| `background/` | Historical source material | Informational |

## Decision workflow

```text
question in decision backlog
        ↓
research or experiment, when needed
        ↓
design proposal
        ↓
adversarial review and disposition of challenges
        ↓
accepted ADR
        ↓
requirements and current-architecture docs updated
```

Accepted ADRs are not rewritten to make history look cleaner. A changed
decision gets a new ADR that supersedes the old one.
