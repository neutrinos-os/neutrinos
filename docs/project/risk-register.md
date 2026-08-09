---
status: draft
last_updated: 2026-08-09
---

# Risk register

| ID | Risk | Impact | Initial response |
| --- | --- | --- | --- |
| R-001 | The project recreates an existing atomic distribution with less maintenance capacity. | Critical | Establish a differentiating invariant and perform adopt/build/borrow comparisons first. |
| R-002 | Rolling back the OS leaves incompatible mutable state. | Critical | Define state ownership, schemas, and migration compatibility before update implementation. |
| R-003 | Signing-key loss or compromise makes machines unrecoverable or untrustworthy. | Critical | Enforce accepted DES-0004 and ADR-0002; exercise authority loss through EX-0001, promotion substitution through EX-0002, and recovery abuse through EX-0003 before creating production keys. |
| R-004 | Package-input churn exceeds available security-maintenance capacity. | High | Compare release models and define patch/rebuild service objectives. |
| R-005 | Hardware breadth prevents reliable qualification. | High | Publish a narrow initial hardware matrix and expand only with tests. |
| R-006 | Role abstraction becomes either duplication or an overly clever configuration language. | High | Model two substantially different roles before fixing the abstraction. |
| R-007 | Rootless containers conflict with identity or home-directory choices. | High | Treat UID, sub-ID, idmapped mount, and bind-mount behavior as a gated design. |
| R-008 | Security mechanisms accumulate without a coherent threat model. | High | Require every mechanism to map to assets, attackers, and recovery behavior. |
| R-009 | Custom kernels create an unsustainable support matrix. | Medium | Begin with a generic reference kernel and require measured benefit for variants. |
| R-010 | Desktop details distract from the end-to-end release lifecycle. | Medium | Defer component selection until the system model and reference role are chosen. |
| R-011 | The spoken name and lowercase identifier collide with existing software companies, including one using OS language. | Low for the personal phase | Use the distinctive `NeutrinOS` display style, retain existing repository identifiers, and review naming before any public distribution or third-party namespace commitment. |
| R-012 | The selected substrate's production backend cannot provide the accepted boot trust or automatic recovery model. | Critical | Accept trust requirements before the substrate ADR and run symmetric lifecycle spikes against production-supported configurations. |
| R-013 | Recovery becomes an alternate privileged boot path that bypasses data, identity, platform, or normal-release controls. | Critical | Enforce the EX-0003 capability transitions; physically test activation, unlock, hostile-state handling, independent evidence, signer replacement, and router out-of-band isolation before production enrollment. |
