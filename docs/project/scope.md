---
status: accepted
last_updated: 2026-08-09
---

# Scope

## Initial operating scope

- The initial deployment scope is Jason's personal fleet.
- The system is designed as a reusable multi-role OS framework rather than as
  a collection of unrelated machine configurations.
- NeutrinOS is not initially offered as a public distribution.
- There is no initial external promise of compatibility, hardware support,
  release cadence, or security-response time.
- Reusability remains a design constraint to test, not a public support
  commitment.

## Initial target strategy

- Every release is qualified first on an x86-64 QEMU/KVM virtual machine with
  UEFI and virtio devices.
- vTPM is available on the qualification platform for tests that exercise the
  measured-boot or machine-enrollment path; it is not yet a universal runtime
  requirement.
- The current workstation is the first physical deployment target.
- The initial workstation uses a reasonably generic kernel. Kernel reduction
  or specialization requires later evidence and must preserve a recovery path.
- The router is the second physical role. Its intentionally different
  networking, availability, and recovery requirements are used to challenge
  the common role abstraction early.
- Supporting these targets does not imply support for arbitrary x86-64
  hardware.

## In scope for the architecture phase

- project goals, non-goals, and system invariants
- machine-role and hardware-support boundaries
- build inputs and release artifact identity
- boot, integrity, encryption, and trust relationships
- immutable and mutable state boundaries
- installation, update, rollback, and recovery lifecycle
- configuration, identity, and secrets ownership
- testing, release promotion, provenance, and security maintenance
- container, microVM, and user-software ownership models
- evaluation of existing systems and reusable upstream work

## Not yet in scope

- production implementation
- final package selections
- desktop theming and cosmetic integration
- kernel micro-optimization
- a public compatibility promise
- bespoke tooling where an upstream mechanism has not first been evaluated

## Non-goals

These were ratified following
[adversarial review](reviews/0001-charter-principles-and-scope.md):

- Maintaining a downstream fork of Arch, Fedora, or another distribution's
  packaging as the primary product. Using its packages as build inputs remains
  in scope.
- Supporting arbitrary mutation of the deployed OS through a host package
  manager.
- Supporting legacy BIOS during the personal-fleet phase.
- Providing every Linux packaging ecosystem as a first-class application
  mechanism.
- Making filesystem snapshots the identity of an OS release.
- Building a new init system, general-purpose package ecosystem, or universal
  configuration language when maintained upstream components can satisfy the
  accepted requirements.
- Requiring every role to use the same kernel, package set, disk layout, or
  artifact shape merely to claim a common lifecycle.
- Transparently rolling back arbitrary application and workload state. Each
  state owner must instead define its own compatibility and recovery contract.
- Removing every scripting language, traditional utility, or general-purpose
  component from every role as an end in itself.

## Accepted non-goals for the initial phase

- Operating a generally available public Linux distribution.
- Supporting third-party users or hardware beyond the personal fleet.
- Providing external compatibility, release, or security-response guarantees.
