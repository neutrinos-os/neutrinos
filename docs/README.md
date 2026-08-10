# NeutrinOS documentation

This directory is the design record for NeutrinOS. The project is currently in
the discovery and architecture phase; documents marked `draft`, `sketch`, or
`proposed` are not commitments.

## Start here

1. [Project charter](project/charter.md)
2. [Scope](project/scope.md)
3. [Design principles](project/principles.md)
4. [Naming](project/naming.md)
5. [Project glossary](project/glossary.md)
6. [Maintenance and security policy](project/maintenance-policy.md)
7. [Decision backlog](project/decision-backlog.md)
8. [Existing-system adopt/build/borrow comparison](research/comparisons/existing-systems.md)
9. [System requirements](requirements/system.md)
10. [First system-model design](designs/0001-system-model/README.md)
11. [State ownership and rollback design](designs/0002-state-ownership/README.md)
12. [Initial threat and trust model](designs/0003-threat-and-trust-model/README.md)
13. [Minimum viable authority and recovery model](designs/0004-authority-and-recovery/README.md)
14. [Fleet intent and configuration composition](designs/0005-fleet-intent-and-configuration/README.md)

The original conversation is preserved as [background material](background/2026-08-09-design-session-transcript.md).

## Document types

| Location | Purpose | Authority |
| --- | --- | --- |
| `project/` | Charter, scope, assumptions, risks, and decision inventory | Project policy |
| `requirements/` | Candidate and accepted testable statements of what the system must accomplish | Per-requirement status |
| `designs/` | Proposals, alternatives, experiments, and review responses | Mutable while under review |
| `adrs/` | Architectural decisions and their rationale | Historical decision record |
| `architecture/` | Description of the currently accepted system | Derived from accepted ADRs |
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
