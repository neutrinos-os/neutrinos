"""T4 disposable-VM boot of the composed slice artifact.

Three assertions, in order of what they cost to get wrong:

1. The literal artifact reaches readiness under a hostname the *harness*
   supplied, which proves both that it boots and that its first-boot
   configuration arrived from outside the image.
2. No unit failed on the way, read from the serial log.
3. The artifact is byte-identical afterwards. It is booted directly, with no
   copy, under QEMU's `snapshot=on`, so a mutation would be a real defect and
   not an artefact of the harness.

Every technique here was measured against the literal pre-amendment artifact
and recorded in RES-0013. Nothing is baked into the image to make this pass:
the guest carries no notify client, no agent, and no extra package. The
readiness channel is pid 1 reading the `vmm.notify_socket` credential this
harness supplies, which is stock systemd behavior.

Readiness is guest-driven, over a vsock the guest connects back on. That
replaces waiting for a `login:` string in a serial log, which measured 2.3
seconds later and asserted something weaker: a prompt is a getty having
started, while `READY=1` is pid 1 declaring the boot transaction complete.
Each sd_notify is a separate connection, so the listener accepts in a loop --
accepting once yields only systemd's early handshake and never the readiness
message.

The notify stream also carries `X_SYSTEMD_HOSTNAME`, which is checked instead
of pattern-matching the login banner. It is structured, it is pid 1's own view
of its identity, and it cannot be satisfied by an unrelated line that happens
to contain the fixture name.

vsock needs `/dev/vhost-vsock`, which a container or a locked-down CI runner
may not have. When it is unavailable this falls back to the serial marker and
says so in `readiness_source`, because a degraded run that reported the same
evidence as a full one would be the same defect as an accelerator that
silently falls back to emulation.
"""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

READ_CHUNK_BYTES = 4 * 1024 * 1024
BOOT_TIMEOUT_SECONDS = 600
POLL_SECONDS = 2.0
# Accepting a notify connection is the loop's cadence, so this also bounds how
# often the serial log is re-read. It is short because it is the resolution of
# the readiness measurement.
NOTIFY_POLL_SECONDS = 0.25
VHOST_DEVICE = "/dev/vhost-vsock"
# The ioctl that reserves a guest CID on an open /dev/vhost-vsock. Reserving is
# also how a free one is found: the kernel refuses a CID already claimed by
# another VM, so a successful call is the reservation, held until the fd
# closes. Two concurrent runs therefore cannot collide.
VHOST_VSOCK_SET_GUEST_CID = 0x4008AF60
# Below 3 are reserved: 0 hypervisor, 1 local, 2 host.
FIRST_GUEST_CID = 3
LAST_GUEST_CID = 0x7FFFFFFF
CID_ATTEMPTS = 64
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


