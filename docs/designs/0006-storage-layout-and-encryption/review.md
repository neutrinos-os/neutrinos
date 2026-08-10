---
design: DES-0006
reviewer: Codex adversarial pass
perspective: failure, security, recovery, operability, alternatives
date: 2026-08-09
status: open
---

# Storage layout, immutable root, and encryption review

## Summary judgment

The proposal cleanly separates authenticated public release artifacts from
encrypted persistent state and maps the deployment lifecycle onto standard
systemd/UAPI objects. Its strongest rejection case is operational fragility:
several root/Verity/UKI resources, multiple encrypted volumes, recovery media,
PCR policy, header backups, and fixed partition capacity can create more ways
to strand a one-person fleet than a simpler mutable encrypted root.

Acceptance should ratify boundaries and falsifiable requirements, not declare
the paper mapping proven.

## Challenges

### C-001: Multi-resource A/B can still produce an authenticated hybrid

- Severity: critical
- Claim: a valid signed UKI can point at a valid root from another deployment,
  or bootloader and GPT metadata can select a half-updated tuple.
- Failure or cost if true: the machine runs release-owned bytes that were never
  jointly qualified even though each component passes a local integrity check.
- Required response or experiment: substitute every pairwise-valid UKI, root,
  Verity, config, label, and manifest combination and inject power loss before
  and after every finalization write.
- Author response: slot and version names are explicitly non-authoritative;
  the signed UKI root hash and deployment manifest must bind the literal tuple,
  and UKI entry-point installation occurs last.
- Disposition: mitigated on paper; implementation evidence required.
- Residual risk: firmware-variable and FAT rename behavior may not provide the
  assumed ordering on actual hardware.

### C-002: Fixed partition slots can make the 16 GB router undeployable

- Severity: critical
- Claim: two roots, two hash trees, boot artifacts, recovery, state,
  diagnostics, and reserve may not fit after realistic package growth.
- Failure or cost if true: updates require shrinking the OS unsafely or give up
  the fallback/recovery guarantees exactly where availability matters most.
- Required response or experiment: build representative router artifacts,
  apply the capacity formula with a declared growth horizon, and compare
  EX-0008 layouts R-A and R-B.
- Author response: no byte size or commitment to the 16 GB disk is accepted
  before this evidence; moving the complete lifecycle to the 1 TB disk is a
  first-class option.
- Disposition: open.
- Residual risk: a compact initial root can conceal long-term package and UKI
  growth.

### C-003: TPM automatic unlock weakens the intuitive theft claim

- Severity: critical
- Claim: a stolen intact machine can boot an authorized vulnerable release and
  decrypt itself without a person present.
- Failure or cost if true: “encrypted at rest” is presented more strongly than
  the actual protection against offline extraction and boot substitution.
- Required response or experiment: document the exact attacker boundary, test
  withdrawn and substituted releases, and compare unattended TPM2 with
  TPM2+PIN/FIDO2 for the workstation.
- Author response: the design repeats PR-0005's narrow claim and keeps session
  authentication, revocation, and compromise recovery separate.
- Disposition: mitigated at the claim level; owner policy remains open.
- Residual risk: an authorized pre-login vulnerability can expose unlocked
  data.

### C-004: Signed PCR policy creates another high-value signer

- Severity: critical
- Claim: a policy-signing key that can authorize arbitrary UKI measurements
  can indirectly unlock every volume enrolled to it.
- Failure or cost if true: compromise of an online release workflow becomes
  data-decryption enablement across the fleet.
- Required response or experiment: define policy-key scope, offline/online
  custody, policy reference, rotation, revocation, audit, and the relationship
  to release and platform authorities before enrollment.
- Author response: ADR-0002 prohibits collapsing release and data authority;
  exact policy-key custody remains an S-006 mechanism decision.
- Disposition: open.
- Residual risk: separate policy signing adds ceremony and update failure modes.

### C-005: Recovery keys and LUKS header backups increase theft surface

- Severity: critical
- Claim: an offline recovery key plus usable header backup can bypass all
  platform and measured-boot restrictions.
- Failure or cost if true: storage confidentiality reduces to the physical and
  procedural security of recovery material.
- Required response or experiment: create an inventory and ceremony covering
  separate storage, access, audit, rotation, restore testing, loss, and
  destruction without placing all copies together.
- Author response: recovery material is explicitly independent, never stored
  only on its target, and separately governed; the concrete ceremony remains
  deliberately unresolved.
- Disposition: open.
- Residual risk: a sole maintainer can lose either availability or separation
  through one poorly designed backup location.

### C-006: Read-only `/etc` can make the system unusable

- Severity: critical
- Claim: upstream tools and services write persistent identity and settings
  under `/etc`; flattening normal config into a read-only root blocks ordinary
  operation.
- Failure or cost if true: the storage design forces a growing custom
  projection system or silently remounts `/etc` writable.
- Required response or experiment: inventory actual workstation/router writes,
  classify every one, and exercise controlled persistent exceptions before
  physical migration.
- Author response: the design explicitly leaves the projection mechanism to
  C-002, reserves an attributable admin-state boundary, and treats unhandled
  writers as unsupported rather than silently weakening the model.
- Disposition: open under C-002 and DES-0002 C-001.
- Residual risk: exceptions can accumulate until `/etc` is effectively mutable.

### C-007: EROFS is novelty without demonstrated value

