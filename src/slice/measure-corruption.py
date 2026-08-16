#!/usr/bin/env python3
"""Corruption behaviour for both arms: PLN-0002-09.

What task 09 owes: **single-bit corruption injected into an authenticated
region of each artifact, recording detection point, diagnostic, and blast
radius per format.** The plan expects the formats to diverge at "compressed
EROFS clusters versus ext4 blocks", which is under test rather than assumed.
Results: docs/project/artifact-corruption-records.md.

Four choices are deliberate.

**The corruption goes into the `/usr` data partition**, the authenticated
region -- not the hash tree, the signature partition or the ESP. The signed
root hash stays correct for the original bytes, which is the condition
dm-verity exists to detect.

**Two targets per arm, because blast radius is data-dependent.** A flipped bit
costs ext4 one 4 KiB block; it costs EROFS one physical cluster, covering as
much logical data as that cluster compressed. So both `System.map` at 25.43%
and already-compressed `vmlinuz` at 98.77% -- byte-identical across arms, same
directory, neither read during boot, so the read is the probe.

**Blast radius is measured in the guest, not computed from the extent map**,
which says what shares a cluster and not what the kernel does when it fails.

**A successful boot is the expected result and not a pass.** dm-verity verifies
lazily, per block: PLN-0002-01 booted a corrupt `/usr` normally, the first of
this plan's seven fail-opens. Detection is where the corrupt block is read.

The originals are never written to. Each run injects into a copy and the
retained digest is checked before and after.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import platform
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

from common import default_build_root
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.validation import vm  # noqa: E402
from tools.validation.slice_boot import (  # noqa: E402
    MASKED_UNITS,
    UNIT_FAILURE,
    drain_notification,
    notify_vsock,
    qmp_query_kvm,
    qmp_quit,
)
from tools.validation.vm import file_digest, strip_control  # noqa: E402

ARMS = {"erofs": "out-erofs", "ext4": "out-ext4"}

# Both are 4096 by declaration: PLN-0002-05 pins the ext4 block size and the
# dm-verity hash block size, and `mkfs.erofs` derives its block size from the
# same page size. One flipped bit therefore falls inside exactly one verity data
# block on either arm, which is what makes the two blast radii comparable at all.
BLOCK = 4096

# Chosen for what they are, not for where they are. See the module docstring.
TARGETS = ("System.map", "vmlinuz")
MODULES = "/lib/modules"

CONSOLE_PREFIX = re.compile(r"^\[\s*[\d.]+\]\s*\S+\[\d+\]:\s*")
MARKER_BEGIN = "PLN0002-09-BEGIN"
MARKER_END = "PLN0002-09-END"
HARNESS_HOSTNAME = "slice-pln0002-09"
BOOT_TIMEOUT_SECONDS = 600
NOTIFY_POLL_SECONDS = 0.25

# The diagnostic this task exists to capture, verbatim. dm-verity names the
# **data block index within the data device**, which is the one number that ties
# the guest's complaint back to the byte this harness flipped. A record that
# stored "the read failed" and discarded this line would be asserting detection
# while throwing away the evidence of what detected it.
VERITY_CONSOLE = re.compile(
    r"(device-mapper|verity|dm-\d+|veritysetup|EROFS|EXT4-fs).*", re.IGNORECASE
)
CORRUPT_BLOCK = re.compile(r"data block (\d+) is corrupted")

NOT_IN_INITRD = "ConditionPathExists=!/etc/initrd-release\n"

# How far either side of the predicted damage the guest scans. Wide enough that
# a blast radius larger than predicted is visible as a wider band rather than as
# a probe that stopped at its own boundary, and narrow enough that the scan is
# 4 KiB reads and not a full-file walk.
WINDOW_BLOCKS = 24


def host_only(unit: str) -> str:
    head, separator, tail = unit.partition("[Unit]\n")
    if not separator:
        raise SystemExit("measure-corruption: unit text has no [Unit] section")
    return head + separator + NOT_IN_INITRD + tail


PROBE_TIMER = (
    "[Unit]\n"
    + NOT_IN_INITRD
    + "Description=PLN-0002-09 corruption probe trigger\n"
    "[Timer]\n"
    "OnBootSec=20s\n"
    "AccuracySec=1ms\n"
    "Unit=pln0002-09.service\n"
)


def probe_script(target: str, first: int, last: int) -> str:
    """What the guest is asked, for one corrupted target.

    The order matters. Caches are dropped first: a block already in page cache
    from the boot is served without reaching dm-verity, recording a clean read
    of a corrupt block. The whole-file read comes before the window scan so
    `records in` reports how far a naive consumer -- `cat`, `cp`, a checksum --
    gets before the first failure. The window scan then bounds the damage.

    **The window is scanned twice, and the second pass is the format
    measurement.** The first run of this task found the two arms losing 45 KiB
    and 16 KiB from a single flipped bit, which is not the ratio the extent maps
    predict, because a 4 KiB `dd` still triggers readahead and a readahead
    request spanning the bad block fails as a unit. `blockdev --setra 0` on the
    dm device removes that term for both arms equally, so the second pass is
    what compressed clusters cost against plain blocks and the first is what a
    reader on a default-configured system actually loses. Reporting only one of
    them would answer a different question than the plan asks.

    No single quotes, no backslash escapes, no `%`. `vm.probe_unit` wraps this
    in `sh -c '...'`; systemd unescapes C-style sequences in `ExecStart` before
    `sh` sees it; and systemd expands its own specifiers first, so `stat -c %s`
    reached the guest as `stat -c /bin/bash` and the first run recorded the root
    shell as the target's size. `wc -c` needs no format string. All three
    measured, and all three look identical from outside -- a boot that produced
    no evidence.
    """
    script = f"""echo "{MARKER_BEGIN}"; \\
