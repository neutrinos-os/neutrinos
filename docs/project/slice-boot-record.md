---
status: active
last_updated: 2026-08-10
governing_plan: PLN-0001
---

# Reference-VM slice boot record

PLN-0001-03. This records the first execution of the composed artifact. The
image was booted **unmodified**: no package was added, no kernel argument was
injected, and no file inside the image was edited to make it start.

**Result: it boots.** Firmware hands off to the disk, the UKI loads, the initrd
switches root, and systemd reaches `basic.target` with **zero failed units**. It
then stops at an interactive prompt and never reaches `multi-user.target`. The
boot is a success; the artifact is not yet autonomously usable, and the reason
is a composition gap, not a boot failure.

## Environment

The boot tools are deliberately absent from
[the input declaration](slice-input-declaration.md): they execute the artifact
but cannot change what composition produced. Their identities belong here.

| Component | Identity | Source |
| --- | --- | --- |
| QEMU | 11.0.3 | Build-host package |
| Firmware | `edk2/x64/OVMF_CODE.4m.fd`, disposable `OVMF_VARS` copy | Build-host package |
| TPM | swtpm 0.10.1, TPM 2.0, `startup-clear` | Build-host package |
| Acceleration | **TCG (software emulation)** | See below |
| Network | None (`-nic none`) | |

These come from the build host's rolling package set and are not exact inputs.
That is acceptable for a boot witness and would not be acceptable for anything
this record claimed about composition output.

**KVM was not used.** `/dev/kvm` does not exist on the build host: the CPU
reports `svm`, and `kvm-amd.ko` is present but not loaded. Loading it requires
root and would mutate `desktop-jason`, which PLN-0001 does not authorize, so the
boot ran under TCG instead. This costs wall-clock time and nothing else for a
boot witness, but a later task that measures timing must not use these numbers.

The artifact itself was never opened for write. The VM ran against disposable
copies of the disk image and firmware variables under the build root.

## What was observed

Booted image: the `raw-a` build of the two-build comparison, UKI
`575c847dd491a081ff364b0139fe3e81b4e00add7f08f12fb6b4c2582a8cd0fd`.

- `Linux version 6.19.10-300.fc44.x86_64`, matching the composition record's
  `kernel-core` closure entry.
- `systemd 259.5-1.fc44 running in system mode`, matching the closure's
  `systemd` entry.
- 26 targets reached, including `initrd-switch-root.target`, `sysinit.target`,
  `basic.target`, `sockets.target`, and `timers.target`.
- **No failed units, and no `Dependency failed` records.**
- The virtual TPM was found: `dev-tpm0.device`, `tpm2.target` reached,
  `systemd-pcrextend` and `systemd-pcrlock` sockets listening. The vTPM is
  present and visible to the guest, which is all this task claims; nothing has
  been sealed to a PCR and no measurement has been verified.
- The ESP automounted and `systemd-boot-random-seed.service` wrote a boot loader
  random seed and initialized a system token EFI variable.

## Where it stops

`systemd-firstboot.service` runs interactively and blocks:

```
Welcome to Fedora Linux 44 (Forty Four)!
Please configure the system!
> Please enter the new timezone name or number ("list" to list options, empty to skip):
```

The direct cause is in the composed tree: `/etc/localtime` is absent, and
`systemd-firstboot` therefore prompts. In the initrd the same unit was correctly
skipped on `ConditionFirstBoot=yes`; it started after the switch to the real
root. The machine waits for a human forever, so `multi-user.target` is never
reached and no login is ever offered.

## Evidence and how it was obtained

Two of the three obvious evidence channels do not exist in this artifact, which
is itself the finding.

- **Serial console: empty.** The UKI carries **no `.cmdline` section**, so there
  is no `console=ttyS0`. The serial log ends at the firmware handoff line
  (`BdsDxe: starting Boot0002 ...`) and records nothing from the kernel or
  systemd.
- **Framebuffer: captured.** Screendumps were taken through the QMP socket at
  20, 45, 75, 120, 180, and 240 seconds. These are the console evidence.
- **Journal: recovered offline.** `/var/log/journal` exists and journald's
  storage default is persistent, so the boot was recorded to disk. The journal
  was extracted from the VM's disposable disk copy without root and without
  mounting: the btrfs partition was copied out at its known offset and read with
  `btrfs restore`. Reading evidence out of an image is not the same as reading
  it from a running machine, and PLN-0001-04 needs the latter.

Screendumps, the serial log, and the extracted journal are retained in the build
root. They are not committed: the hygiene contract's binary and size bounds bind
here.

## Findings against PLN-0001-02

Three composition gaps, none of which prevent booting and all of which prevent
automation:

1. **No first-boot configuration**, so the machine blocks on an interactive
   prompt and never reaches `multi-user.target`.
2. **No kernel command line in the UKI**, so there is no serial console and no
   machine-readable console evidence.
3. **No credential or autologin**, so even past the prompt there is no way in.

These belong to composition, not to this task. PLN-0001-03's scope is to boot
the literal artifact and report what happened, and amending `mkosi.conf` to fix
them is a change to the PLN-0001-02 fixture that needs its own authorization.
**PLN-0001-04 cannot proceed until they are fixed**, because an identity report
from the running machine requires reaching the running machine.

## What this does not establish

- **Not a qualification result.** One boot on one host under emulation.
- **Nothing about Secure Boot.** The UKI is unsigned, firmware ran without
  Secure Boot enabled, and no enrollment or signing authority was used.
- **Nothing about measured boot.** The vTPM was present and PCR machinery
  started; no PCR value was read, sealed against, or verified.
- **No mechanism is selected.** mkosi and Fedora 44 remain candidate fixtures
  and bootc remains the required challenger; an image that boots is not evidence
  for mkosi over an alternative that was never tried. See
  [PR-0029](reviews/0029-g1-gate-approval.md) C-005.
- **Booting mutates the image.** The boot wrote a random seed and an EFI system
  token to its disk copy, so a booted image no longer matches the composed one.
  PLN-0001-07's reconstruction comparison must account for this.