def qmp_query_kvm(socket_path: Path) -> bool | None:
    """Ask the running VM whether KVM is in use. `None` if it could not be asked.

    The harness requests `kvm:tcg`, which means "KVM if you can, emulation
    otherwise". That is deliberate -- TCG produces the same evidence more
    slowly -- but until now the result recorded only what was requested, so a
    silent fall back to emulation was indistinguishable from a KVM run in the
    retained evidence. This asks the VM rather than inferring from the host:
    `/dev/kvm` being present does not mean this guest used it.
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
            stream.write(json.dumps({"execute": "query-kvm"}) + "\n")
            stream.flush()
            answer = json.loads(stream.readline())
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(answer, dict) or "return" not in answer:
        return None
    return bool(answer["return"].get("enabled"))


@contextlib.contextmanager
def notify_vsock() -> Any:
    """Reserve a guest CID and listen for the guest's notifications.

    Yields `(cid, vhost_fd, listener)`, or `(None, None, None)` when the host
    has no usable `/dev/vhost-vsock`. The caller decides what an absent vsock
    means; this only reports it.

    The listener binds `VMADDR_CID_ANY` on an ephemeral port. The guest is told
    where to connect through the `vmm.notify_socket` credential, so the port
    never has to be agreed in advance.
    """
    try:
        vhost_fd = os.open(VHOST_DEVICE, os.O_RDWR | os.O_CLOEXEC)
    except OSError:
        yield None, None, None
        return

    try:
        cid = None
        for _ in range(CID_ATTEMPTS):
            candidate = secrets.randbelow(LAST_GUEST_CID - FIRST_GUEST_CID) + FIRST_GUEST_CID
            try:
                fcntl.ioctl(vhost_fd, VHOST_VSOCK_SET_GUEST_CID, struct.pack("=Q", candidate))
            except OSError:
                continue
            cid = candidate
            break
        if cid is None:
            raise ValueError(f"no free vsock CID after {CID_ATTEMPTS} attempts")

        with socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM) as listener:
            listener.bind((socket.VMADDR_CID_ANY, socket.VMADDR_PORT_ANY))
            listener.listen()
            listener.settimeout(NOTIFY_POLL_SECONDS)
            yield cid, vhost_fd, listener
    finally:
        os.close(vhost_fd)


def drain_notification(listener: socket.socket) -> list[str]:
    """Accept one pending sd_notify connection and return its lines.

    Returns an empty list when nothing is pending. systemd opens a fresh
    connection per notification and closes it, so a short read to EOF is the
    whole message rather than a prefix of a stream.
    """
    try:
        connection, _ = listener.accept()
    except (TimeoutError, socket.timeout):
        return []

    with connection:
        connection.settimeout(NOTIFY_POLL_SECONDS)
        buffered = b""
        with contextlib.suppress(TimeoutError, socket.timeout, OSError):
            while chunk := connection.recv(4096):
                buffered += chunk
    return buffered.decode("utf-8", errors="replace").splitlines()


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
        stack = contextlib.ExitStack()
        try:
            cid, vhost_fd, listener = stack.enter_context(notify_vsock())
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
            if cid is not None and listener is not None:
                # Stock systemd reads this and connects back to say READY=1.
                # Nothing in the guest is configured to make that happen.
                port = listener.getsockname()[1]
                credentials["vmm.notify_socket"] = (
                    f"vsock-stream:{socket.VMADDR_CID_HOST}:{port}"
                )
            smbios: list[str] = []
            for key, value in credentials.items():
                smbios += ["-smbios", f"type=11,value=io.systemd.credential:{key}={value}"]
            # The UKI carries no command line of its own, so the console comes
            # from the harness. systemd-stub measures this string into PCR12.
            smbios += [
                "-smbios",
                "type=11,value=io.systemd.stub.kernel-cmdline-extra=console=ttyS0",
            ]

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

            readiness_source = "vsock-notify" if listener is not None else "serial-marker"
            marker = f"{HARNESS_HOSTNAME} login:"
            started = time.monotonic()
            deadline = started + BOOT_TIMEOUT_SECONDS
            log = ""
            reached = False
            ready_seconds: float | None = None
            marker_seconds: float | None = None
            hostname_from_notify: str | None = None
            while time.monotonic() < deadline:
                if listener is not None:
                    for line in drain_notification(listener):
                        if line == "READY=1" and ready_seconds is None:
                            ready_seconds = round(time.monotonic() - started, 3)
                        elif line.startswith("X_SYSTEMD_HOSTNAME="):
                            hostname_from_notify = line.partition("=")[2]
                if serial.is_file():
                    log = strip_control(
                        serial.read_text(encoding="utf-8", errors="replace")
                    )
                    if marker in log and marker_seconds is None:
                        marker_seconds = round(time.monotonic() - started, 3)
                # The serial marker is still read when vsock is the signal, so
                # the two can be compared, but only the declared source decides
                # whether the boot succeeded.
                reached = ready_seconds is not None if listener is not None else marker_seconds is not None
                if reached:
                    break
                if qemu.poll() is not None:
                    break
                if listener is None:
                    time.sleep(POLL_SECONDS)

            # Asked while the guest is still running: a dead VM answers
            # nothing, and the answer is about this run rather than the host.
            kvm_enabled = qmp_query_kvm(qmp) if qemu.poll() is None else None

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
                awaited = (
                    "READY=1 over the notify vsock"
                    if listener is not None
                    else repr(marker)
                )
                failures.append(
                    f"guest did not reach {awaited} within "
                    f"{BOOT_TIMEOUT_SECONDS}s{detail}"
                )
            # The hostname assertion is the point of the test, so an absent
            # notify hostname is a failure rather than a skipped check. Under
            # the serial fallback the marker carries it instead, and reaching
            # the marker is already that assertion.
            if listener is not None and hostname_from_notify != HARNESS_HOSTNAME:
                failures.append(
                    "guest did not report the harness hostname: expected "
                    f"{HARNESS_HOSTNAME!r}, notify reported {hostname_from_notify!r}"
                )
            unit_failures = sorted(
                {line.strip() for line in log.splitlines() if UNIT_FAILURE.search(line)}
            )
            if unit_failures:
                failures.append("units failed: " + "; ".join(unit_failures[:10]))
            report = {
                "accelerator_requested": "kvm:tcg",
                # What was requested is not what was obtained. Emulation is a
                # permitted outcome, not a failure, so this is recorded rather
                # than asserted -- but a result that names only the request
                # cannot tell a KVM run from a fallback afterwards.
                "accelerator_used": (
                    "unknown" if kvm_enabled is None else "kvm" if kvm_enabled else "tcg"
                ),
                "hostname_from_harness": HARNESS_HOSTNAME,
                "readiness_source": readiness_source,
                "ready_seconds": ready_seconds if listener is not None else marker_seconds,
                "serial_log_bytes": len(log),
                "unit_failures": unit_failures,
            }
            # Only the fields the declared source actually measured. Readiness
            # arrives about two seconds before the login prompt is printed, so
            # under vsock the run stops watching the serial log first -- and a
            # `reached_login_prompt: false` recorded from that would read as a
            # failed assertion rather than as a question no longer asked.
            if listener is not None:
                report["hostname_from_notify"] = hostname_from_notify
            else:
                report["reached_login_prompt"] = marker_seconds is not None
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
            # After QEMU is gone: closing the vhost fd releases the CID, and
            # releasing it while the VM still holds it would be a race.
            stack.close()

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
