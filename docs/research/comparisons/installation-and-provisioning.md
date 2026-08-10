---
id: RES-0010
title: Installation and first-boot provisioning comparison
status: draft
date: 2026-08-10
source_checked: 2026-08-10
related_designs: [DES-0010]
---

# Installation and first-boot provisioning comparison

## Question

Which current upstream mechanisms can prepare storage and hand off a previously
built NeutrinOS deployment without owning machine enrollment or becoming the
normal configuration system?

## Required semantic split

```text
bootstrap transport locates bounded intent
installer prepares and verifies local storage/artifacts
platform owner authorizes firmware trust changes
data owner authorizes unlock and recovery methods
enrollment authority binds a fresh machine key to one record
release authority already authorized the deployment
normal first boot proves the joined result
```

No candidate reviewed here supplies all of these authorities, and that is a
feature rather than a gap to erase.

## systemd-sysinstall

### Current upstream behavior

`systemd-sysinstall` is now part of current upstream systemd. Its manual
describes a terminal and command-line installer intended for install media. It:

- prompts for or accepts a target block device;
- validates available capacity and asks whether to erase or retain existing
  partition space;
- optionally registers the installation in firmware variables;
- displays a plan and asks for confirmation;
- encrypts basic system credentials with `systemd-creds`;
- invokes `systemd-repart` using installer-specific or ordinary definitions;
- links a selected/current UKI and credentials to the target with `bootctl`;
- installs systemd-boot; and
- supports noninteractive invocation.

It deliberately leaves user/root-password setup to the installed system's
first-boot path. ParticleOS currently boots an Installer UKI profile that runs
`systemd-sysinstall`, then completes installation on the target.

### Fit

- Native alignment with NeutrinOS's leading GPT, repart, UKI, systemd-boot, and
  system-credential candidates.
- Interactive and noninteractive paths can share one implementation.
- Existing target validation, dry-run planning through repart, confirmation,
  and firmware-variable choice reduce custom installer work.
- Installer-specific repart definitions can describe the accepted layout.

### Gaps and risks

- The component is new and has limited production history.
- Its native operation copies basic OS partitions and a kernel; NeutrinOS must
  prove exact complete-set installation across root, Verity, UKI, configuration,
  recovery, and evidence objects.
- It does not define NeutrinOS provisioning intent, preservation manifests,
  enrollment vouchers, machine identity, or binding approval.
- Generic credential injection could bypass the accepted configuration boundary
  unless fields and consumers are constrained.
- Interactive confirmation is not protection against a malicious installer.
- Availability in the selected stable package baseline is not yet established.

### Disposition

Leading installer candidate under ADR-0001, gated on a released version and the
literal EX-0012 lifecycle. Preserve a mapping to its lower-level tools so its
limits are visible.

Sources:

- <https://github.com/systemd/systemd/blob/main/man/systemd-sysinstall.xml>
- <https://github.com/systemd/particleos#installation>

## Direct systemd/UAPI composition

`systemd-repart` can create/grow/populate GPT partitions, LUKS2 containers, and
Verity companions. `systemd-cryptenroll` manages passphrase, recovery-key,
FIDO2, PKCS#11, and TPM2 enrollments. `bootctl` manages systemd-boot and UKI
placement. `systemd-firstboot`, system credentials, and machine-id facilities
cover narrow first-boot state.

### Fit

- Each operation and native diagnostic remains explicit.
- NeutrinOS can order multiple deployment artifacts and final entry-point
  activation precisely.
- It composes the same host lifecycle rather than introducing another updater.

### Gaps and risks

- NeutrinOS must orchestrate destructive confirmation, progress, rollback, and
  evidence.
- A wrapper can quickly become a bespoke installer.
- Cross-tool atomicity is not automatic.
- Platform key enrollment and machine enrollment remain separate.

### Disposition

Required reference mapping and fallback. Use directly only where
`systemd-sysinstall` cannot meet an accepted requirement.

Sources:

- <https://www.freedesktop.org/software/systemd/man/latest/systemd-repart.html>
- <https://www.freedesktop.org/software/systemd/man/latest/systemd-cryptenroll.html>
- <https://www.freedesktop.org/software/systemd/man/latest/bootctl.html>
- <https://www.freedesktop.org/software/systemd/man/latest/systemd-firstboot.html>
- <https://www.freedesktop.org/software/systemd/man/latest/systemd.system-credentials.html>

## Ignition

### Current upstream behavior

Ignition is a distribution-agnostic initrd provisioner used by Fedora CoreOS,
Flatcar, openSUSE MicroOS, and related systems. It reads a versioned declarative
JSON configuration from a platform-specific source on first boot, operates on
disks/filesystems and files before switching root, and aims to produce the
requested machine or fail the boot. Current stable specs include 3.6.0.

Its rationale explicitly distinguishes one-time provisioning from configuration
management. Its operator guidance also exposes relevant hazards: filesystem
reuse/wipe rules, platform-specific metadata deletion, secrets in user data,
and the effects of rerunning first-boot behavior.

### Fit

- Strong, mature first-boot and metadata-source machinery.
- Versioned declarative schema and validator.
- QEMU fw_cfg, config drives, removable devices, remote URLs, and many cloud
  datasources are established transports.
- Early disk and network stages can fail before starting the nominal system.

### Gaps and risks

