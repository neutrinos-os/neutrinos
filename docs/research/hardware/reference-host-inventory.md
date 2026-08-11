---
id: RES-0004
status: in-review
last_updated: 2026-08-11
evidence_cutoff: 2026-08-09
evidence_cutoff_scope: |
  The 2026-08-09 cutoff covers every live-inspection observation. Two later
  additions are not live inspection: the router TPM module recorded as acquired
  on 2026-08-10 is owner input, and the note on Haswell-era Intel PTT versions
  is vendor and secondary documentation. Neither changes an observed row.
decision_gates: [P-004, S-004, S-005, S-006]
---

# Initial host and trust-capability inventory

## Question

What hardware and currently observable boot, TPM, storage, and recovery
capabilities constrain the first workstation, router, and future server roles?

## Machine identities and evidence boundary

| Machine | Project relationship | Evidence available |
| --- | --- | --- |
| `desktop-jason` | Current workstation and first physical NeutrinOS target | Sanitized live inspection from the current machine plus owner correction |
| `router` | Router and second physical NeutrinOS target | Sanitized live inspection over SSH plus checked-in `nixconfig` configuration |
| `misc` | Separate server managed by `nixconfig`; not the current workstation | Sanitized live inspection over SSH plus checked-in `nixconfig` configuration |

`misc` and `router` are the two hosts managed by the private `nixconfig`
repository. `desktop-jason` is a separate machine. This distinction is
authoritative owner input and prevents the live AMD workstation observations
from being incorrectly compared with `hardware/misc.nix`.

This inventory deliberately omits serial numbers, MAC addresses, filesystem
UUIDs, private network values, and secret material.

## `desktop-jason`: observed workstation baseline

### Hardware

| Area | Observation |
| --- | --- |
| Architecture | x86-64 |
| CPU | AMD Ryzen 7 3700X, 8 cores and 16 logical CPUs |
| Memory | 64 GB installed according to the owner; Linux reports approximately 62 GiB usable |
| Board | Gigabyte X570 I AORUS PRO WIFI |
| Firmware | American Megatrends firmware, board version F33g dated 2021-03-25 |
| GPU | AMD Radeon PRO W6600 |
| Wired network | Intel I211 Gigabit Ethernet |
| Wireless network | Intel Wi-Fi 6 AX200 |
| Primary storage | Approximately 512 GB NVMe containing the current root, boot, and swap partitions |
| Additional storage | Approximately 1 TB NVMe mounted for `/home` |

The 62 GiB figure is an operating-system usable-memory observation, not a claim
that the installed capacity is 62 GB. The design inventory uses the owner's
64 GB installed-capacity figure.

### Boot and trust capability

| Capability | Observation | Confidence or limitation |
| --- | --- | --- |
| Firmware boot mode | UEFI | Directly observed through the firmware interface exposed to the session |
| Secure Boot | Disabled | Firmware variable reports `SecureBoot=0` |
| Platform setup mode | Enabled | Firmware variable reports `SetupMode=1`; owner-key enrollment has not yet been exercised |
| TPM | TPM 2.0 advertised through ACPI (`MSFT0101`) and sysfs | The tool session is containerized and cannot access a TPM device node, so commands, PCR behavior, ownership, and sealing remain unverified |
| Current root filesystem | ext4 | Direct block-topology observation |
| Current boot filesystem | vfat mounted at `/boot` | The active bootloader and exact ESP layout were not available through `bootctl` in this environment |
| Current storage encryption | No LUKS/dm-crypt mapping visible in the observed block topology | Requires host-level confirmation before being treated as a definitive absence |
| Local recovery | Not yet inventoried | Firmware UI, removable boot, key enrollment, and console recovery must be exercised physically |

The current machine is capable enough to investigate SYS-030, but it does not
currently satisfy it merely by having UEFI and a TPM. Secure Boot key
enrollment, authenticated root content, recovery authorization, and tamper
tests remain design and implementation work.

## `router`: observed appliance baseline

Read-only inspection over the configured SSH port and the checked-in NixOS
configuration at private repository revision `198f797` establish:

- x86-64, an Intel Xeon D-2123IT with four cores and eight logical CPUs, and
  approximately 32 GB installed memory (31 GiB reported usable);
- a Supermicro X11SDV-4C-TP8F board, revision 1.10;
- American Megatrends firmware version 1.2 dated 2019-11-14;
- NixOS 25.11 with Linux 6.15.5 at the evidence cutoff;
- UEFI boot with systemd-boot and NixOS generation files present on the ESP;
- Secure Boot disabled and firmware setup mode enabled;
- no TPM exposed through sysfs or a TPM resource-manager device; systemd's
  TPM probe reports userspace support but no firmware or driver support;
