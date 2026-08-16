---
id: ADR-0009
title: Resolve a deployment variant to a set of disjoint signed confexts with per-confext failure policy
status: proposed
date: 2026-08-16
deciders: [Jason Tarasovic]
designs: [DES-0005, DES-0006]
supersedes: []
superseded_by: []
---

# Resolve a deployment variant to a set of disjoint signed confexts with per-confext failure policy

## Context

[ADR-0004](0004-usr-scoped-release-artifact.md) made signed confexts the only
mechanism that delivers configuration. It answered DES-0005's own deferred
question — whether a separately immutable configuration artifact beats flattened
variants — in the affirmative, **but answered it from outside**. The question
named boot-time binding, fallback and garbage collection, and ADR-0004 adopted the
mechanism without settling any of them. SYS-123 then applies in full to every
confext, and DES-0005 is its home.

The [DES-0005 amendment of
2026-08-11](../designs/0005-fleet-intent-and-configuration/README.md) settles the
nine obligations. **Accepted by Jason Tarasovic on 2026-08-11**; it amends an
accepted design and is policy from that date. The 1:1 draft it replaces was
rejected by the owner in the same pass and survives only in git history.

## Decision

A deployment variant resolves to a **set** of configuration extension images. The
deployment manifest names the complete set by digest; a missing, extra or
substituted member fails the eligibility gate exactly as any other deployment-set
member does.

### The split is by disjoint path ownership, not by scope

This is the constraint that makes several images safe, and it is not a detail.
**Splitting along `common`, `role` and `machine` would fail**, because those
scopes overlap by construction — machine scope exists precisely to override role
scope for the same key — so resolving them would require precedence at activation
time. That is the "generic role image plus boot-time machine assembly" DES-0005
already rejected, and the rejection stands.

Instead each confext owns a disjoint set of paths, drawn along consumer or
subsystem lines: network configuration in one, the graphical stack in another.
`common < role < machine` precedence is resolved **at build time within each
confext**, so each already carries a decided result for the paths it owns. Two
confexts in one deployment writing the same path is a **composition-time error**,
not a runtime conflict to be ordered.

Disjointness buys the property that matters: **merge order cannot change the
effective result.** Activation ordering becomes a scheduling question rather than
a semantic one. Reuse then comes from two machines legitimately having
byte-identical configuration for a subsystem — a fact about the inventory the
composition record can prove — not from layering, which would smuggle precedence
back in.

### Failure policy is declared per confext, in the inventory

Each confext is declared **required**, where failure to merge fails the trial
boot, or **optional**, where failure is reported, marks the deployment degraded
and allows boot to continue. This replaces both the global fail-closed rule and
the per-role rule with a per-subsystem one that follows what the configuration
actually does — a router's network configuration and a workstation's desktop
stack genuinely differ in whether the machine should continue without them.

**The declaration is authored in the fleet inventory and carried by the confext,
never authored by it.** An artifact that decides how important it is would be
deciding its own failure handling, which is the shape this project refuses
everywhere else. The inventory declares criticality as reviewed, identity-bound
intent; the composition record records it; the image transports it. **A confext
whose declared policy disagrees with the manifest's is a substituted member and
fails the gate.**

Two consequences are accepted: **optional is not a soft default** — a deployment
in which an optional confext failed is degraded, not healthy, and must not be
blessed on that boot; and **required is the default for anything unclassified**.

### The remaining SYS-123 obligations

- **Base compatibility** is a declared level and **a guard, not an identity
  binding**. Binding a confext to one exact deployment identity would add no
  integrity and would force every machine's confexts to be rebuilt — and a
  confext bound to one exact identity could never be shared.
- **Activation ordering** is scheduling: each confext must be merged before any
  unit that reads the paths it owns, and which confexts must be present at the
  initrd stage versus which may wait for sysroot is a placement question.
- **Health** follows the declared policy above.
- **Rollback**: the manifest names the complete confext set, so rolling back
  configuration means rolling back the deployment.
- **Retention is a reference count** — a confext is retained as long as any
  retained deployment references it.

## Alternatives considered

### One confext per deployment variant

Rejected by owner ruling 2026-08-11. Configuration identical across machines
would be built, signed and transferred once per machine instead of once, and
duplicated inside every machine's image.

### Splitting confexts along `common` / `role` / `machine` scope

Rejected as unsound rather than merely costly. Those scopes overlap by
construction, so the split would reintroduce activation-time precedence and with
it the boot-time assembly model DES-0005 rejected.

### Layering confexts with a precedence order

Rejected. It recovers reuse by smuggling precedence back into activation, which
is exactly what disjointness exists to remove.

### A confext declaring its own criticality

Rejected. An artifact deciding its own failure handling is the shape this project
refuses everywhere else; criticality is reviewed, identity-bound intent and
belongs in the inventory.

## Consequences

### Benefits

- Shared configuration is built, signed and transferred once.
- Merge order cannot change the result, so activation ordering stops being a
  correctness surface.
- Failure policy follows the subsystem rather than the whole machine or the whole
  role.
- Retention has a defined rule instead of an accumulation.

### Costs and constraints

- **The path split must be designed**, and there is a wrong answer available: too
  fine produces many tiny images, too coarse destroys the reuse this exists to
  capture. The disjointness rule is mechanically checkable, which bounds the cost
  to design effort rather than correctness.
- Every confext carries the full SYS-123 lifecycle.
- The inventory gains a criticality declaration per confext that must stay
  consistent with every manifest naming it.

### Accepted risks

- **The concrete path carve is not decided here.** PLN-0002-03a drew a first
  carve and built first tooling, both marked candidate fixtures; PR-0030 C-006 is
  the standing risk that this protection is procedural rather than structural
  until DES-0005 takes the carve back.
- **Where a separately delivered confext lives and when it is merged is open**
  under `S-004`. PLN-0002 shipped its confext at `/usr/lib/confexts` — inside the
  authenticated artifact, so not separate delivery at all — and the fixture
  decided nothing.
- Per-machine identity and secret delivery are not resolved by having a confext
  available; they pass to `L-003` and `C-002`.
- **The pairing is unattested in the field.** RES-0015 found no shipping
  image-based system with a stateless `/etc`, and none delivering configuration
  as a signed artifact rather than by writing into a persistent `/etc` — including
  systemd's own reference distribution, which has the mechanism and does not use
  it. This is novel work, not adoption of prior art.

## Validation and review triggers

Confext signature enforcement is closed and registered: `--image-policy=root=signed`
as a unit drop-in admits the enrolled signer and refuses the valid-but-unenrolled
one, measured by `T4-CONFEXT-001` and verified failure-sensitive. Against that,
PLN-0002 measured a refused confext reporting `Finished` and leaving the machine
unconfigured — a fail-open that a required-policy confext must not reproduce.

Revisit this decision when:

- the designed path carve produces images whose granularity defeats either reuse
  or reviewability;
- a subsystem genuinely needs precedence between confexts, which would falsify
  the disjointness premise;
- `S-004`'s delivery-location question resolves in a way that changes when a
  confext can be merged; or
- RES-0015's finding is overtaken by a shipping system that operates this pairing,
  which would convert novel work into adoptable prior art.
