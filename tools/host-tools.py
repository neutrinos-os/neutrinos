#!/usr/bin/env python3
"""What this repository needs from the machine it runs on, checked rather than listed.

`docs/project/validation.md` documents bootstrap, which covers the tools mise
and uv install from the lock files. It does not cover the system tools the
composition and the VM harnesses call, and those were undocumented until this
file: every one of them was discovered by something failing on a machine that
did not have it.

The inventory is executable on purpose. A prose list of required packages drifts
the moment a harness grows a call, and the failure mode of a stale list is a
container that looks provisioned and dies mid-measurement. Run this on a fresh
container, VM, or replacement machine and it names what is missing and what each
missing thing would have broken.

Three things are deliberately **not** required here.

**The mkosi tools tree is not host tooling.** `compose.sh` builds a container
holding `erofs-utils`, `e2fsprogs`, `dosfstools`, `mtools`, `btrfs-progs`,
`squashfs-tools`, `createrepo_c` and the rest, and mkosi uses that tree rather
than the host's. That is what makes the composition reproducible on a machine
whose distribution ships different versions. Only `podman` is needed to build it.

**erofs-utils is intentionally absent from this list.** PLN-0002-07 measured
"e2fsprogs is on the build host and erofs-utils is not" as a real inspectability
difference between the two `/usr` candidate formats. Installing it host-side
would be a change to a measured criterion, not a fix to a broken environment.
The measurement scripts reach it through the retained tools tree.

**Nothing here is version-pinned.** The pinned inputs are `mise.lock`,
`uv.lock`, and the declared package snapshot; these are the operator's own
distribution packages, and pinning them would claim an isolation this file does
not provide.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import NamedTuple


class Tool(NamedTuple):
    name: str
    package: str
    needed_for: str
    why: str
    required: bool = True


# `package` names the Fedora/Arch package where they agree and both where they
# do not. `needed_for` is the activity that stops without it, which is the field
# that decides whether a given machine needs the tool at all: a documentation
# checkout needs the first group, a machine that composes artifacts needs all of
# them.
TOOLS = (
    # Repository and validation.
    Tool("mise", "mise", "everything", "resolves the locked python and uv"),
    Tool("git", "git", "everything", "checkout, and collect-evidence.py records the revision"),
    Tool("python3", "python", "everything", "the harnesses and the validation runner"),
    Tool("openssl", "openssl", "validation, composition",
         "synthetic signing material, and the verity signature blobs task 10 rebuilds"),
    Tool("podman", "podman", "composition",
         "builds the mkosi tools tree; rootless, and the only container runtime declared"),

    # Artifact composition and inspection.
    Tool("sfdisk", "util-linux", "composition, measurement",
         "every harness reads the partition table from the artifact rather than assuming it"),
    Tool("veritysetup", "cryptsetup", "measurement",
         "offline verification of a dm-verity pair, which is the detection point that needs no boot"),
    Tool("debugfs", "e2fsprogs", "measurement",
         "ext4 extent maps, which decide where PLN-0002-09 flips a bit"),
    Tool("dumpe2fs", "e2fsprogs", "measurement", "ext4 superblock parameters for the declaration audit"),
    Tool("mcopy", "mtools", "fixtures", "writes auto-enrolment keys into an artifact's ESP"),
    Tool("mdir", "mtools", "fixtures", "proves what was written to the ESP"),
    Tool("mtype", "mtools", "validation", "reads loader configuration out of the ESP"),
    Tool("objcopy", "binutils", "measurement", "reads UKI sections, including the command line"),
    Tool("zstd", "zstd", "measurement", "initrd inspection"),

    # Secure Boot fixtures.
    Tool("sbsiglist", "sbsigntools / sbsigntool", "fixtures", "builds the EFI signature lists for db and PK"),
    Tool("sbvarsign", "sbsigntools / sbsigntool", "fixtures", "signs the variable updates systemd-boot auto-enrols"),
    Tool("sbverify", "sbsigntools / sbsigntool", "measurement", "checks a UKI's signature outside a guest", False),
    Tool("ukify", "systemd-ukify", "composition", "UKI inspection outside mkosi", False),

    # The VM harnesses.
    Tool("qemu-system-x86_64", "qemu-system-x86 / qemu-full", "boot measurement", "every guest"),
    Tool("swtpm", "swtpm", "boot measurement",
         "the vTPM; without it the guest boots but measures nothing into a PCR"),

    # Diagnosis, not operation. Absent when the /tmp quota aborted a PLN-0002-10
    # run and its absence turned a five-second answer into a wrong one.
    Tool("quota", "quota-tools", "diagnosis",
         "reads the per-user quota on a tmpfs, where df reports free space that EDQUOT then refuses",
         False),
)

# `firmware_pair` refuses the plain build when Secure Boot is asked for, and the
# plain build boots fine without it -- which is how a whole spike measured
# signature behaviour on a firmware that structurally had none. So the presence
# of the *secboot* build is checked here rather than discovered at boot.
FIRMWARE = {
    "OVMF secboot build": (
        "/usr/share/edk2/x64/OVMF_CODE.secboot.4m.fd",
        "/usr/share/edk2/ovmf/OVMF_CODE.secboot.fd",
        "/usr/share/OVMF/OVMF_CODE.secboot.fd",
        "/usr/share/edk2-ovmf/x64/OVMF_CODE.secboot.fd",
    ),
    "OVMF plain build": (
        "/usr/share/edk2/x64/OVMF_CODE.4m.fd",
        "/usr/share/edk2/ovmf/OVMF_CODE.fd",
        "/usr/share/OVMF/OVMF_CODE.fd",
        "/usr/share/edk2-ovmf/x64/OVMF_CODE.fd",
    ),
}
FIRMWARE_PACKAGE = "edk2-ovmf / ovmf"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable inventory")
    parser.add_argument(
        "--packages",
        action="store_true",
        help="print only the package names, for provisioning a container or VM",
    )
    arguments = parser.parse_args()

    found = {tool.name: shutil.which(tool.name) for tool in TOOLS}
    firmware = {
        label: next((path for path in paths if Path(path).is_file()), None)
        for label, paths in FIRMWARE.items()
    }

    if arguments.packages:
        packages = sorted({tool.package for tool in TOOLS if tool.required} | {FIRMWARE_PACKAGE})
        print("\n".join(packages))
        return 0

    if arguments.json:
        print(json.dumps(
            {
                "tools": [
                    dict(tool._asdict(), path=found[tool.name]) for tool in TOOLS
                ],
                "firmware": firmware,
            },
            indent=2,
            sort_keys=True,
        ))
    else:
        width = max(len(tool.name) for tool in TOOLS)
        for tool in TOOLS:
            mark = "ok " if found[tool.name] else ("MISSING" if tool.required else "absent ")
            print(f"{mark:8}{tool.name:{width}}  {tool.needed_for}")
        for label, path in firmware.items():
            print(f"{'ok ' if path else 'MISSING':8}{label}")

    missing = [tool for tool in TOOLS if tool.required and not found[tool.name]]
    optional = [tool for tool in TOOLS if not tool.required and not found[tool.name]]
    absent_firmware = [label for label, path in firmware.items() if path is None]

    for tool in missing:
        print(f"missing: {tool.name} ({tool.package}) -- {tool.why}", file=sys.stderr)
    for label in absent_firmware:
        print(
            f"missing: {label} ({FIRMWARE_PACKAGE}) -- vm.firmware_pair refuses to boot without it",
            file=sys.stderr,
        )
    for tool in optional:
        print(f"absent, not required: {tool.name} ({tool.package}) -- {tool.why}", file=sys.stderr)

    return 1 if missing or absent_firmware else 0


if __name__ == "__main__":
    raise SystemExit(main())
