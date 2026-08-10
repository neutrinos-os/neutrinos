---
id: EX-0012
title: First enrollment, installation, and replay tabletop
status: proposed
date: 2026-08-10
exercise_type: tabletop
evidence_class: analysis-only
related_designs: [DES-0010]
---

# First enrollment, installation, and replay tabletop

## Purpose and evidence limit

This exercise instantiates DES-0010 for a blank reference VM and the planned
physical migration sequence. The first pass is a record/state-machine tabletop;
it does not prove disk, firmware, TPM, bootloader, or installer behavior until
replayed with literal artifacts and disposable storage.

## Fixture

- One blank UEFI QEMU VM with a vTPM and stable virtual disk identity.
- One cloned copy presented before and after enrollment.
- Scratch storage matching the proposed `desktop-jason` system/data split.
- A simulated router target with IPMI/alternate access and a qualified discrete
  TPM requirement; absence of the TPM is an expected production blocker.
- Two machine records plus one deliberately wrong record.
- A signed installer artifact, one authorized deployment set, an independently
  authorized recovery environment, and disposable test authorities.

Use only synthetic identities, keys, vouchers, and state. No production secret
or current machine data belongs in the exercise corpus.

## Canonical records

Create inspectable candidate representations for:

| Record | Minimum identity-bound content |
| --- | --- |
| Provisioning intent | operation, machine record/inventory, installer, target constraints, release, erase/preserve policy, ceremonies, voucher, expiry, evidence policy |
| Enrollment voucher | record, operation, nonce, allowed request/key policy, expiry, uses, authority |
| Enrollment request | voucher, fresh key proof, request nonce, platform observations, installer/intent identity |
| Enrollment approval | exact request/public key, record, machine epoch, status/freshness policy, authority |
| Enrollment binding | approval plus current inventory record revision and revocation state |
| Provisioning journal | ordered phases, inputs, native tool results, irreversible boundaries, installed outputs |
| Completion record | final deployment, storage layout, binding, first normal boot, health result, retired inputs |

The exercise must determine which are independent records and which can be
views over a smaller acyclic evidence graph.

## Baseline ceremony

1. Owner selects one machine record and issues a single-use intent/voucher.
2. Installer boots and verifies itself plus intent before mutation.
3. Installer presents target/storage/preservation plan for independent review.
4. Layout and deployment set are installed; final target bytes are verified.
5. Platform and data-unlock ceremonies run through their independent authorities.
6. Target generates a machine key and emits an enrollment request.
7. Owner verifies request bytes through an independent administrative path and
   issues approval.
8. Target verifies approval, binds the current record, and selects one trial.
9. Normal deployment proves boot identity, enrollment, state, and baseline
   health, then writes completion and makes bootstrap inputs inert.

Run the same record flow using network and removable-media round trips.

## Scenario matrix

### E-001: Clean online and offline enrollment

Pass if both paths produce equivalent canonical records, private keys never
leave the target, no online service is required for ordinary boot, and the
offline path cannot approve two bindings from one voucher.

### E-002: Hostile bootstrap hint

Supply wrong SMBIOS, fw_cfg, metadata, seed label, and kernel URL values.

Pass if these can at most locate candidate intent; signature, exact record,
owner confirmation, and approval prevent role or identity reassignment.

### E-003: Voucher theft and race

Submit two independently generated keys with the same voucher before either
target learns the result.

Pass if both requests can be diagnosed but only one ordered approval/binding is
valid, the rejected contender receives no machine secrets, and first-arrival is
not silently the approval policy.

### E-004: Proof-of-possession substitution

Replace the public key or proof between installer display, request transfer,
and authority approval.

Pass if independent parsing shows the exact approved request, altered requests
fail, and a digest rendered only by the installer is insufficient evidence.

### E-005: Wrong disk and device remapping

Present similar disks, change enumeration, and attempt to map the confirmed
path to another device.

Pass if stable properties, topology, plan identity, verified backup, and
last-moment resolution prevent or clearly bound destructive mutation.

### E-006: Interrupted installation

Interrupt before and after partition table write, filesystem creation, root and
Verity population, encryption enrollment, boot artifact write, boot entry,
identity creation, approval, trial selection, and completion.

