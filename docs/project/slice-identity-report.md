---
status: active
last_updated: 2026-08-10
governing_plan: PLN-0001
---

# Reference-VM slice identity report

PLN-0001-04. This asks the running machine what it is, and compares its answers
against what composition claims it built. The question is not "did it boot" --
[the boot record](slice-boot-record.md) answered that -- but whether the thing
running is demonstrably the thing declared.

**Result: everything the machine can report about itself matches. The gap is
what it cannot report.** The running system carries no package database, so it
cannot state its own package closure, and that identity claim rests entirely on
an external artifact.

## Composition amendment

PLN-0001-03 found three gaps that made the machine unreachable. They were fixed
in `src/slice/composition/mkosi.conf` under owner authorization on 2026-08-10,
as an amendment to the PLN-0001-02 fixture:

**Superseded in part, 2026-08-10.** All three gaps were later shown to be
fixable from the harness against the unmodified artifact, using SMBIOS Type 11
credentials and `io.systemd.stub.kernel-cmdline-extra`; see
[RES-0013](../research/comparisons/vm-test-harness.md). The amendment below was
therefore not required for reachability. Whether it should be reverted is an
open `C-002`/`L-003` question, because a physical host has no harness to supply
these.

| Gap | Fix | Effect |
| --- | --- | --- |
| No kernel command line | `KernelCommandLine=console=ttyS0 console=hvc0` | 63 KiB of machine-readable boot log on serial where there was none |
| No first-boot answers | `Timezone=UTC`, `Locale=C.UTF-8`, `Hostname=neutrinos-slice` | `systemd-firstboot` no longer prompts; `first-boot-complete.target` is reached |
| No way in | `RootPassword=hashed:`, `Autologin=yes` | Unlocked passwordless root, autologin on `hvc0` |

`hvc0` is listed last because the last `console=` becomes `/dev/console`, and
mkosi's `Autologin=` covers `hvc0` and `tty1` but not `ttyS0`. Serial still
receives the full kernel and systemd log, so evidence and access are separate
channels.

**The amendment changed configuration, not inputs.** The package manifest digest
is `cb438999575af8889ba4bc23534e7b4a6e683d115e81d10f1b77120ef63bbaa2` and the
kernel digest `4b37e4e542a62c580c751787848be6c99e6f908f6712c8c6da85516b8d541de2`
both before and after, with the same 104 packages. The UKI and initrd changed,
as they must: the command line lives in the UKI, and the firstboot credentials
are inherited into the initrd.

`RootPassword=hashed:` creates an unlocked account with no password. There is no
secret in the repository because there is no secret. This is a disposable-VM
qualification fixture and must not survive into anything installed on a physical
host.

## What the running machine reports

Booted artifact: the amended build, UKI
`5bbe8dfc93dae835ecf8bb59b8758038ba0dead32fbb1e0f38511f048d44273d`. Same
environment as the boot record: QEMU 11.0.3 under TCG, swtpm 2.0, no network,
disposable copies.

| Identity | Reported by the machine | Composition claim | Match |
| --- | --- | --- | --- |
| Kernel | `6.19.10-300.fc44.x86_64` | `kernel-core` closure entry; UKI `.uname` | yes |
| systemd | `259 (259.5-1.fc44)` | `systemd` closure entry | yes |
| Distribution | `ID=fedora`, `VERSION_ID=44` | `Distribution=fedora`, `Release=44` | yes |
| Booted UKI on the ESP | `5bbe8dfc9...` | `neutrinos-slice.efi` `5bbe8dfc9...` | **bit-identical** |
| Kernel command line | `console=ttyS0 console=hvc0` | `KernelCommandLine=` | yes |
| Timezone | `Timezone=UTC` | `Timezone=UTC` | yes |
| Locale | `LANG=C.UTF-8` | `Locale=C.UTF-8` | yes |
| Hostname | `neutrinos-slice` | `Hostname=neutrinos-slice` | yes |
| Credentials | `/usr/lib/credstore`: `firstboot.locale`, `firstboot.timezone`, `passwd.hashed-password.root` | three settings above | yes |
| TPM | `/sys/class/tpm/tpm0` major version `2` | vTPM attached by the harness | yes |
| **Package closure** | **cannot report** | 104 RPMs, `cb438999...` | **not self-verifiable** |

The UKI row is the strongest result available at this stage. The bootloader
entry inside the running machine hashes to exactly the composed output, so the
booted deployment is the composed artifact by content, not by inference from a
filename or a version string.

System state: `systemctl is-system-running` reports `running`, with **no failed
units**. `multi-user.target`, `graphical.target`, and `first-boot-complete.target`
are all reached -- the three targets PLN-0001-03 could not reach. Boot took
30.4s under emulation (7.9s kernel, 10.4s initrd, 12.1s userspace); these
numbers describe TCG, not the artifact, and no later task may use them.

## What the machine cannot report, and why it matters

