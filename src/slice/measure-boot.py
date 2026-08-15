#!/usr/bin/env python3
"""Boot records for both arms: PLN-0002-08.

What task 08 owes: `/usr` read-only and verity-authenticated, `/etc`
regenerated, no failed units, and boot behaviour and memory with the
**repetition count and accelerator state recorded per run**. Both arms, the
same way, from the artifacts PLN-0002-06 built and PLN-0002-07 measured.

Three things are deliberate, none a default.

**The accelerator is measured, not requested.** `-machine accel=kvm:tcg` falls
back invisibly in a passing boot, and PLN-0001 measured the same boot at 72s
under TCG against 18s under KVM -- a 4x difference that would read as a format
result. Every run asks the VM through QMP; a run that cannot be asked, or that
answers differently from the others, fails the comparison rather than being
averaged into it.

**Nothing is added to the artifacts.** Probe unit, credentials and unit masks
arrive from the host as SMBIOS Type 11 credentials and stub command line, the
disk is `snapshot=on`, and the digest is checked before and after each boot.
PLN-0002-06's six are the accepted set and this does not rebuild them.

**A successful boot is not a statement about the artifact** -- the standing
finding, and it applies here most: dm-verity verifies lazily, per block, so
booting proves the blocks the boot touched. Tasks 09 and 10 carry the negative
evidence. This measures that the intended configuration is the one that
obtains, which is a smaller claim.

Plain OVMF, stated rather than defaulted: every assertion here is mount state,
unit health and timing, none a signature claim, and the Secure Boot build would
mean enrolling keys into a *copy*, measuring different bytes than PLN-0002-07
did. `T4-CONFEXT-001` is the signature arm.
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

# The two primaries. The four variants exist only as PLN-0002-10 substitution
# sources -- the plan says so in as many words -- and booting them would produce
# four more numbers that answer no C-007 criterion.
ARMS = {"erofs": "out-erofs", "ext4": "out-ext4"}

# "[    6.213929] sh[467]: " -- kernel timestamp, then the journal identifier
# systemd prepends to console output from a unit.
CONSOLE_PREFIX = re.compile(r"^\[\s*[\d.]+\]\s*\S+\[\d+\]:\s*")

MARKER_BEGIN = "PLN0002-08-BEGIN"
MARKER_END = "PLN0002-08-END"
HARNESS_HOSTNAME = "slice-pln0002-08"
BOOT_TIMEOUT_SECONDS = 600
NOTIFY_POLL_SECONDS = 0.25

# What the guest is asked. Every line is read out of the running system rather
# than out of the configuration meant to produce it -- PLN-0002-07's rule, and
# what caught three wrong claims in the PLN-0002-05 audit.
#
# A probe rather than a `findmnt` parse because a refused remount is the
# property itself, where `ro` in the options is only the flag the mount asked
# for. The two have disagreed here: `systemd.image_policy=` is satisfied by
# both enrollment arms and enforces neither.
PROBE_SCRIPT = f"""echo "{MARKER_BEGIN}"; \\
echo "usr-source=$(findmnt -no SOURCE /usr)"; \\
echo "usr-fstype=$(findmnt -no FSTYPE /usr)"; \\
echo "usr-options=$(findmnt -no OPTIONS /usr)"; \\
mount -o remount,rw /usr >/dev/null 2>&1 \\
  && echo "usr-remount-rw=succeeded" || echo "usr-remount-rw=refused"; \\
echo "usr-options-after=$(findmnt -no OPTIONS /usr)"; \\
echo "dm-uuid=$(cat /sys/class/block/dm-0/dm/uuid 2>/dev/null)"; \\
echo "dm-name=$(cat /sys/class/block/dm-0/dm/name 2>/dev/null)"; \\
echo "dm-ro=$(cat /sys/class/block/dm-0/ro 2>/dev/null)"; \\
echo "$(grep -o "usrhash=[^ ]*" /proc/cmdline)"; \\
echo "etc-fstype=$(findmnt -no FSTYPE /etc || echo none)"; \\
echo "etc-entries=$(ls -A /etc | wc -l)"; \\
echo "etc-passwd=$(test -s /etc/passwd && echo yes || echo no)"; \\
echo "etc-osrelease=$(test -r /etc/os-release && echo yes || echo no)"; \\
echo "etc-machineid=$(test -s /etc/machine-id && echo yes || echo no)"; \\
echo "root-fstype=$(findmnt -no FSTYPE /)"; \\
echo "system-state=$(timeout 30 systemctl is-system-running --wait)"; \\
echo "system-state-now=$(systemctl is-system-running)"; \\
echo "pending-jobs=$(systemctl list-jobs --no-legend --no-pager \\
  | tr -s "[:space:]" " " | tr -s "[:cntrl:]" ";")"; \\
