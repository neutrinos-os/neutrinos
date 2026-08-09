---
status: accepted
last_updated: 2026-08-09
---

# Design principles

These principles were ratified following
[adversarial review](reviews/0001-charter-principles-and-scope.md). They are
review criteria rather than implementation choices.

1. **Artifacts, not converged pets.** A deployed OS release has a concrete,
   cryptographic identity and is replaced as an artifact.
2. **Test what is shipped.** Qualification boots and exercises the literal
   artifact that will be deployed, together with the applicable declarative
   configuration inputs. Later-bound secrets and hardware values remain
   governed by tested schemas and policies.
3. **State has an owner.** OS, machine, administrator, user, and workload state
   have documented boundaries and lifecycles.
4. **Recovery is part of the design.** Update, migration, key management, and
   storage designs include their failure and recovery paths.
5. **One lifecycle, multiple roles.** Roles may vary packages, configuration,
   kernels, and tests without creating unrelated operating systems. Necessary
   divergence is explicit and evidence-based; commonality is not forced when
   it would weaken a role's requirements.
6. **Systemd-first, not systemd-only.** When the systemd ecosystem addresses an
   accepted requirement, use it by default. An alternative needs documented
   evidence of a material requirement, security, reliability, support, or
   lifecycle advantage. See [ADR-0001](../adrs/0001-systemd-first.md).
7. **Evidence outranks familiarity.** Operating experience matters, but major
   choices require current documentation, experiments, or measured results.
8. **Security claims are scoped.** Every integrity, encryption, or attestation
   mechanism states the attacker and failure it addresses.
9. **Local escape hatches are explicit.** Overrides must not silently destroy
   reproducibility, update safety, or the ability to identify a machine.
10. **Complexity is paid over the lifecycle.** Build convenience is not allowed
    to externalize unbounded operational or maintenance cost.
11. **Optimize from evidence.** Minimal kernels, omitted runtime components,
    and specialized artifacts require measured benefit and retain a viable
    general or recovery path until their support cost is understood.
