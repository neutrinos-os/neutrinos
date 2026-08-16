#!/usr/bin/env python3
"""The few things every slice helper does the same way.

Four functions, and the bar for a fifth is high. What belongs here is a fact
about this project that more than one helper states -- which mkosi runs, where
a build root lives -- not a convenience. Each helper's fail-closed messages and
freshness keys stay where they are: those are specific to what that helper
knows, and generalising them would build a framework nobody asked for.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path


def default_build_root() -> Path:
    """Where the build root lives when nobody says otherwise.

    One expression, previously repeated in four measurement tools and two shell
    scripts. The shell copies remain until those scripts do.
    """
    override = os.environ.get("NEUTRINOS_SLICE_BUILD_ROOT")
    if override:
        return Path(override)
    cache = os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
    return Path(cache) / "neutrinos" / "slice"


def digest(path: Path) -> str:
    """SHA-256 of one file, read in chunks because artifacts are gigabytes."""
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            hasher.update(chunk)
    return hasher.hexdigest()


def remove_tree(tree: Path) -> None:
    """Delete a tree that may contain directories with no write permission.

    An extracted `/usr` carries mode-0555 directories, so `rmtree` fails partway
    through. Suppressing that with `ignore_errors` leaves a half-deleted tree
    the next step then reads as if it were complete -- measured 2026-08-16,
    when a tools tree that failed to delete left 1,527 files behind and the
    build reported success. Nothing here suppresses an error: the chmod walk
    makes the delete able to succeed, and a delete that still fails raises.
    """
    if not tree.exists():
        return
    for directory, _, _ in os.walk(tree):
        path = Path(directory)
        path.chmod(path.stat().st_mode | stat.S_IRWXU)
    shutil.rmtree(tree)


def run_mkosi(build_root: Path, arguments: list[str], *, cwd: Path) -> None:
    """Run the mkosi this build root provisioned, against the tools tree it built.

    Which mkosi and which tools tree are the shared facts. Everything else --
    keys, output directory, verbs -- belongs to the caller, because the two
    callers compose different things: an extension signed by one of four
    subjects, and the artifact itself.

    The commit is not named here. buildroot.py checks out the declared one into
    `$build_root/mkosi`, so pointing PYTHONPATH at it is what makes this the
    declared mkosi rather than whatever is installed on the host.
    """
    environment = dict(os.environ, PYTHONPATH=str(build_root / "mkosi"))
    subprocess.run(
        [
            sys.executable, "-m", "mkosi",
            f"--tools-tree={build_root / 'tools'}",
            *arguments,
        ],
        cwd=cwd,
        env=environment,
        check=True,
    )
