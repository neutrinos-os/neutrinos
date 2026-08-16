#!/usr/bin/env python3
"""Negative evidence for the `/usr` artifact: PLN-0002-10.

What task 10 owes: **substitution of a same-format valid `/usr`, its Verity
tree, the confext, and the manifest, plus a wrong-but-valid signing key, each
recorded with the mechanism that rejected it and the diagnostic that
discriminates a root-hash mismatch from a signature failure from a mount
failure.** SYS-049 is the requirement; C-001 binds it to a cross product, so
covered cells are enumerated and uncovered ones named. Results and their
reasoning: docs/project/artifact-substitution-records.md.

Four choices are deliberate.

**Every donor is an independently valid, enrolled-signer-signed artifact** --
PLN-0002-06's variants, not a foreign format and not a corrupt image. PR-0030
C-004: a substitute that fails to mount never reached the binding. A cell that
boots means integrity failed to bind, never that a signature was missing.

**The substituted identity lives in the GPT.** `systemd-repart` derives the
`/usr` and Verity partition UUIDs from the two halves of the root hash, so the
pair cells splice the primary's ESP into the donor's disk. Splicing the other
way would keep the primary's identity in the field the binding uses.

**Both firmware configurations, as a 2x2.** Owner ruling 2026-08-15. Every one
of this plan's seven fail-opens turned on "no mechanism exists" against "the
mechanism was not configured", and one firmware cannot tell those apart.

**A passing boot is the predicted result and is not a pass.** Measuring an
absence of enforcement is the result, so nothing asserts a refusal. What is
asserted is that the measurement can tell the difference -- hence the baseline
cell, which must boot for any negative to be attributable.

The six accepted artifacts are never written to: every cell is a copy, every
disk `snapshot=on`, each digest checked before and after.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from common import default_build_root
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.validation import vm  # noqa: E402
from tools.validation.slice_boot import MASKED_UNITS, UNIT_FAILURE  # noqa: E402
from tools.validation.vm import file_digest, strip_control  # noqa: E402

SECTOR = 512
ARMS = {"erofs": "out-erofs", "ext4": "out-ext4"}
VARIANTS = ("content", "seed")

ESP = "esp"
USR = "neutrinos-usr"
VERITY = "neutrinos-usr-verity"
SIG = "neutrinos-usr-verity-sig"

MARKER_BEGIN = "PLN0002-10-BEGIN"
MARKER_END = "PLN0002-10-END"
CONSOLE_PREFIX = re.compile(r"^\[\s*[\d.]+\]\s*\S+\[\d+\]:\s*")

# The file that exists only in the content variant's tree. It is what makes
# "which /usr is mounted" an observation rather than an inference, in the one
# pair of artifacts whose contents differ at all.
VARIANT_MARKER = "/usr/lib/neutrinos/variant-marker"

# Lines worth keeping from a boot that never reaches the probe, which is the
# outcome this task is looking for. The discrimination the plan asks for lives
# here: dm-verity names a root hash, systemd-veritysetup names a signature, and
# a mount failure names neither.
DIAGNOSTIC = re.compile(
    r"(verity|dm-\d+|device-mapper|EROFS|EXT4-fs|dissect|image policy|"
    r"Failed to mount|emergency|Cannot open access to console|"
    r"root hash|signature|sysroot|initrd-)",
    re.IGNORECASE,
)
BOOT_TIMEOUT_SECONDS = 300

PROBE_SCRIPT = f"""echo "{MARKER_BEGIN}"; \\
echo "secure-boot=$(tail -c1 \
/sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c \
2>/dev/null | od -An -tu1 | tr -d " \\n")"; \\
echo "platform-keys=$(grep -c asymmetri /proc/keys 2>/dev/null)"; \\
echo "cmdline=$(cat /proc/cmdline | tr -s "[:space:]" " ")"; \\
echo "usr-source=$(findmnt -no SOURCE /usr)"; \\
echo "usr-fstype=$(findmnt -no FSTYPE /usr)"; \\
echo "usr-options=$(findmnt -no OPTIONS /usr | cut -c1-60)"; \\
echo "variant-marker=$(test -e {VARIANT_MARKER} && echo present || echo absent)"; \\
echo "veritysetup-result=$(systemctl show systemd-veritysetup@usr.service \
-p Result --value)"; \\
echo "system-state=$(timeout 30 systemctl is-system-running --wait)"; \\
echo "failed-units=$(systemctl list-units --state=failed --no-legend \\
  --plain --no-pager | cut -d" " -f1 | tr -s "[:space:]" ",")"; \\
