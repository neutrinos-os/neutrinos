"""One place that knows how to boot a disposable guest.

**Draft, for owner review.** Nothing calls this yet. `slice_boot.py`,
`confext_policy.py` and `src/spike/pln0002-01/boot.sh` still each carry their
own copy of this knowledge, and migrating them is the obligation this module
creates rather than work it has done.

## Why it exists

Three independent boot paths grew in this repository, each learning different
things the hard way, and **nothing propagated a lesson from one to the others**.
`boot.sh` learned that Fedora ships two OVMF builds whose names differ by one
word and that the obvious one has no Secure Boot support at all.
`confext_policy.py` learned that a probe unit without a poweroff leaves the
guest at a login prompt until something kills it, and that a fresh variable
store makes every boot a first boot. `slice_boot.py` learned notify-vsock
readiness. A fourth probe written on 2026-08-12 inherited only the scars of
whichever file its author happened to open, and rediscovered three lessons that
were already recorded and already fixed elsewhere -- at a cost in wall clock and
in real money.

So this is a merge, not a design. Every rule below is something this project
already paid for once.

## The shape of the fix

The rules are **guards and defaults, not comments**. A comment saying "remember
the poweroff" is the same class of control that already failed; a function that
appends the poweroff cannot be called without it. This is the project's own
stated preference, argued in the `/etc` carve for collision 1: mechanically
impossible rather than reviewed for.

Each guard names the failure it prevents, because a guard whose message does not
identify the fault sends the next reader after the wrong thing. Measured: swtpm
failing to bind an over-long socket path reports only "did not create its
control socket", which reads as a TPM fault, and cost two wrong diagnoses before
anyone counted the bytes.
"""

from __future__ import annotations

import contextlib
import re
import subprocess
import time
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path

# AF_UNIX paths are limited to 108 bytes including the terminator on Linux, and
# swtpm reports the failure as a missing socket rather than as a path length
# problem. Guarded rather than documented for that reason.
SOCKET_PATH_LIMIT = 108

# A guest that cannot finish in this long is not going to. The number is
# confext_policy.py's, which is the only one of the three paths that was chosen
# rather than inherited; the probe that used 600 wasted ten minutes of wall
# clock on a guest sitting at a login prompt.
DEFAULT_TIMEOUT_SECONDS = 300

# Fedora and Debian both ship two OVMF builds whose names differ by one word.
# The plain one is compiled **without Secure Boot support**: no SetupMode, no
# SecureBoot variable, no db, and an empty .platform keyring -- and it boots
# fine, so its absence reads as success. The PLN-0002-01 spike ran on it for the
# whole plan and every signature statement made in that window was measured
# where the mechanism was structurally absent.
SECBOOT_CODE_CANDIDATES = (
    "/usr/share/edk2/x64/OVMF_CODE.secboot.4m.fd",
    "/usr/share/edk2/ovmf/OVMF_CODE.secboot.fd",
    "/usr/share/OVMF/OVMF_CODE.secboot.fd",
    "/usr/share/edk2-ovmf/x64/OVMF_CODE.secboot.fd",
)

PLAIN_CODE_CANDIDATES = (
    "/usr/share/edk2/x64/OVMF_CODE.4m.fd",
    "/usr/share/edk2/ovmf/OVMF_CODE.fd",
    "/usr/share/OVMF/OVMF_CODE.fd",
)


class HarnessError(RuntimeError):
    """A fault in the harness, not in the artifact under test.

    Separate from a failed check on purpose. "The artifact did not boot" and
    "this probe cannot run here" are different results, and reporting the second
    as the first is how a tooling problem becomes an artifact investigation.
    """


def strip_control(text: str) -> str:
    """Remove ANSI escapes and control bytes from console output.

    Single home for what `slice_boot.py` and `confext_policy.py` currently
    define identically, character for character.
    """
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]|[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)


def firmware_pair(*, secure_boot: bool) -> tuple[Path, Path]:
    """The OVMF code/variables pair, with the build stated rather than assumed.

    `secure_boot` is a required keyword because the two builds are not
    interchangeable and the difference is invisible in a passing boot. A caller
    that does not know which it wants is a caller that is about to measure
    signatures on firmware that has none.
    """
    candidates = SECBOOT_CODE_CANDIDATES if secure_boot else PLAIN_CODE_CANDIDATES
    for candidate in candidates:
        code = Path(candidate)
        variables = Path(re.sub(r"CODE(\.secboot)?", "VARS", candidate))
        if code.is_file() and variables.is_file():
            return code, variables
    build = "Secure Boot" if secure_boot else "plain"
    raise HarnessError(f"no {build} OVMF code/variables pair found in {candidates}")


def credential_file(directory: Path, name: str, value: str) -> Path:
    """Write one SMBIOS Type 11 credential payload.

    Through a file rather than an inline `-smbios` string because a multi-line
    payload cannot be carried inline, and every unit or drop-in is multi-line.
    """
    path = directory / f"{name}.cred"
    path.write_text(f"io.systemd.credential:{name}={value}", encoding="utf-8")
    return path


