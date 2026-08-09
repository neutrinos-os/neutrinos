---
id: DES-0001
title: System model and release lifecycle
status: sketch
owners: []
reviewers: []
created: 2026-08-09
last_updated: 2026-08-09
depends_on: []
decision_backlog: [P-001, P-003, P-004, S-001, S-002, S-003, L-004, L-005]
related_adrs: []
---

# System model and release lifecycle

## Problem

NeutrinOS needs an end-to-end model connecting source and package inputs to a
running, identifiable machine. Without that model, local choices about package
ecosystems, filesystems, boot loaders, desktop components, or kernel variants
will define incompatible architecture by accident.

This design must establish the vocabulary and boundaries used by subsequent
designs. It does not select individual implementations yet.

## Goals

- Define the identities and boundaries of a release, artifact, role,
  configuration, deployment, and persistent state.
- Describe build, qualification, publication, installation, update, blessing,
  rollback, and recovery as one lifecycle.
- Identify which parts may vary by role without changing the lifecycle.
- Define the questions that implementation-specific designs must answer.
- Make update and rollback claims falsifiable.

## Non-goals

- Selecting Arch, Fedora, or another package source.
- Committing to mkosi, repart, sysupdate, Nebraska, Btrfs, or another mechanism.
- Defining final partition layouts, package lists, or desktop components.
- Designing a public release service before the initial product scope is known.

## Candidate invariants

1. A released deployment has an immutable artifact identity.
2. Tests qualify that exact identity rather than reconstructing an equivalent
   system on the target.
3. Persistent state is not used as the identity of the OS release.
4. Deployment becomes successful only after a booted machine passes defined
   health criteria and is blessed.
5. Every update has a bounded failure state and a recovery transition.
6. Role variation preserves common release and recovery semantics.

## Established project constraints

- The project provisionally distinguishes itself through one version-controlled,
  test-gated machine model across heterogeneous personal-fleet roles. Exact
  artifacts and relevant role configuration must pass role-specific tests;
  replacement, rollback, and recovery are part of the release contract.
- NeutrinOS is systemd-first: when a systemd ecosystem project addresses an
  accepted requirement, selecting an alternative requires the evidence and
  review defined by ADR-0001.
- The personal-fleet phase maintains one current release line. Older artifacts
  may remain available for rollback or recovery without being represented as
  security-maintained releases.
- The initial qualification target is an x86-64 QEMU/KVM virtual machine using
  UEFI and virtio, with vTPM available for applicable tests.
- The current workstation is the first physical deployment target and begins
  with a reasonably generic kernel.
- The router is the second physical role and must challenge the common model
  before that abstraction is considered established.

## Lifecycle sketch

```text
source revision + pinned inputs + role configuration
                         ↓
                    build outputs
                         ↓
          identify, verify, and qualify artifacts
                         ↓
                  sign and publish release
                         ↓
                  rollout policy selects release
                         ↓
               machine stages candidate deployment
                         ↓
                  reboot and health evaluation
                    ↙                    ↘
             failure/timeout          success
                    ↓                    ↓
           rollback or recovery       bless

persistent state crosses deployment boundaries and therefore needs separate
schema, migration, compatibility, backup, and recovery rules
```

## Core questions

### Product and role

- What is shared among all roles, and what constitutes a separate artifact?
- Must one release version contain mutually compatible artifacts for every
  supported role?
- Which workstation and router requirements must also run on the reference
  qualification platform, and which require physical hardware?

### Identity and composition

- Is the deployment unit a complete disk image, a system image plus boot
  artifact, or another set?
- How are kernel, initrd, command line, OS image, extensions, and machine
  configuration bound to one release identity?
- Which composition occurs during build, publication, installation, or boot?

### State

- Detailed ownership, compatibility, migration, and recovery semantics are
  proposed in [DES-0002](../0002-state-ownership/README.md).
- What survives OS replacement, and who owns it?
- How is `/etc` classified relative to generated defaults and local overrides?
- How are `/var`, `/home`, container data, VM images, credentials, and logs
  migrated, rolled back, backed up, and reset?
- What prevents a newer state schema from making an older deployment unbootable
  or unsafe?

### Trust

- The initial attacker, authority, boot-integrity, confidentiality, and
  compromise-recovery boundaries are proposed in
  [DES-0003](../0003-threat-and-trust-model/README.md).
- Which identities are signed, measured, encrypted, or verified?
- Which authority may publish a release, enroll a machine, or authorize a
  downgrade?
- How does recovery work after key loss or compromise?

### Health and recovery

- Which pre-release tests are common and which are role-specific?
- What constitutes a successful boot beyond reaching a target?
- How many failed boots trigger fallback, and what if both deployments fail?
- What recovery environment remains available independently of mutable state?

## Alternatives that must be compared

- Adopt an existing Fedora Atomic variant and layer only configuration.
- Base the system on GNOME OS or ParticleOS image work.
- Use a Flatcar-style host and separate desktop concerns.
- Express the fleet through NixOS rather than an image-release abstraction.
- Build a systemd/UAPI image model directly from distribution packages.
- Maintain mutable traditional installations and improve only their testing.

The comparison must evaluate whole lifecycle cost, not feature-count parity.

## Verification plan

Before this design can be accepted, it must enable a technology-neutral test
story for at least two substantially different roles. The story must cover:

- deterministic identification of inputs and outputs
- booting the literal candidate artifact
- qualification failure before publication
- interruption while staging an update
- failure before and after the boot-success boundary
- automatic and manual rollback
- incompatible or corrupt mutable state
- loss of network during rollout
- loss or compromise of a signing authority
- rescue and reinstall while preserving selected state

## Initial adversarial prompts

- What useful property does this system provide that an existing atomic distro
  cannot provide with configuration and CI?
- Is “one model for every role” a valuable invariant or a source of accidental
  abstraction?
- Can immutable-artifact rollback be honest without transactional application
  state?
- Which control-plane component becomes required for a machine to remain
  operable?
- Which proposed trust guarantee disappears when the user has physical access
  or administrative control?
- Is reproducibility required, or is traceable provenance the actual need?

## Exit criteria

- The charter and initial reference role are selected.
- Terms and identities in the lifecycle are unambiguous.
- State and trust boundaries are explicit.
- At least one strong existing-system alternative has been evaluated.
- Adversarial reviews have no unresolved critical challenge.
- Resulting decisions are captured in ADRs and candidate requirements are
  updated.
