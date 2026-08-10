---
id: RES-0013
status: in-review
last_updated: 2026-08-10
evidence_cutoff: 2026-08-10
decision_gates: [P-009, C-002, W-002]
---

# VM test harness

## Question

What executes NeutrinOS qualification VMs beyond the first slice, and what may
be taken from existing tooling?

This is not one question. It is three, and conflating them is the trap:

1. **The boot-integrity harness.** Secure Boot enrollment, measured boot, TPM
   sealing, firmware variable persistence. Few VMMs model these, because most
   users do not test them.
2. **The throughput harness.** Many short-lived boots for PLN-0001-05 and
   PLN-0001-06, plus injected failures. Wants fast start and low ceremony.
3. **The product model.** If NeutrinOS workloads are microVMs (`W-002`), the
   VMM stops being a test tool and becomes a declared input.

QEMU is the current fixture, chosen in PLN-0001-03 without a comparison. This
document is the comparison that was skipped, recorded before repeated
successful use turns it into a decision -- the failure
[PR-0029](../../project/reviews/0029-g1-gate-approval.md) C-005 names.

## Candidates

### QEMU

The current fixture. Alone among the three it provides a **writable firmware
variable store** (`-drive if=pflash` over a disposable `OVMF_VARS` copy, with
`smm=on`), which is what makes Secure Boot enrollment and persistent EFI
variables testable at all. It also provides a **TCG software-emulation
fallback**, which is the only reason PLN-0001-03 and PLN-0001-04 produced any
evidence: this build host has no working KVM (see below).

Costs: slow under TCG, large surface, verbose invocation, and no built-in
guest-readiness protocol -- PLN-0001-03 resorted to timed QMP screendumps
because it had no signal to wait on.

### Cloud Hypervisor

rust-vmm based, virtio-only, small and fast. Attaches swtpm over a Unix socket
(`--tpm socket=`, TPM 2.0, CRB interface only). Supports nested virtualization
via `--cpu nested=on`, which is the **default** on x86-64 for both KVM and MSHV;
AMD nesting fixes landed in #7783 and nested Hyper-V for WSL2 guests in #8481.

Two disqualifiers for role 1:

- **No software emulation.** It runs on KVM or MSHV only. It could not have run
  either PLN-0001 boot on this host.
- **"Cloud Hypervisor opens the firmware file in read-only mode."** No writable
  varstore means no persistent EFI variables: no Secure Boot key enrollment
  surviving a reboot, no boot loader system token, no `bootctl` write. The
  system token write that PLN-0001-03 observed would silently vanish.

### test.thing

`https://codeberg.org/lis/test.thing`, PyPI `test.thing`. A single-file
(1431-line) Python QEMU runner from the cockpit-bots lineage, tested against
composefs-rs images. Same systemd-and-image-based-OS world as this project.

It is **GPL-3.0-or-later**. This repository is Apache-2.0 and public
(`P-007`), so its headline offer -- "one-file copypastelib", "simply copy
`testthing.py` into your project" -- **is not available to us**, and importing
it into our own test code is not obviously clean either. Running it as a
separate executable is the conventionally safe use. That is an owner call, not
an agent call. Nothing in this document copies its code; the techniques below
are interface facts.

It also uses `-bios OVMF_CODE.fd` rather than pflash, and contains no TPM
support at all. It requires `qemu-kvm` with `accel=kvm` and `-cpu host`, so it
has no TCG path either.

## What test.thing does that we should do

Four techniques, each of which corrects something built in PLN-0001-03 or
PLN-0001-04.

| Technique | Mechanism | What it replaces |
| --- | --- | --- |
| Guest-driven readiness | `vmm.notify_socket` credential pointing at a vsock; guest systemd sends `READY=1` and `X_SYSTEMD_UNIT_ACTIVE=` | Timed QMP screendumps at 20/45/75/120s and inference from pixels |
| Host-supplied configuration | `-smbios type=11,value=io.systemd.credential:KEY=VALUE` | Baking `Timezone=`/`Locale=` into the image. See the open question below |
| Keyless access | ssh over vsock via `systemd-ssh-proxy`, with the `ssh.ephemeral-authorized_keys-all` credential; no guest networking, no IP, ephemeral per-run key | `RootPassword=hashed:` plus `Autologin=yes` -- a passwordless root account inside the artifact |
| Free disposability | `-drive ...,snapshot=on`; QEMU discards all guest writes, and `quit` replaces `system_powerdown` | Copying a 1.4 GB image per run, and the boot record's "booting mutates the image" |

Minor: `-nodefaults`; a distro path table for locating OVMF; console-log capture
dumped automatically on startup timeout; an ANSI/control-character stripping
regex better than the hand-rolled one used in PLN-0001-04.

The keyless-access row is the most significant. A project whose thesis is
separated authority (ADR-0002) should not need a passwordless root account in
its qualification artifact, and with ephemeral vsock keys it does not.

## Measured 2026-08-10: both techniques work under TCG

Two of the four techniques were tested against **`raw-a`, the literal
pre-amendment artifact from PLN-0001-03** -- the image that blocked forever on
an interactive timezone prompt. Nothing in the image was changed.

**`snapshot=on` works.** The artifact was used directly as the boot disk with no
copy made. Its SHA-256 was
`449767ea7ec4551aa3e3e1fb59d10038f1d8056299a41d5c76e2a3e272a18b91` before the
boot and identical after it. This retires the per-run 1.4 GB copy and the boot
record's "booting mutates the image" caveat: under `snapshot=on` it does not.
It also means every boot is a first boot, because the machine ID never
persists.

