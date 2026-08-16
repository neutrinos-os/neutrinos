#!/usr/bin/env python3
"""Resolve a role's package selections from its capability declaration.

This is what makes src/roles/<role>/capabilities.toml a mechanism rather than a
description. Composition reads the declaration and installs exactly what it
names; a package that is not declared by some capability does not enter the
image, and a capability whose packages change moves the artifact.

One line per package on stdout, so `sh` can consume it without parsing TOML --
the same reason compose.sh duplicates input-set.toml rather than reading it.

Nothing here resolves, validates or orders packages. Whether a name exists in
the declared closure is composition's answer to give, and it gives it by
failing; guessing here would move that failure somewhere quieter.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGES = ("session", "workflow")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True)
    parser.add_argument(
        "--stage",
        action="append",
        choices=STAGES,
        help="Stage to include; repeatable. Omitted means every stage.",
    )
    arguments = parser.parse_args()

    declaration = ROOT / "src" / "roles" / arguments.role / "capabilities.toml"
    if not declaration.is_file():
        print(f"no capability declaration at {declaration}", file=sys.stderr)
        return 1

    record = tomllib.loads(declaration.read_text(encoding="utf-8"))
    wanted = tuple(arguments.stage) if arguments.stage else STAGES

    # Sorted and de-duplicated. Two capabilities may legitimately want the same
    # package, and the order a TOML table happens to iterate in is not something
    # an artifact's contents should depend on.
    selected = sorted(
        {
            package
            for entry in record["capability"].values()
            if entry["stage"] in wanted
            for package in entry["packages"]
        }
    )
    if not selected:
        print(f"no packages declared for stage(s) {', '.join(wanted)}", file=sys.stderr)
        return 1
    print("\n".join(selected))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