- an approximately 1 TB disk split between ext4 `/home` and `/nix`, plus an
  approximately 16 GB system disk containing swap, an ext4 root, and vfat
  `/boot`;
- no LUKS or dm-crypt mapping visible in the live block topology;
- IPMI visible through both sysfs and `/dev/ipmi0`;
- a three-minute runtime watchdog and ten-minute reboot watchdog;
- no serial console argument in the running kernel command line and the
  `ttyS0` serial getty disabled;
- headless network-appliance responsibilities with substantial native systemd
  network and service configuration; and
- no checked-in LUKS, TPM, Secure Boot enrollment, or authenticated-root policy.

The ESP contains `systemd-bootx64.efi`, its fallback copy, loader configuration,
and multiple NixOS generation entries. However, `bootctl is-installed` returned
`not-found`, so the active firmware selection and update behavior remain to be
verified rather than inferred solely from files on disk.

The IPMI and watchdog evidence strengthens the router's unattended-availability
and out-of-band-recovery options. It does not prove remote-console access,
automated rollback, or encrypted unattended boot. In particular, a TPM-bound
unlock design cannot be assumed for this hardware as currently configured.

Supermicro's documentation provides a discrete TPM path but no evidence found
for a firmware TPM on this exact board. The board manual identifies `JTPM1` as
a 10-pin SPI TPM/Port 80 header. Supermicro's exact-board FAQ recommends the
TCG 2.0 `AOM-TPM-9670V-S` or `AOM-TPM-9670H-S`, whose orientation must be
selected for the available chassis clearance. The [module product
page](https://www.supermicro.com/en/products/accessories/addon/AOM-TPM-9670V-S_H-S.php),
[board FAQ](https://www.supermicro.com/en/support/faqs/faq.php?faq=30605), and
[board manual](https://www.supermicro.com/manuals/motherboard/d/MNL-2007.pdf)
are manufacturer evidence of compatibility, not evidence that a module is
installed, provisioned, or usable by the current firmware and Linux stack.

## `misc`: observed server baseline

The same read-only collection and repository revision establish:

- a separate host named `misc`, not the current workstation;
- x86-64, an Intel Core i5-4250U with two cores and four logical CPUs, and
  approximately 16 GB installed memory (15 GiB reported usable);
- an Intel D54250WYK board with Intel firmware version
  `WYLPT10H.86A.0054.2019.0902.1752`, dated 2019-09-02;
- NixOS 25.11 with Linux 6.15.5 at the evidence cutoff;
- UEFI boot with systemd-boot and NixOS generation files present on the ESP;
- Secure Boot disabled and firmware setup mode enabled;
- no TPM exposed through sysfs or a TPM resource-manager device;
- one approximately 256 GB disk containing ext4 root and `/nix`, swap, and a
  vfat `/boot`, with no visible LUKS or dm-crypt mapping;
- no IPMI interface, no serial console argument, and the `ttyS0` serial getty
  disabled; and
- a server archetype with additional controller responsibilities.

As with `router`, the files on the ESP corroborate the checked-in systemd-boot
configuration, but `bootctl is-installed` returned `not-found`; active firmware
selection still requires a more direct check. `misc` is useful evidence for a
later server role but does not change the initial workstation/router
qualification order.

Intel's official specifications for both the [D54250WYK
kit](https://www.intel.com/content/www/us/en/products/sku/76977/intel-nuc-kit-d54250wyk/specifications.html)
and its [D54250WYB
board](https://www.intel.com/content/www/us/en/products/sku/76975/intel-nuc-board-d54250wyb/specifications.html)
state that Intel Platform Trust Technology is supported and a discrete TPM is
not. This establishes a firmware trust capability, not its TPM interface
version or its current activation. Because the live system exposes no TPM,
firmware settings and behavior must be inspected before PTT can influence the
design.

## Trust-capability matrix

`Observed` means direct sanitized inspection. `Configured` means present in
version-controlled NixOS intent but not confirmed on the running machine.

| Capability | `desktop-jason` | `router` | `misc` |
| --- | --- | --- | --- |
| x86-64 | Observed | Observed | Observed |
| UEFI use | Observed | Observed | Observed |
| systemd-boot | Unknown current bootloader | Files observed; active selection unverified | Files observed; active selection unverified |
| Secure Boot enabled | Observed no | Observed no | Observed no |
| Owner-controlled platform keys | Not currently enrolled; capability untested | Not currently enrolled; capability untested | Not currently enrolled; capability untested |
| TPM capability | TPM 2.0 advertised; operation untested | No firmware TPM evidence; a documented discrete TPM 2.0 module was acquired 2026-08-10 but is not installed, so the capability remains absent per PR-0005 | Intel PTT documented; not exposed to Linux and version/operation unverified. Vendor sources do not establish whether Haswell-era PTT presents TPM 1.2 or 2.0 |
| Authenticated immutable root | Not present or demonstrated | Not configured or demonstrated | Not configured or demonstrated |
| Storage encryption | Not visible; confirmation needed | No LUKS/dm-crypt mapping observed | No LUKS/dm-crypt mapping observed |
| Unattended reboot | Not a workstation requirement; TPM2 + PIN ruled 2026-08-11 | Required in principle; mechanism unverified | Required, stated by the owner 2026-08-11; mechanism unverified |
| Independent local recovery | Not yet exercised | IPMI device and watchdog observed; access untested | Not yet inventoried; no IPMI observed |

## Consequences for the next design

1. The minimum key and recovery design can use UEFI, owner-controlled Secure
   Boot, and TPM 2.0 as workstation targets, but must retain a non-TPM recovery
   path until physical tests succeed.
2. Workstation storage encryption is a migration requirement, not an existing
   property that can be assumed.
3. The router's initial unattended design must not depend on a TPM while no
   module is installed and proven. Adding a documented Supermicro TPM 2.0
   module remains an explicit hardware option, not an assumed baseline.
4. The NixOS files are valuable configuration and role evidence but are not a
   hardware inventory or attestation source.
5. `misc` should later exercise the server role, but bringing it into the
   initial gate would expand scope before workstation and router validate the
   lifecycle.
6. `misc` should first test its documented PTT capability in firmware; a
   discrete TPM purchase is neither supported by the official specification
   nor presently justified.

## Required follow-up evidence

### `desktop-jason`

- confirm current bootloader and ESP layout from the host environment;
- inspect TPM algorithms, PCR banks, event log, and clearing/recovery behavior;
- test owner-key enrollment and firmware reset behavior;
- inventory removable-media and firmware-console recovery;
- define the storage-encryption migration and data-preservation boundary; and
- record acceptable interactive versus unattended unlock behavior. The routine
  unlock policy is ruled: **TPM2 + PIN** (DES-0006 C-003, 2026-08-11). What
  remains is exercising it, since TPM operation is untested, Secure Boot is
  off, and owner keys are not enrolled.

### `router`

- state acceptable outage and whether every normal reboot must be unattended;
- install and qualify the discrete TPM 2.0 module acquired 2026-08-10, after
  checking orientation and chassis clearance. Until it is installed and
  exercised the capability stays absent per PR-0005, and the installation is
  physical work on the host carrying the development network, so R-054 applies
  and out-of-band access must be proven first. This replaces the earlier item,
  which asked whether to acquire a module or retain TPM absence as an explicit
  initial hardware constraint;
- verify the active firmware boot entry and systemd-boot update behavior;
- exercise IPMI power control and remote console without depending on the
  router's data-plane network;
- identify recovery paths that work without WAN, DNS, routing, or normal SSH;
  and
- determine which credentials require confidentiality after powered-off theft.

### `misc`

- defer detailed collection until the server role enters active design unless
  its hardware can cheaply provide evidence relevant to the common trust path;
- inspect firmware security settings for Intel PTT and, if enabled, verify the
  interface, TPM version, PCR banks, event log, and clear/recovery behavior.
  The TPM version is the decisive question and cannot be settled from vendor
  documentation: Intel's D54250WYK specification states PTT support without a
  version, PTT on Haswell existed only on low-power chipsets such as this
  board's i5-4250U, and broad PTT compliance with TPM 2.0 dates from Skylake,
  with Haswell-era implementations commonly presenting TPM 1.2. Enable PTT in
  firmware, then read `/sys/class/tpm/tpm0/tpm_version_major` and check for
  `/dev/tpmrm0`, which exists only for TPM 2.0. If the answer is 1.2, the
  capability is unusable for `systemd-cryptenroll --tpm2` and `misc` has no
  hardware-bound unlock path;
- verify the active firmware boot entry and systemd-boot update behavior; and
- inventory its physical recovery path before it becomes a qualification host.

## Evidence limitations

- Live inspection ran in a containerized tool session. CPU, DMI, block, UEFI,
  and sysfs information was visible, but TPM device access and bootloader tools
  were not.
- The private repository worktree contains unrelated untracked files; only
  tracked revision `198f797` and selected checked-in configuration were used.
- Generated NixOS hardware files date from 2023 and establish configuration
  history rather than present runtime state.
- Sanitized read-only inventory commands ran over the user-configured SSH port
  on both NixOS hosts. No privileged commands or state changes were requested.
- Runtime observations establish the state exposed to Linux at the evidence
  cutoff; they do not prove firmware capabilities that are disabled, absent
  from ACPI, or otherwise hidden from the operating system.
- Manufacturer documentation was checked on 2026-08-09. It establishes stated
  product capability and compatibility, not the installed state of these
  individual machines.
