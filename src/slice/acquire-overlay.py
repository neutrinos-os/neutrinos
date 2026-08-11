#!/usr/bin/env python3
"""Acquire and verify the package overlays the input set declares.

PLN-0002-02. An overlay is the one way a package enters the image without
coming from the frozen repository, so it is the one place where the
single-repository guarantee `LocalMirror=` enforces by construction could be
lost. It is not lost here for two reasons: the overlay is injected as a local
package directory rather than as a second repository, so exactly one repository
still exists; and every file in it is declared by SHA-256 and verified against
that digest before the build can use it.

The digests are read from `input-set.toml` directly rather than restated in
`compose.sh`. Verifying against a copy of a declaration checks that the copy is
self-consistent, which is not the property anyone wants.

The declared source is a continuously republished nightly. That is exactly the
case where a URL is not an identity: upstream replaces the file in place, and
without the digest a later build would resolve something else under the same
name and say nothing. Here it stops the build.

Retention is the same idea as `retain-repository.py`: a verified file already
present is left alone and never re-fetched, so an offline rebuild resolves the
bytes that were declared rather than whatever the URL serves today.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            hasher.update(chunk)
    return hasher.hexdigest()


def acquire(overlay: dict, destination: Path) -> list[str]:
    """Fetch what is missing, verify everything, and report what was verified."""
    destination.mkdir(parents=True, exist_ok=True)
    verified: list[str] = []

    for entry in overlay["files"]:
        target = destination / entry["name"]
        if not target.is_file():
            url = f"{overlay['source']}/{entry['name']}"
            try:
                with urllib.request.urlopen(url, timeout=300) as response:  # noqa: S310
                    target.write_bytes(response.read())
            except urllib.error.URLError as error:
                raise SystemExit(
                    f"overlay {overlay['name']}: cannot fetch {entry['name']}: {error}"
                ) from error

        found = digest(target)
        if found != entry["sha256"]:
            # Fail closed, and leave the file in place rather than deleting it:
            # what arrived is evidence about what upstream is serving, and the
            # next run must not quietly re-fetch and re-fail.
            raise SystemExit(
                f"overlay {overlay['name']}: {entry['name']} does not match the "
                f"declaration\n  declared {entry['sha256']}\n  found    {found}"
            )
        verified.append(entry["name"])

    # Anything else in the directory is undeclared. A stale file from an earlier
    # overlay version would still be a package in a directory the build resolves
    # from, which is the whole failure mode this exists to prevent.
    declared = {entry["name"] for entry in overlay["files"]}
    undeclared = sorted(p.name for p in destination.iterdir() if p.name not in declared)
    if undeclared:
        raise SystemExit(
            f"overlay {overlay['name']}: undeclared files present:\n  "
            + "\n  ".join(undeclared)
        )

    return verified


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-set", type=Path, default=ROOT / "input-set.toml", help="declaration to read"
    )
    parser.add_argument("--destination", required=True, type=Path, help="overlay root")
    arguments = parser.parse_args()

    record = tomllib.loads(arguments.input_set.read_text(encoding="utf-8"))
    overlays = record.get("packages", {}).get("overlays", [])
    if not overlays:
        print("no package overlay declared")
        return 0

    for overlay in overlays:
        verified = acquire(overlay, arguments.destination / overlay["name"])
        print(
            f"overlay {overlay['name']}: {len(verified)} files verified against the declaration"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
