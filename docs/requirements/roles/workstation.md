---
status: outline
last_updated: 2026-08-09
---

# Workstation role

The current workstation, `desktop-jason`, is the first physical deployment
target. Its initial sanitized hardware and trust capabilities are recorded in
the [reference-host inventory](../../research/hardware/reference-host-inventory.md#desktop-jason-observed-workstation-baseline).

## Known baseline

- x86-64 AMD Ryzen 7 3700X with 64 GB installed memory
- Gigabyte X570 I AORUS PRO WIFI board
- AMD Radeon PRO W6600 GPU
- Intel wired and wireless networking
- UEFI firmware with Secure Boot currently disabled and setup mode enabled
- TPM 2.0 advertised but not yet exercised from a host environment
- approximately 512 GB system NVMe and 1 TB `/home` NVMe
- current ext4 root and home with no observed block-encryption layer

## Candidate capability areas

- UEFI boot and recovery
- storage encryption and persistent-state layout
- wired and wireless networking as required by the actual machine
- graphical Wayland session and remote-work workflows
- audio, video, screen sharing, input, suspend, and resume
- user-level development tools and graphical applications
- rootless containers and bind-mounted source trees
- microVM execution
- safe update, rollback, backup, and rescue
- access to logs and debugging information after a failed graphical boot

## Initial constraints

- Begin with a reasonably generic kernel rather than an aggressively minimized
  workstation kernel.
- Package and desktop-component selections remain design decisions, not role
  requirements.
- The physical machine must not be the first place a release artifact boots.

## Remaining information needed

- TPM operation, owner-key enrollment, bootloader, and physical recovery tests
- exact GPU/display topology and required monitor behavior
- storage-encryption migration and preservation plan
- audio, camera, Bluetooth, and input hardware requirements
- suspend, hibernate, docking, and remote-work expectations
- applications and development workflows that are release blockers
- acceptable recovery time and data-loss boundaries
