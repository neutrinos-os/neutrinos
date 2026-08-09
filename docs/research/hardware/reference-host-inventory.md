---
id: RES-0004
status: in-review
last_updated: 2026-08-09
evidence_cutoff: 2026-08-09
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
| `router` | Router and second physical NeutrinOS target | Checked-in `nixconfig` configuration only; no live firmware inspection yet |
| `misc` | Separate server managed by `nixconfig`; not the current workstation | Checked-in `nixconfig` configuration only; no live firmware inspection yet |

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
| Current storage encryption | No LUKS/dm-crypt layer visible in the observed block topology | Requires host-level confirmation before being treated as a definitive absence |
| Local recovery | Not yet inventoried | Firmware UI, removable boot, key enrollment, and console recovery must be exercised physically |

The current machine is capable enough to investigate SYS-030, but it does not
currently satisfy it merely by having UEFI and a TPM. Secure Boot key
enrollment, authenticated root content, recovery authorization, and tamper
tests remain design and implementation work.

## `router`: configuration-derived baseline

At private repository revision `198f797`, the checked-in NixOS configuration
shows:

- x86-64 and an Intel CPU configuration;
- `systemd-boot` with EFI-variable access through the common archetype;
- an ext4 root plus separate ext4 `/home` and `/nix`, a vfat `/boot`, and swap;
- an IPMI watchdog module and a 180-second runtime watchdog policy;
- headless network-appliance responsibilities with substantial native systemd
  network and service configuration; and
- no checked-in LUKS, TPM, Secure Boot enrollment, or authenticated-root policy.

These are desired/configured NixOS properties, not proof of the currently
running firmware state. The repository does not identify the exact CPU model,
installed memory, board, firmware configuration, TPM capability, Secure Boot
state, management-controller recovery path, or encryption topology.

The watchdog evidence reinforces the router's unattended-availability
requirement. It does not prove that automated rollback or encrypted unattended
boot is currently safe.

## `misc`: configuration-derived server baseline

At the same repository revision, the checked-in NixOS configuration shows:

- a separate host named `misc`, not the current workstation;
- x86-64 and an Intel CPU configuration;
- the same common `systemd-boot` and EFI-variable policy;
- ext4 root, vfat `/boot`, and swap; and
- a server archetype with additional controller responsibilities.

No live CPU, memory, board, firmware, TPM, Secure Boot, encryption, or physical
recovery facts are established. `misc` is useful evidence for a later server
role but does not change the initial workstation/router qualification order.

## Trust-capability matrix

`Observed` means direct sanitized inspection. `Configured` means present in
version-controlled NixOS intent but not confirmed on the running machine.

| Capability | `desktop-jason` | `router` | `misc` |
| --- | --- | --- | --- |
| x86-64 | Observed | Configured | Configured |
| UEFI use | Observed | Configured | Configured |
| systemd-boot | Unknown current bootloader | Configured | Configured |
| Secure Boot enabled | Observed no | Unknown | Unknown |
| Owner-controlled platform keys | Not currently enrolled; capability untested | Unknown | Unknown |
| TPM 2.0 | Advertised; operation untested | Unknown | Unknown |
| Authenticated immutable root | Not present or demonstrated | Not configured or demonstrated | Not configured or demonstrated |
| Storage encryption | Not visible; confirmation needed | Not declared; live state unknown | Not declared; live state unknown |
| Unattended reboot | Not yet a stated workstation requirement | Required in principle; mechanism unverified | Unknown |
| Independent local recovery | Not yet exercised | Required in principle; IPMI/watchdog are partial evidence only | Unknown |

## Consequences for the next design

1. The minimum key and recovery design can use UEFI, owner-controlled Secure
   Boot, and TPM 2.0 as workstation targets, but must retain a non-TPM recovery
   path until physical tests succeed.
2. Workstation storage encryption is a migration requirement, not an existing
   property that can be assumed.
3. The router cannot receive a concrete unattended unlock or recovery design
   until its live TPM, firmware, storage, console, and management capabilities
   are collected.
4. The NixOS files are valuable configuration and role evidence but are not a
   hardware inventory or attestation source.
5. `misc` should later exercise the server role, but bringing it into the
   initial gate would expand scope before workstation and router validate the
   lifecycle.

## Required follow-up evidence

### `desktop-jason`

- confirm current bootloader and ESP layout from the host environment;
- inspect TPM algorithms, PCR banks, event log, and clearing/recovery behavior;
- test owner-key enrollment and firmware reset behavior;
- inventory removable-media and firmware-console recovery;
- define the storage-encryption migration and data-preservation boundary; and
- record acceptable interactive versus unattended unlock behavior.

### `router`

- collect sanitized CPU, memory, board, firmware, TPM, Secure Boot, bootloader,
  storage, encryption, console, and management-controller facts;
- state acceptable outage and whether every normal reboot must be unattended;
- identify recovery paths that work without WAN, DNS, routing, or normal SSH;
  and
- determine which credentials require confidentiality after powered-off theft.

### `misc`

- defer detailed collection until the server role enters active design unless
  its hardware can cheaply provide evidence relevant to the common trust path.

## Evidence limitations

- Live inspection ran in a containerized tool session. CPU, DMI, block, UEFI,
  and sysfs information was visible, but TPM device access and bootloader tools
  were not.
- The private repository worktree contains unrelated untracked files; only
  tracked revision `198f797` and selected checked-in configuration were used.
- Generated NixOS hardware files date from 2023 and establish configuration
  history rather than present runtime state.
- No remote connection to `router` or `misc` was made.