def probe_unit(script: str, *, description: str, after: str = "multi-user.target") -> str:
    """A probe unit that always ends the boot.

    The poweroff is appended here rather than asked for, because a probe unit
    without one leaves the guest at a login prompt until a timeout kills it.
    `Requires=` as well as `After=` for the same reason the working probe has
    both: `After=` alone orders a unit that may never be pulled in.
    """
    return (
        f"[Unit]\n"
        f"Description={description}\n"
        f"After={after}\n"
        f"Requires={after}\n"
        f"[Service]\n"
        f"Type=oneshot\n"
        f"StandardOutput=journal+console\n"
        f"ExecStart=/usr/bin/sh -c '{script}'\n"
        f"ExecStopPost=/usr/bin/systemctl poweroff\n"
    )


@contextlib.contextmanager
def software_tpm(state: Path) -> Iterator[Path]:
    """A disposable vTPM, yielding its control socket path.

    The path length is checked before swtpm is started, because the failure
    otherwise surfaces as "did not create its control socket" -- which reads as
    a TPM fault and is not one.
    """
    state.mkdir(parents=True, exist_ok=True)
    socket_path = state / "sock"
    if len(str(socket_path).encode()) >= SOCKET_PATH_LIMIT:
        raise HarnessError(
            f"vTPM control socket path is {len(str(socket_path).encode())} bytes, "
            f"limit is {SOCKET_PATH_LIMIT}: {socket_path}. This is a path length "
            f"problem, not a TPM problem. Use a short working directory."
        )
    process = subprocess.Popen(
        (
            "swtpm", "socket",
            f"--tpmstate=dir={state}",
            f"--ctrl=type=unixio,path={socket_path}",
            "--tpm2", "--flags", "startup-clear",
        ),
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 10
        while not socket_path.exists() and time.monotonic() < deadline:
            time.sleep(0.1)
        if not socket_path.exists():
            raise HarnessError(
                f"swtpm did not create {socket_path} within 10s, and the path is "
                f"within the length limit, so this is a genuine swtpm failure"
            )
        yield socket_path
    finally:
        with contextlib.suppress(ProcessLookupError):
            process.terminate()


def boot(
    artifact: Path,
    *,
    work: Path,
    store: Path,
    secure_boot: bool = False,
    credentials: Mapping[str, str] | None = None,
    credential_files: Sequence[Path] = (),
    extra_disks: Sequence[Path] = (),
    tpm_socket: Path | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> str:
    """Boot one disposable guest. Returns the console text, control stripped.

    The artifact is always attached `snapshot=on`, so a boot cannot write to it.
    Measured across the whole plan: the artifact digest is unchanged by every
    boot, and that is a property of this line rather than of good behaviour.

    The variable store is supplied rather than created, and that is
    load-bearing. A fresh store is in setup mode, so systemd-boot enrolls the
    keys from the ESP and reboots -- a per-boot store makes every boot a first
    boot, and a probe unit never runs.

    `console=ttyS0` is always appended through the stub credential, never
    optionally. Without it the kernel switches to the framebuffer partway
    through boot and every later status line -- including a probe's own output
    -- goes to a console the serial log never sees. Measured 2026-08-12: a probe
    ran correctly and reported nothing, twice, for this reason. It is supplied
    from the host so the signed UKI is untouched.
    """
    code, _ = firmware_pair(secure_boot=secure_boot)
    work.mkdir(parents=True, exist_ok=True)
    console = work / "console.log"

    command = [
        "qemu-system-x86_64",
        "-machine", "q35,smm=on,accel=kvm:tcg",
        "-cpu", "host",
        "-m", "2048",
        "-nographic",
        "-no-reboot",
        "-drive", f"if=pflash,unit=0,format=raw,readonly=on,file={code}",
        "-drive", f"if=pflash,unit=1,format=raw,file={store}",
        "-drive", f"if=virtio,format=raw,file={artifact},snapshot=on",
    ]
    for disk in extra_disks:
        command += ["-drive", f"if=virtio,format=raw,file={disk},snapshot=on"]
    if tpm_socket is not None:
        command += [
            "-chardev", f"socket,id=chrtpm,path={tpm_socket}",
            "-tpmdev", "emulator,id=tpm0,chardev=chrtpm",
            "-device", "tpm-tis,tpmdev=tpm0",
        ]
    for name, value in (credentials or {}).items():
        command += ["-smbios", f"type=11,value=io.systemd.credential:{name}={value}"]
    for path in credential_files:
        command += ["-smbios", f"type=11,path={path}"]
    command += [
        "-smbios",
        "type=11,value=io.systemd.stub.kernel-cmdline-extra=console=ttyS0",
        "-serial", "mon:stdio",
    ]

    with console.open("wb") as stream:
        try:
            subprocess.run(
                command,
                stdout=stream,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            # Not raised. A guest that never finishes is a result the caller
            # reads out of the console, and the spike's fault injection produces
            # exactly this on purpose.
            pass
    return strip_control(console.read_text(encoding="utf-8", errors="replace"))
