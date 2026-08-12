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

import os
import re
import shutil
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from tools.validation import vm

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

PROBE_SCRIPT = f"""echo "{MARKER_BEGIN}"; \\
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
echo "{MARKER_END}\""""

PROBE_UNIT = vm.probe_unit(PROBE_SCRIPT, description="Confext signature policy probe")

# ExecStart is cleared before being set: without the empty assignment systemd
# appends, and a Type=oneshot unit would run the stock merge first and the
# policy-bearing one second, so the strict arm would be preceded by a permissive
# merge that had already succeeded.
POLICY_DROPIN = """[Service]
ExecStart=
ExecStart=/usr/bin/systemd-confext --image-policy={policy} --mutable=ephemeral merge
"""


def boot(
    artifact: Path,
    confext: Path | None,
    policy: str | None,
    work: Path,
    tag: str,
    store: Path,
) -> dict[str, str]:
    """One boot. Returns the probe's key=value report, empty if it never ran.

    `secure_boot=True` is stated rather than defaulted: every assertion this
    check makes is about signature enforcement, and the plain OVMF build would
    answer every one of them with a boot that looks like a pass. The store is
    supplied rather than made per boot for the reason recorded in `vm.boot`.
    """
    run = work / tag
    run.mkdir(parents=True)

    credentials = [
        vm.credential_file(run, "systemd.extra-unit.confext-policy.service", PROBE_UNIT),
        vm.credential_file(
            run,
            "systemd.unit-dropin.multi-user.target",
            "[Unit]\nWants=confext-policy.service\n",
        ),
    ]
    if policy is not None:
        credentials.append(
            vm.credential_file(
                run,
                "systemd.unit-dropin.systemd-confext.service",
                POLICY_DROPIN.format(policy=policy),
            )
        )

    text = vm.boot(
        artifact,
        work=run,
        store=store,
        secure_boot=True,
        credentials={
            "firstboot.locale": "C.UTF-8",
            "firstboot.timezone": "UTC",
            "firstboot.keymap": "us",
            "system.hostname": "confext-policy-fixture",
            "passwd.hashed-password.root": "!*",
        },
        credential_files=credentials,
        extra_disks=() if confext is None else (confext,),
    )
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

    before = vm.file_digest(artifact)
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="confext-policy-") as scratch:
        work = Path(scratch)

        # The first boot of a fresh variable store enrolls PK, KEK and db from
        # the ESP and reboots; `-no-reboot` turns that into QEMU exiting. So it
        # is a warm-up whose only product is an enrolled store, and it is not
        # measured. Its report is expected to be absent, not present.
        _, variables = vm.firmware_pair(secure_boot=True)
        enrolled_store = work / "OVMF_VARS.fd"
        shutil.copyfile(variables, enrolled_store)
        boot(artifact, enrolled, None, work, "warmup", enrolled_store)

        # The four cells are independent boots, and the only thing that made
        # them sequential was sharing one variable store -- pflash unit 1 is
        # writable, so concurrent cells would be writing the same file. Each
        # gets its own copy of the *enrolled* store instead, which is both the
        # thing that lets them run at once and a stronger isolation: a cell can
        # no longer inherit variable state a previous cell wrote.
        arms = {
            ("strict", "enrolled"): (enrolled, STRICT_POLICY, "s-e"),
            ("strict", "unenrolled"): (unenrolled, STRICT_POLICY, "s-u"),
            ("default", "enrolled"): (enrolled, None, "d-e"),
            ("default", "unenrolled"): (unenrolled, None, "d-u"),
        }

        def run_cell(arm: tuple[Path, str | None, str]) -> dict[str, str]:
            confext, policy, tag = arm
            store = work / f"OVMF_VARS.{tag}.fd"
            shutil.copyfile(enrolled_store, store)
            return boot(artifact, confext, policy, work, tag, store)

        # Threads, not processes: every one of these blocks in subprocess.run
        # waiting on a QEMU that holds no Python state.
        with ThreadPoolExecutor(max_workers=len(arms)) as pool:
            cells = dict(zip(arms, pool.map(run_cell, arms.values()), strict=True))

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

    after = vm.file_digest(artifact)
    if before != after:
        failures.append("the fixture changed during the run")

    for failure in failures:
        print(f"confext policy: {failure}", file=sys.stderr)
    return 1 if failures else 0