echo "failed-units=$(systemctl list-units --state=failed --no-legend \\
  --plain --no-pager | cut -d" " -f1 | tr -s "[:space:]" ",")"; \\
echo "analyze-time=$(systemd-analyze time 2>/dev/null | head -1)"; \\
echo "mem-total-kb=$(sed -n "s/^MemTotal: *//p" /proc/meminfo)"; \\
echo "mem-available-kb=$(sed -n "s/^MemAvailable: *//p" /proc/meminfo)"; \\
echo "mem-free-kb=$(sed -n "s/^MemFree: *//p" /proc/meminfo)"; \\
echo "mem-cached-kb=$(sed -n "s/^Cached: *//p" /proc/meminfo)"; \\
echo "mem-slab-kb=$(sed -n "s/^Slab: *//p" /proc/meminfo)"; \\
echo "mem-anon-kb=$(sed -n "s/^AnonPages: *//p" /proc/meminfo)"; \\
echo "mem-shmem-kb=$(sed -n "s/^Shmem: *//p" /proc/meminfo)"; \\
echo "{MARKER_END}\""""

# Two faults that look identical from outside -- a boot that produced no
# evidence -- so both are asserted rather than commented. `vm.probe_unit` wraps
# the script in `sh -c '...'`, where one single quote silently truncates the
# command; and systemd unescapes C-style sequences in ExecStart before sh sees
# them, so `tr "\\n" ","` arrives as a literal newline mid-command. Both
# measured here, on the first run.
if "'" in PROBE_SCRIPT or "\\" in PROBE_SCRIPT.replace("\\\n", ""):
    raise SystemExit(
        "measure-boot: the probe script contains a single quote or a "
        "backslash escape; the first terminates the sh -c string "
        "vm.probe_unit builds, the second is consumed by systemd's own "
        "ExecStart unescaping before sh sees it"
    )

# System credentials reach the initrd's systemd as well as the host's, so
# without this the probe runs in the initrd -- `/usr` is rootfs, a read-write
# remount **succeeds**, `/etc` has 93 entries, and the machine powers off
# mid-switch-root. Measured: every assertion would have been made about the
# wrong filesystem and read as a defect in the artifact.
#
# `/etc/initrd-release` is the discriminator systemd itself uses.
NOT_IN_INITRD = "ConditionPathExists=!/etc/initrd-release\n"


def host_only(unit: str) -> str:
    """The same unit, refusing to run in the initrd."""
    head, separator, tail = unit.partition("[Unit]\n")
    if not separator:
        raise SystemExit("measure-boot: unit text has no [Unit] section to condition")
    return head + separator + NOT_IN_INITRD + tail


PROBE_UNIT = host_only(
    vm.probe_unit(
        PROBE_SCRIPT, description="PLN-0002-08 boot record probe", after="timers.target"
    )
)

# Timer-driven rather than wanted by multi-user.target, which is what lets it
# ask `is-system-running --wait`. Inside the initial transaction the boot waits
# for the probe while the probe waits for the boot: measured here as 120s of
# deadlock that also swallowed pid 1's READY=1. A timer is in the transaction;
# the service it triggers is a transaction of its own, so the probe observes a
# settled system instead of blocking what it observes.
#
# `OnBootSec=20s`, not 1s -- the same mistake's second version. The host manager
# starts around five seconds in, so a one-second offset has already elapsed at
# timers.target and the probe is queued straight back into the initial
# transaction. The offset has to clear startup, not merely the initrd.
PROBE_TIMER = (
    "[Unit]\n"
    + NOT_IN_INITRD
    + "Description=PLN-0002-08 boot record probe trigger\n"
    "[Timer]\n"
    "OnBootSec=20s\n"
    "AccuracySec=1ms\n"
    "Unit=pln0002-08.service\n"
)

