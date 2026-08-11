#!/usr/bin/env python3
"""Collect the PLN-0001 evidence bundle outside the repository.

PLN-0001-08. The slice's records cite evidence spread across a build root, two
output directories, and validation run directories that live in a temporary
path. This gathers the parts a reader would need to check those records, into
one place with a digest for every file, and leaves the multi-gigabyte artifacts
where they are: the hygiene contract's bounds mean a bundle records identity and
reconstruction rather than bytes.

What it deliberately does not do is copy the disk images, the retained
repository packages, or the extracted trees. Those are reconstructible from the
declared inputs -- which is the claim the slice exists to make -- so the bundle
carries their digests and the commands that rebuild them.

Everything collected is scanned with the same unsafe-output patterns canonical
validation applies to its own diagnostics. Synthetic credentials are still
credentials in a log.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SLICE = ROOT / "src" / "slice"


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            hasher.update(chunk)
    return hasher.hexdigest()


def artifact_digests(directory: Path) -> dict[str, str]:
    if not directory.is_dir():
        return {}
    return {
        path.name: digest(path)
        for path in sorted(directory.iterdir())
        if path.is_file() and not path.is_symlink()
    }


def esp_uki_digest(image: Path) -> str | None:
    """Digest of the UKI stored on the ESP, read through mtools at an offset."""
    if not image.is_file() or shutil.which("mdir") is None:
        return None
    listing = subprocess.run(
        ["mdir", "-/", "-b", "-i", f"{image}@@1048576", "::/EFI/Linux"],
        capture_output=True,
        text=True,
        check=False,
    )
    entries = [line.strip() for line in listing.stdout.splitlines() if line.strip().endswith(".efi")]
    if len(entries) != 1:
        return None
    payload = subprocess.run(
        ["mcopy", "-n", "-i", f"{image}@@1048576", entries[0], "-"],
        capture_output=True,
        check=False,
    )
    return hashlib.sha256(payload.stdout).hexdigest()


def scan_for_unsafe_output(bundle: Path) -> list[dict[str, str]]:
    """Apply canonical validation's own unsafe-output patterns to the bundle."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.validation.check import UNSAFE_OUTPUT_PATTERNS

    findings: list[dict[str, str]] = []
    for path in sorted(bundle.rglob("*")):
        if not path.is_file():
            continue
        payload = path.read_bytes()
        for label, pattern in UNSAFE_OUTPUT_PATTERNS:
            if pattern.search(payload):
                findings.append(
                    {"file": str(path.relative_to(bundle)), "pattern": label}
                )
    return findings


def copy_run(source: Path, destination: Path) -> dict[str, object]:
    """Copy a validation run directory and summarize its results."""
    shutil.copytree(source, destination, dirs_exist_ok=True)
    results = [
        json.loads(line)
        for line in (destination / "results.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return {
        "run": source.name,
        "tests": {entry["id"]: entry.get("result") for entry in results},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-root", required=True, type=Path)
    parser.add_argument("--fast-run", required=True, type=Path, help="check:fast run directory")
    parser.add_argument("--complete-run", required=True, type=Path)
    parser.add_argument(
        "--tree-manifest",
        action="append",
        default=[],
        type=Path,
        help="extracted image tree manifest; repeatable, compared pairwise",
    )
    parser.add_argument("--destination", required=True, type=Path)
    arguments = parser.parse_args()

    bundle: Path = arguments.destination
    if bundle.exists():
        shutil.rmtree(bundle)
    (bundle / "composition").mkdir(parents=True)
    (bundle / "identity").mkdir()
    (bundle / "validation").mkdir()

    build_root: Path = arguments.build_root

    # The declaration and the mechanism, as committed. A record that cites them
    # by path is unreadable once the checkout moves on.
    for source in (
        SLICE / "input-set.toml",
        SLICE / "compose.sh",
        SLICE / "composition" / "mkosi.conf",
        SLICE / "retain-repository.py",
        SLICE / "schema" / "input-set-v2.schema.json",
    ):
        shutil.copy2(source, bundle / "composition" / source.name)

    for name, source in (
        ("neutrinos-slice.manifest", build_root / "out" / "neutrinos-slice.manifest"),
        ("retained.json", build_root / "inputs" / "repository" / "retained.json"),
        ("repomd.xml", build_root / "inputs" / "repository" / "repodata" / "repomd.xml"),
    ):
        if source.is_file():
            shutil.copy2(source, bundle / "composition" / name)

    identity = {
        "networked_build": artifact_digests(build_root / "out"),
        "offline_rebuild": artifact_digests(build_root / "out-offline"),
        "esp_uki": {
            "networked_build": esp_uki_digest(build_root / "out" / "neutrinos-slice.raw"),
            "offline_rebuild": esp_uki_digest(
                build_root / "out-offline" / "neutrinos-slice.raw"
            ),
        },
    }

    # Tree manifests compress by roughly an order of magnitude and are the
    # bulkiest thing worth keeping verbatim, because they are what a disputed
    # identity claim is checked against.
    trees: dict[str, str] = {}
    for manifest in arguments.tree_manifest:
        if not manifest.is_file():
            continue
        label = manifest.parent.name
        target = bundle / "identity" / f"{label}.manifest.gz"
        target.write_bytes(gzip.compress(manifest.read_bytes()))
        trees[label] = digest(manifest)
    identity["extracted_trees"] = trees
    identity["extracted_trees_identical"] = len(set(trees.values())) <= 1
    (bundle / "identity" / "digests.json").write_text(
        json.dumps(identity, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    runs = [
        copy_run(arguments.fast_run, bundle / "validation" / "fast"),
        copy_run(arguments.complete_run, bundle / "validation" / "complete"),
    ]

    revision = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    findings = scan_for_unsafe_output(bundle)

    index = {
        "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "identity": identity,
        "not_collected": {
            "disk images, UKIs, kernels, initrds": "digests only; reconstructible from declared inputs",
            "extracted image trees": "manifests only; the trees are derived from the images",
            "retained repository packages": (
                "121 packages under inputs/repository; identity is retained.json "
                "plus the repository's own signed metadata"
            ),
            "PLN-0001-06 fault injections": "separate bundle at evidence/pln-0001-06",
        },
        "source_revision": revision,
        "unsafe_output_findings": findings,
        "validation": runs,
    }
    (bundle / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        f"{digest(path)}  {path.relative_to(bundle)}"
        for path in sorted(bundle.rglob("*"))
        if path.is_file()
    ]
    (bundle / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")

    if findings:
        print(f"unsafe output found in the bundle: {findings}", file=sys.stderr)
        return 1
    total = sum(path.stat().st_size for path in bundle.rglob("*") if path.is_file())
    print(f"collected {len(lines) + 1} files, {total / 1024:.0f} KiB, into {bundle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
