---
id: ADR-0005
title: Earn every volume boundary with a policy difference, and place `/var` on the machine-state volume
status: accepted
date: 2026-08-16
deciders: [Jason Tarasovic]
designs: [DES-0006]
supersedes: []
superseded_by: []
---

# Earn every volume boundary with a policy difference, and place `/var` on the machine-state volume

## Context

[DES-0006 C-008](../designs/0006-storage-layout-and-encryption/review.md)
challenged the multi-volume state layout: separate machine and user/workload
volumes require more keys, headers, backups, mounts, status surfaces and
partial-failure paths, which makes recovery slower and more error-prone than a
single encrypted state filesystem.

The challenge **got harder between the original review and the 2026-08-11 pass**,
which is why it produced a ruling rather than a reaffirmation. C-013 (now
[ADR-0004](0004-usr-scoped-release-artifact.md)) introduced a writable root
partition that no volume count included, and the design did not say whether it
*is* the machine-state volume or a partition beside it. C-005 then priced every
volume at a recovery key, an independent header backup, a restore test and an
`S-006` custody entry. C-003 gave each volume its own unlock question — and
chaining one volume's unlock to another collapses exactly the compromise boundary
the split exists to create.

Much of the confusion was terminological. The word **root** was carrying the
superseded read-only authenticated root, the new writable partition, and the
dm-verity root hash simultaneously.

**Ruled and accepted 2026-08-11.** This ADR records that ruling in the
authoritative form rather than leaving it in a design review.

## Decision

**A volume boundary is earned by a policy difference, not by a path, a disk, or a
state owner.** The design must enumerate each volume with the specific custody,
unlock, recovery, preservation or destruction **difference** that justifies its
existence, and collapse any volume that cannot name one.

**`/var` belongs to the machine-state volume**, under that volume's custody,
unlock, recovery, preservation and destruction policy. It is the
machine-lifecycle content that volume already enumerates, and the content that
wants confidentiality.

**Encryption scope is settled and was never actually in question.** `/usr` is
public release content, authenticated by dm-verity and deliberately unencrypted;
`systemd-repart` cannot combine `Verity=` and `Encrypt=` on one partition in any
case. Confidentiality is owed to machine state — journals, boot-assessment
evidence, update records, crash diagnostics — not to release bytes.

**The vocabulary is retired.** `root image` and `root slot` are retired,
`root partition` is defined, and bare **root** is a discouraged term with three
unrelated referents. The binding prohibition now lives in root `AGENTS.md`
§ Language; the replacement vocabulary is in the
[glossary](../project/glossary.md).

This ADR does not decide the partition count. Whether the root partition needs to
persist at all is opened by this ruling and recorded as unresolved in DES-0006.

## Alternatives considered

### One encrypted state filesystem

Rejected, and this was the challenge's own proposal. A single volume genuinely
reduces keys, headers, backups and partial-failure paths, and that benefit is
real. It was rejected because the workstation's split follows separate physical
disks and reprovisioning lifecycles, which is a preservation and destruction
difference rather than a convenience — precisely the kind of difference the
accepted rule requires a volume to name. The rule is what makes this a principled
rejection rather than a preference: a layout that cannot name the difference must
collapse.

### Volumes by path or by state owner

Rejected as the organising principle. Both produce boundaries that multiply
custody and recovery work without a corresponding policy difference, which is the
cost C-008 correctly identified. Path and owner may *describe* a volume; they
cannot *justify* one.

### Chaining one volume's unlock to another to reduce unlock ceremony

Rejected under C-003. It collapses the compromise boundary the split exists to
create, so it converts a policy difference back into a naming difference while
leaving the operating cost in place.

## Consequences

### Benefits

- Volume count becomes a reviewable claim rather than an accumulation. Each
  boundary carries a stated reason a reviewer can reject.
- Recovery work scales with genuine policy differences instead of with paths.
- `/var`'s custody, unlock and destruction policy stop being implicit.
- The retired vocabulary removes a class of ambiguity that had already produced a
  design defect, not merely awkward prose.

### Costs and constraints

- Every volume now owes an explicit justification in the design, and adding one
  later means arguing for it rather than declaring it.
- Each surviving volume still costs a recovery key, an independent header backup,
  a restore test and an `S-006` custody entry (C-005).
- The partition count remains undecided, so the layout is not final.

### Accepted risks

- **Later per-user or workload encryption can expand the matrix**, and the rule
  constrains but does not prevent that expansion.
- A future requirement may demand a boundary whose policy difference is real but
  not expressible in the custody/unlock/recovery/preservation/destruction terms
  this rule enumerates.
- Collapsing a volume is harder than creating one, so an incorrectly collapsed
  boundary is the more expensive error direction.

## Validation and review triggers

Before the layout is accepted as final, enumerate every volume against the five
policy dimensions and show that each names at least one difference. A volume that
cannot is a defect this ADR requires be collapsed.

Revisit this decision when:

- the root partition question resolves and changes the partition count;
- per-user or workload encryption is required and the matrix expands beyond what
  the five dimensions describe;
- measured recovery operation shows the surviving boundaries cost more than the
  single-volume alternative would have; or
- a required boundary cannot name a difference, which would mean the rule is
  wrong rather than the layout.
