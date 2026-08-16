---
id: ADR-0007
title: Set routine unlock policy per role, with TPM2 + PIN on the workstation
status: proposed
date: 2026-08-16
deciders: [Jason Tarasovic]
designs: [DES-0006]
supersedes: []
superseded_by: []
---

# Set routine unlock policy per role, with TPM2 + PIN on the workstation

## Context

[DES-0006 C-003](../designs/0006-storage-layout-and-encryption/review.md)
challenged unattended TPM2 unlock: a stolen intact machine can boot an
authorized vulnerable release and decrypt itself with nobody present, which
makes "encrypted at rest" a stronger claim than the actual protection against
offline extraction and boot substitution.

The permitted claim itself was already fixed by PR-0005 C-001 and is not
reopened here: hardware-bound unlock protects against offline extraction and
unauthorized boot substitution under the platform assumption, while session
authentication and revocation protect the running machine. What C-003 forced was
a policy decision the design had left global.

**Ruled 2026-08-11 for the workstation; the router is unchanged pending
hardware.**

## Decision

**Routine unlock policy is per role, not global.**

**Workstation (`desktop-jason`): TPM2 + PIN.** It defeats the scenario the
challenge names — a stolen intact machine that decrypts itself with nobody
present — and unattended reboot is not a workstation requirement, so the cost is
a typed secret rather than a lost capability. **Unattended TPM2 alone is
rejected for this role.**

**Router and `misc`: unattended TPM2, no human input**, because both must reboot
unattended. This is exactly the pairing PR-0005 says requires a proven
hardware-bound secret facility, and **neither machine has one today**. Until they
do, both accept the narrow claim or carry no powered-off confidentiality claim at
all.

**The PIN joins the recovery-material inventory** under C-005. A forgotten PIN is
an availability event, so the independently retained high-entropy recovery method
is load-bearing rather than ceremonial.

### Enabling conditions, stated so this is not mistaken for a capability

- `desktop-jason` advertises TPM 2.0 but its **operation is untested**, Secure
  Boot is **off**, and owner platform keys are **not enrolled**. This is a
  migration target gated by PR-0005 C-002's mandatory exercises, not a setting to
  turn on.
- The router's discrete TPM 2.0 module is **acquired but not installed**.
  PR-0005 requires treating the capability as absent until a module is installed
  and exercised, so no inventory row or confidentiality claim moves yet.
  Installation is physical work on the machine carrying the development network —
  `R-054`'s first concrete instance.
- **`misc`'s firmware check is decisive rather than routine.** If Haswell-era PTT
  presents **TPM 1.2**, `systemd-cryptenroll --tpm2` cannot enroll it, and
  Intel's specification states the D54250WYK supports no discrete TPM. A 1.2
  answer forecloses unattended encrypted boot on that machine **permanently
  rather than inconveniently**, and `misc` can never be a
  production-confidentiality target without different hardware.

## Alternatives considered

### Unattended TPM2 everywhere

Rejected for the workstation, retained for the router and `misc` by necessity
rather than preference. It is precisely the configuration C-003 challenges, and
on a role with no unattended-reboot requirement it buys convenience at the cost
of the claim.

### TPM2 + FIDO2 for the workstation

Considered as the comparison C-003 required. A PIN was taken because it defeats
the named scenario without adding a token to the recovery-material inventory or a
second thing to lose. FIDO2 remains available if PIN entry proves untenable in
operation.

### A single global unlock policy

Rejected. It forces either an unattended-reboot capability the workstation does
not need, or a typed secret on machines that must reboot unattended. The roles
genuinely differ, and one of the two failures is a lost capability rather than an
inconvenience.

## Consequences

### Benefits

- The workstation's powered-off confidentiality claim survives the stolen-intact-
  machine scenario.
- The router and `misc` carry an explicit, narrow claim instead of an implied
  strong one.
- `misc`'s hardware limit is named as permanent rather than pending.

### Costs and constraints

- Every workstation boot requires a typed secret.
- The PIN enters recovery-material custody under `S-006`, with the retained
  high-entropy method now load-bearing.
- The qualification matrix gains a per-role unlock dimension.
- Neither the router nor `misc` can claim production confidentiality until a
  hardware-bound secret facility is installed and exercised.

### Accepted risks

- **An authorized pre-login vulnerability can expose unlocked data.** Unlock
  policy does not address it.
- **A PIN moves part of the protection into something memorized**, which fails
  differently from a sealed secret and fails at the worst time.
- The router's module could fail qualification after installation, leaving the
  role where it is today.

## Validation and review triggers

PR-0005 C-002's exercises gate the workstation migration; TPM operation, Secure
Boot state and owner key enrollment must all be demonstrated rather than
advertised. The `misc` firmware check is a decisive one-time determination.

Revisit this decision when:

- the router's TPM 2.0 module is installed and exercised, which would let its
  role carry a production confidentiality claim;
- `misc`'s firmware answers TPM 1.2, which permanently forecloses the role;
- workstation PIN entry proves untenable in operation, making FIDO2 the
  challenger; or
- a role appears whose unattended-reboot requirement and confidentiality
  objective cannot both be met, which is a hardware procurement question rather
  than a policy one.
