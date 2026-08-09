---
status: outline
last_updated: 2026-08-09
---

# Workstation role

The current workstation is the first physical deployment target. Its hardware
inventory and operational requirements must be captured before this document
becomes normative.

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

## Information needed

- CPU architecture and model
- motherboard, firmware, TPM, and Secure Boot capabilities
- GPU and display topology
- storage devices and current filesystem layout
- network, audio, camera, Bluetooth, and input hardware
- suspend, hibernate, docking, and remote-work expectations
- applications and development workflows that are release blockers
- acceptable recovery time and data-loss boundaries

