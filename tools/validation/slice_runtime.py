"""T4 runtime assertions about the booted `/usr` artifact.

Two properties DES-0006 C-013 relies on and nothing in this repository has ever
checked: the authenticated `/usr` is read-only at runtime, and nothing in `/etc`
is durable.

Both are asserted from inside the guest, because both are properties of the
running machine rather than of the bytes on disk. A static check can say `/etc`
shipped empty; only a boot can say the `/etc` the machine actually assembles has
no durable backing. The probe reports a marked block on the console and this
module parses it -- the same shape `confext_policy.py` uses, and the reason it
is a shape rather than a convention is in `vm.probe_unit`, which appends the
poweroff a probe cannot be trusted to remember.

The failure this exists for is the one the whole plan keeps meeting: a mechanism
that is configured, runs, reports success, and gates nothing. `/usr` mounted
`ro` is not the same claim as `/usr` cannot be written, and a probe that only
read the mount options would report the weaker one. So the probe writes.
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

from tools.validation import vm
from tools.validation.vm import file_digest

BEGIN = "NEUTRINOS-RUNTIME-BEGIN"
END = "NEUTRINOS-RUNTIME-END"
MOUNTS_BEGIN = "NEUTRINOS-MOUNTS-BEGIN"
MOUNTS_END = "NEUTRINOS-MOUNTS-END"
HARNESS_HOSTNAME = "slice-t4-runtime"
PROBE_UNIT_NAME = "neutrinos-runtime-probe.service"
# The same two masks T4-SLICE-001 and PLN-0002-08 ran under, for the same
# measured reason: the artifact ships no `tpm2-pcr-public-key.pem` and supplying
# one is TPM policy, which PLN-0002 excludes. Carried in the result so the
# condition travels with the evidence.
MASKED_UNITS = (
    "systemd-tpm2-setup-early.service",
    "systemd-pcrproduct.service",
)

# Filesystems with no durable backing. A machine whose writable `/etc` layer is
# on one of these cannot carry configuration across a reboot, which is what
# C-013 asserts when it says `/etc` holds nothing durable.
VOLATILE_FILESYSTEMS = ("tmpfs", "ramfs")
UPPERDIR = re.compile(r"\bupperdir=([^,]+)")

PROBE = "; ".join(
    [
        f'echo {BEGIN}',
        'echo "usr-options=$(findmnt -no OPTIONS /usr)"',
        'echo "usr-source=$(findmnt -no SOURCE /usr)"',
        'echo "usr-fstype=$(findmnt -no FSTYPE /usr)"',
        # `findmnt --target`, not `stat -f -c %T`: the unit's ExecStart is
        # parsed by systemd, which reads `%T` as its own temporary-directory
        # specifier and substitutes it before /bin/sh ever sees it.
        'echo "etc-fstype=$(findmnt -no FSTYPE --target /etc)"',
        'echo "root-fstype=$(findmnt -no FSTYPE /)"',
        # The assertions that write. `2>/dev/null` on the attempt itself: the
        # error text is the shell's and varies, while the exit status is the
        # answer.
        'touch /usr/.neutrinos-probe 2>/dev/null; echo "usr-write-rc=$?"',
        'mount -o remount,rw /usr 2>/dev/null; echo "usr-remount-rc=$?"',
        'touch /etc/.neutrinos-probe 2>/dev/null; echo "etc-write-rc=$?"',
        'echo "etc-entries=$(ls -A /etc | wc -l)"',
        f'echo {MOUNTS_BEGIN}',
        'findmnt -rn -o TARGET,SOURCE,FSTYPE,OPTIONS',
        f'echo {MOUNTS_END}',
        f'echo {END}',
    ]
)


def probe_fields(console: str) -> dict[str, str]:
    if BEGIN not in console or END not in console:
        return {}
    body = console.split(BEGIN, 1)[1].split(END, 1)[0]
    fields: dict[str, str] = {}
    for line in body.splitlines():
        # The console carries systemd's own prefixes on the same lines, so the
        # key is anchored rather than split on the first `=` in the line.
        match = re.search(r"\b([a-z-]+)=(.*)$", line.strip())
        if match and match.group(1) in {
            "usr-options", "usr-source", "usr-fstype", "etc-fstype",
            "root-fstype", "usr-write-rc", "usr-remount-rc", "etc-write-rc",
            "etc-entries",
        }:
            fields[match.group(1)] = match.group(2).strip()
    return fields


def probe_mounts(console: str) -> list[dict[str, str]]:
    if MOUNTS_BEGIN not in console or MOUNTS_END not in console:
        return []
    body = console.split(MOUNTS_BEGIN, 1)[1].split(MOUNTS_END, 1)[0]
    mounts: list[dict[str, str]] = []
    for line in body.splitlines():
        # `findmnt -rn` output is four space-separated fields, and the console
        # may prefix the line. Anchored on a target that starts at `/`.
        match = re.search(r"(/\S*)\s+(\S+)\s+(\S+)\s+(\S+)\s*$", line.strip())
        if match:
            mounts.append(
                {
                    "target": match.group(1),
                    "source": match.group(2),
                    "fstype": match.group(3),
                    "options": match.group(4),
                }
            )
    return mounts


def hosting_filesystem(path: str, mounts: list[dict[str, str]]) -> str:
    """The filesystem type of the mount that contains `path`.

    Longest matching mount point wins, which is what the kernel does. Returns
    an empty string when no mount contains it, which the caller treats as a
    failure rather than as tmpfs -- an unlocatable writable layer is exactly the
    case that must not read as volatile.
    """
    best = ""
    best_length = -1
    for mount in mounts:
        target = mount["target"]
        if (path == target or path.startswith(target.rstrip("/") + "/")) and len(
            target
        ) > best_length:
            best, best_length = mount["fstype"], len(target)
    return best


def check_runtime_boundaries() -> int:
    from tools.validation.check import SLICE_ARTIFACT_ENV

    artifact = Path(os.environ[SLICE_ARTIFACT_ENV]).resolve() / "neutrinos-slice.raw"
    before = file_digest(artifact)
    failures: list[str] = []

    _, variables = vm.firmware_pair(secure_boot=False)
    with tempfile.TemporaryDirectory(prefix="neutrinos-slice-t4r-") as raw:
        work = Path(raw)
        store = work / "OVMF_VARS.fd"
        shutil.copy(variables, store)
        store.chmod(0o600)
        credentials = work / "credentials"
        credentials.mkdir()
        # Two credentials, not one, and the second is the one that is easy to
        # miss: `systemd.extra-unit.` drops the unit in, and nothing pulls it in
        # without a target drop-in wanting it. `confext_policy.py` records the
        # same pair for the same reason; a probe unit that is present and
        # unwanted leaves the guest at a login prompt until a timeout kills it.
        credential_files = [
            vm.credential_file(
                credentials,
                f"systemd.extra-unit.{PROBE_UNIT_NAME}",
                vm.probe_unit(PROBE, description="PLN-0002-11 runtime boundaries"),
            ),
            vm.credential_file(
                credentials,
                "systemd.unit-dropin.multi-user.target",
                f"[Unit]\nWants={PROBE_UNIT_NAME}\n",
            ),
        ]
        console = vm.boot(
            artifact,
            work=work,
            store=store,
            credentials={"system.hostname": HARNESS_HOSTNAME},
            credential_files=credential_files,
            cmdline_extra=[
                f"systemd.mask={unit_name} rd.systemd.mask={unit_name}"
                for unit_name in MASKED_UNITS
            ],
            timeout_seconds=420,
        )

    fields = probe_fields(console)
    mounts = probe_mounts(console)
    if not fields:
        # A guest that never ran the probe cannot report that nothing is wrong.
        print(
            "the probe produced no marked report, so the guest did not reach it; "
            f"console was {len(console)} bytes",
            file=sys.stderr,
        )
        return 1

    observed, report = evaluate(fields, mounts)
    failures.extend(observed)

    after = file_digest(artifact)
    if before != after:
        failures.append(
            f"the artifact was mutated by booting it: {before} before, {after} after"
        )

    if failures:
        # The mount table travels with the failure. A runtime assertion that
        # reports only its verdict sends the next reader back for another boot
        # to find out what the machine actually looked like, and this one costs
        # a VM to reproduce.
        print("\n".join(failures), file=sys.stderr)
        print(
            "observed: " + json.dumps(
                {"fields": fields, "mounts": mounts},
                ensure_ascii=False, separators=(",", ":"), sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    report.update(
        {
            "artifact_digest": after,
            "establishes": (
                "the booted machine cannot write to /usr, and /etc has no "
                "durable layer for a write to land on"
            ),
            "does_not_establish": (
                "that /usr was authenticated -- a successful mount is not a "
                "signature claim, which PLN-0002-10 measured directly"
            ),
            "masked_units": list(MASKED_UNITS),
            "result": "passing",
        }
    )
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    return 0


def evaluate(
    fields: dict[str, str], mounts: list[dict[str, str]]
) -> tuple[list[str], dict[str, Any]]:
    """The assertions, separated from the boot that produces their input.

    Split out so failure sensitivity can be established against the shipped
    assertions rather than a copy of them. Inducing each of these in a real
    guest would mean building an artifact per property; the boot is real and
    its report is the guest's, and each injection mutates one observation of it.
    """
    failures: list[str] = []
    options = fields.get("usr-options", "")
    if "ro" not in options.split(","):
        failures.append(f"/usr is mounted {options!r}, which does not include ro")
    source = fields.get("usr-source", "")
    # The authenticated artifact is reached through device-mapper, not through
    # the partition. A /usr mounted straight off /dev/vda2 would be the same
    # filesystem with no verity under it, and every read-only assertion here
    # would still pass.
    if not re.match(r"^/dev/(mapper/|dm-)", source):
        failures.append(
            f"/usr is mounted from {source!r}, which is not a device-mapper "
            f"device, so it is not the verity-authenticated artifact"
        )
    if fields.get("usr-write-rc") == "0":
        failures.append("a file was created in /usr, which is read-only by design")
    if fields.get("usr-remount-rc") == "0":
        failures.append("/usr accepted a remount read-write")

    # Nothing durable in /etc, asserted against what the machine does rather
    # than against what it is made of. Two drafts of this were wrong before the
    # boot corrected them, and both errors are worth keeping visible:
    #
    #   1. "/etc is tmpfs" -- false. It is an `overlay`, because a confext merge
    #      is an overlay mount. DES-0005's mechanism, working.
    #   2. "the overlay's upperdir is on tmpfs" -- also false. Measured
    #      2026-08-15: the /etc overlay is mounted **ro** with lowerdirs only --
    #      the sysext metadata, the confext's own /etc, and /sysroot/etc from
    #      the initrd's factory replay -- and no upperdir at all.
    #
    # So the property is stronger than either draft assumed, and the rule is
    # the disjunction that covers both this machine and one that merges no
    # confext: a write to /etc must be refused outright, or must land on a
    # volatile filesystem. A machine that satisfies neither can carry
    # configuration across a reboot, which is what C-013 says it must not.
    etc_fstype = fields.get("etc-fstype", "")
    etc_writable = fields.get("etc-write-rc") == "0"
    etc_backing = "writes refused"
    if etc_writable:
        etc_mount = next((mount for mount in mounts if mount["target"] == "/etc"), None)
        upper = (
            UPPERDIR.search(etc_mount["options"])
            if etc_mount is not None and etc_fstype == "overlay"
            else None
        )
        # An overlay names where its writes land; anything else takes them on
        # the filesystem holding /etc itself.
        etc_backing = hosting_filesystem(
            upper.group(1) if upper else "/etc", mounts
        )
        if etc_backing not in VOLATILE_FILESYSTEMS:
            failures.append(
                f"/etc accepted a write and it landed on {etc_backing!r}, which "
                f"is not one of the volatile filesystems {VOLATILE_FILESYSTEMS}, "
                f"so /etc can hold durable content"
            )

    # The general statement behind the specific one: nothing block-backed is
    # writable anywhere, so there is no durable surface for /etc or anything
    # else to land on. Stated as an enumeration rather than as a claim about
    # /etc alone, because a writable partition mounted elsewhere would make the
    # /etc result true and the property it stands for false.
    writable_devices = [
        mount for mount in mounts
        if mount["source"].startswith("/dev/") and "ro" not in mount["options"].split(",")
    ]
    if writable_devices:
        failures.append(
            "block-backed mounts are writable, so the machine has durable "
            "storage this artifact does not declare: "
            + "; ".join(f"{m['target']} from {m['source']}" for m in writable_devices)
        )

    return failures, {
        "etc_entries": fields.get("etc-entries"),
        "etc_filesystem": etc_fstype,
        # Where a write to /etc actually lands, which is the durability claim.
        "etc_writable_layer": etc_backing,
        "etc_write_refused": not etc_writable,
        "mounts": mounts,
        "root_filesystem": fields.get("root-fstype"),
        "usr_options": options,
        "usr_source": source,
        "usr_write_refused": fields.get("usr-write-rc") != "0",
        "usr_remount_refused": fields.get("usr-remount-rc") != "0",
    }
