# Designs

A design is a mutable, reviewable argument that answers one or more questions
from the decision backlog. Use a numbered directory when a design needs review
records, diagrams, or supporting material.

Statuses:

```text
sketch → proposed → in-review → accepted
                              ↘ withdrawn
accepted → superseded
```

Acceptance requires:

- goals, non-goals, constraints, and decision drivers
- meaningful alternatives, including adoption of existing work
- failure, recovery, security, and operational analysis
- falsifiable acceptance criteria
- durable disposition of adversarial review challenges
- one or more ADRs recording the resulting decisions

Current designs:

- [DES-0001: system model and deployment unit](0001-system-model/README.md)
- [DES-0002: state ownership and rollback contract](0002-state-ownership/README.md)
- [DES-0003: initial threat and trust model](0003-threat-and-trust-model/README.md)
- [DES-0004: minimum viable authority and recovery model](0004-authority-and-recovery/README.md)
- [DES-0005: fleet intent and configuration composition](0005-fleet-intent-and-configuration/README.md)
- [DES-0006: storage layout, immutable root, and encryption](0006-storage-layout-and-encryption/README.md)
- [DES-0007: package inputs and snapshot policy](0007-package-inputs-and-snapshot-policy/README.md)
- [DES-0008: supply-chain evidence, reproducibility, and vulnerability assessment](0008-supply-chain-evidence-and-vulnerability/README.md)
- [DES-0009: fleet release promotion and rollout control](0009-fleet-release-rollout/README.md)
- [DES-0010: installation, provisioning, and machine enrollment](0010-installation-and-enrollment/README.md)
