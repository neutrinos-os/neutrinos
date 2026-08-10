---
design: DES-0010
reviewer: Codex adversarial pass
perspective: security, operations, failure, maintainability, alternatives
date: 2026-08-10
status: open
---

# Installation, provisioning, and machine enrollment review

## Summary judgment

The proposal closes the largest open fleet-intent trust gap: a bootstrap hint
locates work, while an explicit single-use authority and proof-of-possession
ceremony creates the machine binding. It also correctly treats disk selection
as a safety problem that signatures alone cannot solve.

The strongest reason to reject it is ceremony and custom protocol risk. A
single-maintainer OS could spend more effort securely enrolling three machines
than operating them. Acceptance requires a literal offline flow that fits on a
short runbook and reuses upstream systemd tooling for everything except the
irreducible binding decision.

## Challenges

### C-001: The installer can display a safe plan and erase another disk

- Severity: critical
- Claim: a compromised installer controls both the device list and the display,
  so interactive confirmation is not independent verification.
- Evidence: the installer has raw block-device access and renders its own UI.
- Failure or cost if true: catastrophic loss of unrelated user/workload data.
- Required response or experiment: boot a measured/verified installer, minimize
  its code, identify target using stable properties, disconnect uninvolved disks
  where practical, require verified backup, and test hostile remapping.
- Author response: confirmation reduces mistakes but is not a security boundary
  against a malicious installer.
- Disposition: accepted-risk with layered mitigation.
- Residual risk: physical devices can be indistinguishable after replacement or
  controller changes.

### C-002: A voucher is just a shared enrollment password with a new name

- Severity: critical
- Claim: whoever copies the voucher can race the intended machine and claim its
  record.
- Evidence: the machine has no prior credential at first enrollment.
- Failure or cost if true: attacker identity receives machine-scoped policy or
  secrets.
- Required response or experiment: make the voucher one-use, short-lived,
  record- and operation-scoped; bind approval to a fresh proof-of-possession and
  independent owner comparison; expose races rather than first-writer-wins.
- Author response: the voucher authorizes a proposal, not unconditional binding.
- Disposition: open pending EX-0012.
- Residual risk: remote unattended bare-metal enrollment needs another trusted
  hardware or out-of-band path.

### C-003: Owner confirmation still trusts a compromised installer display

- Severity: critical
- Claim: comparing a fingerprint shown only by the installer does not verify the
  key actually submitted.
- Evidence: the same compromised environment generates and displays the request.
- Failure or cost if true: an attacker substitutes its key during enrollment.
- Required response or experiment: use an independent channel derived from the
  submitted request, hardware-backed attestation where useful, or a removable
  request that the administrative verifier parses itself.
- Author response: independent verification of request bytes is required; a
  local digest display alone is insufficient.
- Disposition: open.
- Residual risk: hardware attestation adds vendor and privacy complexity.

### C-004: systemd-sysinstall is too new to be the foundation

- Severity: high
- Claim: a recently introduced component may change interfaces or omit recovery
  behavior needed by NeutrinOS.
- Evidence: it entered current upstream systemd after earlier project research
  and has limited production history.
- Failure or cost if true: installation becomes pinned to git-main systemd or a
  local fork.
- Required response or experiment: pin a released packaged version, run all
  power-loss and storage cases, and maintain a direct lower-level-tool mapping.
- Author response: it is the leading candidate, not an accepted dependency.
- Disposition: mitigated.
- Residual risk: the selected Fedora or Arch baseline may lag required fixes.

### C-005: Provisioning input becomes a second configuration language

- Severity: critical
- Claim: once Ignition, cloud-init, or installer credentials can write files and
  units, operators will put ordinary machine policy there to avoid rebuilds.
- Evidence: all candidates make such customization convenient.
- Failure or cost if true: deployed behavior no longer matches qualified
  configuration identity.
- Required response or experiment: whitelist generated handoff fields and
  destinations; reject release-owned files, services, users, and network policy
  unless they follow an accepted late-bound contract.
- Author response: first boot completes identity and machine-local state only.
- Disposition: mitigated.
- Residual risk: emergency debugging may create persistent local modification.

### C-006: Completion marker loss either bricks or replays provisioning

- Severity: critical
- Claim: a single local flag cannot safely distinguish interrupted completion
  from an old disk restored before enrollment.
- Evidence: local state can be lost, rolled back, cloned, or corrupted.
- Failure or cost if true: destructive replay or permanent inability to boot.
- Required response or experiment: join durable phase with immutable intent,
  spent-voucher state, current enrollment binding/epoch, and provisioning
  evidence; never accept absence of one flag as permission to restart.
- Author response: completion is a joined state, not one magic file.
- Disposition: resolved in design; mechanism open.
- Residual risk: offline loss of both local and authority records may require
  deliberate reset.

