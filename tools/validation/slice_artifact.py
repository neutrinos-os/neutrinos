"""T3 static inspection of the composed slice artifact.

This asks whether the shipped bytes are the bytes the declaration describes,
without booting anything. Its central assertion is the one PLN-0001-04 made by
hand and by hand only: the UKI stored on the ESP inside the disk image is
byte-identical to the standalone UKI composition emitted. Those two files have
different names, so nothing but their content can establish that the machine
would boot what was built.

The artifact is declared through the environment rather than built here.
Composition needs the network and a package repository; canonical validation is
offline. An absent artifact blocks this test, it does not skip it.
"""

from __future__ import annotations

import hashlib
import base64
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
import tomllib
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
INPUT_SET = ROOT / "src" / "slice" / "input-set.toml"
SECTOR_BYTES = 512
GPT_HEADER_LBA = 1
GPT_SIGNATURE = b"EFI PART"
REQUIRED_UKI_SECTIONS = (".linux", ".initrd", ".osrel", ".uname")
READ_CHUNK_BYTES = 4 * 1024 * 1024


def gpt_partitions(image: Path) -> list[dict[str, Any]]:
    """Every GPT entry, read from the table rather than assumed.

    Hard-coding offsets would pass today and silently inspect the wrong region
    the first time the partition layout changes. Both UUIDs are decoded
    `bytes_le`, which is the on-disk mixed-endian encoding: reading them any
    other way produces a plausible-looking UUID that matches nothing.
    """
    partitions: list[dict[str, Any]] = []
    with image.open("rb") as stream:
        stream.seek(GPT_HEADER_LBA * SECTOR_BYTES)
        header = stream.read(92)
        if header[:8] != GPT_SIGNATURE:
            raise ValueError("image has no GPT header")
        entries_lba = struct.unpack("<Q", header[72:80])[0]
        entry_count = struct.unpack("<I", header[80:84])[0]
        entry_size = struct.unpack("<I", header[84:88])[0]
        stream.seek(entries_lba * SECTOR_BYTES)
        for _ in range(entry_count):
            entry = stream.read(entry_size)
            if entry[:16] == bytes(16):
                continue
            first = struct.unpack("<Q", entry[32:40])[0]
            last = struct.unpack("<Q", entry[40:48])[0]
            partitions.append(
                {
                    "name": entry[56:128].decode("utf-16-le").rstrip("\0"),
                    "type_uuid": str(uuid.UUID(bytes_le=entry[:16])),
                    "uuid": str(uuid.UUID(bytes_le=entry[16:32])),
                    "offset_bytes": first * SECTOR_BYTES,
                    # GPT last-LBA is inclusive.
                    "size_bytes": (last - first + 1) * SECTOR_BYTES,
                }
            )
    return partitions


def esp_offset_bytes(image: Path) -> int:
    """Byte offset of the ESP."""
    for partition in gpt_partitions(image):
        if partition["name"] == "esp":
            return int(partition["offset_bytes"])
    raise ValueError("image has no partition named esp")