echo "{MARKER_END}\""""

NOT_IN_INITRD = "ConditionPathExists=!/etc/initrd-release\n"


def host_only(unit: str) -> str:
    head, separator, tail = unit.partition("[Unit]\n")
    if not separator:
        raise SystemExit("measure-substitution: unit text has no [Unit] section")
    return head + separator + NOT_IN_INITRD + tail


# The probe is fired by a timer at 20s rather than pulled in by
# multi-user.target, which is how PLN-0002-09 runs it and is a correction rather
# than a copy. Wanted by the target, the probe is inside the same transaction it
# asks about: `systemctl is-system-running --wait` then waits on a job that waits
# on the probe, `timeout 30` kills it, and every booted cell of the first full
# run reported an empty system state. A boot that reports nothing about its own
# state is exactly the fail-open shape this task exists to catch, so it is not
# left in the apparatus.
PROBE_UNIT = host_only(
    vm.probe_unit(
        PROBE_SCRIPT,
        description="PLN-0002-10 substitution probe",
        after="timers.target",
    )
)
PROBE_TIMER = (
    "[Unit]\n"
    + NOT_IN_INITRD
    + "Description=PLN-0002-10 substitution probe trigger\n"
    "[Timer]\n"
    "OnBootSec=20s\n"
    "AccuracySec=1ms\n"
    "Unit=pln0002-10.service\n"
)

PROBE_KEYS = (
    "secure-boot",
    "platform-keys",
    "cmdline",
    "usr-source",
    "usr-fstype",
    "usr-options",
    "variant-marker",
    "veritysetup-result",
    "system-state",
    "failed-units",
)


def table(image: Path) -> dict[str, dict[str, Any]]:
    """Partition entries by label, with byte offsets resolved.

    Read from each image rather than assumed constant: the content variants are
    genuinely larger and their later partitions therefore start elsewhere, which
    is the fact that decides how a cell can be built at all.
    """
    parsed = json.loads(
        subprocess.run(
            ["sfdisk", "-J", str(image)], capture_output=True, text=True, check=True
        ).stdout
    )["partitiontable"]
    sector = parsed.get("sectorsize", SECTOR)
    entries: dict[str, dict[str, Any]] = {}
    for partition in parsed["partitions"]:
        name = partition.get("name") or ""
        entries[name] = {
            "offset": partition["start"] * sector,
            "length": partition["size"] * sector,
            "uuid": partition["uuid"],
        }
    for required in (ESP, USR, VERITY, SIG):
        if required not in entries:
            raise SystemExit(f"measure-substitution: {image} has no {required} partition")
    return entries


def splice(destination: Path, at: dict[str, Any], source: Path, frm: dict[str, Any]) -> None:
    """Copy one partition's bytes over another's, in place, refusing to resize.

    The refusal is the point. A donor larger than its slot could only be written
    by truncating it, and a truncated `/usr` is a corrupt image rather than a
    valid substitute -- it would fail for the reason PR-0030 C-004 says makes a
    substitution cell meaningless.
    """
    if frm["length"] > at["length"]:
        raise SystemExit(
            f"measure-substitution: donor partition is {frm['length']} bytes and the "
            f"slot is {at['length']}; splicing would truncate a valid member into a "
            "corrupt one"
        )
    with source.open("rb") as reader, destination.open("r+b") as writer:
        reader.seek(frm["offset"])
        writer.seek(at["offset"])
        remaining = frm["length"]
        while remaining > 0:
            chunk = reader.read(min(1 << 20, remaining))
            if not chunk:
                break
            writer.write(chunk)
            remaining -= len(chunk)
        # Whatever the donor did not fill is left as the slot found it. Only the
        # equal-size splices are used for the integrity cells; the ESP splice is
        # the one place a few unwritten trailing sectors are harmless, because
        # nothing hashes the ESP.


def partition_bytes(image: Path, entry: dict[str, Any]) -> bytes:
    with image.open("rb") as handle:
        handle.seek(entry["offset"])
        return handle.read(entry["length"])