**SMBIOS Type 11 credentials work**, supplied as
`-smbios type=11,value=io.systemd.credential:KEY=VALUE`:

| Credential | Value | Observed |
| --- | --- | --- |
| `firstboot.timezone` | `UTC` | Prompt gone |
| `firstboot.locale` | `C.UTF-8` | Prompt gone |
| `system.hostname` | `tt-smbios-proof` | Appeared in the login banner |
| `passwd.hashed-password.root` | empty (unlocked, no password) | Prompt gone |

The first run supplied only the top three and advanced from the timezone
question to the *root password* question -- a useful partial result, since it
showed the mechanism working before it showed the credential set was
incomplete. With the fourth added, the unmodified artifact reaches
`tt-smbios-proof login:`.

**A kernel command line also works from the harness**, via
`-smbios type=11,value=io.systemd.stub.kernel-cmdline-extra="console=ttyS0"`.
The same UKI that has no `.cmdline` section produced 91 KB of serial log.
systemd-stub's documentation places no Secure Boot condition on this string,
and notes it **is measured into PCR12** -- so it is accounted for rather than
ignored, but it will move PCR12 and any future policy sealed against that
register must expect it.

### Consequence for PLN-0001-04

**All three composition amendments made in PLN-0001-04 are now known to be
unnecessary for reachability.** The literal artifact can be given a console,
first-boot answers, a hostname, and an unlocked root account entirely from
outside, leaving the artifact byte-identical.

**Owner decision 2026-08-10: revert, but not yet -- wait for KVM.** Dropping
`Autologin=` leaves a `login:` prompt that a human can use and a script cannot,
and the intended replacement is ssh over vsock with ephemeral keys, which is
untested and untestable while this host has no KVM. Reverting now would buy a
clean artifact at the cost of a harness that cannot drive its guest. Doing both
in one motion after SVM is enabled costs one re-run of PLN-0001-04 instead of
two. The revert is verifiable when it happens: the UKI must hash back to
`575c847d...` and the initrd to `e7061e25...`, the digests recorded before the
amendment.

Reverting does not by itself settle where first-boot configuration belongs. A physical host has no harness to inject
SMBIOS strings, so something must still own first-boot configuration --
the installer, the enrollment record, or the image. That is `L-003` and
`C-002`, and it should be decided on its own terms. What has changed is that
"the image must carry it or the VM is unreachable" is no longer an argument,
because it is false.

The one amendment with an independent justification is the kernel command line:
a cmdline in the UKI is measured as part of the signed image, while an SMBIOS
extra is host-supplied. Which of those a NeutrinOS deployment should rely on is
a boot-integrity question, not a convenience question.

## The Virtual Machine Image API Specification

test.thing's most interesting artifact is not its code but
`doc/VirtualMachineAPI.md`: a written contract for what a guest image must
provide. Virtio block, vsock, and network devices; EFI boot with a suitable
ESP; SMBIOS Type 11 OEM string credentials in both text and binary form; a
vsock listener on port 22 with ed25519, multiplexed sessions, and sftp; the
`ssh.ephemeral-authorized_keys-all` credential; `READY=1` over the notify
socket; and partition auto-grow on resize.

That is the bounded, declarative, reviewable contract shape this project
already prefers, written by someone else and already implemented by other
images. It is a candidate **conformance target** -- something a NeutrinOS
deployment could be tested against -- rather than a harness we adopt. It is not
a NeutrinOS requirement and nothing here proposes adopting it.

## Build-host constraint

Measured 2026-08-10 on `desktop-jason`, read-only:

- `/dev/kvm` absent, no `kvm` modules loaded.
- **`/proc/cpuinfo` reports no `svm` flag**, on a Ryzen 7 3700X, on bare metal
  (`systemd-detect-virt: none`).

A 3700X supports AMD-V, so an absent `svm` flag means **SVM is disabled in
firmware setup**, not that a module is missing and not that a permission is
wrong. `modprobe kvm_amd` will load and then fail to enable. This corrects an
error in the [boot record](../../project/slice-boot-record.md), which claimed
the CPU reports `svm`.

Secondary and currently moot: the `kvm` group (gid 992) has members
`libvirt-qemu` and `qemu` and does not include `jason`. Arch's udev rule
normally makes `/dev/kvm` mode 0666, so this is unlikely to bite, but it is
worth checking once the flag is enabled.

Until then TCG is the only option, which rules out cloud-hypervisor and
test.thing entirely and makes all three roles above untestable at speed.

## Nested virtualization

Both QEMU (`-accel kvm -cpu host`, host `kvm_amd.nested=1`, the modern default)
and Cloud Hypervisor (`--cpu nested=on`, the default) expose SVM to guests, and
either can be L2 inside either L1. So nesting does not discriminate between
them.

Two constraints do bind:

- **Nesting requires KVM.** TCG cannot host a nested KVM guest. On this host
  nesting is unavailable for the firmware reason above, which is a host
  question and not a VMM question.
- **If NeutrinOS workloads are microVMs, testing NeutrinOS in a VM is
  inherently nested.** That makes `W-002` a prerequisite for the long-term
  harness decision rather than a consequence of it.

## Reading

- The harness is currently excluded from the
  [input declaration](../../project/slice-input-declaration.md) because it
  cannot change what composition produced. That exclusion is correct only while
  the VMM is purely a test tool. If NeutrinOS ships a VMM under `W-002`, it
  becomes a declared input.
- No mechanism is selected here. QEMU remains a fixture, and this comparison
  exists so that its continued use is a choice rather than an accident.