echo "target={target}"; \\
echo "target-size=$(wc -c < {target})"; \\
echo "readahead-default-sectors=$(blockdev --getra /dev/mapper/usr)"; \\
sync; echo 3 > /proc/sys/vm/drop_caches; \\
echo "whole-file-read=$(dd if={target} of=/dev/null bs={BLOCK} 2>&1 \\
  | tr -s "[:space:]" " ")"; \\
echo "readable-prefix-blocks=$(dd if={target} of=/dev/null bs={BLOCK} 2>&1 \\
  | grep -o "[0-9]*.0 records in" | cut -d+ -f1 | head -1)"; \\
sync; echo 3 > /proc/sys/vm/drop_caches; \\
for i in $(seq {first} {last}); do \\
  dd if={target} of=/dev/null bs={BLOCK} skip=$i count=1 2>/dev/null \\
  || echo "bad-block=$i"; done; \\
blockdev --setra 0 /dev/mapper/usr; \\
echo "readahead-now-sectors=$(blockdev --getra /dev/mapper/usr)"; \\
sync; echo 3 > /proc/sys/vm/drop_caches; \\
for i in $(seq {first} {last}); do \\
  dd if={target} of=/dev/null bs={BLOCK} skip=$i count=1 2>/dev/null \\
  || echo "bad-block-nora=$i"; done; \\
sync; echo 3 > /proc/sys/vm/drop_caches; \\
echo "whole-file-read-nora=$(dd if={target} of=/dev/null bs={BLOCK} 2>&1 \\
  | tr -s "[:space:]" " ")"; \\
echo "usr-source=$(findmnt -no SOURCE /usr)"; \\
echo "usr-fstype=$(findmnt -no FSTYPE /usr)"; \\
echo "usr-still-mounted=$(test -d /usr/bin && echo yes || echo no)"; \\
echo "unrelated-file-read=$(dd if=/usr/lib/os-release of=/dev/null bs={BLOCK} \\
  2>&1 | grep -c "Input/output error")"; \\
echo "system-state=$(timeout 30 systemctl is-system-running --wait)"; \\
echo "failed-units=$(systemctl list-units --state=failed --no-legend \\
  --plain --no-pager | cut -d" " -f1 | tr -s "[:space:]" ",")"; \\
echo "{MARKER_END}\""""
    if "'" in script or "\\" in script.replace("\\\n", "") or "%" in script:
        raise SystemExit(
            "measure-corruption: the probe script contains a single quote, a "
            "backslash escape, or a percent sign; the first terminates the "
            "sh -c string vm.probe_unit builds, and the other two are consumed "
            "by systemd's ExecStart unescaping and specifier expansion before "
            "sh sees them"
        )
    return script