def fat_entries(image: Path, offset: int, directory: str) -> list[str]:
    result = subprocess.run(
        ("mdir", "-b", "-i", f"{image}@@{offset}", f"::{directory}"),
        check=False,
        env={**os.environ, "MTOOLS_SKIP_CHECK": "1"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise ValueError(f"cannot list {directory} on the ESP: {result.stderr.strip()}")
    # `mdir -b` prints full `::/path` names; the caller wants leaf names.
    return [
        line.strip().rsplit("/", 1)[-1]
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def fat_file_digest(image: Path, offset: int, path: str) -> str:
    digest = hashlib.sha256()
    with subprocess.Popen(
        ("mtype", "-i", f"{image}@@{offset}", f"::{path}"),
        env={**os.environ, "MTOOLS_SKIP_CHECK": "1"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as process:
        assert process.stdout is not None
        while chunk := process.stdout.read(READ_CHUNK_BYTES):
            digest.update(chunk)
        if process.wait() != 0:
            raise ValueError(f"cannot read {path} from the ESP")
    return digest.hexdigest()


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(READ_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def pe_sections(path: Path) -> dict[str, tuple[int, int]]:
    """Section name to (file offset, size) for a PE image."""
    with path.open("rb") as stream:
        if stream.read(2) != b"MZ":
            raise ValueError("UKI is not a PE image")
        stream.seek(0x3C)
        pe_offset = struct.unpack("<I", stream.read(4))[0]
        stream.seek(pe_offset)
        if stream.read(4) != b"PE\0\0":
            raise ValueError("UKI has no PE signature")
        coff = stream.read(20)
        section_count = struct.unpack("<H", coff[2:4])[0]
        optional_size = struct.unpack("<H", coff[16:18])[0]
        stream.seek(pe_offset + 24 + optional_size)
        sections: dict[str, tuple[int, int]] = {}
        for _ in range(section_count):
            raw = stream.read(40)
            name = raw[:8].rstrip(b"\0").decode("ascii", errors="replace")
            size = struct.unpack("<I", raw[16:20])[0]
            offset = struct.unpack("<I", raw[20:24])[0]
            sections[name] = (offset, size)
    return sections


def section_text(path: Path, span: tuple[int, int]) -> str:
    offset, size = span
    with path.open("rb") as stream:
        stream.seek(offset)
        return stream.read(size).rstrip(b"\0").decode("utf-8", errors="replace").strip()


def check_artifact() -> int:
    from tools.validation.check import SLICE_ARTIFACT_ENV

    directory = Path(os.environ[SLICE_ARTIFACT_ENV]).resolve()
    image = directory / "neutrinos-slice.raw"
    uki = directory / "neutrinos-slice.efi"
    manifest_path = directory / "neutrinos-slice.manifest"
    declared = tomllib.loads(INPUT_SET.read_text(encoding="utf-8"))
    failures: list[str] = []

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    config = manifest.get("config", {})
    packages = manifest.get("packages", [])
    for field, expected in (
        ("distribution", declared["packages"]["distribution"]),
        ("release", declared["packages"]["release"]),
        ("architecture", declared["packages"]["architecture"]),
        ("output_format", "disk"),
    ):
        # The builder and the package ecosystem spell the same architecture
        # differently -- mkosi writes `x86-64`, RPM writes `x86_64`. Comparing
        # them literally would fail on a naming convention rather than on an
        # input, so the separator is normalized. Nothing else is: a release or
        # distribution that differs by any character is a different input.
        observed = str(config.get(field))
        if observed.replace("-", "_") != str(expected).replace("-", "_"):
            failures.append(
                f"manifest {field} is {observed!r}, declaration says {expected!r}"
            )

    architectures = {declared["packages"]["architecture"], "noarch"}
    seen: set[tuple[str, str]] = set()
    for package in packages:
        identity = (str(package.get("name")), str(package.get("architecture")))
        # `gpg-pubkey` is a real member of the RPM database and a real part of
        # what the image trusts, but it is a key rather than a build, so it
        # carries no architecture. Excluding it from the architecture rule is
        # narrower than relaxing the rule for every entry.
        required = ("type", "name", "version")
        if package.get("name") != "gpg-pubkey":
            required += ("architecture",)
        if not all(package.get(field) for field in required):
            failures.append(f"manifest entry is not fully identified: {package!r}")
        elif package.get("architecture") and package["architecture"] not in architectures:
            failures.append(
                f"package {package['name']} has undeclared architecture "
                f"{package['architecture']}"
            )
        if identity in seen:
            failures.append(f"manifest lists {identity[0]} twice for {identity[1]}")
        seen.add(identity)
    if not packages:
        failures.append("manifest declares an empty package closure")

    sections = pe_sections(uki)
    missing = [name for name in REQUIRED_UKI_SECTIONS if name not in sections]
    if missing:
        failures.append(f"UKI is missing sections: {', '.join(missing)}")

    uname = section_text(uki, sections[".uname"]) if ".uname" in sections else ""
    kernel = next(
        (package for package in packages if package.get("name") == "kernel-core"), None
    )
    if kernel is None:
        failures.append("closure contains no kernel-core to bind the UKI to")
    else:
        expected_uname = f"{kernel['version']}.{kernel['architecture']}"
        if uname != expected_uname:
            failures.append(
                f"UKI .uname is {uname!r}; the closure's kernel-core is {expected_uname!r}"
            )

    offset = esp_offset_bytes(image)
    esp_entries = fat_entries(image, offset, "/EFI/Linux")
    if len(esp_entries) != 1:
        failures.append(
            f"ESP holds {len(esp_entries)} boot entries, not exactly one: {esp_entries}"
        )
    composed_digest = file_digest(uki)
    installed_digest = ""
    if esp_entries:
        installed_digest = fat_file_digest(image, offset, f"/EFI/Linux/{esp_entries[0]}")
        if installed_digest != composed_digest:
            failures.append(
                "the UKI on the ESP is not the composed UKI: "
                f"{installed_digest} on the ESP, {composed_digest} composed"
            )

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1

    report: dict[str, Any] = {
        "closure_packages": len(packages),
        "esp_boot_entry": esp_entries[0],
        "esp_offset_bytes": offset,
        "kernel_uname": uname,
        # The same bytes under two names. This is the whole point of the test.
        "uki_digest": composed_digest,
        "uki_matches_esp_copy": installed_digest == composed_digest,
        "uki_sections": sorted(sections),
        "result": "passing",
    }
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    return 0


# The certificate published beside the artifact by compose.sh. Read from the
# artifact directory rather than from a build root, so the directory carries its
# own provenance and a retained copy stays checkable after the build root is
# gone.
PUBLISHED_CERTIFICATE = "neutrinos-slice.verity.crt"


# Discovered Partition Specification type UUIDs for x86-64. Partitions are
# found by type rather than by the names this repository's repart definitions
# happen to give them, because the type is what systemd's own dissection reads:
# a check keyed on our labels would keep passing after a rename that stops the
# machine finding the partition at all.
DPS_USR_X86_64 = "8484680c-9521-48c6-9c11-b0720656f69e"
DPS_USR_VERITY_X86_64 = "77ff5f63-e7b6-4633-acf4-1565b864c0e6"
DPS_USR_VERITY_SIG_X86_64 = "e7bb33fb-06cf-4e81-8273-e543b413e2e2"
USRHASH = re.compile(r"usrhash=([0-9a-f]{64})\b", re.ASCII)


def cmdline_root_hash(uki: Path) -> str:
    """The root hash the UKI's own `.cmdline` section carries.

    Read from the PE section rather than by scanning the whole file, so the
    value is the one systemd-stub will hand the kernel and not a copy of it
    sitting somewhere else in the image -- the initrd, for one, contains the
    same string.
    """
    sections = pe_sections(uki)
    if ".cmdline" not in sections:
        raise ValueError("UKI carries no .cmdline section, so it names no root hash")
    matches = set(USRHASH.findall(section_text(uki, sections[".cmdline"])))
    if len(matches) != 1:
        raise ValueError(
            f"UKI .cmdline names {len(matches)} distinct usrhash values, not one"
        )
    return matches.pop()


def check_usr_verity_binding() -> int:
    """Assert the UKI, the partition table, and the verity signature name one artifact.

    The chain, each link failing separately:

    1. The UKI's signed `.cmdline` carries exactly one `usrhash=`.
    2. Its two halves are the `/usr` and `/usr`-verity partition UUIDs, which is
       how the Discovered Partition Specification binds a root hash to the
       partitions it covers. This is what lets the initrd find the right pair
       without being told; PLN-0002-10 measured every substitution that breaks
       it failing closed with a device-resolution diagnostic.
    3. The verity signature partition's payload names the same root hash.
    4. Its `certificateFingerprint` is the certificate published beside the
       artifact.
    5. The detached CMS signature over that root hash verifies against that
       certificate.

    What this establishes: these bytes were signed, by the key whose certificate
    ships with them, over the root hash this UKI will ask the kernel for. That
    is strictly more than `T3-SLICE-003`, which finds certificate bytes inside
    the image and says so.

    What it does not establish, stated because this plan's mechanisms have
    repeatedly failed open in exactly the gap between a check and its reading.
    First, it does not verify the hash tree against the data: an image whose
    `/usr` was replaced and whose UUIDs, root hash and signature were all
    reissued consistently passes here. `veritysetup verify` is that assertion
    and is measured under `src/slice/measure-corruption.py`. Second, trust is
    anchored on the certificate published beside the artifact, so this says the
    signature is *by that certificate*, never that any machine trusts it --
    PLN-0002-10 measured that an untrusted `/usr` verity signer does not stop
    the boot at all.
    """
    from tools.validation.check import SLICE_ARTIFACT_ENV

    directory = Path(os.environ[SLICE_ARTIFACT_ENV]).resolve()
    image = directory / "neutrinos-slice.raw"
    uki = directory / "neutrinos-slice.efi"
    certificate = directory / PUBLISHED_CERTIFICATE
    failures: list[str] = []

    if not certificate.is_file():
        print(
            f"{certificate} does not exist, so the signature cannot be checked "
            f"against anything; compose.sh publishes it on every run",
            file=sys.stderr,
        )
        return 1

    root_hash = cmdline_root_hash(uki)
    partitions = gpt_partitions(image)
    by_type: dict[str, list[dict[str, Any]]] = {}
    for partition in partitions:
        by_type.setdefault(str(partition["type_uuid"]), []).append(partition)

    found: dict[str, dict[str, Any]] = {}
    for label, type_uuid in (
        ("usr", DPS_USR_X86_64),
        ("verity", DPS_USR_VERITY_X86_64),
        ("verity-sig", DPS_USR_VERITY_SIG_X86_64),
    ):
        entries = by_type.get(type_uuid, [])
        if len(entries) != 1:
            failures.append(
                f"image holds {len(entries)} partitions of the {label} type "
                f"{type_uuid}, not exactly one"
            )
        else:
            found[label] = entries[0]

    # The DPS convention: the first half of the root hash is the /usr partition
    # UUID, the second half the verity partition UUID, both with the hyphens
    # removed. This is the binding, and it is why a substituted image cannot be
    # resolved by a UKI that names the original.
    for label, half in (("usr", root_hash[:32]), ("verity", root_hash[32:])):
        if label not in found:
            continue
        observed = str(found[label]["uuid"]).replace("-", "")
        if observed != half:
            failures.append(
                f"the {label} partition UUID is {found[label]['uuid']}, which is "
                f"not the matching half of the UKI's root hash ({half})"
            )

    payload: dict[str, Any] = {}
    if "verity-sig" in found:
        with image.open("rb") as stream:
            stream.seek(int(found["verity-sig"]["offset_bytes"]))
            raw = stream.read(int(found["verity-sig"]["size_bytes"]))
        try:
            payload = json.loads(raw.rstrip(b"\0").decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            failures.append(f"verity signature partition holds no JSON payload: {error}")

    if payload:
        if payload.get("rootHash") != root_hash:
            failures.append(
                f"the verity signature covers root hash {payload.get('rootHash')!r}; "
                f"the UKI asks for {root_hash!r}"
            )
        der = subprocess.run(
            ["openssl", "x509", "-outform", "DER", "-in", str(certificate)],
            check=True, stdout=subprocess.PIPE,
        ).stdout
        fingerprint = hashlib.sha256(der).hexdigest()
        if payload.get("certificateFingerprint") != fingerprint:
            failures.append(
                "the verity signature names certificate fingerprint "
                f"{payload.get('certificateFingerprint')!r}; the certificate "
                f"published beside the artifact is {fingerprint}"
            )
        with tempfile.TemporaryDirectory(prefix="neutrinos-verity-sig-") as raw_dir:
            work = Path(raw_dir)
            signature = work / "signature.der"
            content = work / "roothash"
            try:
                signature.write_bytes(base64.b64decode(payload.get("signature", "")))
            except (ValueError, TypeError) as error:
                failures.append(f"verity signature is not base64: {error}")
                signature.write_bytes(b"")
            # Signed over the ASCII root hash exactly as the payload spells it,
            # with no terminator: that is what systemd-veritysetup verifies.
            content.write_text(str(payload.get("rootHash", "")), encoding="utf-8")
            verified = subprocess.run(
                [
                    "openssl", "smime", "-verify", "-binary",
                    "-inform", "DER", "-in", str(signature),
                    "-content", str(content),
                    # The published certificate is both the signer and the
                    # anchor. Self-signed synthetic material has no chain to
                    # build, and `-purpose any` says so rather than letting a
                    # missing extension read as a signature failure.
                    "-certfile", str(certificate),
                    "-CAfile", str(certificate),
                    "-purpose", "any",
                    "-out", os.devnull,
                ],
                check=False, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
            )
            if verified.returncode != 0:
                failures.append(
                    "the verity signature does not verify against the published "
                    f"certificate: {verified.stderr.strip()}"
                )

            # The CMS structure carries its own copy of the signer certificate,
            # and verification does not read it: `-certfile` supplies the
            # trusted copy and OpenSSL matches the signer by issuer and serial.
            # Measured while establishing failure sensitivity -- a bit flipped
            # at offset 621, inside the embedded certificate, verified
            # successfully while flips at 900, 1100, 1210 and 1241 all failed.
            # Left uncovered that is a region of a signed artifact that can be
            # changed with nothing noticing, which is this plan's recurring
            # shape, so the embedded copy is compared rather than trusted.
            embedded = subprocess.run(
                ["openssl", "pkcs7", "-inform", "DER", "-in", str(signature),
                 "-print_certs", "-outform", "PEM"],
                check=False, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
            ).stdout
            embedded_fingerprints = set()
            for block in re.findall(
                r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----",
                embedded, re.DOTALL,
            ):
                converted = subprocess.run(
                    ["openssl", "x509", "-outform", "DER"],
                    input=block.encode(), check=False, stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                )
                if converted.returncode == 0:
                    embedded_fingerprints.add(hashlib.sha256(converted.stdout).hexdigest())
            if embedded_fingerprints != {fingerprint}:
                failures.append(
                    "the certificate embedded in the CMS signature is not the "
                    f"published one: embedded {sorted(embedded_fingerprints)}, "
                    f"published {fingerprint}"
                )

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "certificate_subject": subprocess.run(
                    ["openssl", "x509", "-noout", "-subject", "-in", str(certificate)],
                    check=True, stdout=subprocess.PIPE, text=True,
                ).stdout.strip(),
                "establishes": (
                    "the UKI's root hash, the /usr and verity partition UUIDs, and "
                    "a CMS signature by the published certificate all name one artifact"
                ),
                "does_not_establish": (
                    "that the hash tree covers this data, or that any machine "
                    "trusts the signer"
                ),
                "partition_names": {
                    label: found[label]["name"] for label in sorted(found)
                },
                "root_hash": root_hash,
                "root_hash_source": "UKI .cmdline section",
                "signature_bytes": len(base64.b64decode(payload["signature"])),
                "result": "passing",
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


def check_signing_material_current() -> int:
    """Assert the artifact was built with the signing material published beside it.

    The failure this exists for is an artifact that outlived its own signing
    key. Both build scripts guard key generation on the certificate existing, and
    mkosi declines to rebuild when the output exists, so regenerating the verity
    key and re-running the composition leaves a new certificate beside an image
    still carrying the old signature. Measured on 2026-08-12 while implementing
    PLN-0002 amendment 4: it read as success, because every check then available
    looked at the build root's certificate rather than at the image.

    The assertion is by content and needs no filesystem driver. compose.sh
    stages the verity certificate into `/usr/lib/verity.d` inside `/usr`, and
    EROFS stores a file that small contiguously and uncompressed, so the
    certificate's exact bytes appear in the image. Measured: the current
    certificate appears once and the superseded one does not appear at all.

    What this does and does not establish. It establishes that these image bytes
    were produced with this certificate, which is what makes a stale artifact
    visible. It is not a signature verification: it finds bytes, it does not
    check that anything was signed by the corresponding key, and it cannot until
    task 06 adds a verity signature partition to verify against.
    """
    from tools.validation.check import SLICE_ARTIFACT_ENV

    directory = Path(os.environ[SLICE_ARTIFACT_ENV]).resolve()
    image = directory / "neutrinos-slice.raw"
    certificate = directory / PUBLISHED_CERTIFICATE
    failures: list[str] = []

    if not certificate.is_file():
        # Blocking rather than passing quietly: an artifact directory with no
        # published certificate cannot answer the question this asks, and
        # answering "nothing is wrong" would be the same defect as the one under
        # test.
        print(
            f"{certificate} does not exist, so the artifact's signing material "
            f"cannot be identified; compose.sh publishes it on every run",
            file=sys.stderr,
        )
        return 1

    payload = certificate.read_bytes()
    occurrences = image.read_bytes().count(payload)
    if occurrences == 0:
        failures.append(
            f"the certificate published as {PUBLISHED_CERTIFICATE} does not "
            f"appear in {image.name}, so the image was not built with it. The "
            f"usual cause is a regenerated key with no rebuild: mkosi declines "
            f"to rebuild when the output already exists"
        )

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "artifact_digest": file_digest(image),
                "certificate_digest": hashlib.sha256(payload).hexdigest(),
                "certificate_occurrences": occurrences,
                "certificate_subject": subprocess.run(
                    ["openssl", "x509", "-noout", "-subject", "-in", str(certificate)],
                    check=True, stdout=subprocess.PIPE, text=True,
                ).stdout.strip(),
                # Named so the result is not read as more than it is.
                "establishes": "the image contains these certificate bytes",
                "does_not_establish": "that any signature was verified",
                "result": "passing",
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0
