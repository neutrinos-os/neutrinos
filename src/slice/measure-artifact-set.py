#!/usr/bin/env python3
"""Offline measurements over the PLN-0002-06 artifact set: PLN-0002-07.

Three of task 07's five measurements are static -- they read the artifacts that
already exist and rebuild nothing. Those are here. Build wall time and build
determinism need rebuilds and live in measure-build-time.py.

  image size            filesystem bytes in use, with partition size reported
                        separately and never in its place
  update transfer size  what a whole-artifact update ships, and what a
                        block-differential update ships for one changed file
  inspectability        what can read the artifact offline, unprivileged, and
                        with which tooling present

**Filesystem bytes in use, not partition size.** Both arms hold
`Minimize=guess` and `Minimize=best` is unavailable on ext4, so a
partition-table figure measures systemd-repart's estimator on one arm and the
filesystem on the other: measured here, the EROFS partition is exactly its
filesystem while the ext4 partition carries estimator slack. Reporting
partition size as image size would charge ext4 for it.

Every figure is read from the built artifact, never from the configuration that
produced it, which agrees with itself by construction.

This writes digests and figures, not bytes. The images stay in the build root.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# The six of amendment 5, named rather than globbed, for the reason
# retain-artifact-digests.py records: a glob measures five and reports success.
ARTIFACTS = (
    "out-erofs",
    "out-erofs-content",
    "out-erofs-seed",
    "out-ext4",
    "out-ext4-content",
    "out-ext4-seed",
)

ARMS = {"erofs": "out-erofs", "ext4": "out-ext4"}

IMAGE = "neutrinos-slice.raw"

# Compression levels for the whole-artifact update figure. Two rather than one:
# level 3 is zstd's default and what an updater would ship without thinking
# about it, level 19 is what one would ship if transfer size mattered. A single
# level would make the format comparison depend on an unstated choice.
ZSTD_LEVELS = (3, 19)

# The block size a block-differential updater would work in. 4096 because it is
# the filesystem block size on both arms and the dm-verity data block size on
# both, so a differing-block count is countable in the same unit the artifact
# is already built in.
DELTA_BLOCK = 4096


def run(argv: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, check=False, **kwargs)


def partition_table(image: Path) -> dict[str, dict[str, int]]:
    """Partition offsets and sizes in bytes, keyed by GPT partition name."""
    result = run(["sfdisk", "-J", str(image)])
    if result.returncode != 0:
        raise SystemExit(f"sfdisk failed on {image}: {result.stderr.strip()}")
    table = json.loads(result.stdout)["partitiontable"]
    sector = table["sectorsize"]
    return {
        part["name"]: {
            "offset_bytes": part["start"] * sector,
            "partition_bytes": part["size"] * sector,
        }
        for part in table["partitions"]
    }


def erofs_superblock(image: Path, offset: int) -> dict[str, object]:
    """EROFS geometry read from the on-disk superblock.

    Parsed here rather than shelled out to dump.erofs because dump.erofs is not
    on the build host at all -- which is itself one of the inspectability
    findings below, and a measurement should not depend on the thing it is
    measuring being available.

    EROFS packs its image with no free space, so `blocks` is both the image
    size and the bytes in use. That is the property that makes the two arms
    comparable at all: on ext4 the two figures differ and both must be read.
    """
    with image.open("rb") as handle:
        handle.seek(offset + 1024)
        raw = handle.read(128)
    magic, _checksum, _compat, blkszbits, _slots, _root, _inos, _bt, _btn, blocks = (
        struct.unpack_from("<IIIBBHQQII", raw, 0)
    )
    if magic != 0xE0F5E1E2:
        raise SystemExit(f"{image}: no EROFS superblock at offset {offset}")
    block_size = 1 << blkszbits
    return {
        "format": "erofs",
        "block_size": block_size,
        "total_blocks": blocks,
        "free_blocks": 0,
        "image_bytes": blocks * block_size,
        "bytes_in_use": blocks * block_size,
        "source": "on-disk superblock",
    }


def ext4_superblock(image: Path, offset: int) -> dict[str, object]:
    """ext4 geometry from dumpe2fs, run against an extracted partition.

    dumpe2fs takes no offset, so the partition is copied out to a temporary
    file and removed again. The alternative -- parsing the superblock in place
    as the EROFS path does -- was rejected here because e2fsprogs is present on
    the build host and an authoritative tool should be used where it exists.

    bytes in use is (total - free) blocks. The difference between that and
    image_bytes is ext4's own free space, and the difference between
    image_bytes and the partition size is systemd-repart's estimator. They are
    different overheads with different owners and are never summed.
    """
    with tempfile.NamedTemporaryFile(prefix="pln0002-07-", suffix=".img") as scratch:
        with image.open("rb") as handle:
            handle.seek(offset)
            remaining = 64 << 20  # the superblock and group descriptors are early
            while remaining > 0:
                chunk = handle.read(min(1 << 20, remaining))
                if not chunk:
                    break
                scratch.write(chunk)
                remaining -= len(chunk)
        scratch.flush()
        result = run(["dumpe2fs", "-h", scratch.name])
    fields: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    if "Block count" not in fields:
        raise SystemExit(f"{image}: dumpe2fs read no superblock: {result.stderr.strip()}")
    block_size = int(fields["Block size"])
    total = int(fields["Block count"])
    free = int(fields["Free blocks"])
    return {
        "format": "ext4",
        "block_size": block_size,
        "total_blocks": total,
        "free_blocks": free,
        "image_bytes": total * block_size,
        "bytes_in_use": (total - free) * block_size,
        "features": fields.get("Filesystem features", ""),
        "source": "dumpe2fs -h",
    }


def verity_geometry(image: Path, offset: int, size: int) -> dict[str, object]:
    """dm-verity hash tree: bytes actually occupied against partition size.

    `veritysetup dump` reports the hash device size, which is the superblock
    plus the tree. The partition is far larger on both arms and by the same
    amount, so this is a second place where a partition figure would measure
    the estimator rather than the artifact.
    """
    with tempfile.NamedTemporaryFile(prefix="pln0002-07-verity-", suffix=".img") as scratch:
        with image.open("rb") as handle:
            handle.seek(offset)
            remaining = size
            while remaining > 0:
                chunk = handle.read(min(1 << 20, remaining))
                if not chunk:
                    break
                scratch.write(chunk)
                remaining -= len(chunk)
        scratch.flush()
        result = run(["veritysetup", "dump", scratch.name])
    if result.returncode != 0:
        raise SystemExit(f"veritysetup dump failed on {image}: {result.stderr.strip()}")
    fields = {}
    for line in result.stdout.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().split()[0] if value.strip() else ""
    return {
        "data_blocks": int(fields["Data blocks"]),
        "data_block_size": int(fields["Data block size"]),
        "hash_blocks": int(fields["Hash blocks"]),
        "hash_block_size": int(fields["Hash block size"]),
        "hash_algorithm": fields.get("Hash algorithm", ""),
        "bytes_in_use": int(fields["Hash device size"]),
        "partition_bytes": size,
    }


def zstd_size(image: Path, offset: int, size: int, level: int) -> int:
    """Compressed size of a partition region, streamed rather than copied out."""
    with image.open("rb") as handle:
        handle.seek(offset)
        proc = subprocess.Popen(
            ["zstd", f"-{level}", "-T0", "-c", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        compressed = 0

        def pump() -> None:
            remaining = size
            try:
                while remaining > 0:
                    chunk = handle.read(min(1 << 20, remaining))
                    if not chunk:
                        break
                    proc.stdin.write(chunk)
                    remaining -= len(chunk)
            finally:
                proc.stdin.close()

        import threading

        thread = threading.Thread(target=pump)
        thread.start()
        while True:
            out = proc.stdout.read(1 << 20)
            if not out:
                break
            compressed += len(out)
        thread.join()
        proc.wait()
    return compressed


def block_delta(
    left: Path, left_offset: int, right: Path, right_offset: int, size: int
) -> dict[str, int]:
    """Differing 4 KiB blocks between two partitions of the same arm.

    This is the update-transfer figure that separates the formats. One changed
    file under /usr is one changed file on ext4 and a re-compressed region on
    EROFS, so a block count here is the amplification the format imposes on a
    differential update -- a criterion no whole-image compressed size can show.
    """
    differing = 0
    compared = 0
    with left.open("rb") as a, right.open("rb") as b:
        a.seek(left_offset)
        b.seek(right_offset)
        remaining = size
        while remaining > 0:
            want = min(DELTA_BLOCK, remaining)
            block_a = a.read(want)
            block_b = b.read(want)
            if not block_a or not block_b:
                break
            compared += 1
            if block_a != block_b:
                differing += 1
            remaining -= want
    return {
        "block_size": DELTA_BLOCK,
        "blocks_compared": compared,
        "blocks_differing": differing,
        "bytes_differing": differing * DELTA_BLOCK,
    }


def measure_artifact(directory: Path) -> dict[str, object]:
    image = directory / IMAGE
    table = partition_table(image)
    usr = table["neutrinos-usr"]
    verity = table["neutrinos-usr-verity"]
    if "erofs" in directory.name:
        filesystem = erofs_superblock(image, usr["offset_bytes"])
    else:
        filesystem = ext4_superblock(image, usr["offset_bytes"])
    filesystem["partition_bytes"] = usr["partition_bytes"]
    # Two overheads, kept apart because they have different owners, and named
    # after where they were measured rather than after who is blamed for them.
    #
    # `partition_minus_image_bytes` is space in the partition that the
    # filesystem does not claim. Measured zero on both arms: systemd-repart
    # sizes the partition to its estimate and the filesystem is made to fill
    # it, so nothing is left outside.
    #
    # `filesystem_free_bytes` is therefore where `Minimize=guess` actually
    # lands on ext4 -- inside the filesystem, as free blocks. It is zero on
    # EROFS, which packs with no free space. This is the whole reason task 07
    # is required to report bytes in use: the partition figure charges ext4 for
    # the estimator's margin, and both figures are needed to see that.
    filesystem["partition_minus_image_bytes"] = (
        usr["partition_bytes"] - filesystem["image_bytes"]
    )
    filesystem["filesystem_free_bytes"] = (
        filesystem["image_bytes"] - filesystem["bytes_in_use"]
    )
    return {
        "partitions": table,
        "usr_filesystem": filesystem,
        "verity": verity_geometry(image, verity["offset_bytes"], verity["partition_bytes"]),
        "files": {
            path.name: path.stat().st_size
            for path in sorted(directory.iterdir())
            if path.is_file() and not path.is_symlink()
        },
        "raw_bytes": image.stat().st_size,
    }


def measure_transfer(build_root: Path, measurements: dict[str, dict]) -> dict[str, object]:
    full: dict[str, object] = {}
    for arm, primary in ARMS.items():
        image = build_root / primary / IMAGE
        usr = measurements[primary]["partitions"]["neutrinos-usr"]
        entry = {
            "usr_partition_bytes": usr["partition_bytes"],
            "usr_bytes_in_use": measurements[primary]["usr_filesystem"]["bytes_in_use"],
        }
        for level in ZSTD_LEVELS:
            entry[f"zstd_{level}_bytes"] = zstd_size(
                image, usr["offset_bytes"], usr["partition_bytes"], level
            )
        full[arm] = entry

    delta: dict[str, object] = {}
    for arm, primary in ARMS.items():
        for variant in ("content", "seed"):
            other = f"{primary}-{variant}"
            left = build_root / primary / IMAGE
            right = build_root / other / IMAGE
            left_usr = measurements[primary]["partitions"]["neutrinos-usr"]
            right_usr = measurements[other]["partitions"]["neutrinos-usr"]
            # Compare over the smaller of the two, and record that they differ
            # in size rather than papering over it: the content variant is
            # three filesystem blocks larger on ext4, which is a real part of
            # what an update ships.
            size = min(left_usr["partition_bytes"], right_usr["partition_bytes"])
            result = block_delta(
                left, left_usr["offset_bytes"], right, right_usr["offset_bytes"], size
            )
            result["partition_bytes_left"] = left_usr["partition_bytes"]
            result["partition_bytes_right"] = right_usr["partition_bytes"]
            delta[f"{arm}:primary->{variant}"] = result
    return {"full_image": full, "block_delta": delta}


def measure_inspectability(build_root: Path, measurements: dict[str, dict]) -> dict[str, object]:
    """What can read each artifact offline and unprivileged, and with what.

    Both arms are inspectable. The measured difference is what has to be
    present: e2fsprogs ships with the build host's own distribution, while the
    EROFS tools reach the host only through the declared tools tree, which is a
    build input rather than an operator's environment. That is a property of
    the format's tooling reach, not of the image, and the record must say so
    rather than scoring one arm "inspectable" and the other not.
    """
    tools_tree = build_root / "tools"
    tools_lib = tools_tree / "usr/lib64"
    wanted = ("dumpe2fs", "debugfs", "dump.erofs", "fsck.erofs", "systemd-dissect")
    host = {tool: shutil.which(tool) for tool in wanted}
    in_tree = {}
    for tool in wanted:
        for directory in ("usr/sbin", "usr/bin"):
            candidate = tools_tree / directory / tool
            if candidate.exists():
                in_tree[tool] = str(candidate)
                break
        else:
            in_tree[tool] = None

    environment = dict(os.environ, LD_LIBRARY_PATH=str(tools_lib))
    listings: dict[str, object] = {}
    for arm, primary in ARMS.items():
        image = build_root / primary / IMAGE
        usr = measurements[primary]["partitions"]["neutrinos-usr"]
        with tempfile.NamedTemporaryFile(prefix="pln0002-07-ls-", suffix=".img") as scratch:
            with image.open("rb") as handle:
                handle.seek(usr["offset_bytes"])
                remaining = usr["partition_bytes"]
                while remaining > 0:
                    chunk = handle.read(min(1 << 20, remaining))
                    if not chunk:
                        break
                    scratch.write(chunk)
                    remaining -= len(chunk)
            scratch.flush()
            if arm == "ext4":
                tool = host["debugfs"] or in_tree["debugfs"]
                listed = run([tool, "-R", "ls -l /", scratch.name], env=environment)
                entries = [
                    line for line in listed.stdout.splitlines() if line.strip().startswith(("1", "2", "3", "4", "5", "6", "7", "8", "9"))
                ]
                source = "debugfs -R 'ls -l /'"
                from_host = host["debugfs"] is not None
            else:
                tool = host["dump.erofs"] or in_tree["dump.erofs"]
                listed = run([tool, "--ls", "--path=/", scratch.name], env=environment)
                started = False
                entries = []
                for line in listed.stdout.splitlines():
                    if line.strip().startswith("NID"):
                        started = True
                        continue
                    if started and line.strip():
                        entries.append(line)
                source = "dump.erofs --ls --path=/"
                from_host = host["dump.erofs"] is not None

            # Two extraction probes, not one. The single-file probe is the
            # question an operator actually asks -- "what does this artifact
            # say in /usr/lib/os-release" -- and the directory probe is what
            # the EROFS arm has to fall back to, because the single-file route
            # fails open there. Both are recorded per arm so the fallback is
            # visible as a cost rather than hidden behind a passing figure.
            extract_dir = Path(tempfile.mkdtemp(prefix="pln0002-07-extract-"))
            file_target = extract_dir / "one"
            dir_target = extract_dir / "many"
            if arm == "ext4":
                extract_tool = host["debugfs"] or in_tree["debugfs"]
                extracted = run(
                    [extract_tool, "-R", f"dump /lib/os-release {file_target}", scratch.name],
                    env=environment,
                )
                extracted_bytes = (
                    file_target.stat().st_size if file_target.exists() else 0
                )
                directory = run(
                    [extract_tool, "-R", "ls -l /lib/systemd/system-preset", scratch.name],
                    env=environment,
                )
                directory_entries = len(
                    [line for line in directory.stdout.splitlines() if ".preset" in line]
                )
            else:
                extract_tool = host["fsck.erofs"] or in_tree["fsck.erofs"]
                extracted = run(
                    [
                        extract_tool,
                        f"--extract={file_target}",
                        "--path=/lib/os-release",
                        scratch.name,
                    ],
                    env=environment,
                )
                found = (
                    list(file_target.rglob("os-release")) if file_target.exists() else []
                )
                extracted_bytes = found[0].stat().st_size if found else 0
                directory = run(
                    [
                        extract_tool,
                        f"--extract={dir_target}",
                        "--path=/lib/systemd/system-preset",
                        scratch.name,
                    ],
                    env=environment,
                )
                directory_entries = (
                    len(list(dir_target.rglob("*.preset"))) if dir_target.exists() else 0
                )
            shutil.rmtree(extract_dir, ignore_errors=True)

        listings[arm] = {
            "listing_tool": source,
            "listing_tool_on_host": from_host,
            "root_entries": len(entries),
            "listing_ok": listed.returncode == 0 and len(entries) > 0,
            "extract_tool": Path(extract_tool).name if extract_tool else None,
            "extract_tool_on_host": (
                host["debugfs" if arm == "ext4" else "fsck.erofs"] is not None
            ),
            "extracted_bytes": extracted_bytes,
            "extract_ok": extracted.returncode == 0 and extracted_bytes > 0,
            # Recorded separately from extract_ok because they disagree on the
            # EROFS arm, and the disagreement is the finding: the tool reports
            # success and produces nothing.
            "extract_exit_status": extracted.returncode,
            "directory_extract_entries": directory_entries,
            "directory_extract_ok": directory.returncode == 0 and directory_entries > 0,
            "required_root": False,
        }
    return {
        "host_tools": host,
        "tools_tree_tools": in_tree,
        "per_arm": listings,
        "note": (
            "Every probe here ran unprivileged, from an extracted partition "
            "image, with no loop device and no mount."
        ),
        "erofs_single_file_extract_fails_open": (
            "fsck.erofs --extract=X --path=<file> at the pinned erofs-utils "
            "version prints 'Extracted filesystem successfully', exits 0, and "
            "writes nothing. Only a directory path extracts. Recorded because "
            "a measurement that trusted the exit status would have scored the "
            "arm as inspectable on the strength of a tool that did nothing."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--build-root",
        type=Path,
        default=Path(
            os.environ.get(
                "NEUTRINOS_SLICE_BUILD_ROOT",
                Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
                / "neutrinos/slice",
            )
        ),
    )
    parser.add_argument("--output", type=Path, default=None)
    arguments = parser.parse_args()

    build_root: Path = arguments.build_root
    missing = [name for name in ARTIFACTS if not (build_root / name / IMAGE).exists()]
    if missing:
        print(
            "measure: the artifact set is incomplete; PLN-0002-07 measures six "
            f"artifacts and these are absent: {', '.join(missing)}",
            file=sys.stderr,
        )
        return 1

    measurements = {name: measure_artifact(build_root / name) for name in ARTIFACTS}
    record = {
        "task": "PLN-0002-07",
        "measured": datetime.now().astimezone().isoformat(timespec="seconds"),
        "build_root": str(build_root),
        "artifact_count": len(ARTIFACTS),
        "artifacts": measurements,
        "transfer": measure_transfer(build_root, measurements),
        "inspectability": measure_inspectability(build_root, measurements),
    }

    output = arguments.output or build_root / "evidence/pln0002-07/static.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(f"measure: wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