# Fields that must be identical across every repetition of an arm. A figure
# that moved between reps is not a property of the format, and averaging it
# would hide that.
INVARIANT_FIELDS = (
    "usr-fstype",
    "usr-remount-rw",
    "dm-uuid",
    "system-state",
    "etc-entries",
)


def verity_uuid(artifact: Path) -> str:
    """The verity superblock UUID, read out of the artifact's own hash partition.

    This is what the running kernel puts in the dm device UUID
    (`CRYPT-VERITY-<uuid>-usr`), so it is the field that ties the device the
    guest mounted to the partition on the disk.
    """
    table = json.loads(
        subprocess.run(
            ["sfdisk", "-J", str(artifact)], capture_output=True, text=True, check=True
        ).stdout
    )["partitiontable"]
    sector = table.get("sectorsize", 512)
    entry = next(
        part for part in table["partitions"]
        if (part.get("name") or "").endswith("usr-verity")
    )
    with tempfile.NamedTemporaryFile(prefix="pln0002-08-verity-", suffix=".img") as scratch:
        with artifact.open("rb") as handle:
            handle.seek(entry["start"] * sector)
            remaining = entry["size"] * sector
            while remaining > 0:
                chunk = handle.read(min(1 << 20, remaining))
                if not chunk:
                    break
                scratch.write(chunk)
                remaining -= len(chunk)
        scratch.flush()
        dump = subprocess.run(
            ["veritysetup", "dump", scratch.name],
            capture_output=True, text=True, check=True,
        ).stdout
    for line in dump.splitlines():
        if line.strip().startswith("UUID:"):
            return line.partition(":")[2].strip()
    raise SystemExit(f"measure-boot: no verity UUID in the dump of {artifact}")


def uki_root_hash(uki: Path) -> str:
    """The `usrhash=` the signed UKI carries.

    Read from the UKI bytes rather than from the composition that wrote it,
    which is the rule the whole plan measures under. Exactly one distinct value
    must appear: more than one would mean the section this is reading is not the
    command line, and a claim built on the wrong section is worse than no claim.
    """
    matches = set(re.findall(rb"usrhash=([0-9a-f]{64})", uki.read_bytes()))
    if len(matches) != 1:
        raise SystemExit(
            f"measure-boot: expected exactly one usrhash in {uki}, found {len(matches)}"
        )
    return matches.pop().decode()


def report_fields(text: str) -> dict[str, str]:
    """The probe's key=value block, or empty if the probe never ran.

    Empty is a result, not an exception: a guest that never reached the probe
    has failed the boot assertion, and the console text is what says why.
    """
    if MARKER_BEGIN not in text or MARKER_END not in text:
        return {}
    body = text.split(MARKER_BEGIN, 1)[1].split(MARKER_END, 1)[0]
    fields: dict[str, str] = {}
    for line in body.splitlines():
        # Probe lines arrive wearing a kernel timestamp and journal prefix --
        # "[ 6.21] sh[467]: usr-fstype=erofs". Stripped here because the prefix
        # is added after the guest has spoken.
        key, separator, value = CONSOLE_PREFIX.sub("", line.strip()).partition("=")
        if separator:
            fields[key] = value.strip()
    # Reported by the guest in kB with the unit attached. Converted here so the
    # retained record holds numbers that can be compared rather than strings
    # that have to be parsed again by whoever reads it.
    for key, value in list(fields.items()):
        if key.startswith("mem-") and value.endswith(" kB"):
            with contextlib.suppress(ValueError):
                fields[key] = int(value.removesuffix(" kB"))
    return fields


# Kept for what one of them says: `Root hash verification failed (-ENOKEY)`
# appears *before* the mount succeeds -- the kernel declines the signature and
# the boot proceeds on unsigned verity. Dropping the line would assert a
# verity-authenticated boot while discarding the evidence of what verity did
# not do.
VERITY_CONSOLE = re.compile(
    r"(device-mapper|verity|dm-\d+|veritysetup).*", re.IGNORECASE
)


