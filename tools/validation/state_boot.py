"""T4 check: the state artifact's /var and /home are backed by block devices.

The assertion is deliberately about the *mount*, not about a write succeeding,
and that distinction was measured rather than reasoned. Before the mount units
existed, a probe wrote to /var and /home and reported success on both. Nothing
failed, nothing logged, and both writes went to the tmpfs root and disappeared
at poweroff -- the ninth instance of this project's characteristic defect, an
operation that looks successful and asserts nothing.

So a check that writes a file and reads it back would have passed on a machine
with no state volumes at all. This one requires each path to be a mount whose
source is a block device carrying the declared partition label, which is false
in exactly the case the write test could not see.

What is not asserted here: that anything survives a power cycle. QEMU runs with
`-no-reboot` and the artifact is attached `snapshot=on`, so this harness cannot
observe a second boot of the same disk. Persistence across a real reboot needs
a harness that keeps a disk, and until one exists this check must not be read as
evidence for it.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.validation import vm  # noqa: E402
from tools.validation.slice_boot import HARNESS_MACHINE_ID  # noqa: E402

# Each expected mount, with the partition label its source must carry. The
# labels are declared in src/slice/composition/state-partitions/.
EXPECTED_MOUNTS = (
    ("/var", "neutrinos-var"),
    ("/home", "neutrinos-home"),
)

PROBE_UNIT = """[Unit]
Description=NeutrinOS state volume probe
DefaultDependencies=no
After=local-fs.target sysinit.target var.mount home.mount
Wants=local-fs.target
Conflicts=shutdown.target

[Service]
Type=oneshot
StandardOutput=journal+console
StandardError=journal+console
ExecStart=/usr/bin/sh -c 'echo "NEUTRINOS-STATE-BEGIN"; \
for m in /var /home; do \
  echo "STATE $m source=$(findmnt -no SOURCE --target $m) \
fstype=$(findmnt -no FSTYPE --target $m) \
label=$(findmnt -no PARTLABEL --target $m)"; \
done; \
echo "STATE / fstype=$(findmnt -no FSTYPE --target /)"; \
echo "NEUTRINOS-STATE-END"'
ExecStopPost=/usr/bin/systemctl poweroff --no-block

[Install]
WantedBy=multi-user.target
"""

# Not anchored to the start of a line. Every probe line arrives on the serial
# console behind a kernel timestamp and an `sh[pid]:` prefix, so an anchored
# pattern matches nothing and the check reports "no mount line" for a guest that
# answered correctly. Measured, after exactly that.
LINE = re.compile(
    r"STATE (?P<where>\S+) source=(?P<source>\S*) fstype=(?P<fstype>\S*) "
    r"label=(?P<label>\S*)\s*$",
    re.MULTILINE,
)


def check_state_boot() -> int:
    from tools.validation.check import STATE_ARTIFACT_ENV

    artifact = Path(os.environ[STATE_ARTIFACT_ENV]).resolve() / "neutrinos-slice.raw"
    code, variables = vm.firmware_pair(secure_boot=False)

    with tempfile.TemporaryDirectory(prefix="neutrinos-state-t4-") as raw:
        work = Path(raw)
        store = work / "OVMF_VARS.fd"
        shutil.copy(variables, store)
        store.chmod(0o600)
        credential_dir = work / "credentials"
        credential_dir.mkdir()
        console = vm.boot(
            artifact,
            work=work,
            store=store,
            secure_boot=False,
            credentials={
                "system.hostname": "state-t4-fixture",
                # Not decoration. The /var partition's UUID is derived from this
                # value, and T2-STATE-001 holds the two together. A guest booted
                # with a different machine-id is a different machine as far as
                # the Discoverable Partitions Specification is concerned.
                "system.machine_id": HARNESS_MACHINE_ID,
                "passwd.hashed-password.root": "",
            },
            credential_files=[
                vm.credential_file(
                    credential_dir,
                    "systemd.extra-unit.neutrinos-state-probe.service",
                    PROBE_UNIT,
                )
            ],
            # Host-supplied, so it changes no byte of the artifact. The mount
            # units themselves are inside /usr and are not injected here: what
            # is under test is whether the artifact mounts its own volumes.
            cmdline_extra=["systemd.wants=neutrinos-state-probe.service"],
            timeout_seconds=180,
        )

    failures: list[str] = []
    if "NEUTRINOS-STATE-BEGIN" not in console or "NEUTRINOS-STATE-END" not in console:
        # A probe that did not run is not a pass. Without this the parse below
        # finds no lines, reports no mismatches, and the check succeeds having
        # observed nothing.
        print("state probe did not run to completion in the guest", file=sys.stderr)
        return 1

    observed = {
        match.group("where"): match.groupdict() for match in LINE.finditer(console)
    }
    report: dict[str, Any] = {"mounts": {}}

    for where, label in EXPECTED_MOUNTS:
        seen = observed.get(where)
        if seen is None:
            failures.append(f"{where}: probe reported no mount line")
            continue
        report["mounts"][where] = {
            "fstype": seen["fstype"],
            "partlabel": seen["label"],
            "source": seen["source"],
        }
        if not seen["source"].startswith("/dev/"):
            failures.append(
                f"{where}: source is {seen['source']!r}, not a block device; "
                "writes here would land on the root tmpfs and be lost at poweroff"
            )
        if seen["fstype"] == "tmpfs":
            failures.append(f"{where}: filesystem is tmpfs, so nothing written to it persists")
        if seen["label"] != label:
            failures.append(
                f"{where}: partition label is {seen['label']!r}, expected {label!r}"
            )

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1

    report["result"] = "passing"
    report["persistence_across_reboot"] = "not asserted; the harness keeps no disk"
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    return 0