def sig_blob(root_hash: str, certificate: Path, key: Path, length: int) -> bytes:
    """A verity signature partition's payload, rebuilt for a chosen signer.

    The structure is copied from what `systemd-repart` produced, read out of the
    artifacts rather than from documentation: a JSON object of `rootHash`, the
    signer certificate's SHA-256 fingerprint, and a base64 detached CMS
    signature over the root hash's ASCII form, SHA-256, with no signed
    attributes.

    Faithfulness is verified rather than asserted -- see `verify_reconstruction`
    and the `sig-rebuilt-enrolled` control cell. Byte equality with the
    artifact's own blob was the first check written and it is the wrong one:
    RSA PKCS#1 v1.5 is deterministic, but `systemd-repart` reaches OpenSSL
    through its API and emits the SHA-256 `digestAlgorithm` with an explicit
    NULL parameter where the command line omits it. Four bytes, semantically
    identical, both verify. So faithfulness is checked cryptographically, and
    what closes the remaining gap is a control: the same rebuild with the
    *enrolled* key is booted alongside the wrong-key cell, so any difference
    between them is the signer and not the encoding.
    """
    signature = subprocess.run(
        [
            "openssl", "cms", "-sign",
            "-signer", str(certificate),
            "-inkey", str(key),
            "-binary", "-noattr", "-nosmimecap",
            "-md", "sha256",
            "-outform", "DER",
        ],
        input=root_hash.encode(),
        capture_output=True,
        check=True,
    ).stdout
    der = subprocess.run(
        ["openssl", "x509", "-in", str(certificate), "-outform", "DER"],
        capture_output=True, check=True,
    ).stdout
    payload = json.dumps(
        {
            "rootHash": root_hash,
            "certificateFingerprint": hashlib.sha256(der).hexdigest(),
            "signature": base64.b64encode(signature).decode(),
        },
        separators=(",", ":"),
    ).encode()
    if len(payload) > length:
        raise SystemExit("measure-substitution: rebuilt signature exceeds its partition")
    return payload + bytes(length - len(payload))


def verify_reconstruction(artifact: Path, entries: dict[str, Any], keys: Path) -> dict[str, Any]:
    """Whether this harness can rebuild the artifact's own signature blob.

    Three things are checked and the third is the one that matters. The
    certificate fingerprint must match the artifact's. The artifact's own
    signature must verify against its root hash under the enrolled certificate
    -- measured, so that a later failure to verify the rebuilt one is
    attributable to the rebuild rather than to a wrong assumption about what was
    signed. And the rebuilt signature must verify the same way.

    Byte equality is deliberately not required; see `sig_blob`.
    """
    original = json.loads(partition_bytes(artifact, entries[SIG]).rstrip(b"\0"))
    rebuilt = json.loads(
        sig_blob(
            original["rootHash"],
            keys / "verity.crt",
            keys / "verity.key",
            entries[SIG]["length"],
        ).rstrip(b"\0")
    )
    return {
        "certificate_fingerprint_matches": (
            rebuilt["certificateFingerprint"] == original["certificateFingerprint"]
        ),
        "artifact_signature_verifies": cms_verifies(
            original["signature"], original["rootHash"], keys / "verity.crt"
        ),
        "rebuilt_signature_verifies": cms_verifies(
            rebuilt["signature"], original["rootHash"], keys / "verity.crt"
        ),
        "rebuilt_signature_bytes_match": rebuilt["signature"] == original["signature"],
        "root_hash": original["rootHash"],
    }


def cms_verifies(signature_base64: str, root_hash: str, certificate: Path) -> bool:
    """Whether a detached CMS signature covers this root hash under this signer.

    `-purpose any` and `-CAfile` on a self-signed synthetic certificate: the
    question is whether the bytes are signed by that key over that content, not
    whether a synthetic authority is fit to be a CA.
    """
    with tempfile.NamedTemporaryFile(suffix=".der") as signature, \
            tempfile.NamedTemporaryFile(suffix=".txt") as content:
        signature.write(base64.b64decode(signature_base64))
        signature.flush()
        content.write(root_hash.encode())
        content.flush()
        return subprocess.run(
            [
                "openssl", "cms", "-verify", "-inform", "DER",
                "-in", signature.name, "-content", content.name, "-binary",
                "-CAfile", str(certificate), "-purpose", "any", "-out", os.devnull,
            ],
            capture_output=True, check=False,
        ).returncode == 0


