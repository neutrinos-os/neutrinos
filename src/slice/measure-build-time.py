#!/usr/bin/env python3
"""Timed rebuilds of the PLN-0002-06 artifact set: PLN-0002-07.

Two of task 07's five measurements need the artifacts rebuilt rather than read,
and they are taken together because one rebuild answers both:

  build wall time     how long compose.sh takes per artifact, repeated, with
                      the repetition count and the accelerator state recorded
  build determinism   whether each rebuild reproduces the digests PLN-0002-06
                      retained, with the confext rebuilt

Taking them from the same runs is deliberate. A determinism check that ran a
build the timing did not measure would be measuring a different build, and this
plan has already recorded one determinism closure that claimed more than it
measured.

**Rebuilds overwrite the accepted artifact set in place.** Owner ruling
2026-08-15: the six are copied aside before this runs and the copies are
discarded only once every rebuild has reproduced. This script does not make
that copy -- it verifies against the retained digests and reports a mismatch
loudly, and the copy is what makes a mismatch recoverable rather than
terminal.

**The confext is rebuilt on the timed runs.** compose.sh's
NEUTRINOS_SKIP_CONFEXT reuses a previously built extension, so a determinism
claim taken with it skipped is narrower than it sounds. The skip is used only
in the separate overhead pass below, which makes no determinism claim.

The overhead pass exists because compose.sh is not only the artifact build: it
rebuilds two confexts, retains the repository, and writes the enrollment
fixture, and all of that is identical across arms. Timing it on the primaries
with the confext skipped prices the shared part, so the arm-to-arm difference
can be read against the build rather than against the wrapper.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from common import default_build_root

# (directory, arm, variant). The six of amendment 5, named rather than globbed.
ARTIFACTS = (
    ("out-erofs", "erofs", "primary"),
    ("out-erofs-content", "erofs", "content"),
    ("out-erofs-seed", "erofs", "seed"),
    ("out-ext4", "ext4", "primary"),
    ("out-ext4-content", "ext4", "content"),
    ("out-ext4-seed", "ext4", "seed"),
)

PRIMARIES = tuple(entry for entry in ARTIFACTS if entry[2] == "primary")


def digests(directory: Path) -> dict[str, str]:
    result = {}
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.is_symlink():
            continue
        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            while chunk := handle.read(1 << 20):
                hasher.update(chunk)
        result[path.name] = hasher.hexdigest()
    return result


def compare(observed: dict[str, str], reference: dict[str, str]) -> dict[str, object]:
    """Every file compared, not just the image.

    The image is what a deployment ships, but the UKI carries the command line
    and the root hash, and PLN-0002-06's retention covers all of them. A
    determinism figure taken on neutrinos-slice.raw alone would miss a UKI that
    stopped reproducing.
    """
    differing = sorted(
        name
        for name in set(observed) | set(reference)
        if observed.get(name) != reference.get(name)
    )
    return {
        "files_compared": len(set(observed) | set(reference)),
        "files_differing": differing,
        "reproduced": not differing,
    }


def build_environment() -> dict[str, object]:
    """What the timing figures are figures of.

    Accelerator state is recorded because the plan requires it of every timed
    measurement. For a build it is not applicable and saying so is the record:
    nothing here runs in a VM, so there is no KVM-versus-TCG difference of the
    kind that moved PLN-0001's boot measurement from 72s to 18s. What does move
    a build time is core count and cache warmth, so those are recorded instead.
    """
    cpu = ""
    for line in Path("/proc/cpuinfo").read_text().splitlines():
        if line.startswith("model name"):
            cpu = line.split(":", 1)[1].strip()
            break
    return {
        "accelerator": "not applicable: no VM is booted, the build is host CPU work",
        "cpu_model": cpu,
        "cpu_count": os.cpu_count(),
        "kernel": platform.release(),
        "python": platform.python_version(),
    }


def timed_build(
    compose: Path, build_root: Path, arm: str, variant: str, skip_confext: bool
) -> dict[str, object]:
    environment = dict(
        os.environ,
        NEUTRINOS_SLICE_BUILD_ROOT=str(build_root),
        NEUTRINOS_SLICE_ARM=arm,
        NEUTRINOS_SLICE_VARIANT=variant,
    )
    if skip_confext:
        environment["NEUTRINOS_SKIP_CONFEXT"] = "1"
    else:
        environment.pop("NEUTRINOS_SKIP_CONFEXT", None)
    started = time.monotonic()
    result = subprocess.run(
        [str(compose), "--force", "build"],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed = time.monotonic() - started
    return {
        "wall_seconds": round(elapsed, 2),
        "exit_status": result.returncode,
        "stderr_tail": result.stderr.strip().splitlines()[-3:] if result.returncode else [],
    }


def summarize(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    middle = len(ordered) // 2
    median = (
        ordered[middle]
        if len(ordered) % 2
        else (ordered[middle - 1] + ordered[middle]) / 2
    )
    return {
        "repetitions": len(ordered),
        "min_seconds": ordered[0],
        "median_seconds": round(median, 2),
        "max_seconds": ordered[-1],
        "spread_seconds": round(ordered[-1] - ordered[0], 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--build-root",
        type=Path,
        default=default_build_root(),
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=3,
        help="timed rebuilds per artifact; owner ruling 2026-08-15 is three",
    )
    parser.add_argument("--output", type=Path, default=None)
    arguments = parser.parse_args()

    build_root: Path = arguments.build_root
    compose = Path(__file__).resolve().parent / "compose.sh"
    reference_path = build_root / "evidence/pln0002-06/digests.json"
    if not reference_path.exists():
        print(
            "measure: no PLN-0002-06 digests to compare against at "
            f"{reference_path}; determinism cannot be measured without the "
            "retained set",
            file=sys.stderr,
        )
        return 1
    reference = json.loads(reference_path.read_text())["artifacts"]

    runs: dict[str, list[dict]] = {}
    for directory, arm, variant in ARTIFACTS:
        runs[directory] = []
        for repetition in range(1, arguments.repetitions + 1):
            record = timed_build(compose, build_root, arm, variant, skip_confext=False)
            record["repetition"] = repetition
            record["determinism"] = compare(
                digests(build_root / directory), reference[directory]["files"]
            )
            runs[directory].append(record)
            status = "reproduced" if record["determinism"]["reproduced"] else "DIFFERS"
            print(
                f"{directory} rep {repetition}: {record['wall_seconds']}s {status}",
                flush=True,
            )

    overhead: dict[str, list[dict]] = {}
    for directory, arm, variant in PRIMARIES:
        overhead[directory] = []
        for repetition in range(1, arguments.repetitions + 1):
            record = timed_build(compose, build_root, arm, variant, skip_confext=True)
            record["repetition"] = repetition
            overhead[directory].append(record)
            print(
                f"{directory} rep {repetition} (confext skipped): "
                f"{record['wall_seconds']}s",
                flush=True,
            )

    record = {
        "task": "PLN-0002-07",
        "measured": datetime.now().astimezone().isoformat(timespec="seconds"),
        "build_root": str(build_root),
        "environment": build_environment(),
        "package_cache": "warm: every run resolves from the retained repository "
        "in the build root, and no run acquires packages from the network",
        "confext_rebuilt": True,
        "timed_builds": runs,
        "timed_builds_summary": {
            directory: summarize([run["wall_seconds"] for run in entries])
            for directory, entries in runs.items()
        },
        "confext_skipped_builds": overhead,
        "confext_skipped_summary": {
            directory: summarize([run["wall_seconds"] for run in entries])
            for directory, entries in overhead.items()
        },
        "determinism": {
            directory: all(run["determinism"]["reproduced"] for run in entries)
            for directory, entries in runs.items()
        },
        "determinism_claim_scope": (
            "Every timed build above rebuilt the confext. The confext-skipped "
            "pass is a build-time measurement only and no determinism claim is "
            "taken from it."
        ),
    }

    output = arguments.output or build_root / "evidence/pln0002-07/build.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(f"measure: wrote {output}")
    return 0 if all(record["determinism"].values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
