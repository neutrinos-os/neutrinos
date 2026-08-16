#!/usr/bin/env python3
"""Retain a digest for every PLN-0002-06 artifact.

Task 06's completion criterion is "build all six; retain digests", and a digest
computed once into a terminal is not retained. This writes them, with the two
facts that decide whether they mean anything: the kernel command line each UKI
actually carries, and whether the confext was rebuilt.

Why those two. The command line is inside the signed UKI and is declared as a
constant held across arms, so an artifact whose command line differs is not a
member of the declared set -- which is exactly the defect the 2026-08-14 audit
found in an ext4 arm built an hour before the policy landed. And any
determinism claim for this slice is meaningless without the confext's state:
compose.sh's NEUTRINOS_SKIP_CONFEXT reuses a previously built extension, and a
2026-08-12 closure claimed reproducibility while skipping it.

This records identity, not bytes. The images stay in the build root; the
hygiene contract's bounds mean evidence carries digests and the commands that
rebuild them.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from common import digest

# The six of amendment 5, named rather than globbed. A glob would silently
# retain five and report success; the count is the completion criterion.
ARTIFACTS = (
    "out-erofs",
    "out-erofs-content",
    "out-erofs-seed",
    "out-ext4",
    "out-ext4-content",
    "out-ext4-seed",
)


def kernel_command_line(uki: Path) -> str:
    """The .cmdline section of the UKI, which is what the artifact boots with.

    Read from the built UKI rather than from mkosi.conf: the point of recording
    it here is to catch an artifact that disagrees with the configuration, and
    reading the configuration would agree with itself by construction.
    """
    result = subprocess.run(
        ["objcopy", "-O", "binary", "--only-section=.cmdline", str(uki), "/dev/stdout"],
        capture_output=True,
        check=True,
    )
    return result.stdout.decode("utf-8").strip("\x00").strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-root", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument(
        "--confext-rebuilt",
        choices=("yes", "no"),
        required=True,
        help="whether this artifact set was built with the confext rebuilt "
        "(no means NEUTRINOS_SKIP_CONFEXT was set for any of the six)",
    )
    arguments = parser.parse_args()

    artifacts: dict[str, dict[str, object]] = {}
    missing: list[str] = []
    for name in ARTIFACTS:
        directory = arguments.build_root / name
        image = directory / "neutrinos-slice.raw"
        uki = directory / "neutrinos-slice.efi"
        if not image.is_file() or not uki.is_file():
            missing.append(name)
            continue
        command_line = kernel_command_line(uki)
        artifacts[name] = {
            "files": {
                path.name: digest(path)
                for path in sorted(directory.iterdir())
                if path.is_file() and not path.is_symlink()
            },
            "kernel_command_line": command_line,
            "usrhash": command_line.split("usrhash=")[1].split()[0]
            if "usrhash=" in command_line
            else None,
        }

    if missing:
        print(
            "retain-artifact-digests: incomplete artifact set, missing "
            + ", ".join(missing),
            file=sys.stderr,
        )
        return 1

    # The command line is a held constant across the set. Reported rather than
    # enforced: a set that fails this is a finding for the record to carry, not
    # a reason to refuse to record what was built.
    lines = {
        # usrhash= necessarily differs per artifact; everything else must not.
        name: " ".join(
            word
            for word in str(entry["kernel_command_line"]).split()
            if not word.startswith("usrhash=")
        )
        for name, entry in artifacts.items()
    }
    uniform = len(set(lines.values())) == 1

    record = {
        "task": "PLN-0002-06",
        "retained": datetime.now().astimezone().isoformat(),
        "artifact_count": len(artifacts),
        "confext_rebuilt": arguments.confext_rebuilt == "yes",
        "kernel_command_line_uniform": uniform,
        "kernel_command_line_less_usrhash": sorted(set(lines.values())),
        "artifacts": artifacts,
    }

    arguments.destination.parent.mkdir(parents=True, exist_ok=True)
    arguments.destination.write_text(
        json.dumps(record, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"retained {len(artifacts)} artifact digests to {arguments.destination}")
    if not uniform:
        print(
            "retain-artifact-digests: the kernel command line is NOT uniform "
            "across the set; the artifacts are not all members of the declared "
            "parameter set",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
