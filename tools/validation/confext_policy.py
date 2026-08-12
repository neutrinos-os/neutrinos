"""T4 confext signature-enforcement policy, measured in a disposable VM.

The property under test is not "a signed confext merges". It is that a confext
signed by an authority the machine does not trust is **refused**, and that the
refusal is visible as a unit failure rather than as a log line beside a
successful merge.

That distinction is the reason this exists. Four mechanisms in PLN-0002 have
now been observed failing open while reporting success -- a corrupt /usr that
booted because dm-verity is lazy, a refused confext whose unit reported
`Finished`, an unvalidated signature that merged, and a firmware without Secure
Boot support that produced signature evidence for a whole spike. Each was
found by a boot and none by review.

So the assertion is a 2x2 and three of its four cells are load-bearing:

    policy=root=signed  enrolled -> merged, unit success
    policy=root=signed  unenrolled -> NOT merged, unit failure   <- the point
    policy=default      enrolled -> merged
    policy=default      unenrolled -> merged                     <- asserted

The last row asserts the fail-open. That looks perverse and is deliberate: the
day systemd starts refusing an untrusted confext under the default policy is a
fact this plan needs to learn, and a check that tolerated either outcome there
would not tell anyone. If it changes, this fails and the finding gets recorded
rather than absorbed.

The policy is applied as a drop-in on `systemd-confext.service`, not on a
command line, per the owner ruling of 2026-08-11. The unit form is what
NeutrinOS would ship, and it is strictly stronger: the failure is a unit
failure the rest of the transaction can order against.

Nothing is baked into the artifact to make this pass. The confext arrives on a
second disk, the policy and the probe unit arrive as SMBIOS Type 11
credentials, and the fixture is opened `snapshot=on` with its digest checked
before and after.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

READ_CHUNK_BYTES = 4 * 1024 * 1024
BOOT_TIMEOUT_SECONDS = 300
# Every OVMF build Fedora and Debian ship under this name is compiled *without*
# Secure Boot support. Booting one produces no SetupMode, no SecureBoot, no db,
# and an empty .platform keyring -- and the guest boots perfectly well, so the
# absence reads as success. The whole PLN-0002-01 spike ran on one. This check
# accepts only the secboot builds, and blocks rather than skips when there is
# none.
SECBOOT_CODE_CANDIDATES = (
    "/usr/share/edk2/x64/OVMF_CODE.secboot.4m.fd",
    "/usr/share/edk2/ovmf/OVMF_CODE.secboot.fd",
    "/usr/share/OVMF/OVMF_CODE.secboot.fd",
    "/usr/share/edk2-ovmf/x64/OVMF_CODE.secboot.fd",
)
FIXTURE_ENV = "NEUTRINOS_CONFEXT_FIXTURE_DIR"
FIXTURE_MEMBERS = (
    "enrolled-artifact.raw",
    "confext-enrolled.raw",
    "confext-unenrolled.raw",
)
MARKER_BEGIN = "CONFEXT-POLICY-BEGIN"
MARKER_END = "CONFEXT-POLICY-END"
# The file the confext owns. Its presence in /etc is the merge, observed from
# the outside rather than taken from systemd-confext's own report.
MERGED_FILE = "10-neutrinos-default.network"
STRICT_POLICY = "root=signed"

PROBE_UNIT = f"""[Unit]
Description=Confext signature policy probe
After=multi-user.target
Requires=multi-user.target
[Service]
Type=oneshot
StandardOutput=journal+console
ExecStart=/usr/bin/sh -c 'echo "{MARKER_BEGIN}"; \\
echo "secure-boot=$(tail -c1 \
/sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c \
2>/dev/null | od -An -tu1 | tr -d " \\n")"; \\
echo "platform-keys=$(grep -c "asymmetri" /proc/keys 2>/dev/null)"; \\
echo "exec-start=$(systemctl show systemd-confext.service -p ExecStart --value \
| tr -d "\\n" | tail -c 400)"; \\
mkdir -p /run/confexts; \\
dd if=/dev/vdb of=/run/confexts/neutrinos-network.raw bs=1M status=none; \\
systemd-confext unmerge >/dev/null 2>&1; \\
systemctl restart systemd-confext.service >/dev/null 2>&1; \\
echo "unit-result=$(systemctl show systemd-confext.service -p Result --value)"; \\
echo "unit-status=$(systemctl show systemd-confext.service -p ExecMainStatus --value)"; \\
echo "merged-file=$(test -e /etc/systemd/network/{MERGED_FILE} && echo yes || echo no)"; \\
echo "{MARKER_END}"'
ExecStopPost=/usr/bin/systemctl poweroff
"""

# ExecStart is cleared before being set: without the empty assignment systemd
# appends, and a Type=oneshot unit would run the stock merge first and the
# policy-bearing one second, so the strict arm would be preceded by a permissive
# merge that had already succeeded.
POLICY_DROPIN = """[Service]
ExecStart=
ExecStart=/usr/bin/systemd-confext --image-policy={policy} --mutable=ephemeral merge
"""


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(READ_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def firmware_pair() -> tuple[Path, Path]:
    for candidate in SECBOOT_CODE_CANDIDATES:
        code = Path(candidate)
        variables = Path(re.sub(r"CODE\.secboot", "VARS", candidate))
        if code.is_file() and variables.is_file():
            return code, variables
    raise ValueError("no Secure Boot OVMF firmware code/variables pair found")


def strip_control(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]|[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)


def credential_file(directory: Path, name: str, value: str) -> Path:
    """Write one SMBIOS credential payload.

    Through a file rather than an inline `-smbios` string because every payload
    here is multi-line, and an inline string cannot carry a newline.
    """
    path = directory / f"{name}.cred"
    path.write_text(f"io.systemd.credential:{name}={value}", encoding="utf-8")
    return path


def boot(
    artifact: Path,
    confext: Path | None,
    policy: str | None,
    work: Path,
    tag: str,
    store: Path,
) -> dict[str, str]:
    """One boot. Returns the probe's key=value report, empty if it never ran.

    The variable store is supplied rather than made here, and that is
    load-bearing. A fresh store is in setup mode, so systemd-boot enrolls the
    keys from the ESP and reboots -- meaning a per-boot store would make every
    boot a first boot, and the probe would never run. Measured, after writing
    it the other way first.
    """
    code, _ = firmware_pair()
    run = work / tag
    run.mkdir(parents=True)

    credentials = [
        credential_file(run, "systemd.extra-unit.confext-policy.service", PROBE_UNIT),
        credential_file(
            run,
            "systemd.unit-dropin.multi-user.target",
            "[Unit]\nWants=confext-policy.service\n",
        ),
    ]
    if policy is not None:
        credentials.append(
            credential_file(
                run,
                "systemd.unit-dropin.systemd-confext.service",
                POLICY_DROPIN.format(policy=policy),
            )
        )

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
    if confext is not None:
        command += ["-drive", f"if=virtio,format=raw,file={confext},snapshot=on"]
    for name, value in (
        ("firstboot.locale", "C.UTF-8"),
        ("firstboot.timezone", "UTC"),
        ("firstboot.keymap", "us"),
        ("system.hostname", "confext-policy-fixture"),
        ("passwd.hashed-password.root", "!*"),
    ):
        command += ["-smbios", f"type=11,value=io.systemd.credential:{name}={value}"]
    for path in credentials:
        command += ["-smbios", f"type=11,path={path}"]
    command += ["-serial", "mon:stdio"]

    console = run / "console.log"
    with console.open("wb") as stream:
        try:
            subprocess.run(
                command,
                stdout=stream,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                timeout=BOOT_TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired:
            pass

    text = strip_control(console.read_text(encoding="utf-8", errors="replace"))
    if MARKER_BEGIN not in text or MARKER_END not in text:
        return {}
    body = text.split(MARKER_BEGIN, 1)[1].split(MARKER_END, 1)[0]
    report: dict[str, str] = {}
    for line in body.splitlines():
        match = re.search(r"([a-z-]+)=(.*)$", line.strip())
        if match:
            report[match.group(1)] = match.group(2).strip()
    return report


def check_confext_signature_policy() -> int:
    directory = Path(os.environ[FIXTURE_ENV]).expanduser().resolve()
    artifact = directory / "enrolled-artifact.raw"
    enrolled = directory / "confext-enrolled.raw"
    unenrolled = directory / "confext-unenrolled.raw"

    before = file_digest(artifact)
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="confext-policy-") as scratch:
        work = Path(scratch)

        # The first boot of a fresh variable store enrolls PK, KEK and db from
        # the ESP and reboots; `-no-reboot` turns that into QEMU exiting. So it
        # is a warm-up whose only product is an enrolled store, and it is not
        # measured. Its report is expected to be absent, not present.
        code, variables = firmware_pair()
        store = work / "OVMF_VARS.fd"
        shutil.copyfile(variables, store)
        boot(artifact, enrolled, None, work, "warmup", store)

        cells = {
            ("strict", "enrolled"): boot(artifact, enrolled, STRICT_POLICY, work, "s-e", store),
            ("strict", "unenrolled"): boot(artifact, unenrolled, STRICT_POLICY, work, "s-u", store),
            ("default", "enrolled"): boot(artifact, enrolled, None, work, "d-e", store),
            ("default", "unenrolled"): boot(artifact, unenrolled, None, work, "d-u", store),
        }

        for name, report in cells.items():
            if not report:
                failures.append(f"{name}: the probe never reported")
                continue

            # Asserted per cell rather than once, because a firmware regression
            # that silently disabled Secure Boot would otherwise be invisible
            # in exactly the cells it invalidates. This is the defect that hid
            # for a whole spike.
            if report.get("secure-boot") != "1":
                failures.append(
                    f"{name}: SecureBoot is {report.get('secure-boot', 'unreported')!r},"
                    " expected 1"
                )
            if report.get("platform-keys", "0") == "0":
                failures.append(f"{name}: no certificates in any kernel keyring")

            policy, signer = name
            if policy == "strict" and STRICT_POLICY not in report.get("exec-start", ""):
                failures.append(
                    f"{name}: the policy drop-in did not take effect;"
                    f" ExecStart is {report.get('exec-start', '')!r}"
                )

            merged = report.get("merged-file") == "yes"
            result = report.get("unit-result", "")
            refuse = policy == "strict" and signer == "unenrolled"

            if refuse:
                if merged:
                    failures.append(
                        f"{name}: an untrusted confext merged under {STRICT_POLICY};"
                        " signature enforcement is not closing"
                    )
                if result == "success":
                    failures.append(
                        f"{name}: systemd-confext.service succeeded on a refused"
                        " confext, so the refusal is invisible to the transaction"
                    )
            else:
                if not merged:
                    failures.append(
                        f"{name}: the confext did not merge; expected it to"
                        + (
                            " (a trusted image must not be refused)"
                            if signer == "enrolled"
                            else " (the default policy is expected to fail open;"
                            " if it no longer does, that is a finding to record,"
                            " not a silent improvement)"
                        )
                    )

    after = file_digest(artifact)
    if before != after:
        failures.append("the fixture changed during the run")

    for failure in failures:
        print(f"confext policy: {failure}", file=sys.stderr)
    return 1 if failures else 0
