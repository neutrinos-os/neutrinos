"""T2 conformance check for the state variant's declared machine identity.

The machine-id is declared in one place and derived into another, and neither
can be validated by looking at itself:

  slice_boot.py                   declares it and delivers it as an SMBIOS
                                  credential
  state-partitions/20-var.conf    carries a UUID derived from it

It used to be declared a third time, in compose.sh, which delivered nothing and
never read it -- a harness value living in a build script because that script
was once the only place to put one. The copy is gone with the script; the
deliverer declares it.

The Discoverable Partitions Specification requires a /var partition's UUID to be
HMAC-SHA256(key=machine-id, msg=the var GPT type UUID), truncated to 128 bits
with the version and variant bits set as for a v4 UUID. systemd-gpt-auto-
generator recomputes that and silently declines to mount a /var whose UUID does
not match. That is the failure this check exists for: it is not an error, not a
failed unit, and not a message anyone reads. The machine boots, /var is simply
not there, and every later boot writes to a tmpfs that disappears.

The derivation below was verified against systemd 261's own implementation --
`systemd-id128 machine-id -a 4d21b016-b534-45c2-a9fb-5c16e091fd2d` returns the
identical value for the same machine-id.

Not checked here, because neither is a property of the declaration: that /var
actually mounts in a booted guest, and that anything written to it survives.
Both need a composed state artifact and a VM, and belong to a T4 check.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOOT = ROOT / "tools" / "validation" / "slice_boot.py"
STATE_DIR = ROOT / "src" / "slice" / "composition" / "state-partitions"

# From the Discoverable Partitions Specification. Named rather than inlined so
# a reader can check it against the specification without decoding a literal.
GPT_TYPE_VAR = uuid.UUID("4d21b016-b534-45c2-a9fb-5c16e091fd2d")


def dps_partition_uuid(machine_id: str, gpt_type: uuid.UUID) -> uuid.UUID:
    digest = hmac.new(
        bytes.fromhex(machine_id), gpt_type.bytes, hashlib.sha256
    ).digest()
    octets = bytearray(digest[:16])
    octets[6] = (octets[6] & 0x0F) | 0x40
    octets[8] = (octets[8] & 0x3F) | 0x80
    return uuid.UUID(bytes=bytes(octets))


def _extract(path: Path, pattern: str, label: str, failures: list[str]) -> str | None:
    match = re.search(pattern, path.read_text(encoding="utf-8"), re.MULTILINE)
    if match is None:
        failures.append(f"{label} not found in {path.relative_to(ROOT)}")
        return None
    return match.group(1)


def check_state_volumes() -> int:
    failures: list[str] = []

    declared = _extract(
        BOOT,
        r'^HARNESS_MACHINE_ID = "([0-9a-f]{32})"$',
        "declared machine-id",
        failures,
    )
    var_conf = STATE_DIR / "20-var.conf"
    home_conf = STATE_DIR / "21-home.conf"
    for conf in (var_conf, home_conf):
        if not conf.is_file():
            failures.append(f"missing state partition definition {conf.relative_to(ROOT)}")

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1

    assert declared is not None

    # The declared-versus-delivered comparison that stood here is gone with the
    # second copy: one constant is both, so there is nothing left to disagree.
    # The derivation below is what the check now rests on, and it was always the
    # part that caught a silent failure -- a /var whose UUID does not match
    # simply does not mount, with no error and no failed unit.

    if declared == "0" * 32:
        # systemd treats an all-zero machine-id as unset, so the credential
        # would be ignored and the derivation below would be meaningless.
        failures.append("declared machine-id is all zeroes, which systemd treats as unset")

    var_text = var_conf.read_text(encoding="utf-8")
    written = _extract(var_conf, r"^UUID=([0-9a-fA-F-]{36})$", "var partition UUID", failures)
    expected = dps_partition_uuid(declared, GPT_TYPE_VAR)
    if written is not None and uuid.UUID(written) != expected:
        failures.append(
            f"20-var.conf declares UUID={written}, but the Discoverable Partitions "
            f"Specification derivation from machine-id {declared} gives {expected}. "
            "systemd-gpt-auto-generator would decline to mount /var, silently."
        )

    if not re.search(r"^Type=var$", var_text, re.MULTILINE):
        failures.append("20-var.conf does not declare Type=var, so the derived UUID governs nothing")

    home_text = home_conf.read_text(encoding="utf-8")
    if not re.search(r"^Type=home$", home_text, re.MULTILINE):
        failures.append("21-home.conf does not declare Type=home")
    if re.search(r"^UUID=", home_text, re.MULTILINE):
        # The specification puts no derivation constraint on /home, precisely so
        # a home volume can move between machines. A UUID here would either be
        # arbitrary or would import the /var constraint for no reason.
        failures.append(
            "21-home.conf declares a UUID; the specification constrains no /home "
            "partition UUID, so this either means nothing or wrongly pins the volume "
            "to one machine"
        )

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "delivered_by": str(BOOT.relative_to(ROOT)),
                "derived_var_uuid": str(expected),
                "gpt_type_var": str(GPT_TYPE_VAR),
                "result": "passing",
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(check_state_volumes())
