---
id: EX-0009
title: Reference package input closure and refresh exercise
status: proposed
date: 2026-08-10
decision_gates: [L-001, L-002, L-007]
---

# Reference package input closure and refresh exercise

## Purpose

Compare Fedora stable and dated Arch official repositories using literal
NeutrinOS reference-role inputs. The exercise must reveal downstream packaging
work and ongoing owner cost, not merely prove that mkosi can install `systemd`.

## Capability floor

Before selecting versions, derive a finite capability list from accepted and
in-review designs:

- UEFI, signed UKI, Secure Boot, boot assessment, and TPM2 tooling;
- dm-verity, LUKS2, EROFS and ext4 root candidates, and Btrfs state tooling;
- systemd-repart, systemd-sysupdate, systemd-cryptenroll, networkd, resolved,
  timesyncd, credentials, and VM qualification support;
- workstation graphics, Wayland, audio, input, storage, container, and microVM
  prerequisites without prematurely selecting the desktop applications; and
- router networking, firewalling, DHCP/DNS, observability, console, and
  hardware-support prerequisites.

Record capability evidence separately from package version. A newer version
does not win if the required behavior is already present and qualified.

## Candidate inputs

### Fedora

- One currently supported stable release with at least six months of expected
  support remaining, unless the exception is documented.
- Official release and stable updates repositories only.
- Exact repository metadata, key identities, package bytes, source RPM
  identities, solver version, and resolution log retained locally.

### Arch

- One dated ALA state for official repositories only.
- All repositories taken from the same archive date and architecture.
- Exact database files, keyring identity, package bytes, recipe/source
  references, pacman version, and resolution log retained locally.

No AUR, RPM Fusion, COPR, or upstream binary may fill a gap silently. Record
each gap first, then process the same finite candidate through the proposed
third-party intake policy.

## Variants

Resolve at least:

1. a minimal UEFI qualification VM;
2. the `desktop-jason` base OS closure; and
3. the `router` base OS closure.

Shared input objects may be deduplicated, but dependency reasons and role
membership remain independently inspectable.

## Measurements

For each candidate and variant, capture:

| Measure | Why it matters |
| --- | --- |
| Direct and transitive package counts | Reveals closure complexity rather than requested-list size |
| Compressed package and installed-root bytes | Sizes intake retention and deployment artifacts |
| Weak/optional dependency contribution | Exposes policy-driven bloat and hidden capability loss |
| Missing capabilities and packages | Predicts private overlay and third-party burden |
| Scriptlets/triggers and filesystem side effects | Maps executable build inputs and configuration surprises |
| Source/recipe and build-reference coverage | Measures provenance inspection quality |
| Signature and key-verification behavior | Exercises upstream trust and rotation handling |
| Build and qualification time | Measures normal and emergency response cost |
| Human intervention and owner minutes | Tests the one-maintainer constraint |
| Input delta across refresh | Measures unrelated security-response churn |

## Refresh scenarios

Run or replay three transitions:

1. **routine refresh:** advance each candidate by a comparable interval and
   explain every closure change;
2. **urgent fix:** select a representative kernel, systemd, cryptographic
   library, or exposed router-service update and measure all unrelated changes
   required by the supported upstream model; and
3. **large transition:** tabletop or execute Fedora N-to-N+1 and a comparable
   Arch ecosystem transition, including state-compatibility and fallback
   effects.

Record when upstream advisory data became available, when fixed packages became
available, and which NeutrinOS gates dominate delivery. Do not infer a general
response-time promise from one sample.

## Negative tests

- Replace one package with the same NEVRA but different bytes.
- Mix one repository database or package from a different date/branch.
- Rotate, expire, revoke, omit, and substitute an upstream signing key.
- Remove an intake object and disable every upstream network source.
- Add an undeclared repository with a higher-priority package name.
- Permit a hostile install script to probe network, release keys, and machine
  credentials and to write outside expected image/build locations.
- Re-evaluate a valid old snapshot after a newly applicable advisory.
- Retire or remove a third-party source after a deployment contains it.

Each case must fail at an attributable boundary or produce the exact stale,
unsupported, or compromised status required by policy.

## Decision record

The completed exercise must end with a compact table:

| Gate | Fedora result | Arch result | Decisive? |
| --- | --- | --- | --- |
| Required capabilities | TBD | TBD | Yes |
| Project-built package burden | TBD | TBD | Yes |
| Third-party imports | TBD | TBD | Yes |
| Routine refresh churn | TBD | TBD | Yes |
| Urgent-fix churn and elapsed owner work | TBD | TBD | Yes |
| Major-transition burden | TBD | TBD | Yes |
| Offline reconstruction | TBD | TBD | Both must pass |
| Provenance/source attribution | TBD | TBD | Both must pass minimum |
| Closure/image/storage cost | TBD | TBD | Contextual |

The ecosystem ADR may be proposed only after this table is populated and every
blocking failure has an owner and disposition.