def one_boot(artifact: Path, work: Path) -> dict[str, Any]:
    """Boot one artifact once. Returns the run record.

    Structured after `slice_boot.check_boot`, which is the measured boot path in
    this repository, and importing its vsock, QMP and mask handling rather than
    copying them. `vm.py`'s own docstring records what three divergent copies of
    this cost the project.
    """
    code, variables = vm.firmware_pair(secure_boot=False)
    before = file_digest(artifact)
    work.mkdir(parents=True, exist_ok=True)
    tpm_state = work / "tpm"
    tpm_state.mkdir(mode=0o700)
    firmware = work / "OVMF_VARS.fd"
    shutil.copy(variables, firmware)
    firmware.chmod(0o600)
    serial = work / "serial.log"
    qmp = work / "qmp.sock"

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
            vm.credential_file(work, "systemd.extra-unit.pln0002-08.service", PROBE_UNIT),
            vm.credential_file(work, "systemd.extra-unit.pln0002-08.timer", PROBE_TIMER),
            vm.credential_file(
                work,
                "systemd.unit-dropin.timers.target",
                "[Unit]\nWants=pln0002-08.timer\n",
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
                "-device",
                f"vhost-vsock-pci,guest-cid={cid},vhostfd={vhost_fd}",
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
                # snapshot=on: the accepted artifact is the boot disk, uncopied,
                # and every guest write is discarded.
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
        # Asked once, early, while the guest is certain to still be running: a
        # dead VM answers nothing, and the answer is about this run.
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
    verity_lines = sorted(
        {
            CONSOLE_PREFIX.sub("", line.strip())
            for line in log.splitlines()
            if VERITY_CONSOLE.search(line)
        }
    )
    unit_failure_lines = sorted(
        {line.strip() for line in log.splitlines() if UNIT_FAILURE.search(line)}
    )
    after = file_digest(artifact)
    return {
        "accelerator_requested": "kvm:tcg",
        "accelerator_used": (
            "unknown" if kvm_enabled is None else "kvm" if kvm_enabled else "tcg"
        ),
        "artifact_unchanged_by_boot": before == after,
        "console_unit_failure_lines": unit_failure_lines,
        "console_verity_lines": verity_lines,
        "masked_units": list(MASKED_UNITS),
        "probe_ran": bool(fields),
        "probe": fields,
        "ready_seconds": ready_seconds,
        "readiness_source": "vsock-notify" if ready_seconds is not None else "none",
        "serial_log_bytes": len(log),
    }


def assess(runs: list[dict[str, Any]], expected: dict[str, str]) -> dict[str, Any]:
    """What the runs of one arm say, and where they disagree with each other.

    Disagreement between repetitions is reported rather than smoothed. This is
    the whole reason the plan asks for a repetition count: one boot is an
    anecdote, and three that differ are a finding about the arm.
    """
    problems: list[str] = []
    probes = [run["probe"] for run in runs if run["probe_ran"]]
    if len(probes) != len(runs):
        problems.append(f"{len(runs) - len(probes)} of {len(runs)} runs never reached the probe")

    accelerators = {run["accelerator_used"] for run in runs}
    if accelerators != {"kvm"}:
        problems.append(
            f"accelerator was not KVM on every run: {sorted(accelerators)}; "
            "a TCG run is not comparable with a KVM one"
        )
    if not all(run["artifact_unchanged_by_boot"] for run in runs):
        problems.append("an artifact was mutated by booting it")

    for field in INVARIANT_FIELDS:
        values = {probe.get(field) for probe in probes}
        if len(values) > 1:
            problems.append(f"{field} differed between repetitions: {sorted(map(str, values))}")

    for index, probe in enumerate(probes, start=1):
        if probe.get("usr-remount-rw") != "refused":
            problems.append(f"rep {index}: /usr accepted a read-write remount")
        # Two separate bindings, and conflating them was this harness's first
        # wrong assertion: the dm device UUID carries the verity **superblock**
        # UUID, not the root hash, so a run that mounted the right device failed
        # a check that was looking for the wrong field.
        #
        # They are also worth different amounts. The superblock UUID is
        # identical on both arms -- PLN-0002-05 declares it, for determinism --
        # so it proves the guest mounted *a* verity device built by this plan
        # and nothing narrower. The root hash is per-artifact, and it is the one
        # that ties the running kernel to the artifact under test.
        dm_uuid = probe.get("dm-uuid") or ""
        if not dm_uuid.startswith("CRYPT-VERITY-"):
            problems.append(f"rep {index}: /usr is not backed by a dm-verity target")
        elif expected["verity_uuid"].replace("-", "") not in dm_uuid.replace("-", ""):
            problems.append(
                f"rep {index}: the verity device UUID is not the artifact's: "
                f"{dm_uuid} against {expected['verity_uuid']}"
            )
        if (probe.get("usrhash") or "") != expected["root_hash"]:
            problems.append(
                f"rep {index}: the running command line's usrhash is not the one "
                f"the signed UKI carries: {probe.get('usrhash')!r} against "
                f"{expected['root_hash']!r}"
            )
        if probe.get("system-state") != "running":
            problems.append(f"rep {index}: system state is {probe.get('system-state')!r}")
        if (probe.get("failed-units") or "").strip(","):
            problems.append(f"rep {index}: failed units {probe['failed-units']}")

    # Two different boot figures, kept apart on purpose. `ready_seconds` is
    # host-observed and includes OVMF and QEMU start-up; `systemd-analyze` is
    # the guest's own kernel/initrd/userspace split. The second is the
    # comparable one between arms, the first is what a person waiting for the
    # machine experiences, and reporting either alone would answer a different
    # question than the one asked.
    analyze = [probe.get("analyze-time", "") for probe in probes]
    ready = [run["ready_seconds"] for run in runs if run["ready_seconds"] is not None]
    return {
        "problems": problems,
        "expected": expected,
        "systemd_analyze": analyze,
        "ready_seconds": {
            "repetitions": len(ready),
            "min": min(ready) if ready else None,
            "max": max(ready) if ready else None,
            "median": sorted(ready)[len(ready) // 2] if ready else None,
        },
    }


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
        default=Path(
            os.environ.get(
                "NEUTRINOS_SLICE_BUILD_ROOT",
                Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
                / "neutrinos/slice",
            )
        ),
    )
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--output", type=Path, default=None)
    arguments = parser.parse_args()

    build_root: Path = arguments.build_root
    results: dict[str, Any] = {}
    output = arguments.output or build_root / "evidence/pln0002-08/boot.json"
    serial_dir = output.parent / "serial"
    serial_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="neutrinos-pln0002-08-") as raw:
        scratch = Path(raw)
        for arm, directory in ARMS.items():
            artifact = build_root / directory / "neutrinos-slice.raw"
            if not artifact.is_file():
                print(f"measure: no artifact at {artifact}", file=sys.stderr)
                return 1
            expected = {
                "verity_uuid": verity_uuid(artifact),
                "root_hash": uki_root_hash(
                    build_root / directory / "neutrinos-slice.efi"
                ),
            }
            runs = []
            for repetition in range(1, arguments.repetitions + 1):
                work = scratch / f"{arm}-{repetition}"
                run = one_boot(artifact, work)
                run["repetition"] = repetition
                # Retained rather than discarded with the scratch directory. The
                # console is the only place several of these findings exist, and
                # a record whose evidence was deleted is a summary.
                retained = serial_dir / f"{arm}-{repetition}.log"
                shutil.copy(work / "serial.log", retained)
                run["serial_log"] = str(retained)
                runs.append(run)
                probe = run["probe"]
                print(
                    f"{arm} rep {repetition}: ready={run['ready_seconds']}s "
                    f"accel={run['accelerator_used']} "
                    f"state={probe.get('system-state', 'no-probe')} "
                    f"usr={probe.get('usr-fstype', '?')}/"
                    f"{probe.get('usr-remount-rw', '?')}",
                    flush=True,
                )
            results[arm] = {
                "runs": runs,
                "assessment": assess(runs, expected),
            }

    record = {
        "task": "PLN-0002-08",
        "measured": datetime.now().astimezone().isoformat(timespec="seconds"),
        "build_root": str(build_root),
        "environment": environment(),
        "firmware": "plain OVMF; no Secure Boot claim is made by this task",
        "repetitions_per_arm": arguments.repetitions,
        "arms": results,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(f"measure: wrote {output}")

    problems = {arm: data["assessment"]["problems"] for arm, data in results.items()}
    for arm, entries in problems.items():
        for entry in entries:
            print(f"{arm}: {entry}", file=sys.stderr)
    return 0 if not any(problems.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