- Writing systemd units, users, files, and kernel arguments overlaps the normal
  NeutrinOS configuration boundary.
- Its first-boot marker is not NeutrinOS enrollment approval or replay state.
- Platform metadata and kernel URL override are bootstrap inputs, not authority.
- Broad inclusion increases the installer/initrd trusted computing base.
- Secrets may persist in platform user data unless the provider supports secure
  deletion and NeutrinOS exercises it.

### Disposition

Mandatory generated-adapter challenger for VM/cloud and first-boot handoff.
Do not use its configuration as operator-authored fleet intent and do not
include it unless it removes more custom trusted code than it adds.

Sources:

- <https://coreos.github.io/ignition/>
- <https://coreos.github.io/ignition/rationale/>
- <https://coreos.github.io/ignition/specs/>
- <https://coreos.github.io/ignition/operator-notes/>
- <https://coreos.github.io/ignition/supported-platforms/>

## cloud-init

Cloud-init offers broad cloud datasource, network, user, key, package, script,
and lifecycle modules. It maintains cached instance state and chooses first-
versus-subsequent boot partly from datasource instance identity.

Its documentation identifies a directly relevant security failure: on a
physical appliance, attacker-supplied datasource identity can make default
first-boot detection treat the device as a new instance and apply attacker
configuration. Its cache-clean tooling can also deliberately cause stages to
rerun.

### Fit

- Widest cloud-image compatibility.
- Existing provider integrations and diagnostics.
- Useful for external environments that cannot supply Ignition or a direct
  NeutrinOS seed.

### Gaps and risks

- Per-boot and per-instance modules exceed one-time bounded provisioning.
- Instance ID is not an enrollment identity or reliable replay boundary.
- Script and package capabilities violate normal NeutrinOS image semantics.
- Removing or permanently confining all continuing authority is environment-
  specific.

### Disposition

Compatibility-only challenger, outside the initial trusted path. If adopted,
use a strict datasource/module allowlist, generated inputs, and an exercised
post-enrollment disable/neutralization state.

Sources:

- <https://docs.cloud-init.io/en/latest/explanation/first_boot.html>
- <https://docs.cloud-init.io/en/latest/reference/cli.html>

## bootc install

Current bootc supplies `install to-disk`, `to-filesystem`, and
`to-existing-root`. `to-disk` is an opinionated wrapper over lower-level storage
and `to-filesystem` allows an external installer to prepare complex storage.
The install runs from the container image being installed and can configure
TPM2-bound LUKS. `install finalize` supports external installation workflows.

### Fit

- Integrated install and later lifecycle for the bootc challenger.
- Supported command surface and installation provenance.
- External filesystem mode permits richer storage ownership.

### Gaps and risks

- Uses the OCI/OSTree deployment model not currently leading for NeutrinOS.
- Privileged container invocation and installed-image coupling have their own
  trust boundaries.
- Injection before first boot can again become a normal configuration escape.
- Enrollment, platform ownership, preservation, and exact multi-artifact
  closure remain NeutrinOS obligations.

### Disposition

Mandatory integrated-lifecycle challenger, not the default installer decision.

Sources:

- <https://bootc.dev/bootc/bootc-install.html>
- <https://bootc.dev/bootc/man/bootc-install.8.html>

## Comparison

| Criterion | systemd-sysinstall | Direct systemd composition | Ignition | cloud-init | bootc install |
| --- | --- | --- | --- | --- | --- |
| Local disk install | Native | Composed | First-boot disk manipulation | Environment-dependent | Native |
| NeutrinOS storage mapping | Promising, must prove | Most explicit | Schema adapter | Weak fit | External filesystem path |
| Exact deployment-set finalization | Must extend/prove | Can orchestrate | Not native | Not native | Strong for bootc image, gaps for external artifacts |
| One-time model | Install invocation | NeutrinOS-owned | Native intent | Mixed frequencies | Install invocation |
| Normal-config overlap | Credential risk | Wrapper risk | Broad | Very broad | Injection risk |
| Cloud metadata support | Bootstrap adapter needed | Adapter needed | Strong | Strongest | External provisioning |
| Machine enrollment | Not provided | Not provided | Not provided | Not provided | Not provided |
| Upstream maturity | New | Mature components, custom join | Mature | Mature | Production challenger |
| systemd-first alignment | Direct | Direct | Integrates with systemd | Generic | Uses systemd pieces but different lifecycle |

## Candidate posture

1. Lead with systemd-sysinstall plus NeutrinOS repart definitions.
2. Keep a direct lower-level systemd mapping as the conformance reference.
3. Add only the irreducible provisioning-intent and enrollment ceremony around
   upstream tools.
4. Exercise Ignition as a generated VM/cloud handoff, not an authoring surface.
5. Retain bootc install as the integrated lifecycle challenger.
6. Defer cloud-init until a concrete target requires it.
7. Accept no mechanism until interruption, replay, clone, preservation,
   authority, and secret-retirement tests pass.

## Evidence still required

- Packaged/released systemd-sysinstall version in Fedora and Arch candidates.
- Exact command/output capture on a blank QEMU disk.
- Multi-resource install/finalization and literal target verification.
- Credential visibility, TPM/null-key behavior, and removal after consumption.
- Ignition initrd size, dependency, and allowlist comparison.
- bootc storage and enrollment mapping on the same fixture.
- Measured operator time, custom code, and long-term maintenance for each path.
