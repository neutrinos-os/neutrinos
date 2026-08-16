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
| [ADR-0007](0007-per-role-routine-unlock-policy.md) | **Proposed** | Routine unlock policy is per role: TPM2 + PIN on `desktop-jason`, unattended TPM2 on `router` and `misc`, neither of which has a proven hardware-bound secret facility today. Records DES-0006 C-003. |
| [ADR-0008](0008-authenticate-selection-state-not-stored-state.md) | **Proposed** | Offline authenticity stays out of scope for encrypted volumes, matching every comparable system; unencrypted boot-selection state carries an integrity obligation with no mechanism selected. Records DES-0006 C-010. |
| [ADR-0009](0009-disjoint-confext-set-per-deployment-variant.md) | **Proposed** | A deployment variant resolves to a set of confexts split by **disjoint path ownership**, never by scope; failure policy is declared per confext in the fleet inventory; retention is a reference count. Records the DES-0005 amendment. |

Strong preferences from the design-session transcript remain stated directions
in the decision backlog until they are deliberately ratified.

## Design rulings now recorded here

Every accepted architectural ruling that had been living only in a design review
— which `AGENTS.md` classifies as non-authoritative — is now an ADR. None was a
new decision; drafting one did not reopen it.

| Ruling | Accepted | Recorded as |
| --- | --- | --- |
| DES-0006 C-013 | 2026-08-11 | ADR-0004 |
| DES-0006 C-008 | 2026-08-11 | ADR-0005 |
| DES-0006 C-014, C-015 | 2026-08-11 | ADR-0006 |
| DES-0006 C-003 | 2026-08-11 | ADR-0007 |
| DES-0006 C-010 | 2026-08-11 | ADR-0008 |
| DES-0005 confext lifecycle | 2026-08-11 | ADR-0009 |

Two DES-0006 challenges are deliberately **not** here, both because they are
open rather than because they were missed:

- **C-007**, the `/usr` filesystem format. PLN-0002-13 recommends EROFS
  conditional on the updater not being whole-image-only and **explicitly does not
  accept a format**; PLN-0003 measures the read workload that could reverse it.
- **C-009**, the state filesystem. Its disposition is *open, deferred to the
  substrate spike*, with the candidate set corrected to a three-way comparison of
  **ext4, XFS and Btrfs**. ZFS is excluded for being out-of-tree and CDDL against
  a public repository shipping a GPL kernel; bcachefs for being removed from the
  tree in Linux 6.18 and now DKMS-only; LVM thin provisioning is noted as the
  alternative snapshot path. The exclusions are decided; the selection is not.