def uki_root_hash(uki: Path) -> str:
    matches = set(re.findall(rb"usrhash=([0-9a-f]{64})", uki.read_bytes()))
    if len(matches) != 1:
        raise SystemExit(
            f"measure-substitution: expected exactly one usrhash in {uki}, "
            f"found {len(matches)}"
        )
    return matches.pop().decode()


def build_cell(
    name: str,
    arm: str,
    build_root: Path,
    scratch: Path,
    reconstruction: dict[str, Any],
) -> dict[str, Any]:
    """One substituted disk, and the record of exactly what moved.

    Cells split into two shapes and the split is forced by geometry, not by
    taste. The content variant is genuinely larger -- eight sectors on EROFS,
    twenty-four on ext4 -- so it cannot be spliced into the primary's slot
    without truncation. It can be the *base*, with the primary's ESP spliced into
    it, because the ESP is 512 MiB in all six. The seed variant is byte-for-byte
    the same size as its primary, so it can be either.
    """
    primary = build_root / ARMS[arm] / "neutrinos-slice.raw"
    primary_table = table(primary)
    disk = scratch / f"{arm}-{name}.raw"
    record: dict[str, Any] = {"cell": name, "arm": arm}

    if name == "baseline":
        shutil.copy(primary, disk)
        record["what_moved"] = "nothing; the unmodified primary"

    elif name in ("pair-content", "pair-seed"):
        variant = name.split("-", 1)[1]
        donor = build_root / f"{ARMS[arm]}-{variant}" / "neutrinos-slice.raw"
        donor_table = table(donor)
        shutil.copy(donor, disk)
        splice(disk, donor_table[ESP], primary, primary_table[ESP])
        record.update({
            "donor": str(donor),
            "what_moved": (
                "the whole disk is the donor's -- /usr, its Verity tree, its "
                "signature partition and their GPT identities -- with the "
                "primary's ESP, and therefore the primary's signed UKI, spliced "
                "over the donor's"
            ),
            "donor_usr_uuid": donor_table[USR]["uuid"],
            "donor_verity_uuid": donor_table[VERITY]["uuid"],
            "uki_names_root_hash": reconstruction["root_hash"],
        })

    elif name in ("usr-only", "verity-only", "sig-foreign"):
        donor = build_root / f"{ARMS[arm]}-seed" / "neutrinos-slice.raw"
        donor_table = table(donor)
        moved = {"usr-only": USR, "verity-only": VERITY, "sig-foreign": SIG}[name]
        shutil.copy(primary, disk)
        splice(disk, primary_table[moved], donor, donor_table[moved])
        record.update({
            "donor": str(donor),
            "partition_substituted": moved,
            "what_moved": (
                f"the seed variant's {moved} bytes, into the primary's slot and "
                "under the primary's GPT identity; everything else is the primary's"
            ),
        })

    elif name in ("sig-wrong-key", "sig-rebuilt-enrolled"):
        keys = build_root / "keys"
        signer = "verity-wrong" if name == "sig-wrong-key" else "verity"
        shutil.copy(primary, disk)
        blob = sig_blob(
            reconstruction["root_hash"],
            keys / f"{signer}.crt",
            keys / f"{signer}.key",
            primary_table[SIG]["length"],
        )
        with disk.open("r+b") as handle:
            handle.seek(primary_table[SIG]["offset"])
            handle.write(blob)
        record.update({
            "what_moved": (
                "the signature partition only: the primary's own root hash, "
                f"re-signed by {signer}. The image and its root hash are untouched"
            )
            + (
                ", and this signer is valid and in no machine's db"
                if signer == "verity-wrong"
                else ", by the enrolled signer -- this is the control for the "
                "wrong-key cell, and its only difference from the artifact's own "
                "blob is how this harness encodes it"
            ),
            "signer": signer,
        })

    else:
        raise SystemExit(f"measure-substitution: unknown cell {name}")

    record["disk"] = disk
    return record