### C-007: TPM identity overclaims physical-machine identity

- Severity: high
- Claim: a TPM key proves possession by a TPM context, not that the chassis,
  board, operator, or machine record is correct.
- Evidence: TPMs and vTPMs can be replaced, cleared, virtualized, or proxied.
- Failure or cost if true: inventory binding gains false assurance.
- Required response or experiment: report key protection and attestation claims
  separately; retain explicit owner/administrative binding and replacement
  procedure.
- Author response: platform evidence constrains but does not assign identity.
- Disposition: resolved.
- Residual risk: remote hardware supply-chain identity remains out of scope.

### C-008: Offline enrollment cannot know whether a voucher was already spent

- Severity: critical
- Claim: two disconnected machines can use copies of the same signed voucher.
- Evidence: single-use enforcement is normally online mutable state.
- Failure or cost if true: duplicate valid requests or bindings.
- Required response or experiment: permit multiple requests to exist but allow
  the enrollment authority to issue at most one ordered approval; targets require
  the approval, not only the voucher. Reconciliation surfaces rejected races.
- Author response: voucher use need not be globally prevented at submission;
  authoritative binding is singular.
- Disposition: mitigated.
- Residual risk: an operator can still approve the wrong contender.

### C-009: Restored machine state resurrects revoked identity

- Severity: critical
- Claim: a backup or disk clone includes private key and old binding records.
- Evidence: machine state is intentionally preserved independently of OS.
- Failure or cost if true: revocation is defeated after reinstall or rollback.
- Required response or experiment: authority currentness and identity epoch are
  checked independently; backups classify identity material separately; clone
  and restore tests cover simultaneous use.
- Author response: identity preservation is conditional, never an automatic
  consequence of restoring machine state.
- Disposition: mitigated.
- Residual risk: offline machines retain a bounded stale-revocation window.

### C-010: Platform enrollment and data unlock form an unrecoverable sequence

- Severity: critical
- Claim: changing Secure Boot keys or PCR policy before testing recovery can
  strand the newly installed machine or its state.
- Evidence: platform state, UKI signatures, TPM policies, and LUKS slots interact.
- Failure or cost if true: loss of access or fallback during first install.
- Required response or experiment: define add-test-remove ceremonies, independent
  recovery unlock, header backup, firmware-reset case, and last-known recovery
  artifact before retiring any prior method.
- Author response: ceremonies are separate and each needs a verified return path.
- Disposition: open pending physical exercise.
- Residual risk: firmware bugs can invalidate the modeled order.

### C-011: Reinstall silently trusts hostile preserved state

- Severity: critical
- Claim: installing authentic OS bytes while reattaching compromised machine,
  administrator, user, or workload state does not recover a compromised host.
- Evidence: immutable root does not authenticate external executable state.
- Failure or cost if true: compromise immediately persists across reinstall.
- Required response or experiment: use owner-aware preservation, quarantine by
  default after compromise, and separate ordinary reinstall from compromise
  recovery.
- Author response: DES-0002 and SYS-035 remain authoritative.
- Disposition: resolved.
- Residual risk: determining which data is safe to restore remains difficult.

### C-012: Enrollment service becomes required for ordinary boot

- Severity: high
- Claim: short-lived certificates or online status checks can make WAN failure
  disable a healthy router.
- Evidence: freshness and revocation are often centralized.
- Failure or cost if true: network outage blocks the machine needed to restore
  the network.
- Required response or experiment: retain bounded local binding and revocation
  policy; require service only for new enrollment/rotation, not boot completion;
  exercise stale and offline status.
- Author response: enrollment authority is not an online boot dependency.
- Disposition: resolved in policy.
- Residual risk: longer offline validity increases compromise exposure.

## Missing alternatives or evidence

- Released systemd-sysinstall package and exact stability/compatibility status.
- Literal NeutrinOS repart definitions and target dry-run output.
- Signed/verified installer boot on QEMU and physical UEFI.
- Minimal offline request/approval record schemas.
- Independent request verification that does not trust installer display.
- TPM, vTPM, and explicit no-TPM identity comparisons.
- Ignition and cloud-init field allowlists plus post-completion disablement.
- Power-loss results across partition, encryption, bootloader, identity, and
  binding transitions.
- Timed scratch-disk migration and recovery runbooks.

## Required changes before design acceptance

1. Execute EX-0012 with online and offline enrollment.
2. Prove exact deployment installation and boot-entry-last semantics.
3. Select request, approval, binding, and identity-key representations.
4. Resolve independent first-request verification.
5. Demonstrate replay, clone, restore, re-enrollment, and reset behavior.
6. Complete TPM/platform/data-recovery ordering exercises.
7. Compare systemd-sysinstall, direct composition, Ignition, and bootc cost.
8. Measure normal install, reinstall, and recovery owner time.