**There is no package database in the image.** `/usr/lib/sysimage/rpm` does not
exist, `/usr/lib/sysimage/libdnf5` does not exist, and there is no `rpm` or
`dnf` executable. The cause is mkosi's `CleanPackageMetadata=auto` default: with
`auto`, package databases are removed unless the package manager itself is
installed in the image.

The consequence is a real boundary on what identity means here. **The running
machine cannot enumerate or verify its own packages.** Every package-level claim
in this report is a claim about `neutrinos-slice.manifest`, an artifact produced
by the builder and held outside the machine. If the manifest is wrong, nothing
inside the machine contradicts it. Nothing observed suggests it is wrong; the
point is that the machine offers no independent check, and SYS-058's "retained
closure" is satisfied by the builder's record alone.

**This is discharged by accepted policy, not a new gap.** SYS-068 already
requires each deployment SBOM to *bind exact deployment or artifact subjects*,
and SYS-073 requires policy-referenced evidence to remain *queryable without
mutable upstream services*. So the intended answer is that a deployment
identifies itself and the SBOM enumerates it, rather than the deployment
carrying a package database.

The machine-side half of that chain is already demonstrated here: the guest
computed the SHA-256 of its own UKI, using tools present in the image, and it
matched the composed artifact exactly. A machine can therefore establish which
deployment it is without external help, which is the key an SBOM is bound to.

Two consequences follow rather than one gap. Vulnerability questions about a
running machine must be answered out of band against retained evidence -- there
is no `rpm -qa` path and there is not meant to be. And SYS-073's retention
requirement carries the real risk: a machine that can name its deployment but
whose evidence set has been lost is unanswerable, and nothing on the machine
will reveal that until someone asks.

**Correction to the composition record.** `CleanPackageMetadata=auto` skips
cleaning entirely for `directory` and `tar` output
(`mkosi/installer/__init__.py:209`). PLN-0001-02 measured reproducibility by
comparing two `Format=directory` builds, so **the tree it compared is not the
tree in the disk image**: the directory builds contain a package database that
the shipped artifact does not. Two consequences:

1. The `RemoveFiles=` entries for the sqlite sidecars are no-ops for
   `Format=disk`. They are retained because they keep the directory comparison
   -- the actual measurement method -- meaningful, not because they change the
   artifact.
2. The reproducibility result is sound but narrower than stated. It shows the
   composition process is deterministic; it is not a direct measurement of the
   shipped tree. A tighter measurement would compare trees extracted from two
   disk images.

Neither weakens any G1 claim, and reproducibility is a goal rather than a
requirement at this stage. Both belong in the record rather than in a comment.

## Identities that are per-boot, not per-image

- **Machine ID** is generated on first boot (`46b737dd...` in one run,
  differing in others) and written to `/etc/machine-id`, which is mode `0444`
  and dated at boot time rather than the fixed epoch.
- **Boot ID** differs every boot, by design.

Neither is an input identity, and PLN-0001-07's reconstruction comparison must
exclude both, along with the boot loader random seed and EFI system token that
the boot record already names.

## Findings

1. **No self-reported package identity**, as above. The most significant result
   in this report.
2. **The root filesystem is mounted read-write**: `/dev/vda2 / btrfs
   rw,nodev,relatime`. PLN-0001's requirement trace lists SYS-049 as partially
   demonstrated by a "read-only root mount". **It is not demonstrated.**
   Resolved 2026-08-10 by owner decision: the trace is corrected and SYS-049 is
   **deferred to G2**, not grown here. Both halves are absent, and the
   authenticated half needs a UKI-to-root/Verity binding over a substrate
   `S-004` has not selected, a signature the slice has no authority to make, and
   a second deployment to substitute. Mounting the root read-only on its own was
   considered and rejected: it would make the requirement read as partly met
   while the half that carries the security value stayed absent.
3. **systemd cannot use the TPM in this image.** The vTPM is present and the
   kernel driver binds it, but `systemd-cryptenroll` reports "TPM2 support is
   not installed". Refined 2026-08-10: systemd itself is built `+TPM2`, as its
   own banner reports, so the gap is the **tss2 runtime libraries**, which
   `cryptenroll` loads dynamically and which are not in the 104-package
   closure. The boot record's "vTPM found" stands; anything requiring systemd
   to *use* the TPM needs a package that is not in the closure.
4. **The image has no `awk`.** `util-linux-core` is deliberately minimal. Not a
   defect, but harness scripts must not assume a POSIX userland.

## What this does not establish

- **Not a qualification result.** One artifact, one host, under emulation.
- **No mechanism is selected.** mkosi and Fedora 44 remain candidate fixtures
  and bootc remains the required challenger. A machine that reports the right
  identities is not evidence for mkosi over an alternative never tried; see
  [PR-0029](reviews/0029-g1-gate-approval.md) C-005.
- **Nothing about Secure Boot or measured boot.** The UKI is unsigned, Secure
  Boot was not enabled, and no PCR was read, sealed against, or verified.
- **No authority claim.** The root account is synthetic and passwordless by
  construction.