def report_fields(text: str) -> dict[str, str]:
    """The probe's report, keyed only on the fields the probe emits.

    Partitioning every line on its first `=` was the first implementation and it
    is wrong on this console: kernel audit records and the terminal's own OSC
    sequences interleave with the probe's output and carry `=` themselves, so
    the report came back holding an audit line as a key. Only the declared keys
    are read, and each is taken from the last occurrence -- a line the kernel
    split across an audit record would otherwise be read from its truncated
    half.
    """
    if MARKER_BEGIN not in text or MARKER_END not in text:
        return {}
    body = text.split(MARKER_BEGIN, 1)[1].split(MARKER_END, 1)[0]
    fields: dict[str, str] = {}
    for key in PROBE_KEYS:
        matches = re.findall(rf"(?m)^(?:.*?\b)?{re.escape(key)}=(.*)$", body)
        if matches:
            fields[key] = CONSOLE_PREFIX.sub("", matches[-1].strip()).strip()
    return fields


def one_boot(
    disk: Path, work: Path, store: Path, secure_boot: bool, serial: Path
) -> dict[str, Any]:
    """Boot one substituted disk once, under one firmware state.

    The two TPM units PLN-0002-08 and -09 masked are masked here too, and for
    the same reason: the artifact ships no `tpm2-pcr-public-key.pem` and
    supplying one is TPM policy, which this plan excludes. The mask travels in
    the record rather than in a comment, because a boot measured under a mask is
    a different boot.
    """
    work.mkdir(parents=True, exist_ok=True)
    tpm_state = work / "tpm"
    tpm_state.mkdir(mode=0o700)
    with vm.software_tpm(tpm_state) as tpm_socket:
        text = vm.boot(
            disk,
            work=work,
            store=store,
            secure_boot=secure_boot,
            credentials={
                "firstboot.locale": "C.UTF-8",
                "firstboot.timezone": "UTC",
                "system.hostname": "slice-pln0002-10",
                "passwd.hashed-password.root": "!*",
            },
            credential_files=[
                vm.credential_file(work, "systemd.extra-unit.pln0002-10.service", PROBE_UNIT),
                vm.credential_file(work, "systemd.extra-unit.pln0002-10.timer", PROBE_TIMER),
                vm.credential_file(
                    work,
                    "systemd.unit-dropin.timers.target",
                    "[Unit]\nWants=pln0002-10.timer\n",
                ),
            ],
            tpm_socket=tpm_socket,
            cmdline_extra=[
                f"systemd.mask={unit} rd.systemd.mask={unit}" for unit in MASKED_UNITS
            ],
            timeout_seconds=BOOT_TIMEOUT_SECONDS,
        )
    text = strip_control(text)
    serial.parent.mkdir(parents=True, exist_ok=True)
    serial.write_text(text)
    fields = report_fields(text)
    return {
        "booted_to_userspace": bool(fields),
        "probe": fields,
        "console_diagnostic_lines": [
            CONSOLE_PREFIX.sub("", line.strip())
            for line in text.splitlines()
            if DIAGNOSTIC.search(line)
        ][-60:],
        "console_unit_failure_lines": sorted(
            {line.strip() for line in text.splitlines() if UNIT_FAILURE.search(line)}
        ),
        "masked_units": list(MASKED_UNITS),
        "serial_log": str(serial),
        "serial_log_bytes": len(text),
    }


def assess(cell: str, firmware: str, run: dict[str, Any]) -> list[str]:
    """Where the measurement disagrees with itself.

    Not where it disagrees with a prediction. A substituted deployment that
    boots is this task's expected finding and is reported as a finding, never as
    a failure of the harness. What is checked is that the harness could have
    seen the other outcome: the baseline must boot, and an enrolled cell that
    reaches userspace must report Secure Boot actually on -- the defect that hid
    for a whole spike.
    """
    problems: list[str] = []
    probe = run["probe"]
    if cell == "baseline" and not run["booted_to_userspace"]:
        problems.append(
            "the unmodified primary did not reach the probe, so no negative cell "
            "in this firmware state is attributable to the substitution"
        )
    if firmware == "enrolled" and run["booted_to_userspace"]:
        if probe.get("secure-boot") != "1":
            problems.append(
                f"SecureBoot reported {probe.get('secure-boot', 'nothing')!r} under the "
                "enrolled firmware, so this cell measures the plain state twice"
            )
        if probe.get("platform-keys", "0") == "0":
            problems.append("no certificates in any kernel keyring under enrolled firmware")
    if run["booted_to_userspace"]:
        if probe.get("usr-source", "") == "":
            problems.append("the guest reached userspace with no /usr mount reported")
        # An empty system state is the first full run's defect and must not
        # come back silently: a cell that boots is this task's finding, and a
        # finding recorded without the state of the machine it was found on is
        # the fail-open shape one level up.
        if probe.get("system-state", "") == "":
            problems.append("the guest booted but reported no system state")
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
    }


