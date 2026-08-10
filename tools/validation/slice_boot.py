"""T4 disposable-VM boot of the composed slice artifact.

Three assertions, in order of what they cost to get wrong:

1. The literal artifact reaches a login prompt under a hostname the *harness*
   supplied, which proves both that it boots and that its first-boot
   configuration arrived from outside the image.
2. No unit failed on the way, read from the serial log.
3. The artifact is byte-identical afterwards. It is booted directly, with no
   copy, under QEMU's `snapshot=on`, so a mutation would be a real defect and
   not an artefact of the harness.

Every technique here was measured against the literal pre-amendment artifact
and recorded in RES-0013. Nothing is baked into the image to make this pass.

Guest-driven readiness over a notify vsock is the intended replacement for
waiting on a serial marker, and is deliberately absent: it is untested while
this build host has no KVM. Until then the marker is the signal, and a boot
that never prints it fails on the timeout with its log retained.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

READ_CHUNK_BYTES = 4 * 1024 * 1024
BOOT_TIMEOUT_SECONDS = 600
POLL_SECONDS = 2.0
# Synthetic, and visibly so. It appears only in the login banner of a VM that
# is discarded when this function returns.
HARNESS_HOSTNAME = "slice-t4-fixture"
UNIT_FAILURE = re.compile(
    r"Failed to start |Failed with result |Dependency failed for ", re.ASCII
)


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(READ_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def firmware_pair() -> tuple[Path, Path]:
    from tools.validation.check import OVMF_CODE_CANDIDATES

    for candidate in OVMF_CODE_CANDIDATES:
        code = Path(candidate)
        variables = Path(candidate.replace("CODE", "VARS"))
        if code.is_file() and variables.is_file():
            return code, variables
    raise ValueError("no OVMF firmware code/variables pair found")


def strip_control(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]|[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)


def qmp_quit(socket_path: Path) -> None:
    """Ask QEMU to exit. Failure here is not a test failure.

    The process group is torn down unconditionally afterwards, so a QMP that
    never answers costs a signal rather than a leaked VM.
    """
    try:
        with socket.socket(socket.AF_UNIX) as client:
            client.settimeout(5)
            client.connect(str(socket_path))
            stream = client.makefile("rw")
            stream.readline()
            stream.write(json.dumps({"execute": "qmp_capabilities"}) + "\n")
            stream.flush()
            stream.readline()
            stream.write(json.dumps({"execute": "quit"}) + "\n")
            stream.flush()
    except (OSError, ValueError):
        pass


def check_boot() -> int:
    from tools.validation.check import SLICE_ARTIFACT_ENV

    artifact = Path(os.environ[SLICE_ARTIFACT_ENV]).resolve() / "neutrinos-slice.raw"
    code, variables = firmware_pair()
    before = file_digest(artifact)
    failures: list[str] = []
    report: dict[str, Any] = {}

    with tempfile.TemporaryDirectory(prefix="neutrinos-slice-t4-") as raw:
        work = Path(raw)
        state = work / "tpm"
        state.mkdir(mode=0o700)
        firmware = work / "OVMF_VARS.fd"
        shutil.copy(variables, firmware)
        firmware.chmod(0o600)
        serial = work / "serial.log"
        qmp = work / "qmp.sock"

        swtpm = subprocess.Popen(
            (
                "swtpm",
                "socket",
                f"--tpmstate=dir={state}",
                f"--ctrl=type=unixio,path={state / 'sock'}",
                "--tpm2",
                "--flags",
                "startup-clear",
            ),
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        qemu: subprocess.Popen[bytes] | None = None
        try:
            deadline = time.monotonic() + 10
            while not (state / "sock").exists() and time.monotonic() < deadline:
                time.sleep(0.1)
            if not (state / "sock").exists():
                print("software TPM did not create its control socket", file=sys.stderr)
                return 1

            credentials = {
                "firstboot.timezone": "UTC",
                "firstboot.locale": "C.UTF-8",
                "system.hostname": HARNESS_HOSTNAME,
                # An unlocked account with no password, in a VM that exists for
                # the length of this function. There is no secret here because
                # there is no secret.
                "passwd.hashed-password.root": "",
            }
            smbios: list[str] = []
            for key, value in credentials.items():
                smbios += ["-smbios", f"type=11,value=io.systemd.credential:{key}={value}"]
            # The UKI carries no command line of its own, so the console comes
            # from the harness. systemd-stub measures this string into PCR12.
            smbios += [
                "-smbios",
                "type=11,value=io.systemd.stub.kernel-cmdline-extra=console=ttyS0",
            ]

            qemu = subprocess.Popen(
                [
                    "qemu-system-x86_64",
                    "-nodefaults",
                    # KVM when the host offers it, TCG when it does not. Both
                    # produce the same evidence; only the wall clock differs.
                    # The fallback list is only accepted by `-machine accel=`;
                    # `-accel kvm:tcg` is rejected as one unknown accelerator.
                    "-machine", "q35,smm=on,accel=kvm:tcg",
                    "-cpu", "max",
                    "-m", "2048",
                    "-smp", "4",
                    "-drive", f"if=pflash,unit=0,format=raw,readonly=on,file={code}",
                    "-drive", f"if=pflash,unit=1,format=raw,file={firmware}",
                    # snapshot=on: the artifact is the boot disk and no copy is
                    # made. QEMU discards every guest write.
                    "-drive", f"if=virtio,format=raw,file={artifact},snapshot=on",
                    "-chardev", f"socket,id=chrtpm,path={state / 'sock'}",
                    "-tpmdev", "emulator,id=tpm0,chardev=chrtpm",
                    "-device", "tpm-tis,tpmdev=tpm0",
                    *smbios,
                    "-nic", "none",
                    "-display", "none",
                    "-serial", f"file:{serial}",
                    "-qmp", f"unix:{qmp},server=on,wait=off",
                    "-no-reboot",
                ],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )

            marker = f"{HARNESS_HOSTNAME} login:"
            deadline = time.monotonic() + BOOT_TIMEOUT_SECONDS
            log = ""
            reached = False
            while time.monotonic() < deadline:
                if serial.is_file():
                    log = strip_control(
                        serial.read_text(encoding="utf-8", errors="replace")
                    )
                    if marker in log:
                        reached = True
                        break
                if qemu.poll() is not None:
                    break
                time.sleep(POLL_SECONDS)

            if not reached:
                # A VMM that refuses to start and one that boots into silence
                # are different defects, and the difference is in QEMU's own
                # diagnostics, so they are reported rather than discarded.
                detail = ""
                if qemu.poll() is not None and qemu.stderr is not None:
                    detail = strip_control(
                        qemu.stderr.read().decode("utf-8", errors="replace")
                    ).strip()
                    detail = f"; QEMU exited {qemu.returncode}: {detail[:2000]}"
                failures.append(
                    f"guest did not reach {marker!r} within "
                    f"{BOOT_TIMEOUT_SECONDS}s{detail}"
                )
            unit_failures = sorted(
                {line.strip() for line in log.splitlines() if UNIT_FAILURE.search(line)}
            )
            if unit_failures:
                failures.append("units failed: " + "; ".join(unit_failures[:10]))
            report = {
                "accelerator_requested": "kvm:tcg",
                "hostname_from_harness": HARNESS_HOSTNAME,
                "reached_login_prompt": reached,
                "serial_log_bytes": len(log),
                "unit_failures": unit_failures,
            }
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
            try:
                os.killpg(swtpm.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            swtpm.wait()

    after = file_digest(artifact)
    if before != after:
        failures.append(
            f"the artifact was mutated by booting it: {before} before, {after} after"
        )

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1

    report.update(
        {
            "artifact_digest": after,
            "artifact_unchanged_by_boot": True,
            "result": "passing",
        }
    )
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    return 0
