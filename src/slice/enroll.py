#!/usr/bin/env python3
"""Build the signature-enforcement fixture for T4-CONFEXT-001.

Needs firmware that trusts the confext signer, and needs the artifact to stay
byte-identical because T3-SLICE-001 and T4-SLICE-001 assert that. So it never
touches the artifact: it copies and enrolls into the copy.

Through the ESP rather than from inside the guest, which cannot do it --
efivarfs marks existing variables immutable and the artifact carries no
`chattr`. systemd-boot auto-enrolls `PK.auth`, `KEK.auth` and `db.auth` from
`\\loader\\keys\\auto` on firmware in setup mode, which a fresh store always is.

All three keys synthetic, enrolled nowhere but a disposable VM's variable
store, destroyed with the build root. What is measured is whether an unenrolled
signer is refused, not whose key does the enrolling.

This was 128 lines of shell. Four of its guards were fail-open and are closed
here, each noted where it stood:

  - directory creation on the ESP suppressed every error, not only "exists"
  - the image DER was guarded by existence, so an image-certificate change
    left the previous signer in `db` and the enrollment reported success
  - `platform.crt` was used to sign the variable updates and never guarded
  - a missing `uuidgen` produced a nil owner GUID rather than a failure
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path

from common import default_build_root, digest

# The ESP's GPT type GUID. Compared case-insensitively because sfdisk reports it
# uppercase and the constant reads better lowered.
ESP_TYPE = "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"

# The variables systemd-boot auto-enrolls, and which signature list each one
# carries. PK and KEK carry the platform key; db carries the image signer and
# the verity signer.
VARIABLES = (("PK", "pk"), ("KEK", "pk"), ("db", "db"))

TOOLS = ("sbsiglist", "sbvarsign", "mcopy", "mmd", "mdir", "sfdisk", "openssl")

# Fixed name: T4-CONFEXT-001 consumes this directory as a declared capability,
# and a name varying with the artifact would make it guess.
FIXTURE_NAME = "enrolled-artifact.raw"


def esp_offset(table: dict) -> int:
    """Byte offset of the ESP in an sfdisk `--json` partition table.

    Read from the artifact's own table rather than assumed. It has moved once
    already between the spike and the slice, and a wrong offset writes into a
    filesystem that is not the ESP.
    """
    partitions = table["partitiontable"]
    sector = partitions.get("sectorsize", 512)
    for partition in partitions.get("partitions", ()):
        if partition["type"].lower() == ESP_TYPE:
            return partition["start"] * sector
    raise SystemExit("enroll: no ESP in the artifact's partition table")


def read_partition_table(image: Path) -> dict:
    result = subprocess.run(
        ["sfdisk", "--json", str(image)],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def der(certificate: Path, output: Path) -> Path:
    """Convert one PEM certificate to the DER a UEFI signature list takes.

    Unconditional, and written beside the fixture rather than into the shared
    keys directory. Both are fixes. The image DER used to be guarded by
    existence in `keys/`, so pointing `NEUTRINOS_ENROLL_IMAGE_CERT` at a second
    certificate re-used the first one's DER and enrolled the wrong signer while
    reporting success; and `verity-wrong`'s DER landing on `verity.der` would
    corrupt the shared directory for every later run.
    """
    subprocess.run(
        ["openssl", "x509", "-outform", "DER", "-in", str(certificate), "-out", str(output)],
        check=True, capture_output=True,
    )
    return output


def signature_list(owner: str, certificate_der: Path, output: Path) -> Path:
    subprocess.run(
        ["sbsiglist", "--owner", owner, "--type", "x509",
         "--output", str(output), str(certificate_der)],
        check=True,
    )
    return output


def make_directory(image: Path, offset: int, path: str) -> None:
    """Create one directory on the ESP, tolerating only that it already exists.

    `mmd ... 2>/dev/null || true` stood here, which suppressed every error --
    a wrong offset, an unwritable image, a full filesystem -- and let the
    `mcopy` below fail on a path that was never created. Existence is tested
    rather than inferred from a failure, so every other failure raises.
    """
    location = f"{image}@@{offset}"
    probe = subprocess.run(
        ["mdir", "-i", location, f"::{path}"], check=False, capture_output=True
    )
    if probe.returncode == 0:
        return
    subprocess.run(["mmd", "-i", location, f"::{path}"], check=True)


def require(paths: dict[Path, str]) -> None:
    """Stop on every missing input at once, naming what generates it."""
    missing = [f"{path}: {reason}" for path, reason in paths.items() if not path.is_file()]
    if missing:
        raise SystemExit("enroll: " + "\n       ".join(missing))


def enroll(
    build_root: Path | None = None,
    *,
    artifact: Path | None = None,
    fixture_dir: Path | None = None,
    image_cert: Path | None = None,
    verity_cert: Path | None = None,
) -> Path:
    """Copy the artifact and enroll the synthetic keys into the copy's ESP.

    Every input is overridable, so the same enrollment runs against the
    PLN-0002-01 spike artifact without a slice composition, and so the negative
    fixture -- `db` trusting a different authority -- needs no second program to
    drift from this one. PLN-0002-06's image-policy matrix passes
    `verity-wrong.crt`.
    """
    environment = os.environ
    build_root = build_root or default_build_root()
    keys = build_root / "keys"
    artifact = artifact or Path(
        environment.get("NEUTRINOS_ENROLL_ARTIFACT")
        or build_root / "out" / "neutrinos-slice.raw"
    )
    fixture_dir = fixture_dir or Path(
        environment.get("NEUTRINOS_ENROLL_FIXTURE_DIR") or build_root / "fixture"
    )
    image_cert = image_cert or Path(
        environment.get("NEUTRINOS_ENROLL_IMAGE_CERT") or keys / "secureboot.crt"
    )
    verity_cert = verity_cert or Path(
        environment.get("NEUTRINOS_ENROLL_VERITY_CERT") or keys / "verity.crt"
    )

    unavailable = [tool for tool in TOOLS if shutil.which(tool) is None]
    if unavailable:
        # All of them, not the first. The shell loop reported one per run, so
        # provisioning a host took as many runs as it had gaps.
        raise SystemExit(f"enroll: unavailable on PATH: {', '.join(unavailable)}")

    require({
        artifact: "no artifact to enroll into",
        # Not optional: db with the verity certificate alone is a machine whose
        # firmware refuses its own UKI and times out with no console --
        # measured, by the first fixture built here.
        image_cert: "no image-signing certificate; db without it produces an "
                    "unbootable machine",
        verity_cert: "no verity certificate; buildroot.py generates it",
        # The platform key signs the variable updates and is enrolled as PK,
        # taking the firmware out of setup mode. All three parts are guarded:
        # `platform.crt` was used by sbvarsign and checked by nothing.
        keys / "platform.key": "no platform key; buildroot.py generates it",
        keys / "platform.crt": "no platform certificate; buildroot.py generates it",
        keys / "platform.der": "no platform DER; buildroot.py generates it",
    })

    fixture_dir.mkdir(parents=True, exist_ok=True)
    fixture = fixture_dir / FIXTURE_NAME

    # A real GUID or a failure. `uuidgen 2>/dev/null || echo 0000...` stood
    # here, which made every signature list on a host without uuidgen claim the
    # nil owner, and nothing downstream would have said so.
    owner = str(uuid.uuid4())

    image_esl = signature_list(
        owner, der(image_cert, fixture_dir / "image.der"), fixture_dir / "image.esl"
    )
    verity_esl = signature_list(
        owner, der(verity_cert, fixture_dir / "verity.der"), fixture_dir / "verity.esl"
    )
    # A signature list is a concatenation of lists, so db is built by appending
    # rather than by re-signing one combined certificate. The second verity key
    # is absent from db, and that absence is the measurement: a confext signed
    # with it carries a valid signature by an untrusted authority.
    db_esl = fixture_dir / "db.esl"
    db_esl.write_bytes(image_esl.read_bytes() + verity_esl.read_bytes())
    pk_esl = signature_list(owner, keys / "platform.der", fixture_dir / "pk.esl")

    # Signed with the platform key. Setup mode accepts the update without
    # verifying the signature, but the structure is still required -- an
    # unsigned payload is rejected as malformed.
    lists = {"db": db_esl, "pk": pk_esl}
    for variable, which in VARIABLES:
        subprocess.run(
            ["sbvarsign",
             "--key", str(keys / "platform.key"),
             "--cert", str(keys / "platform.crt"),
             "--output", str(fixture_dir / f"{variable}.auth"),
             variable, str(lists[which])],
            check=True,
        )

    subprocess.run(
        ["cp", "--reflink=auto", str(artifact), str(fixture)], check=True
    )

    offset = esp_offset(read_partition_table(fixture))
    location = f"{fixture}@@{offset}"
    for path in ("/loader", "/loader/keys", "/loader/keys/auto"):
        make_directory(fixture, offset, path)
    for variable, _ in VARIABLES:
        subprocess.run(
            ["mcopy", "-o", "-i", location, str(fixture_dir / f"{variable}.auth"),
             f"::/loader/keys/auto/{variable}.auth"],
            check=True,
        )

    # Build-side proof that the copy differs only as intended and the artifact
    # was not touched. Nothing reads either today; they are evidence, in the
    # format `sha256sum -c` takes.
    subprocess.run(["mdir", "-i", location, "::/loader/keys/auto"], check=True)
    (fixture_dir / "artifact.sha256").write_text(
        f"{digest(artifact)}  {artifact}\n", encoding="utf-8"
    )
    print(f"enroll: wrote {fixture}")
    return fixture