For each point record whether retry is idempotent, reversible, recovery-only, or
requires a fresh operation. No case may become a partially enrolled normal
machine or select a hybrid deployment.

### E-007: Provisioning replay

Reattach original seed media and replay metadata after successful completion,
then after loss of only the local completion marker.

Pass if consumed intent remains inert through binding/epoch and spent approval
state; deliberate reprovision requires a new authorized operation.

### E-008: Clone before and after enrollment

Clone the blank/unconfigured image, then clone the disk after identity creation
and again after enrollment.

Pass if blank clones generate distinct identities, post-enrollment duplicates
are detected/quarantined under current authority state, and fixture cloning has
an explicit reset/re-enrollment procedure.

### E-009: Platform and data-unlock ordering

Inject Secure Boot enrollment failure, TPM clear, PCR-policy mismatch, LUKS
header damage, lost routine unlock, and firmware reset.

Pass if each authority and recovery path remains distinct, a verified recovery
method exists before retirement, and failure never silently disables protection.

### E-010: Preservation and hostile state

Use mixed machine, administrator, user, workload, cache, and diagnostic state.
Run ordinary reinstall and suspected-compromise reprovision.

Pass if only the named owner scopes move, application consistency and schema
checks run, identity material is handled separately, and compromise state
remains locked/quarantined until deliberate restore.

### E-011: Revoked identity restored from backup

Revoke epoch 1, enroll epoch 2, then restore an old disk/state backup containing
epoch 1 credentials and binding.

Pass if current authority status rejects/quarantines epoch 1 and OS rollback or
completion-marker state cannot resurrect it.

### E-012: First normal boot failure

Make the installed deployment fail before and after it can access machine state
and report health.

Pass if provisioning does not automatically rerun, diagnostics survive, and
the outcome is eligible fallback, deliberate installer repair, or separately
authorized maintenance recovery.

### E-013: Factory reset versus reinstall

Exercise both commands against the same populated fixture.

Pass if reinstall preserves only its declared owners and identity policy, while
factory reset destroys every selected identity/secret/state scope, revokes as
required, and returns to unprovisioned—not automatically enrolled—state.

### E-014: Mechanism mapping

Map the baseline and failure cases onto:

1. systemd-sysinstall;
2. direct systemd-repart/bootctl/cryptenroll composition;
3. generated Ignition input; and
4. bootc install.

Cloud-init is mapped only if a concrete target requires it.

## Measurements

| Measure | sysinstall | Direct composition | Ignition adapter | bootc install |
| --- | --- | --- | --- | --- |
| Trusted installer components | TBD | TBD | TBD | TBD |
| NeutrinOS-specific code/records | TBD | TBD | TBD | TBD |
| Blank VM install time | TBD | TBD | TBD | TBD |
| Owner interactions | TBD | TBD | TBD | TBD |
| Offline media/transfers | TBD | TBD | TBD | TBD |
| Recoverable interruption points | TBD | TBD | TBD | TBD |
| Persistent secrets/remnants | TBD | TBD | TBD | TBD |
| Restore/re-enrollment time | TBD | TBD | TBD | TBD |

## Physical readiness gates

Before changing `desktop-jason`:

- restore verified backups to scratch storage;
- exercise the intended dual-disk preservation map;
- verify installer Secure Boot and owner-key rollback;
- verify TPM2 enrollment, firmware update, clear, and independent recovery;
- confirm every disk using physical and system topology; and
- prove return to the current system or an independently bootable recovery path.

Before changing `router`:

- install and exercise the qualified TPM or explicitly reopen the accepted
  hardware-bound-unlock requirement;
- verify IPMI console and alternate management path without the production data
  plane;
- exercise watchdog, fallback, and power interruption;
- restore its configuration/state owners on scratch storage; and
- retain a known-good bootable router/recovery path.

## Acceptance output

- exact canonical record schemas and authority map;
- resolved online/offline approval ceremony;
- installation phase and interruption table;
- replay, clone, reset, and identity-epoch policy;
- minimal first-boot allowlist;
- mechanism comparison with measured operating cost;
- physical migration checklists; and
- proposed ADR text only if the mechanism evidence supports a decision.
