#!/usr/bin/env python3
"""Collect an evidence bundle outside the repository.

PLN-0001-08, and PLN-0002-14 on the same terms. The records cite evidence spread
across a build root, several output directories, per-task evidence directories,
and validation run directories that live in a temporary path a reboot removes.
This gathers the parts a reader would need to check those records, into one
place with a digest for every file, and leaves the multi-gigabyte artifacts
where they are: the hygiene contract's bounds mean a bundle records identity and
reconstruction rather than bytes.

The per-task measurement evidence PLN-0002 produced is the exception to
"identity, not bytes": `--task-evidence` copies those directories verbatim,
because a measurement's JSON and the serial console it was read from are the
evidence and are not reconstructible from anything else. They are small.

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

from declaration import load

ROOT = Path(__file__).resolve().parents[2]
SLICE = ROOT / "src" / "slice"


def schema_path() -> Path:
    """The schema `input-set.toml` declares, resolved the way T2-SLICE-001 does.

    Reading the version rather than naming a file keeps the bundle's schema and
    the validated one the same object. A missing file is not raised here: the
    caller skips anything absent, and T2-SLICE-001 is where a declared version
    with no committed schema is a failure.
    """
    declaration = load(SLICE / "input-set.toml")
    return SLICE / "schema" / f"input-set-v{declaration['schema']['version']}.schema.json"


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
    parser.add_argument(
        "--task-evidence",
        action="append",
        default=[],
        type=Path,
        help="per-task evidence directory, copied verbatim; repeatable",
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
        # compose.sh is no longer the whole mechanism. Acquisition, build-root
        # provisioning, the extension fixtures and retention each moved to the
        # helper that owns them, and each reads input-set.toml through
        # declaration.py. A bundle carrying compose.sh alone would carry the
        # selection and none of the resolution.
        SLICE / "declaration.py",
        SLICE / "compose.py",
        SLICE / "buildroot.py",
        SLICE / "acquire-overlay.py",
        SLICE / "fixtures.py",
        SLICE / "retain-repository.py",
        # The schema the declaration names, not a version written here. This
        # said v2 while the declaration had said version 3 since v3 landed, so
        # the bundle carried a schema the record was not validated against --
        # the same defect as an existence guard, in a file list.
        schema_path(),
        *sorted(SLICE.glob("mkosi.repart/*.conf")),
        *sorted(SLICE.glob("composition/mkosi.repart/*.conf")),
        # The measurement mechanisms, on the same ground as compose.sh: every
        # figure in PLN-0002's records was produced by one of these, and a
        # record citing one by path stops being checkable when the checkout
        # moves on.
        *sorted(SLICE.glob("measure-*.py")),
        SLICE / "retain-artifact-digests.py",
        # The enrolment fixture: what the signature dimension of the
        # substitution matrix was measured against.
        SLICE / "enroll-fixture.sh",
    ):
        if source.is_file():
            shutil.copy2(source, bundle / "composition" / source.name)

    for name, source in (
        # Renamed on the way in, because the confext has an `mkosi.conf` of its
        # own and the bundle is flat.
        ("confext-mkosi.conf", SLICE / "confext" / "neutrinos-network" / "mkosi.conf"),
        ("neutrinos-slice.manifest", build_root / "out" / "neutrinos-slice.manifest"),
        ("retained.json", build_root / "inputs" / "repository" / "retained.json"),
        ("repomd.xml", build_root / "inputs" / "repository" / "repodata" / "repomd.xml"),
    ):
        if source.is_file():
            shutil.copy2(source, bundle / "composition" / name)

    # PLN-0002-06 retains a digest for every artifact it builds, and amendment 5
    # makes that six: a primary, a content variant and a seed variant per arm.
    # Discovered by scanning rather than listed, because a hardcoded pair is
    # what this function already was and it silently stopped describing the
    # build root the moment a second arm existed.
    #
    # `out` is skipped: it is the compatibility symlink to out-erofs that
    # compose.sh maintains, and following it would record the EROFS primary
    # twice under two names. `out-offline` is skipped because it is PLN-0001's
    # offline rebuild, already recorded above under its own key, and it is not
    # one of the six.
    spike_artifacts = {
        directory.name: artifact_digests(directory)
        for directory in sorted(build_root.glob("out-*"))
        if directory.is_dir()
        and not directory.is_symlink()
        and directory.name != "out-offline"
    }

    identity = {
        "networked_build": artifact_digests(build_root / "out"),
        "offline_rebuild": artifact_digests(build_root / "out-offline"),
        "pln0002_artifacts": spike_artifacts,
        "pln0002_artifact_count": len(spike_artifacts),
        "pln0002_esp_uki": {
            name: esp_uki_digest(build_root / name / "neutrinos-slice.raw")
            for name in sorted(spike_artifacts)
        },
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

    measurements: dict[str, object] = {}
    for source in arguments.task_evidence:
        if not source.is_dir():
            continue
        target = bundle / "measurements" / source.name
        shutil.copytree(source, target, dirs_exist_ok=True)
        files = [path for path in target.rglob("*") if path.is_file()]
        measurements[source.name] = {
            "files": len(files),
            "bytes": sum(path.stat().st_size for path in files),
            "source": str(source),
        }

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
        "measurements": measurements,
        "not_collected": {
            "disk images, UKIs, kernels, initrds": "digests only; reconstructible from declared inputs",
            "extracted image trees": "manifests only; the trees are derived from the images",
            "retained repository packages": (
                "121 packages under inputs/repository; identity is retained.json "
                "plus the repository's own signed metadata"
            ),
            "PLN-0001-06 fault injections": "separate bundle at evidence/pln-0001-06",
            "VM disks, firmware variables, vTPM state": (
                "destroyed at task end per PLN-0002's boundary; the serial console "
                "of every boot is retained under measurements/"
            ),
            "synthetic signing material": (
                "generated into the build root and destroyed with it; subjects are "
                "declared in the parameter declaration, keys are never collected"
            ),
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