CELLS = (
    "baseline",
    "pair-content",
    "pair-seed",
    "usr-only",
    "verity-only",
    "sig-foreign",
    "sig-rebuilt-enrolled",
    "sig-wrong-key",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--build-root",
        type=Path,
        default=default_build_root(),
    )
    parser.add_argument("--arm", choices=sorted(ARMS), action="append", default=None)
    parser.add_argument("--cell", choices=CELLS, action="append", default=None)
    parser.add_argument(
        "--firmware", choices=("plain", "enrolled"), action="append", default=None
    )
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--output", type=Path, default=None)
    arguments = parser.parse_args()

    build_root: Path = arguments.build_root
    arms = arguments.arm or sorted(ARMS)
    cells = arguments.cell or list(CELLS)
    firmwares = arguments.firmware or ["plain", "enrolled"]
    output = arguments.output or build_root / "evidence/pln0002-10/substitution.json"
    serial_dir = output.parent / "serial"

    # Every artifact this run reads, primary and donor alike, digested before and
    # after. The claim that the accepted set is unmodified is the one claim this
    # harness makes about the artifacts themselves, so it is measured.
    originals: dict[str, str] = {}
    for arm in arms:
        for directory in (ARMS[arm], *(f"{ARMS[arm]}-{v}" for v in VARIANTS)):
            path = build_root / directory / "neutrinos-slice.raw"
            if not path.is_file():
                print(f"measure-substitution: no artifact at {path}", file=sys.stderr)
                return 1
            originals[str(path)] = file_digest(path)

    results: list[dict[str, Any]] = []
    # Scratch lives in the build root, not in the system temporary directory.
    # `/tmp` here is a 32 GB tmpfs and a cell's disk is a full ~750 MB copy of an
    # artifact: the first full run of this matrix stopped on a quota error
    # mid-way, which is a harness failure that looks like a measurement failure.
    # The build root is a declared development location with the room.
    #
    # The prefix is short, and that is not tidiness. The vTPM's control socket
    # lives under this directory and a UNIX socket path is limited to 108 bytes;
    # a descriptive scratch name plus a descriptive per-cell name went over it,
    # and `vm.software_tpm` refused. Names below are shortened for the same
    # reason.
    with tempfile.TemporaryDirectory(prefix="p10-", dir=build_root) as raw:
        scratch = Path(raw)

        reconstruction: dict[str, dict[str, Any]] = {}
        for arm in arms:
            primary = build_root / ARMS[arm] / "neutrinos-slice.raw"
            entries = table(primary)
            check = verify_reconstruction(primary, entries, build_root / "keys")
            check["uki_root_hash"] = uki_root_hash(
                build_root / ARMS[arm] / "neutrinos-slice.efi"
            )
            reconstruction[arm] = check
            rebuilds = {"sig-wrong-key", "sig-rebuilt-enrolled"} & set(cells)
            if rebuilds and not (
                check["certificate_fingerprint_matches"]
                and check["artifact_signature_verifies"]
                and check["rebuilt_signature_verifies"]
            ):
                print(
                    "measure-substitution: this harness cannot produce a signature over "
                    f"the {arm} artifact's root hash that verifies the way the "
                    "artifact's own does, so a blob built with the wrong key would "
                    "differ in more than the signer and the cell would not measure what "
                    "it claims",
                    file=sys.stderr,
                )
                return 1
            if check["root_hash"] != check["uki_root_hash"]:
                print(
                    f"measure-substitution: the {arm} signature partition names "
                    f"{check['root_hash'][:16]}… and its UKI names "
                    f"{check['uki_root_hash'][:16]}…",
                    file=sys.stderr,
                )
                return 1

        # One enrolled variable store, made once and then read copy-on-write, as
        # T4-CONFEXT-001 does. The first boot of a fresh store is the enrolment
        # and produces a store rather than a report, so it is a warm-up and is
        # not measured. It runs off the fixture artifact, whose ESP carries the
        # auto-enrolment keys; the cells' own ESPs carry none, which is why no
        # cell disk needs to be touched to reach the enrolled state.
        enrolled_store: Path | None = None
        if "enrolled" in firmwares:
            fixture = build_root / "fixture/enrolled-artifact.raw"
            if not fixture.is_file():
                print(
                    f"measure-substitution: no enrolment fixture at {fixture}; "
                    "compose.sh builds it",
                    file=sys.stderr,
                )
                return 1
            _, variables = vm.firmware_pair(secure_boot=True)
            enrolled_store = scratch / "OVMF_VARS.enrolled.fd"
            shutil.copyfile(variables, enrolled_store)
            enrolled_store.chmod(0o600)
            warmup = scratch / "warmup"
            warmup.mkdir()
            vm.boot(
                fixture,
                work=warmup,
                store=enrolled_store,
                secure_boot=True,
                persist_store=True,
                timeout_seconds=BOOT_TIMEOUT_SECONDS,
            )
            enrolled_digest = file_digest(enrolled_store)

        plain_store: Path | None = None
        if "plain" in firmwares:
            _, variables = vm.firmware_pair(secure_boot=False)
            plain_store = scratch / "OVMF_VARS.plain.fd"
            shutil.copyfile(variables, plain_store)
            plain_store.chmod(0o600)

        def run_one(item: tuple[dict[str, Any], str]) -> dict[str, Any]:
            built, firmware = item
            tag = f"{built['arm']}-{built['cell']}-{firmware}"
            store = enrolled_store if firmware == "enrolled" else plain_store
            assert store is not None
            run = one_boot(
                built["disk"],
                scratch / f"w-{tag}",
                store,
                firmware == "enrolled",
                serial_dir / f"{tag}.log",
            )
            record = {key: value for key, value in built.items() if key != "disk"}
            record["firmware"] = firmware
            record["run"] = run
            record["problems"] = assess(built["cell"], firmware, run)
            print(
                f"{tag}: booted={run['booted_to_userspace']} "
                f"usr={run['probe'].get('usr-source', '-')} "
                f"state={run['probe'].get('system-state', '-')} "
                f"marker={run['probe'].get('variant-marker', '-')}",
                flush=True,
            )
            return record

        # One cell at a time, its firmware states in parallel, and the disk
        # deleted before the next cell is built. Building all sixteen up front
        # was the first shape and it filled the filesystem: each is a full copy
        # of a ~750 MB artifact. Peak cost is now one cell's disk rather than
        # the matrix's.
        with ThreadPoolExecutor(max_workers=max(1, arguments.jobs)) as pool:
            for arm in arms:
                for cell in cells:
                    built = build_cell(cell, arm, build_root, scratch, reconstruction[arm])
                    results.extend(
                        pool.map(run_one, [(built, firmware) for firmware in firmwares])
                    )
                    built["disk"].unlink()

        if enrolled_store is not None and file_digest(enrolled_store) != enrolled_digest:
            results.append({
                "cell": "harness",
                "problems": [
                    "the shared enrolled variable store changed during the run, so the "
                    "cells were not independent"
                ],
            })

    unchanged = {path: file_digest(Path(path)) == digest for path, digest in originals.items()}

    record = {
        "task": "PLN-0002-10",
        "measured": datetime.now().astimezone().isoformat(timespec="seconds"),
        "build_root": str(build_root),
        "environment": environment(),
        "artifacts_unchanged": unchanged,
        "signature_reconstruction": reconstruction,
        "cells": results,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2, sort_keys=True, default=str) + "\n")
    print(f"measure-substitution: wrote {output}")

    failed = not all(unchanged.values())
    if failed:
        print("measure-substitution: an accepted artifact changed", file=sys.stderr)
    for entry in results:
        for problem in entry.get("problems", []):
            failed = True
            print(f"{entry.get('arm', '-')}/{entry['cell']}: {problem}", file=sys.stderr)
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
