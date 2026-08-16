#!/usr/bin/env python3
"""Retain the declared repository subset the build actually resolved against.

PLN-0001-07 found that the slice retained packages and no repository metadata,
so a rebuild with the network removed could not resolve at all: the declared
repository was a URL, and the bytes behind it were retained only by accident,
as a side effect of whichever build ran last. This makes retention a build step
instead of an accident.

What is retained: the declared repository's metadata exactly as published, and
every package the build downloaded, laid out at the paths that metadata names.
The metadata is upstream's and unmodified, so resolving against the retained
copy is resolving against the declared repository -- restricted to what was
retained. A package that was never retained fails the build rather than being
reached for elsewhere.

Retention fails closed on a package the declared repository does not contain.
PLN-0001-06's injected faults left 58 such RPMs in a shared cache; a retention
step that copied them forward would launder an undeclared input into a declared
one.

This is not a mirror of the repository. It is the subset one composition
resolved, which is the only part reconstruction needs and the only part whose
provenance this slice can state.

Which publication of the repository is checked here, against the declared
`metadata_digest`, and not only downstream in T2-SLICE-002. The declaration
records a URL *and* a digest because the URL alone is not an identity, and a
retention step that fetched whatever the URL served would retain the wrong
repository and say nothing. The digest is also what makes an already-retained
tree reusable: it is the key that says the tree on disk is the declared
repository rather than merely a repository.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from common import digest
from declaration import load, repository

ROOT = Path(__file__).resolve().parent

COMMON_NS = "{http://linux.duke.edu/metadata/common}"
REPO_NS = "{http://linux.duke.edu/metadata/repo}"
RETENTION_RECORD = "retained.json"


def fetch(url: str, destination: Path) -> bytes:
    """Download one file and return its bytes, writing it under the retention root."""
    with urllib.request.urlopen(url, timeout=120) as response:  # noqa: S310
        payload = response.read()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    return payload


def decompress(path: Path) -> bytes:
    if path.suffix == ".zst":
        return subprocess.run(
            ["zstd", "-dc", str(path)], check=True, stdout=subprocess.PIPE
        ).stdout
    if path.suffix == ".gz":
        import gzip

        return gzip.decompress(path.read_bytes())
    return path.read_bytes()


def retain_metadata(url: str, declared_digest: str, destination: Path) -> Path:
    """Fetch `repomd.xml` and every file it references. Returns the primary index.

    Everything `repomd.xml` names is retained, not just the primary index. A
    later check may need the filelists, and a partial copy of a signed index is
    a copy whose completeness nobody can verify.
    """
    repomd = destination / "repodata" / "repomd.xml"
    if repomd.is_file():
        # The declared repository is frozen, so its metadata cannot have moved.
        # Re-fetching it every build would put a network dependency on the
        # offline rebuild this retention exists to make possible.
        #
        # Reuse is keyed on the declared digest, not on the file existing. An
        # existence guard reuses whatever is in the directory, so editing the
        # declared repository left the previous one's metadata in place and
        # retention went on attributing packages to it. That failed open at
        # build time and was caught only downstream, by T2-SLICE-002 comparing
        # the same two values this now compares before using either.
        found = digest(repomd)
        if found != declared_digest:
            raise SystemExit(
                f"the retained metadata under {destination} is not the declared "
                f"repository\n  declared {declared_digest}\n  found    {found}\n"
                "Remove the retention directory and re-run to retain the "
                "declared one. It is not removed here: it is the input an "
                "offline rebuild resolves against, and discarding it on a "
                "declaration edit would trade a stop you can recover from for "
                "a loss you cannot."
            )
        primary = next(
            (
                path
                for path in (destination / "repodata").glob("*primary.xml.*")
                if path.suffix in (".zst", ".gz")
            ),
            None,
        )
        if primary is not None:
            return primary
    fetch(f"{url}/repodata/repomd.xml", repomd)

    # Verified before anything it names is fetched, so a repository that is not
    # the declared one costs one request rather than a full retention. Left in
    # place rather than deleted, as acquire_overlay.py leaves a mismatched
    # overlay file: what arrived is evidence about what the URL is serving, and
    # the next run must fail on it again rather than quietly re-fetch.
    found = digest(repomd)
    if found != declared_digest:
        raise SystemExit(
            f"{url} serves metadata that is not the declared publication\n"
            f"  declared {declared_digest}\n  found    {found}"
        )

    primary: Path | None = None
    for data in ET.fromstring(repomd.read_bytes()):
        location = data.find(f"{REPO_NS}location")
        if location is None:
            continue
        href = location.get("href")
        if href is None:
            continue
        target = destination / href
        fetch(f"{url}/{href}", target)
        if data.get("type") == "primary" and target.name.endswith(("primary.xml.zst", "primary.xml.gz")):
            primary = target

    if primary is None:
        raise SystemExit("declared repository publishes no primary index this can read")
    return primary


def retain(
    *, cache: Path, destination: Path, overlay: Path | None = None,
    input_set: Path | None = None,
) -> None:
    """Retain the declared repository subset this build resolved against.

    `overlay` is the root of the verified package overlays. Their files are
    declared inputs, so a copy of one appearing in the build cache is expected
    rather than a fault -- but only a file the overlay actually contains,
    matched by name against what acquire_overlay has already verified by digest.
    """
    # Read here rather than passed in. compose.sh restated the URL because a
    # shell script cannot parse TOML without a dependency this slice has not
    # declared, which left the last copy of a declared value outside the
    # declaration; and the digest below has no argument at all, so a caller
    # supplying the URL could not have supplied the identity that goes with it.
    declared = repository(load(input_set))

    overlay_files: set[str] = set()
    if overlay is not None and overlay.is_dir():
        overlay_files = {path.name for path in overlay.rglob("*.rpm")}

    destination.mkdir(parents=True, exist_ok=True)

    primary = retain_metadata(declared["url"], declared["metadata_digest"], destination)
    locations: dict[str, str] = {}
    for package in ET.fromstring(decompress(primary)):
        location = package.find(f"{COMMON_NS}location")
        if location is None:
            continue
        href = location.get("href")
        if href:
            locations[Path(href).name] = href

    retained: list[str] = []
    undeclared: list[str] = []
    from_overlay: list[str] = []
    for rpm in sorted(Path(cache).rglob("*.rpm")):
        href = locations.get(rpm.name)
        if href is None:
            # The overlay is retained by acquire_overlay.py, at its own path and
            # against its own declaration. It is not copied in here: the
            # repository retention is a copy of one repository, and mixing a
            # second source into it would make the retained tree say the
            # declared repository contains packages it does not.
            if rpm.name in overlay_files:
                from_overlay.append(rpm.name)
            else:
                undeclared.append(rpm.name)
            continue
        target = destination / href
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            try:
                os.link(rpm, target)
            except OSError:
                target.write_bytes(rpm.read_bytes())
        retained.append(href)

    if undeclared:
        # Fail closed. A package in the build's own cache that the declared
        # repository does not contain came from somewhere the declaration does
        # not name, and retaining it would make it look declared next time.
        print(
            "packages in the build cache are absent from the declared repository:\n  "
            + "\n  ".join(sorted(undeclared)),
            file=sys.stderr,
        )
        raise SystemExit(
            "retention refuses to launder an undeclared input into a declared one"
        )

    record = {
        "overlay_package_count": len(from_overlay),
        "package_count": len(retained),
        "repomd_sha256": digest(destination / "repodata" / "repomd.xml"),
        "retained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_url": declared["url"],
    }
    (destination / RETENTION_RECORD).write_text(
        json.dumps(record, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"retained {len(retained)} packages and the repository metadata under "
        f"{destination}; {len(from_overlay)} came from the declared overlay and are "
        "retained with it"
    )
