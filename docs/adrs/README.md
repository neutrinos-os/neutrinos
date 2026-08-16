# Architecture decision records

ADRs record decisions, not explorations. A design may result in several ADRs;
small decisions may need only an ADR if the alternatives and consequences fit
comfortably in the template.

Statuses are `proposed`, `accepted`, `rejected`, `deprecated`, and
`superseded`. Accepted ADRs remain historical records. Corrections may be
annotated, but changing a decision requires a new ADR with explicit
`supersedes` and `superseded_by` links.

## Index

| ADR | Status | Decision |
| --- | --- | --- |
| [ADR-0001](0001-systemd-first.md) | Accepted | Prefer systemd ecosystem mechanisms; require strong justification for overlapping alternatives. |
| [ADR-0002](0002-separate-authority-and-recovery.md) | Accepted; amended 2026-08-11 | Separate routine, exceptional, machine, and data authorities while keeping recovery independently usable. The amendment adds measurement-policy authority as a fifth custody class. |
| [ADR-0003](0003-bounded-fleet-intent-representation.md) | Accepted | Use bounded TOML records and exact native configuration, with JSON Schema validation and generated JSON evidence. |
| [ADR-0004](0004-usr-scoped-release-artifact.md) | **Proposed** | Authenticate `/usr` with its Verity pair and signed UKI as the release artifact; deliver configuration exclusively by signed confext with `Mutable=disabled`. Records the DES-0006 C-013 ruling of 2026-08-11. |
| [ADR-0005](0005-volume-boundaries-by-policy-difference.md) | **Proposed** | A volume boundary is earned by a custody, unlock, recovery, preservation or destruction difference — not by a path, disk or state owner. `/var` belongs to the machine-state volume. Records DES-0006 C-008. |
| [ADR-0006](0006-ineligibility-before-overwrite-and-terminal-selection.md) | **Proposed** | Mark a slot durably ineligible before writing any byte into it (level 3 authenticated marking is the target); stop automatic selection at an attributable terminal state that keeps running rather than halting. Records DES-0006 C-014 and C-015. **Beyond SYS-038, which is read narrowly.** |

Strong preferences from the design-session transcript remain stated directions
in the decision backlog until they are deliberately ratified.

## Rulings not yet recorded as ADRs

Accepted architectural rulings still living only in a design review, which
`AGENTS.md` classifies as non-authoritative. Each is a candidate ADR; none is
a new decision. Drafting one does not re-open it.

| Ruling | Accepted | Decision in brief |
| --- | --- | --- |
| DES-0006 C-003 | 2026-08-11 | Routine unlock policy is TPM2 + PIN. |
| DES-0006 C-009 | 2026-08-11 | The state filesystem comparison is three-way: Btrfs, XFS, ext4. |
| DES-0006 C-010 | 2026-08-11 | Encrypted volumes deliberately do not extend to metadata-only encryption. |
| DES-0005 confext lifecycle | 2026-08-11 | A deployment variant resolves to a set of confexts split by disjoint path ownership; base compatibility is a guard, not an identity binding; failure policy is per confext; retention is a reference count. |

Recorded so far: C-013 as ADR-0004, C-008 as ADR-0005, C-014 and C-015 as
ADR-0006.

DES-0006 C-007, the `/usr` filesystem format, is **not** in this table. It is
open, and PLN-0002-13's recommendation explicitly does not accept a format.
