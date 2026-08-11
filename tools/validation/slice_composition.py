"""Checks that the composition mechanism still enforces the declaration.

Two tests live here, and they are the two mitigations PLN-0001-06 proposed for
F-RES-01 -- the injected fault that did not fail. Replacing `LocalMirror=` with
`Mirror=` restored mkosi's default repository set, admitted Fedora's `updates`
repository, built a complete artifact with 45 of its 104 packages from it, and
passed every check the slice had.

`check_composition_fixture` is the cheap mitigation: assert that the mechanism
file still spells the construction that does the real work. It reads the
fixture, not the artifact, so it cannot speak for an image built somewhere else.

`check_repository_attribution` is the expensive one: assert that every package
in the shipped closure exists in the declared repository. mkosi's manifest
carries no per-package repository field, so attribution is established by
content -- an exact NEVRA present in the declared repository's own metadata --
rather than by a label the builder wrote about itself.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
INPUT_SET = ROOT / "src" / "slice" / "input-set.toml"
COMPOSITION = ROOT / "src" / "slice" / "composition" / "mkosi.conf"
COMPOSE = ROOT / "src" / "slice" / "compose.sh"
COMMON_NS = "{http://linux.duke.edu/metadata/common}"
SETTING = re.compile(r"^([A-Za-z][A-Za-z0-9]*)=(.*)$")
ASSIGNMENT = re.compile(r"^([a-z_]+)=(\S+)$")

# Settings that would widen resolution beyond the single declared repository.
# `LocalMirror=` makes the declared repository the only one that exists; either
# of these puts mkosi's distribution defaults back, and for Fedora that means
# `updates`.
FORBIDDEN_SETTINGS = ("Mirror", "Repositories")


def composition_settings() -> dict[str, str]:
    """Read `Key=Value` settings from the composition fixture.

    Continuation lines are indented and carry no `=`, so a line-anchored match
    reads exactly the settings and none of their continuations. Later
    assignments win, as mkosi resolves them.
    """
    settings: dict[str, str] = {}
    for line in COMPOSITION.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or line.startswith("["):
            continue
        match = SETTING.match(line)
        if match:
            settings[match.group(1)] = match.group(2).strip()
    return settings


def compose_assignments() -> dict[str, str]:
    """Read the shell variables `compose.sh` duplicates from the declaration."""
    assignments: dict[str, str] = {}
    for line in COMPOSE.read_text(encoding="utf-8").splitlines():
        match = ASSIGNMENT.match(line)
        if match:
            assignments[match.group(1)] = match.group(2)
    return assignments


def check_composition_fixture() -> int:
    declared = tomllib.loads(INPUT_SET.read_text(encoding="utf-8"))
    repositories = declared["packages"]["repositories"]
    settings = composition_settings()
    assignments = compose_assignments()
    failures: list[str] = []

    if len(repositories) != 1:
        failures.append(
            f"declaration names {len(repositories)} repositories; this fixture "
            "can only enforce exactly one"
        )
    repository = repositories[0]["url"] if repositories else ""

    local_mirror = settings.get("LocalMirror")
    if local_mirror is None:
        failures.append(
            "composition sets no LocalMirror=, so the declared repository is not "
            "the only one that exists during the build"
        )
    elif local_mirror != repository:
        failures.append(
            f"composition resolves against {local_mirror!r}; the declaration "
            f"names {repository!r}"
        )

    for setting in FORBIDDEN_SETTINGS:
        if setting in settings:
            failures.append(
                f"composition sets {setting}={settings[setting]!r}, which restores "
                "the distribution's default repository set"
            )

    # The mixed-branch faults failed closed on Fedora's per-release GPG keys --
    # an inherited guarantee rather than an enforced one, and one that does not
    # survive a change of distribution. Comparing the fixture's own branch
    # against the declaration makes it enforced here.
    for setting, field in (("Distribution", "distribution"), ("Release", "release")):
        observed = settings.get(setting)
        expected = str(declared["packages"][field])
        if observed is None:
            failures.append(f"composition sets no {setting}=")
        elif observed != expected:
            failures.append(
                f"composition builds {setting}={observed!r}; the declaration "
                f"names {expected!r}"
            )

    # PLN-0001-02 recorded this drift as possible and unguarded: compose.sh
    # repeats the declaration's values because a shell script cannot read TOML
    # without a dependency the slice has not declared.
    tools = {tool["name"]: tool for tool in declared.get("tools", [])}
    for variable, expected in (
        ("repository_url", repository),
        ("mkosi_commit", tools.get("mkosi", {}).get("identity", "")),
        ("tools_image", declared["tools_tree"]["base_image"]),
    ):
        observed = assignments.get(variable)
        if observed is None:
            failures.append(f"compose.sh assigns no {variable}")
        elif observed != expected:
            failures.append(
                f"compose.sh uses {variable}={observed!r}; the declaration names "
                f"{expected!r}"
            )

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "declared_repository": repository,
                "enforced_by": "LocalMirror",
                "forbidden_settings_absent": list(FORBIDDEN_SETTINGS),
                "fixture": str(COMPOSITION.relative_to(ROOT)),
                "result": "passing",
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


def declared_repository_nevras(retained: Path) -> tuple[set[str], str]:
    """Every NEVRA the declared repository publishes, plus its metadata digest.

    Read from the retained copy of the repository's own metadata, which is
    upstream's bytes unmodified. The digest is returned so the caller can bind
    this index to the declaration rather than trusting whatever repository
    happens to be sitting in the retention directory.
    """
    repomd = retained / "repodata" / "repomd.xml"
    digest = hashlib.sha256(repomd.read_bytes()).hexdigest()
    primary = next(
        path
        for path in (retained / "repodata").glob("*primary.xml.*")
        if path.suffix in (".zst", ".gz")
    )
    if primary.suffix == ".zst":
        payload = subprocess.run(
            ["zstd", "-dc", str(primary)], check=True, stdout=subprocess.PIPE
        ).stdout
    else:
        import gzip

        payload = gzip.decompress(primary.read_bytes())

    nevras = set()
    for package in ET.fromstring(payload):
        name = package.find(f"{COMMON_NS}name")
        arch = package.find(f"{COMMON_NS}arch")
        version = package.find(f"{COMMON_NS}version")
        if name is None or arch is None or version is None:
            continue
        epoch = version.get("epoch", "0")
        nevras.add(
            f"{name.text}-{epoch}:{version.get('ver')}-{version.get('rel')}.{arch.text}"
        )
    return nevras, digest


def check_repository_attribution() -> int:
    from tools.validation.check import SLICE_ARTIFACT_ENV, SLICE_REPOSITORY_ENV

    artifact = Path(os.environ[SLICE_ARTIFACT_ENV]).resolve()
    retained = Path(os.environ[SLICE_REPOSITORY_ENV]).resolve()
    declared = tomllib.loads(INPUT_SET.read_text(encoding="utf-8"))
    repository = declared["packages"]["repositories"][0]
    manifest = json.loads(
        (artifact / "neutrinos-slice.manifest").read_text(encoding="utf-8")
    )
    failures: list[str] = []

    published, metadata_digest = declared_repository_nevras(retained)
    if metadata_digest != repository["metadata_digest"]:
        # Without this the test would happily attribute the closure to whatever
        # repository someone put in the retention directory.
        failures.append(
            f"retained metadata digest {metadata_digest} is not the declared "
            f"{repository['metadata_digest']}"
        )

    record_path = retained / "retained.json"
    record = json.loads(record_path.read_text(encoding="utf-8")) if record_path.is_file() else {}
    if record.get("source_url") != repository["url"]:
        failures.append(
            f"retention records source {record.get('source_url')!r}; the "
            f"declaration names {repository['url']!r}"
        )

    unattributed: list[str] = []
    attributed = 0
    for package in manifest.get("packages", []):
        # `gpg-pubkey` is a key in the RPM database, not a build from a
        # repository, so no repository publishes it.
        if package.get("name") == "gpg-pubkey":
            continue
        version = str(package.get("version"))
        epoch, _, evr = version.rpartition(":") if ":" in version else ("0", "", version)
        nevra = f"{package['name']}-{epoch or '0'}:{evr}.{package['architecture']}"
        if nevra in published:
            attributed += 1
        else:
            unattributed.append(nevra)

    if unattributed:
        failures.append(
            "packages in the shipped closure are not published by the declared "
            "repository:\n  " + "\n  ".join(sorted(unattributed))
        )

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "attributed_packages": attributed,
                "declared_repository": repository["url"],
                # Attribution is by exact NEVRA against the declared
                # repository's published index. It establishes that the closure
                # could have come entirely from the declared repository; it
                # cannot detect a rebuild published elsewhere under an identical
                # NEVRA, which would need per-package checksums the manifest
                # does not carry.
                "attribution_basis": "exact NEVRA in the declared repository's primary index",
                "published_packages": len(published),
                "repository_metadata_sha256": metadata_digest,
                "result": "passing",
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


def _main() -> int:
    return check_composition_fixture()


if __name__ == "__main__":
    raise SystemExit(_main())
