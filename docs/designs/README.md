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

- [DES-0001: system model and release lifecycle](0001-system-model/README.md)
- [DES-0002: state ownership and rollback contract](0002-state-ownership/README.md)
- [DES-0003: initial threat and trust model](0003-threat-and-trust-model/README.md)
