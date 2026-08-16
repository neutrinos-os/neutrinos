#!/usr/bin/env python3
"""Recovery affordances of both `/usr` artifact formats: PLN-0002-12.

What task 12 owes: **a disposition for DES-0006 verification item 2's recovery
criterion, and the `crypttab` element of its early-boot clause addressed against
the encryption non-goal.** This harness measures the part of that a format can
answer offline, so the disposition is evidence rather than argument. Results:
docs/project/artifact-recovery-disposition.md.

Two questions, both offline and neither of them a boot.

**Given a damaged authenticated `/usr`, what does the format's own tooling do?**
The checker (does it see the damage), the repairer (does one exist, does it
write, and does the image still verify after it wrote), and salvage (can the
damaged file be read back out, and is what comes out correct).

**Four injection sites per arm, not two.** Two are task 09's, unchanged and for
the same reasons -- one bit, in the middle physical block of the middle extent
of a file that is byte-identical across the arms -- so the two records measure
one event from the boot side and the tooling side. But a data-corruption cell
asks the checkers a question two of them cannot answer: e2fsprogs has no command
that reads file content, and an EROFS cluster stored raw has no decompressor to
fail. So two more sites per arm land in **metadata** -- the superblock and an
inode -- where a format that checksums its structures has a mechanism to notice.
That is what turns "the checker said nothing" from a fact about the injection
into a fact about the format.

**What does early boot consume before `/usr` is verified?** An inventory, not a
comparison: the initrd's member list and a fixed set of paths in the `/usr`
tree, so item 2's `fstab`/`crypttab` clause is answered by what the artifact
contains rather than by the plan's non-goal alone.

Salvage is measured against ground truth from the pristine image, never against
the tool's exit status, and the two are recorded separately. That is how this
task found that both arms hand back a full-length file that is silently wrong --
and, on the way, that PLN-0002-07's seventh fail-open is not one: `fsck.erofs
--extract=X --path=<file>` writes the content to `X` itself, so a probe looking
for the file *inside* `X` finds nothing and scores a working tool as a failure.

The originals are never written to. Every cell works on a copy and the artifact
digest is checked before and after.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from common import default_build_root
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.validation.vm import file_digest  # noqa: E402

ARMS = {"erofs": "out-erofs", "ext4": "out-ext4"}

# PLN-0002-05 pins both, and task 09 depends on the same equality: one flipped
# bit falls inside exactly one verity data block on either arm.
BLOCK = 4096

TARGETS = ("System.map", "vmlinuz")
MODULES = "/lib/modules"

# Paths probed in the `/usr` tree for the early-boot clause. Presence and absence
# both matter: the cryptsetup machinery shipping while no `crypttab` exists is
# the finding, and it cannot be stated from either half alone.
USR_PROBES = (
    "/lib/systemd/systemd-cryptsetup",
    "/lib/systemd/system-generators/systemd-cryptsetup-generator",
    "/lib/systemd/system-generators/systemd-fstab-generator",
    "/lib/systemd/system-generators/systemd-veritysetup-generator",
    "/lib/systemd/system/cryptsetup.target",
    "/lib/systemd/systemd-veritysetup",
    "/lib/verity.d",
)

# Names looked for in the initrd member list. `etc/fstab`, `etc/crypttab` and
# `etc/veritytab` are what item 2's early-boot clause names; the rest is the
# machinery that would consume them.
INITRD_EXACT = ("etc/fstab", "etc/crypttab", "etc/veritytab", "init")
INITRD_PATTERNS = ("crypttab", "veritytab", "fstab", "cryptsetup", "verity.d")

# What counts as a checker complaint. Exit status alone is not enough: measured
# here, `fsck.erofs` prints `<E> erofs: failed to verify superblock checksum`
# and **exits 0**, so a harness reading only the return code records a detected
# corruption as an undetected one. The first draft of this file did exactly that.
COMPLAINT = re.compile(
    r"<E>|invalid|corrupt|does not match|still has errors|failed to", re.IGNORECASE
)


def tools_tree(build_root: Path) -> Path:
    tools = build_root / "tools/usr"
    if not (tools / "bin").is_dir():
        raise SystemExit(f"measure-recovery: no tools tree at {tools}")
    return tools


def tool(build_root: Path, name: str, *arguments: str) -> subprocess.CompletedProcess:
    """Run one filesystem tool from the declared tools tree, never from the host.

    PLN-0002-07 measured the erofs tools reaching this host only through that
    tree. Running the ext4 tools from the same place is not symmetry for its own
    sake: a recovery claim that came from whichever `e2fsck` the workstation
    happens to carry would not be a claim about the artifact's own closure.
    """
    tools = tools_tree(build_root)
    binary = tools / "bin" / name
    if not binary.is_file():
        raise SystemExit(f"measure-recovery: no {name} in {tools}")
    return subprocess.run(
        [str(binary), *arguments],
        capture_output=True, text=True, check=False,
        env=dict(os.environ, LD_LIBRARY_PATH=str(tools / "lib64")),
    )


def tool_version(build_root: Path, name: str, flag: str) -> str:
    result = tool(build_root, name, flag)
    text = (result.stdout + result.stderr).splitlines()
    return text[0].strip() if text else ""


def partition(artifact: Path, suffix: str) -> tuple[int, int]:
    table = json.loads(
        subprocess.run(
            ["sfdisk", "-J", str(artifact)], capture_output=True, text=True, check=True
        ).stdout
    )["partitiontable"]
    sector = table.get("sectorsize", 512)
    entry = next(
        part for part in table["partitions"]
        if (part.get("name") or "").endswith(suffix)
    )
    return entry["start"] * sector, entry["size"] * sector


def extract(artifact: Path, offset: int, length: int, destination: Path) -> None:
    with artifact.open("rb") as handle, destination.open("wb") as out:
        handle.seek(offset)
        remaining = length
        while remaining > 0:
            chunk = handle.read(min(1 << 20, remaining))
            if not chunk:
                break
            out.write(chunk)
            remaining -= len(chunk)


def ext4_extents(build_root: Path, image: Path, path: str) -> list[tuple[int, int, int]]:
    stat = tool(build_root, "debugfs", "-R", f"stat {path}", str(image)).stdout
    if "EXTENTS:" not in stat:
        raise SystemExit(f"measure-recovery: no extents for {path} in {image}")
    body = stat.split("EXTENTS:", 1)[1]
    extents: list[tuple[int, int, int]] = []
    for logical, physical in re.findall(r"\(([\d-]+)\):([\d-]+)", body):
        if "-" in logical:
            start, end = (int(value) for value in logical.split("-"))
            count = end - start + 1
        else:
            start, count = int(logical), 1
        extents.append((start, int(physical.split("-")[0]), count))
    if not extents:
        raise SystemExit(f"measure-recovery: unparsed extent line for {path}")
    return extents


def erofs_extents(build_root: Path, image: Path, path: str) -> list[dict[str, int]]:
    output = tool(build_root, "dump.erofs", "-e", f"--path={path}", str(image)).stdout
    extents: list[dict[str, int]] = []
    for line in output.splitlines():
        match = re.match(
            r"\s*\d+:\s*(\d+)\.\.\s*(\d+)\s*\|\s*\d+\s*:\s*(\d+)\.\.\s*(\d+)\s*\|\s*(\d+)",
            line,
        )
        if match:
            logical_start, logical_end, physical_start, _, physical_length = (
                int(value) for value in match.groups()
            )
            extents.append({
                "logical_start": logical_start,
                "logical_end": logical_end,
                "physical_start": physical_start,
                "physical_length": physical_length,
            })
    if not extents:
        raise SystemExit(f"measure-recovery: no extents parsed for {path}")
    return extents


def injection_offset(arm: str, build_root: Path, image: Path, target: str) -> int:
    """Task 09's byte, chosen the same way, so the two records describe one event.

    Middle extent, middle physical block, middle byte of that block: the damage
    lands in ordinary file body and cannot be attributed to a neighbouring block.
    """
    if arm == "ext4":
        extents = ext4_extents(build_root, image, target)
        middle = sum(count for _, _, count in extents) // 2
        for logical, physical, count in extents:
            if logical <= middle < logical + count:
                return (physical + middle - logical) * BLOCK + BLOCK // 2
        raise SystemExit(f"measure-recovery: middle block {middle} in no extent")
    extents = erofs_extents(build_root, image, target)
    chosen = extents[len(extents) // 2]
    return (chosen["physical_start"] // BLOCK) * BLOCK + BLOCK // 2


def flip(image: Path, offset: int) -> dict[str, int]:
    with image.open("r+b") as handle:
        handle.seek(offset)
        before = handle.read(1)[0]
        handle.seek(offset)
        handle.write(bytes([before ^ 0x01]))
    return {"absolute_offset": offset, "byte_before": before, "byte_after": before ^ 0x01}


def verity_verifies(data: Path, hashes: Path, root_hash: str) -> bool:
    return subprocess.run(
        ["veritysetup", "verify", str(data), str(hashes), root_hash],
        capture_output=True, text=True, check=False,
    ).returncode == 0


def uki_root_hash(uki: Path) -> str:
    matches = set(re.findall(rb"usrhash=([0-9a-f]{64})", uki.read_bytes()))
    if len(matches) != 1:
        raise SystemExit(
            f"measure-recovery: expected exactly one usrhash in {uki}, "
            f"found {len(matches)}"
        )
    return matches.pop().decode()


def tail(text: str, lines: int = 8) -> list[str]:
    return [line for line in text.strip().splitlines() if line.strip()][-lines:]


def check(build_root: Path, arm: str, image: Path) -> dict[str, Any]:
    """The format's checkers on a damaged image, without permission to write.

    Two checks per arm, because they are not the same question. The **metadata**
    check is what `fsck` means on either format: `e2fsck -fn` and a bare
    `fsck.erofs`. The **content** check reads every file back through the
    decompressor, which only EROFS offers -- `--extract` with no destination is
    documented as "check if all files are well encoded". e2fsprogs has no
    equivalent, because ext4 stores no checksum over file data at all. That
    asymmetry is a recovery finding and is recorded as a null rather than
    skipped.
    """
    if arm == "ext4":
        metadata = tool(build_root, "e2fsck", "-fn", str(image))
        content = None
    else:
        metadata = tool(build_root, "fsck.erofs", str(image))
        content = tool(build_root, "fsck.erofs", "--extract", str(image))
    result: dict[str, Any] = {
        "metadata_command": "e2fsck -fn" if arm == "ext4" else "fsck.erofs",
        "content_command": None if content is None else "fsck.erofs --extract",
        "content_available": content is not None,
    }
    for label, run in (("metadata", metadata), ("content", content)):
        if run is None:
            continue
        text = run.stdout + run.stderr
        complaints = [line.strip() for line in text.splitlines() if COMPLAINT.search(line)]
        result[f"{label}_returncode"] = run.returncode
        result[f"{label}_output_tail"] = tail(text)
        result[f"{label}_complaints"] = complaints[:6]
        result[f"{label}_reports_damage"] = bool(run.returncode or complaints)
        # The two disagree when a tool prints the failure and exits 0 anyway.
        result[f"{label}_exit_status_agrees"] = bool(run.returncode) == bool(complaints)
    result["reports_damage"] = bool(result.get("metadata_reports_damage")) or bool(
        result.get("content_reports_damage")
    )
    result["exit_status_agrees"] = all(
        result[key] for key in result if key.endswith("_exit_status_agrees")
    )
    return result


def repair(build_root: Path, arm: str, image: Path, hashes: Path, root_hash: str) -> dict[str, Any]:
    """Whether a repairer exists, whether it writes, and what verity says after.

    An authenticated artifact makes this question sharper than it is for an
    ordinary filesystem: a repair that writes is a repair that changes bytes the
    signed root hash covers. Both outcomes are recorded because both are
    dispositive -- a repairer that writes voids the signature, and one that
    writes nothing cannot see data damage in the first place.
    """
    if arm == "erofs":
        help_text = tool(build_root, "fsck.erofs", "--help")
        offered = help_text.stdout + help_text.stderr
        return {
            "repairer_exists": False,
            "evidence": "fsck.erofs --help offers no write or repair option",
            "options": sorted(set(re.findall(r"--[a-z][a-z0-9-]+", offered))),
        }
    before = file_digest(image)
    result = tool(build_root, "e2fsck", "-fy", str(image))
    after = file_digest(image)
    return {
        "repairer_exists": True,
        "command": "e2fsck -fy",
        "returncode": result.returncode,
        "output_tail": tail(result.stdout + result.stderr),
        "wrote_to_image": before != after,
        "digest_before": before,
        "digest_after": after,
        "verity_verifies_after_repair": verity_verifies(image, hashes, root_hash),
    }


def metadata_offsets(build_root: Path, arm: str, image: Path, target: str) -> list[dict[str, Any]]:
    """Two bytes per arm that a checker has a mechanism to notice.

    The file-data cells are the weakest possible test of a checker: e2fsprogs
    has no command that reads file content at all, and an EROFS cluster stored
    uncompressed propagates a flipped bit one for one, so two of those four
    cells could not have been detected by anything but verity whatever the tool
    did. These two are the opposite case -- a field inside a structure the
    format covers with its own checksum -- so "the checker did not see it"
    becomes a statement about the format rather than about where the bit landed.

    ext4 carries `metadata_csum` (measured, not assumed: it is in the declared
    feature set and in the on-disk superblock), so both cells are checksummed.
    EROFS checksums its superblock only, which is itself the finding for the
    inode cell.
    """
    if arm == "ext4":
        # s_blocks_count_lo, so the damage is a real disagreement about the
        # filesystem's size and not a flipped bit in padding.
        superblock = 1024 + 4
        located = tool(build_root, "debugfs", "-R", f"imap {target}", str(image))
        match = re.search(r"located at block (\d+), offset (0x[0-9a-f]+)", located.stdout)
        if not match:
            raise SystemExit(f"measure-recovery: no imap for {target}: {located.stdout}")
        # i_size_lo, four bytes into the ext4 inode.
        inode = int(match.group(1)) * BLOCK + int(match.group(2), 16) + 4
        return [
            {"region": "superblock", "field": "s_blocks_count_lo", "offset": superblock},
            {"region": "inode", "field": "i_size_lo", "offset": inode},
        ]

    header = image.read_bytes()[1024:1024 + 64]
    meta_blkaddr = int.from_bytes(header[40:44], "little")
    nid = None
    for line in tool(build_root, "dump.erofs", f"--path={target}", str(image)).stdout.splitlines():
        found = re.search(r"NID:\s*(\d+)", line)
        if found:
            nid = int(found.group(1))
    if nid is None:
        raise SystemExit(f"measure-recovery: no NID for {target}")
    return [
        # `blocks`, inside the region the EROFS superblock checksum covers.
        {"region": "superblock", "field": "blocks", "offset": 1024 + 36},
        # i_size, eight bytes into a compact EROFS inode.
        {
            "region": "inode",
            "field": "i_size",
            "offset": meta_blkaddr * BLOCK + nid * 32 + 8,
            "nid": nid,
        },
    ]


def repair_pristine(
    build_root: Path, arm: str, pristine: Path, hashes: Path, root_hash: str, work: Path
) -> dict[str, Any]:
    """The repairer on an **undamaged** image, which is where the claim lives.

    Running it on a damaged image cannot separate the two reasons verity would
    reject afterwards -- the injected bit and the repairer's own writes. On a
    pristine copy there is only one candidate left, so this is the cell that
    says whether repair is compatible with an authenticated artifact at all.
    """
    if arm == "erofs":
        return {"repairer_exists": False}
    work.mkdir(parents=True, exist_ok=True)
    copy = work / "pristine-repaired.img"
    shutil.copyfile(pristine, copy)
    before = file_digest(copy)
    result = tool(build_root, "e2fsck", "-fy", str(copy))
    after = file_digest(copy)
    outcome = {
        "repairer_exists": True,
        "command": "e2fsck -fy",
        "returncode": result.returncode,
        "output_tail": tail(result.stdout + result.stderr),
        "wrote_to_image": before != after,
        "verity_verifies_after_repair": verity_verifies(copy, hashes, root_hash),
    }
    copy.unlink()
    return outcome


def salvage(build_root: Path, arm: str, image: Path, target: str, work: Path) -> dict[str, Any]:
    """Read the target file back out of an image, by the format's own path.

    Returns what the tool reported and what it actually produced. Those are
    different fields on purpose.
    """
    work.mkdir(parents=True, exist_ok=True)
    out = work / "salvaged"
    if arm == "ext4":
        result = tool(build_root, "debugfs", "-R", f"dump {target} {out}", str(image))
        command = f"debugfs -R 'dump {target} …'"
    else:
        # The destination must not exist: `fsck.erofs --extract=X --path=<file>`
        # writes the file's content *to X itself*, and refuses if X is already
        # there. PLN-0002-07 read this as the tool writing nothing; see the
        # correction in the record.
        result = tool(
            build_root, "fsck.erofs", f"--extract={out}", f"--path={target}", str(image)
        )
        command = f"fsck.erofs --extract=… --path={target}"
    produced = out.is_file()
    return {
        "command": command,
        "returncode": result.returncode,
        "output_tail": tail(result.stdout + result.stderr, 4),
        "reported_success": result.returncode == 0,
        "file_produced": produced,
        "bytes_produced": out.stat().st_size if produced else 0,
        "digest": file_digest(out) if produced and out.stat().st_size else "",
    }


def compare(salvaged: dict[str, Any], control: dict[str, Any], work: Path) -> dict[str, Any]:
    """How wrong the salvaged bytes are, against the same file from the pristine image.

    The digest answers whether salvage was correct; this answers what an operator
    would be holding if they trusted it. Byte and block counts, not a boolean,
    because the whole reason the arms could differ here is the size of the region
    one flipped bit destroys.
    """
    if not (salvaged["file_produced"] and control["file_produced"]):
        return {"comparable": False}
    damaged_bytes = (work / "salvaged" / "salvaged").read_bytes()
    pristine_bytes = (work / "control" / "salvaged").read_bytes()
    if len(damaged_bytes) != len(pristine_bytes):
        return {
            "comparable": True,
            "identical": False,
            "length_differs": True,
            "damaged_length": len(damaged_bytes),
            "pristine_length": len(pristine_bytes),
        }
    differing = [
        index for index, (left, right) in enumerate(zip(damaged_bytes, pristine_bytes))
        if left != right
    ]
    blocks = sorted({index // BLOCK for index in differing})
    return {
        "comparable": True,
        "identical": not differing,
        "length_differs": False,
        "differing_bytes": len(differing),
        "differing_blocks": len(blocks),
        "first_differing_offset": differing[0] if differing else None,
        "last_differing_offset": differing[-1] if differing else None,
    }


def initrd_inventory(initrd: Path) -> dict[str, Any]:
    """The initrd's member list, which is what runs before `/usr` is verified.

    The list is read through the tools on the host because the initrd is a plain
    zstd-compressed cpio and no artifact-format claim rides on it. The trailing
    bytes of the UKI-extracted initrd are not a zstd frame, so zstd's own status
    is ignored and completeness is asserted from the member list instead.
    """
    decompressed = subprocess.run(
        ["zstd", "-dc", str(initrd)], capture_output=True, check=False
    ).stdout
    listing = subprocess.run(
        ["cpio", "-t"], input=decompressed, capture_output=True, check=False
    ).stdout.decode("utf-8", "replace")
    members = [line.strip() for line in listing.splitlines() if line.strip()]
    if "init" not in members or not any(m.startswith("usr/lib/systemd/") for m in members):
        raise SystemExit(f"measure-recovery: initrd listing from {initrd} looks truncated")
    return {
        "member_count": len(members),
        "present": {name: name in members for name in INITRD_EXACT},
        "matches": {
            pattern: sorted(m for m in members if pattern in m)[:12]
            for pattern in INITRD_PATTERNS
        },
    }


def usr_inventory(build_root: Path, arm: str, image: Path) -> dict[str, bool]:
    found: dict[str, bool] = {}
    for path in USR_PROBES:
        if arm == "ext4":
            result = tool(build_root, "debugfs", "-R", f"stat {path}", str(image))
            found[path] = "File not found" not in (result.stdout + result.stderr)
        else:
            result = tool(build_root, "dump.erofs", f"--path={path}", str(image))
            found[path] = result.returncode == 0
    return found


def environment(build_root: Path) -> dict[str, Any]:
    return {
        "host_kernel": platform.release(),
        "tools_tree": str(tools_tree(build_root)),
        "e2fsck": tool_version(build_root, "e2fsck", "-V"),
        "fsck_erofs": tool_version(build_root, "fsck.erofs", "--version"),
        "dump_erofs": tool_version(build_root, "dump.erofs", "--version"),
        "veritysetup": subprocess.run(
            ["veritysetup", "--version"], capture_output=True, text=True, check=False
        ).stdout.strip(),
    }


def assess(case: dict[str, Any]) -> list[str]:
    """Conditions that would make this record's claims untrue if they held."""
    problems: list[str] = []
    if not case["original_unchanged"]:
        problems.append("the artifact changed during the run")
    if not case["verity_verifies_pristine"]:
        problems.append("verity rejected the pristine image; the baseline is wrong")
    if case["verity_verifies_damaged"]:
        problems.append("verity accepted the damaged image; the injection missed")
    if not case["salvage_pristine"]["file_produced"]:
        problems.append("salvage produced nothing from the pristine image; no control")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--build-root",
        type=Path,
        default=default_build_root(),
    )
    parser.add_argument(
        "--kernel-version",
        required=True,
        help="the directory under /usr/lib/modules holding the two targets",
    )
    parser.add_argument("--output", type=Path, default=None)
    arguments = parser.parse_args()

    build_root: Path = arguments.build_root
    output = arguments.output or build_root / "evidence/pln0002-12/recovery.json"

    cases: list[dict[str, Any]] = []
    early_boot: dict[str, Any] = {}
    repair_baseline: dict[str, Any] = {}
    metadata_cases: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="neutrinos-pln0002-12-") as raw:
        scratch = Path(raw)
        for arm, directory in ARMS.items():
            artifact = build_root / directory / "neutrinos-slice.raw"
            if not artifact.is_file():
                print(f"measure: no artifact at {artifact}", file=sys.stderr)
                return 1
            original_digest = file_digest(artifact)
            root_hash = uki_root_hash(build_root / directory / "neutrinos-slice.efi")

            data_offset, data_size = partition(artifact, "neutrinos-usr")
            hash_offset, hash_size = partition(artifact, "usr-verity")
            pristine = scratch / f"usr-{arm}.img"
            hashes = scratch / f"hash-{arm}.img"
            extract(artifact, data_offset, data_size, pristine)
            extract(artifact, hash_offset, hash_size, hashes)
            pristine_verifies = verity_verifies(pristine, hashes, root_hash)

            repair_baseline[arm] = repair_pristine(
                build_root, arm, pristine, hashes, root_hash, scratch / f"{arm}-repair"
            )
            print(f"{arm}: repair-on-pristine={repair_baseline[arm]}", flush=True)

            early_boot[arm] = {
                "usr_tree": usr_inventory(build_root, arm, pristine),
                "initrd": initrd_inventory(build_root / directory / "neutrinos-slice.initrd"),
                "initrd_digest": file_digest(build_root / directory / "neutrinos-slice.initrd"),
            }

            # Metadata first: these are the cells that give the checker a
            # mechanism to work with, and the data cells below are only
            # interpretable next to them.
            first_target = f"{MODULES}/{arguments.kernel_version}/{TARGETS[0]}"
            for spot in metadata_offsets(build_root, arm, pristine, first_target):
                work = scratch / f"{arm}-meta-{spot['region']}"
                work.mkdir()
                damaged = work / "damaged.img"
                shutil.copyfile(pristine, damaged)
                cell: dict[str, Any] = {
                    "arm": arm,
                    "region": spot["region"],
                    "field": spot["field"],
                    "checksummed_by_format": arm == "ext4" or spot["region"] == "superblock",
                    "verity_verifies_pristine": pristine_verifies,
                }
                cell.update({k: v for k, v in spot.items() if k not in ("region", "field")})
                cell.update(flip(damaged, spot["offset"]))
                cell["verity_verifies_damaged"] = verity_verifies(damaged, hashes, root_hash)
                cell["check_damaged"] = check(build_root, arm, damaged)
                damaged.unlink()
                metadata_cases.append(cell)
                print(
                    f"{arm}/{spot['region']} ({spot['field']}): "
                    f"checksummed={cell['checksummed_by_format']} "
                    f"verity-damaged={cell['verity_verifies_damaged']} "
                    f"checker-sees-it={cell['check_damaged']['reports_damage']}",
                    flush=True,
                )

            for name in TARGETS:
                target = f"{MODULES}/{arguments.kernel_version}/{name}"
                work = scratch / f"{arm}-{name}"
                work.mkdir()
                damaged = work / "damaged.img"
                shutil.copyfile(pristine, damaged)
                offset = injection_offset(arm, build_root, damaged, target)
                case: dict[str, Any] = {
                    "arm": arm,
                    "target": f"/usr{target}",
                    "target_name": name,
                    "verity_data_block": offset // BLOCK,
                    "verity_verifies_pristine": pristine_verifies,
                    "salvage_pristine": salvage(
                        build_root, arm, pristine, target, work / "control"
                    ),
                }
                case.update(flip(damaged, offset))
                case["verity_verifies_damaged"] = verity_verifies(damaged, hashes, root_hash)
                case["check_damaged"] = check(build_root, arm, damaged)
                case["salvage_damaged"] = salvage(
                    build_root, arm, damaged, target, work / "salvaged"
                )
                case["salvage_matches_pristine"] = (
                    bool(case["salvage_damaged"]["digest"])
                    and case["salvage_damaged"]["digest"] == case["salvage_pristine"]["digest"]
                )
                case["salvage_difference"] = compare(
                    case["salvage_damaged"], case["salvage_pristine"], work
                )
                # Last, because it is the only cell allowed to write to the image.
                case["repair_damaged"] = repair(build_root, arm, damaged, hashes, root_hash)
                case["original_unchanged"] = file_digest(artifact) == original_digest
                case["problems"] = assess(case)
                cases.append(case)
                print(
                    f"{arm}/{name}: block={case['verity_data_block']} "
                    f"verity-damaged={case['verity_verifies_damaged']} "
                    f"checker-sees-it={case['check_damaged']['reports_damage']} "
                    f"repairer={case['repair_damaged']['repairer_exists']} "
                    f"salvage-reported={case['salvage_damaged']['reported_success']} "
                    f"salvage-bytes={case['salvage_damaged']['bytes_produced']} "
                    f"salvage-correct={case['salvage_matches_pristine']}",
                    flush=True,
                )

    record = {
        "task": "PLN-0002-12",
        "measured": datetime.now().astimezone().isoformat(timespec="seconds"),
        "build_root": str(build_root),
        "block_size": BLOCK,
        "kernel_version": arguments.kernel_version,
        "environment": environment(build_root),
        "early_boot_inventory": early_boot,
        "repair_on_pristine": repair_baseline,
        "metadata_cases": metadata_cases,
        "cases": cases,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(f"measure: wrote {output}")

    failed = False
    for case in cases:
        for entry in case["problems"]:
            failed = True
            print(f"{case['arm']}/{case['target_name']}: {entry}", file=sys.stderr)
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