def ext4_extents(image: Path, path: str) -> list[tuple[int, int, int]]:
    """(logical block, physical block, block count) for one file, from debugfs.

    debugfs prints `(0-285):32482-32767, (286-4511):32825-37050` for a ranged
    extent and `(7):9001` for a single block. Both forms are parsed; anything
    else is refused rather than guessed at, because a misparsed extent puts the
    injection somewhere this record would then describe wrongly.
    """
    stat = subprocess.run(
        ["debugfs", "-R", f"stat {path}", str(image)],
        capture_output=True, text=True, check=True,
    ).stdout
    if "EXTENTS:" not in stat:
        raise SystemExit(f"measure-corruption: no extents for {path} in {image}")
    body = stat.split("EXTENTS:", 1)[1]
    extents: list[tuple[int, int, int]] = []
    for entry in re.findall(r"\(([\d-]+)\):([\d-]+)", body):
        logical, physical = entry
        if "-" in logical:
            start, end = (int(value) for value in logical.split("-"))
            count = end - start + 1
        else:
            start, count = int(logical), 1
        first_physical = int(physical.split("-")[0])
        extents.append((start, first_physical, count))
    if not extents:
        raise SystemExit(f"measure-corruption: unparsed extent line for {path}")
    return extents


def erofs_extents(build_root: Path, image: Path, path: str) -> list[dict[str, int]]:
    """Logical byte range and physical byte range per extent, from dump.erofs.

    The tool reaches this host only through the declared tools tree -- PLN-0002-07
    measured exactly that as the inspectability difference between the arms -- so
    it is invoked from there with the tree's own libraries, the same way
    `measure-artifact-set.py` does it.
    """
    tools = build_root / "tools"
    binary = tools / "usr/bin/dump.erofs"
    if not binary.is_file():
        raise SystemExit(f"measure-corruption: no dump.erofs at {binary}")
    output = subprocess.run(
        [str(binary), "-e", f"--path={path}", str(image)],
        capture_output=True, text=True, check=True,
        env=dict(os.environ, LD_LIBRARY_PATH=str(tools / "usr/lib64")),
    ).stdout
    extents: list[dict[str, int]] = []
    for line in output.splitlines():
        # "   0:        0..    5529 |    5529 :   18722816..  18726912 |    4096"
        match = re.match(
            r"\s*\d+:\s*(\d+)\.\.\s*(\d+)\s*\|\s*\d+\s*:\s*(\d+)\.\.\s*(\d+)\s*\|\s*(\d+)",
            line,
        )
        if match:
            logical_start, logical_end, physical_start, _, physical_length = (
                int(value) for value in match.groups()
            )
            extents.append({
                "logical_start": logical_start,
                "logical_end": logical_end,
                "physical_start": physical_start,
                "physical_length": physical_length,
            })
    if not extents:
        raise SystemExit(f"measure-corruption: no extents parsed for {path}")
    return extents


def usr_partition(artifact: Path) -> tuple[int, int]:
    table = json.loads(
        subprocess.run(
            ["sfdisk", "-J", str(artifact)], capture_output=True, text=True, check=True
        ).stdout
    )["partitiontable"]
    sector = table.get("sectorsize", 512)
    entry = next(
        part for part in table["partitions"]
        if (part.get("name") or "").endswith("neutrinos-usr")
    )
    return entry["start"] * sector, entry["size"] * sector


def extract(artifact: Path, offset: int, length: int, destination: Path) -> None:
    with artifact.open("rb") as handle, destination.open("wb") as out:
        handle.seek(offset)
        remaining = length
        while remaining > 0:
            chunk = handle.read(min(1 << 20, remaining))
            if not chunk:
                break
            out.write(chunk)
            remaining -= len(chunk)