- Severity: high
- Claim: ext4+dm-verity already supplies a familiar authenticated root, while
  EROFS adds tool and kernel compatibility work.
- Failure or cost if true: the project spends qualification effort on a format
  whose compression or runtime benefits do not matter for three machines.
- Required response or experiment: produce equivalent deterministic EROFS and
  ext4 roots and compare size, build, boot, memory, update, inspection,
  corruption, and recovery behavior.
- Author response: ext4 remains a mandatory challenger and fallback; EROFS is
  not accepted merely because it is read-only.
- Disposition: open.
- Residual risk: measurements may be platform- and package-set-specific.

### C-008: Multiple state volumes multiply failure and recovery work

- Severity: high
- Claim: separate machine and user/workload volumes require more keys, headers,
  backups, mounts, status, and partial-failure paths.
- Failure or cost if true: recovery becomes slower and more error-prone than a
  single encrypted state filesystem.
- Required response or experiment: enumerate actual custody/unlock differences
  and collapse volumes whenever preservation, recovery, and destruction policy
  is identical.
- Author response: the proposal explicitly uses volumes by custody/unlock
  boundary, not by path or every state owner; the workstation's two-volume split
  follows separate physical disks and reprovisioning lifecycles.
- Disposition: mitigated on paper; exercise required.
- Residual risk: later per-user or workload encryption can expand the matrix.

### C-009: Btrfs features may not justify their operating cost everywhere

- Severity: high
- Claim: scrub, quotas, low-space behavior, snapshot retention, send/receive,
  and CoW policy can cost more on a router or small state volume than reflinks
  and subvolumes provide.
- Failure or cost if true: the common default adds recovery and capacity
  incidents to roles that do not use its distinguishing features.
- Required response or experiment: exercise actual workstation and router
  state on Btrfs and ext4, including VM/container CoW, corruption, low space,
  backup, restore, and operator runbooks.
- Author response: Btrfs is the leading candidate because the owner explicitly
  wants filesystem-assisted container and VM workflows; ext4 remains a
  role-specific challenger rather than the project default.
- Disposition: open.
- Residual risk: role-specific filesystem choices increase the qualification
  matrix.

### C-010: Mutable state remains vulnerable to offline tampering

- Severity: high
- Claim: dm-crypt confidentiality and ordinary filesystem checksums do not
  authenticate state against a malicious offline writer.
- Failure or cost if true: an attacker can corrupt or plant executable state
  that is consumed after a valid root boots.
- Required response or experiment: keep the claim narrow, exercise hostile
  state recovery, inventory executable mutable inputs, and measure
  dm-integrity/authenticated-encryption alternatives before rejecting them for
  sensitive roles.
- Author response: the design makes no mutable-authenticity claim and routes
  suspected access to SYS-035 compromise recovery rather than normal mount.
- Disposition: accepted risk for the initial scope, subject to hostile-state
  exercise.
- Residual risk: compromise may be undetectable, so operators can mistakenly
  choose availability recovery.

### C-011: Local recovery shares too much failure domain

- Severity: critical
- Claim: an on-disk recovery UKI and root can be destroyed with the disk, GPT,
  firmware variables, or platform keys it is meant to repair.
- Failure or cost if true: recovery is unavailable during disk replacement or
  platform-authority failure.
- Required response or experiment: exercise at least one independently stored
  recovery medium or IPMI virtual-media path in addition to any convenient
  local recovery artifact.
- Author response: local recovery is optional and never the only independent
  recovery capability; DES-0004 remains authoritative.
- Disposition: mitigated by design; physical exercise required.
- Residual risk: removable media can be stale or inaccessible when needed.

### C-012: Layout reserve is easy to consume or mis-size

- Severity: high
- Claim: shared free space and flexible state growth can consume the capacity
  promised for staging, diagnostics, or future layout migration.
- Failure or cost if true: an update fails only after acquisition, or recovery
  cannot retain evidence under full-disk pressure.
- Required response or experiment: represent reserve as an explicit protected
  region or enforceable quota, alert before violation, and test full-storage
  behavior.
- Author response: the design makes reserve an owned region and forbids normal
  state growth from silently consuming it; exact mechanism remains open.
- Disposition: open.
- Residual risk: fixed reserve wastes scarce router capacity while flexible
  reserve is harder to guarantee.

## Missing alternatives or evidence

- A measured comparison with a single versioned root-image-file store rather
  than partition slots.
- Actual mkosi/systemd version availability after L-001 selects package inputs.
- Firmware and bootloader behavior with an ESP-only artifact store and, only if
  capacity requires it, a split ESP/XBOOTLDR layout.
- A concrete self-contained recovery UKI versus recovery root-partition
  comparison.
- Actual TPM2 signed-policy behavior on `desktop-jason` and the proposed router
  module.
- A plaintext-spill audit covering suspend, hibernation, kdump, journal,
  container, VM, and application temporary files.

## Requirements accepted; changes before design acceptance

SYS-048 through SYS-056 were accepted on 2026-08-10. The mechanism design
remains in review and must:

1. Keep root format, recovery packaging, workstation mutable filesystem,
   router target disk, and exact TPM policy explicitly gated by experiments.
2. Add the multi-resource hybrid, capacity exhaustion, recovery-material loss,
   hostile state, `/etc` writer, and full-storage cases to the spike plan.
3. Do not accept a production router claim until hardware-bound unlock and
   independent console recovery are physically exercised.
