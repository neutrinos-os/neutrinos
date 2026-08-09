---
status: draft
last_updated: 2026-08-09
---

# Reference qualification platform

## Purpose

Provide a fast, reproducible environment in which the literal candidate
release artifacts can exercise the common build, boot, update, rollback, and
recovery lifecycle before physical deployment.

## Initial platform boundary

- x86-64 QEMU/KVM virtual machine
- UEFI firmware
- virtio-backed storage, networking, console, and other modeled devices
- optional vTPM for tests involving measurement, enrollment, or sealed data

Exact virtual hardware versions and resource sizes remain open. They must
eventually be pinned or recorded as test inputs.

## Candidate acceptance capabilities

- Boot a newly built candidate artifact without reconstructing it on the VM.
- Expose a release identity that can be matched to build and test records.
- Exercise clean installation or initial provisioning.
- Stage and boot an update.
- Detect success and bless the candidate deployment.
- Simulate boot failure and return to the previous deployment.
- Interrupt update staging without losing the last known-good deployment.
- Exercise rescue when normal deployments cannot boot.
- Preserve, migrate, corrupt, and restore representative mutable state.
- Run trust-path tests both with and without a vTPM where supported by the
  design.

## Non-goals

- Proving support for arbitrary physical hardware.
- Replacing tests of workstation or router hardware-specific behavior.
- Defining the microVM guest role or requiring a microVM-optimized kernel.

## Open questions

- Which firmware implementation and configuration are part of the test input?
- Which failures require hypervisor fault injection?
- What minimum test topology is required for networking and update services?
- Which tests are mandatory per change, per release candidate, or periodically?