def plan_injection(
    arm: str, build_root: Path, partition: Path, target_path: str
) -> dict[str, Any]:
    """Where one bit goes, and what the extent map says it should cost.

    The extent chosen is the one covering the middle of the file, so the damage
    lands in ordinary file body rather than in a first or last extent whose
    length is an artifact of where the file starts and stops. The byte chosen is
    the middle of that physical block, so a flip cannot land on a boundary and
    be attributed to the wrong block.

    `predicted_*` is the extent map's claim. The guest is what decides whether
    it holds.
    """
    if arm == "ext4":
        extents = ext4_extents(partition, target_path)
        total_blocks = sum(count for _, _, count in extents)
        middle = total_blocks // 2
        for logical, physical, count in extents:
            if logical <= middle < logical + count:
                block_in_extent = middle - logical
                physical_block = physical + block_in_extent
                return {
                    "physical_offset": physical_block * BLOCK + BLOCK // 2,
                    "verity_data_block": physical_block,
                    "predicted_first_bad_block": middle,
                    "predicted_last_bad_block": middle,
                    "predicted_lost_bytes": BLOCK,
                    "extent_map": [
                        {"logical_block": l, "physical_block": p, "blocks": c}
                        for l, p, c in extents
                    ],
                }
        raise SystemExit(f"measure-corruption: middle block {middle} in no extent")

    extents = erofs_extents(build_root, partition, target_path)
    chosen = extents[len(extents) // 2]
    physical_block = chosen["physical_start"] // BLOCK
    first_bad = chosen["logical_start"] // BLOCK
    # `logical_end` is exclusive of the next extent's start, so the last damaged
    # block is the one containing the final byte this cluster decompresses to.
    last_bad = (chosen["logical_end"] - 1) // BLOCK
    return {
        "physical_offset": physical_block * BLOCK + BLOCK // 2,
        "verity_data_block": physical_block,
        "predicted_first_bad_block": first_bad,
        "predicted_last_bad_block": last_bad,
        "predicted_lost_bytes": chosen["logical_end"] - chosen["logical_start"],
        "chosen_extent": chosen,
        "extent_count": len(extents),
    }


def verity_verifies(build_root: Path, artifact: Path, root_hash: str, work: Path) -> bool:
    """Whether offline `veritysetup verify` still accepts the image.

    This is the detection point that does not need a boot, and it is the same on
    both arms by construction: verity hashes every data block whatever the
    filesystem above it does. It is measured anyway, because "the offline check
    catches what the lazy online one does not" is a claim this record makes and
    an unmeasured claim is the pattern this plan keeps being caught by.
    """
    data_offset, data_size = usr_partition(artifact)
    table = json.loads(
        subprocess.run(
            ["sfdisk", "-J", str(artifact)], capture_output=True, text=True, check=True
        ).stdout
    )["partitiontable"]
    sector = table.get("sectorsize", 512)
    hash_entry = next(
        part for part in table["partitions"]
        if (part.get("name") or "").endswith("usr-verity")
    )
    data = work / "verify-data.img"
    hashes = work / "verify-hash.img"
    extract(artifact, data_offset, data_size, data)
    extract(artifact, hash_entry["start"] * sector, hash_entry["size"] * sector, hashes)
    result = subprocess.run(
        ["veritysetup", "verify", str(data), str(hashes), root_hash],
        capture_output=True, text=True, check=False,
    )
    data.unlink()
    hashes.unlink()
    return result.returncode == 0


def uki_root_hash(uki: Path) -> str:
    matches = set(re.findall(rb"usrhash=([0-9a-f]{64})", uki.read_bytes()))
    if len(matches) != 1:
        raise SystemExit(
            f"measure-corruption: expected exactly one usrhash in {uki}, "
            f"found {len(matches)}"
        )
    return matches.pop().decode()


def report_fields(text: str) -> dict[str, Any]:
    if MARKER_BEGIN not in text or MARKER_END not in text:
        return {}
    body = text.split(MARKER_BEGIN, 1)[1].split(MARKER_END, 1)[0]
    fields: dict[str, Any] = {}
    bad: dict[str, list[int]] = {"bad-block": [], "bad-block-nora": []}
    for line in body.splitlines():
        key, separator, value = CONSOLE_PREFIX.sub("", line.strip()).partition("=")
        if not separator:
            continue
        if key in bad:
            with contextlib.suppress(ValueError):
                bad[key].append(int(value.strip()))
        else:
            fields[key] = value.strip()
    fields["bad-blocks"] = sorted(bad["bad-block"])
    fields["bad-blocks-no-readahead"] = sorted(bad["bad-block-nora"])
    return fields


def one_boot(artifact: Path, target: str, first: int, last: int, work: Path) -> dict[str, Any]:
    """Boot one corrupted copy once, and ask it to read the damaged file.

    Structured after `measure-boot.py`, which is structured after
    `slice_boot.check_boot`. The one difference that matters: the disk here is a
    corrupted copy and is still attached `snapshot=on`, so the copy is
    reusable and nothing the guest does can widen the damage this harness
    injected.
    """
    code, variables = vm.firmware_pair(secure_boot=False)
    work.mkdir(parents=True, exist_ok=True)
    tpm_state = work / "tpm"
    tpm_state.mkdir(mode=0o700)
    firmware = work / "OVMF_VARS.fd"
    shutil.copy(variables, firmware)
    firmware.chmod(0o600)
    serial = work / "serial.log"
    qmp = work / "qmp.sock"

    probe_unit = host_only(
        vm.probe_unit(
            probe_script(target, first, last),
            description="PLN-0002-09 corruption probe",
            after="timers.target",
        )
    )

    qemu: subprocess.Popen[bytes] | None = None
    stack = contextlib.ExitStack()
    ready_seconds: float | None = None
    kvm_enabled: bool | None = None
    log = ""
    try:
        cid, vhost_fd, listener = stack.enter_context(notify_vsock())
        tpm_socket = stack.enter_context(vm.software_tpm(tpm_state))

        credentials = {
            "firstboot.timezone": "UTC",
            "firstboot.locale": "C.UTF-8",
            "system.hostname": HARNESS_HOSTNAME,
            "passwd.hashed-password.root": "",
        }
        if cid is not None and listener is not None:
            port = listener.getsockname()[1]
            credentials["vmm.notify_socket"] = (
                f"vsock-stream:{socket.VMADDR_CID_HOST}:{port}"
            )
        credential_files = [
            vm.credential_file(work, "systemd.extra-unit.pln0002-09.service", probe_unit),
            vm.credential_file(work, "systemd.extra-unit.pln0002-09.timer", PROBE_TIMER),
            vm.credential_file(
                work,
                "systemd.unit-dropin.timers.target",
                "[Unit]\nWants=pln0002-09.timer\n",
            ),
        ]
        smbios = vm.smbios_args(
            credentials,
            credential_files,
            cmdline_extra=[
                f"systemd.mask={unit} rd.systemd.mask={unit}" for unit in MASKED_UNITS
            ],
        )
        vsock_device: list[str] = []
        if cid is not None and vhost_fd is not None:
            vsock_device = [
                "-device", f"vhost-vsock-pci,guest-cid={cid},vhostfd={vhost_fd}",
            ]

        qemu = subprocess.Popen(
            [
                "qemu-system-x86_64",
                "-nodefaults",
                "-machine", "q35,smm=on,accel=kvm:tcg",
                "-cpu", "max",
                "-m", "2048",
                "-smp", "4",
                "-drive", f"if=pflash,unit=0,format=raw,readonly=on,file={code}",
                "-drive", f"if=pflash,unit=1,format=raw,file={firmware}",
                "-drive", f"if=virtio,format=raw,file={artifact},snapshot=on",
                "-chardev", f"socket,id=chrtpm,path={tpm_socket}",
                "-tpmdev", "emulator,id=tpm0,chardev=chrtpm",
                "-device", "tpm-tis,tpmdev=tpm0",
                *vsock_device,
                *smbios,
                "-nic", "none",
                "-display", "none",
                "-serial", f"file:{serial}",
                "-qmp", f"unix:{qmp},server=on,wait=off",
                "-no-reboot",
            ],
            start_new_session=True,
            pass_fds=() if vhost_fd is None else (vhost_fd,),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

        started = time.monotonic()
        deadline = started + BOOT_TIMEOUT_SECONDS
        time.sleep(2)
        if qemu.poll() is None:
            kvm_enabled = qmp_query_kvm(qmp)
        while time.monotonic() < deadline:
            if listener is not None:
                for line in drain_notification(listener):
                    if line == "READY=1" and ready_seconds is None:
                        ready_seconds = round(time.monotonic() - started, 3)
            if qemu.poll() is not None:
                break
            if listener is None:
                time.sleep(NOTIFY_POLL_SECONDS)
        if serial.is_file():
            log = strip_control(serial.read_text(encoding="utf-8", errors="replace"))
    finally:
        if qemu is not None:
            qmp_quit(qmp)
            try:
                qemu.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(qemu.pid, signal.SIGKILL)
                qemu.wait()
            if qemu.stderr is not None:
                qemu.stderr.close()
        stack.close()

    fields = report_fields(log)
    filesystem_lines = sorted(
        {
            CONSOLE_PREFIX.sub("", line.strip())
            for line in log.splitlines()
            if VERITY_CONSOLE.search(line)
        }
    )
    return {
        "accelerator_used": (
            "unknown" if kvm_enabled is None else "kvm" if kvm_enabled else "tcg"
        ),
        "booted_to_userspace": bool(fields),
        "console_corrupt_block_indices": sorted(
            {int(value) for value in CORRUPT_BLOCK.findall(log)}
        ),
        "console_filesystem_lines": filesystem_lines,
        "console_unit_failure_lines": sorted(
            {line.strip() for line in log.splitlines() if UNIT_FAILURE.search(line)}
        ),
        "masked_units": list(MASKED_UNITS),
        "probe": fields,
        "ready_seconds": ready_seconds,
        "serial_log_bytes": len(log),
    }


def assess(case: dict[str, Any], run: dict[str, Any]) -> list[str]:
    """Where the measurement disagrees with itself. Not where it disagrees with
    a hypothesis: a blast radius wider than the extent map predicted is a
    finding, not a defect, and is reported as a number rather than as a problem.
    """
    problems: list[str] = []
    if run["accelerator_used"] != "kvm":
        problems.append(f"accelerator was {run['accelerator_used']}, not KVM")
    if not run["booted_to_userspace"]:
        problems.append("the guest never reached the probe")
        return problems
    probe = run["probe"]
    for pass_name in ("bad-blocks", "bad-blocks-no-readahead"):
        if not probe[pass_name]:
            problems.append(
                f"{pass_name}: no block of the corrupted file failed to read; "
                "the injection did not reach a block the guest read, or it was "
                "served from cache"
            )
    # Strictly "0", not "0 or missing": an absent `blockdev` would leave this
    # empty and a tolerant check would let the second pass be reported as the
    # readahead-free one while readahead was still on.
    if probe.get("readahead-now-sectors") != "0":
        problems.append(
            f"readahead was still {probe.get('readahead-now-sectors')} for the second "
            "pass, so it does not isolate the format's own amplification"
        )
    if probe.get("usr-still-mounted") != "yes":
        problems.append("/usr did not survive the read")
    if probe.get("unrelated-file-read") not in ("0", ""):
        problems.append("an unrelated file also failed to read")
    if not run["console_corrupt_block_indices"]:
        problems.append("no dm-verity diagnostic named a corrupted data block")
    elif case["verity_data_block"] not in run["console_corrupt_block_indices"]:
        problems.append(
            f"dm-verity named blocks {run['console_corrupt_block_indices']} but the "
            f"bit was flipped in block {case['verity_data_block']}"
        )
    return problems


def environment() -> dict[str, Any]:
    return {
        "cpu_model": next(
            (
                line.split(":", 1)[1].strip()
                for line in Path("/proc/cpuinfo").read_text().splitlines()
                if line.startswith("model name")
            ),
            "",
        ),
        "cpu_count": os.cpu_count(),
        "host_kernel": platform.release(),
        "qemu": subprocess.run(
            ["qemu-system-x86_64", "--version"],
            capture_output=True, text=True, check=False,
        ).stdout.splitlines()[0:1],
        "guest_memory_mib": 2048,
        "guest_vcpus": 4,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--build-root",
        type=Path,
        default=default_build_root(),
    )
    parser.add_argument(
        "--kernel-version",
        required=True,
        help="the directory under /usr/lib/modules holding the two targets",
    )
    parser.add_argument("--output", type=Path, default=None)
    arguments = parser.parse_args()

    build_root: Path = arguments.build_root
    output = arguments.output or build_root / "evidence/pln0002-09/corruption.json"
    serial_dir = output.parent / "serial"
    serial_dir.mkdir(parents=True, exist_ok=True)

    cases: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="neutrinos-pln0002-09-") as raw:
        scratch = Path(raw)
        for arm, directory in ARMS.items():
            artifact = build_root / directory / "neutrinos-slice.raw"
            if not artifact.is_file():
                print(f"measure: no artifact at {artifact}", file=sys.stderr)
                return 1
            original_digest = file_digest(artifact)
            root_hash = uki_root_hash(build_root / directory / "neutrinos-slice.efi")
            data_offset, data_size = usr_partition(artifact)

            partition = scratch / f"usr-{arm}.img"
            extract(artifact, data_offset, data_size, partition)

            for name in TARGETS:
                target_path = f"{MODULES}/{arguments.kernel_version}/{name}"
                case = plan_injection(arm, build_root, partition, target_path)
                case.update({
                    "arm": arm,
                    "target": f"/usr{target_path}",
                    "target_name": name,
                })

                copy = scratch / f"{arm}-{name}.raw"
                shutil.copy(artifact, copy)
                absolute = data_offset + case["physical_offset"]
                with copy.open("r+b") as handle:
                    handle.seek(absolute)
                    byte = handle.read(1)
                    handle.seek(absolute)
                    handle.write(bytes([byte[0] ^ 0x01]))
                case["absolute_offset"] = absolute
                case["byte_before"] = byte[0]
                case["byte_after"] = byte[0] ^ 0x01
                case["bits_flipped"] = 1

                work = scratch / f"work-{arm}-{name}"
                work.mkdir()
                case["verity_verify_original"] = verity_verifies(
                    build_root, artifact, root_hash, work
                )
                case["verity_verify_corrupted"] = verity_verifies(
                    build_root, copy, root_hash, work
                )

                first = max(0, case["predicted_first_bad_block"] - WINDOW_BLOCKS)
                last = case["predicted_last_bad_block"] + WINDOW_BLOCKS
                case["window"] = [first, last]
                run = one_boot(copy, case["target"], first, last, work)
                retained = serial_dir / f"{arm}-{name}.log"
                shutil.copy(work / "serial.log", retained)
                run["serial_log"] = str(retained)

                copy.unlink()
                case["original_unchanged"] = file_digest(artifact) == original_digest
                case["run"] = run
                case["problems"] = assess(case, run)
                probe = run["probe"] or {}
                bad = probe.get("bad-blocks", [])
                cold = probe.get("bad-blocks-no-readahead", [])
                case["measured_lost_blocks"] = len(bad)
                case["measured_lost_bytes"] = len(bad) * BLOCK
                case["measured_lost_blocks_no_readahead"] = len(cold)
                case["measured_lost_bytes_no_readahead"] = len(cold) * BLOCK
                cases.append(case)
                print(
                    f"{arm}/{name}: verity-block={case['verity_data_block']} "
                    f"predicted={case['predicted_lost_bytes']}B "
                    f"default-ra={case['measured_lost_bytes']}B {bad[:1]}..{bad[-1:]} "
                    f"no-ra={case['measured_lost_bytes_no_readahead']}B "
                    f"{cold[:1]}..{cold[-1:]} "
                    f"booted={run['booted_to_userspace']} "
                    f"offline-verify={case['verity_verify_corrupted']}",
                    flush=True,
                )

    record = {
        "task": "PLN-0002-09",
        "measured": datetime.now().astimezone().isoformat(timespec="seconds"),
        "build_root": str(build_root),
        "block_size": BLOCK,
        "environment": environment(),
        "firmware": "plain OVMF; no Secure Boot claim is made by this task",
        "kernel_version": arguments.kernel_version,
        "cases": cases,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(f"measure: wrote {output}")

    failed = False
    for case in cases:
        for entry in case["problems"]:
            failed = True
            print(f"{case['arm']}/{case['target_name']}: {entry}", file=sys.stderr)
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
