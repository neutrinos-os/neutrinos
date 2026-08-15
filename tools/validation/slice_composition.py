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

# The two arms of the C-007 comparison, each an arm directory beside the shared
# repart definitions, selected by NEUTRINOS_SLICE_ARM in compose.sh.
DECLARED_ARMS = ("erofs", "ext4")
ARM_DEFINITION = "10-usr.conf"
# Every setting the arms are allowed to disagree about, with why, and on which
# arms it may appear at all. Anything else that differs is a second variable in
# a comparison whose whole design is one.
#
# `present_on` is the part that does the work, and it was added after the first
# draft was measured: with the permission expressed as a bare list of keys, an
# injected `Compression=zstd` on the ext4 arm passed. That is not a hypothetical
# -- a compressing ext4 arm would silently turn the size and transfer-size
# criteria into a comparison of two compressors. The permission is a shape, not
# a key.
PERMITTED_ARM_ASYMMETRY = {
    "Format": {
        "reason": "the variable under test",
        "present_on": DECLARED_ARMS,
    },
    "Compression": {
        "reason": "ext4 cannot compress, so no symmetric setting exists",
        "present_on": ("erofs",),
    },
    "CompressionLevel": {
        "reason": "ext4 cannot compress, so no symmetric setting exists",
        "present_on": ("erofs",),
    },
}


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

    # PLN-0002-11: the fixture this check reads is no longer one artifact's.
    # It builds two arms, and the comparison they exist for is void if they
    # differ anywhere but the measured variable.
    arms = arm_symmetry(failures)

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "arms": arms,
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


def partition_settings(path: Path) -> dict[str, str]:
    """Read `Key=Value` settings from a repart definition.

    Same line-anchored rule as `composition_settings`, and for the same reason:
    a continuation line carries no `=` at column zero.
    """
    settings: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or line.startswith("["):
            continue
        match = SETTING.match(line)
        if match:
            settings[match.group(1)] = match.group(2).strip()
    return settings


def arm_symmetry(failures: list[str]) -> dict[str, Any]:
    """Assert the two arms differ only in the variable PLN-0002 measures.

    `mkosi.repart.erofs/10-usr.conf` says it out loud -- "the diff between them
    is the whole of what PLN-0002 is measuring, and anything else that drifts
    apart here is a second variable and voids the comparison" -- and then asks
    the reader to enforce it by eye. Every other control in this repository that
    was left to the eye has been caught failing: the superseded certificate, the
    module list that ships 130 against 21 declared, the uncompressed EROFS arm.
    This makes the comparison's central premise a check.

    The permitted asymmetry is enumerated rather than tolerated as a class.
    `Format=` is the variable. Compression is asymmetric because ext4 cannot
    compress, which is a stated limit of the comparison and not a free
    parameter: it is what makes PLN-0002-13 owe a sentence saying part of any
    EROFS win is compression rather than format. A third difference appearing
    here is a second variable, and it fails.
    """
    arm_directories = sorted(
        path for path in COMPOSITION.parent.glob("mkosi.repart.*") if path.is_dir()
    )

    if {path.name for path in arm_directories} != {
        f"mkosi.repart.{arm}" for arm in DECLARED_ARMS
    }:
        failures.append(
            f"arm definition directories are {[p.name for p in arm_directories]}; "
            f"the declared arms are {sorted(DECLARED_ARMS)}"
        )

    # The arm files share a filename and the shared directory has none, so
    # exactly one is ever read. If the shared directory grew a 10-usr.conf the
    # result would depend on systemd's masking order between definition
    # directories, which is precisely the reasoning the arm files rely on.
    shared = COMPOSITION.parent / "mkosi.repart" / ARM_DEFINITION
    if shared.is_file():
        failures.append(
            f"{shared.relative_to(ROOT)} exists, so which /usr definition wins "
            f"depends on masking order between definition directories"
        )

    settings: dict[str, dict[str, str]] = {}
    for arm in sorted(DECLARED_ARMS):
        definition = COMPOSITION.parent / f"mkosi.repart.{arm}" / ARM_DEFINITION
        if not definition.is_file():
            failures.append(f"arm {arm} has no {ARM_DEFINITION}")
            continue
        settings[arm] = partition_settings(definition)

    differing: dict[str, dict[str, str | None]] = {}
    if len(settings) == len(DECLARED_ARMS):
        keys = set().union(*(set(values) for values in settings.values()))
        for key in sorted(keys):
            observed = {arm: values.get(key) for arm, values in settings.items()}
            if len(set(observed.values())) > 1:
                differing[key] = observed
        unexpected = sorted(set(differing) - set(PERMITTED_ARM_ASYMMETRY))
        if unexpected:
            failures.append(
                "the arms differ in settings beyond the measured variable, so "
                "the comparison carries more than one variable: "
                + "; ".join(f"{key}={differing[key]}" for key in unexpected)
            )
        for key, permission in PERMITTED_ARM_ASYMMETRY.items():
            allowed = set(permission["present_on"])
            observed = {arm for arm, values in settings.items() if key in values}
            if observed - allowed:
                failures.append(
                    f"{key} is set on {sorted(observed)}; the comparison permits "
                    f"it only on {sorted(allowed)}, because {permission['reason']}"
                )
        for arm, values in settings.items():
            if values.get("Format") != arm:
                failures.append(
                    f"arm directory mkosi.repart.{arm} sets Format="
                    f"{values.get('Format')!r}, so its name does not describe "
                    f"the artifact it builds"
                )

    return {
        "declared_arms": sorted(DECLARED_ARMS),
        "held_constant": sorted(
            key
            for arm in sorted(settings)[:1]
            for key in settings[arm]
            if key not in differing
        ),
        "permitted_asymmetry": dict(PERMITTED_ARM_ASYMMETRY),
        "observed_asymmetry": {key: differing[key] for key in sorted(differing)},
    }


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

    # The closure has two declared sources: the repository, and an overlay
    # supplying systemd 261 because C-013 needs it and Fedora 44 ships 259.x.
    # Keyed by file name, matched against one built from the manifest's separate
    # fields -- never parsed back out of one, since only the last two hyphens of
    # `name-version-release.arch` are separators and the name may contain more.
    overlay_published: dict[str, str] = {
        member["name"]: overlay["name"]
        for overlay in declared["packages"].get("overlays", [])
        for member in overlay["files"]
    }

    unattributed: list[str] = []
    overlay_attributed: dict[str, str] = {}
    attributed = 0
    for package in manifest.get("packages", []):
        # `gpg-pubkey` is a key in the RPM database, not a build from a
        # repository, so no repository publishes it.
        if package.get("name") == "gpg-pubkey":
            continue
        version = str(package.get("version"))
        epoch, _, evr = version.rpartition(":") if ":" in version else ("0", "", version)
        nevra = f"{package['name']}-{epoch or '0'}:{evr}.{package['architecture']}"
        filename = f"{package['name']}-{evr}.{package['architecture']}.rpm"
        if nevra in published:
            attributed += 1
        elif filename in overlay_published:
            overlay_attributed[filename] = overlay_published[filename]
        else:
            unattributed.append(nevra)

    if unattributed:
        failures.append(
            "packages in the shipped closure are published by neither the "
            "declared repository nor a declared overlay:\n  "
            + "\n  ".join(sorted(unattributed))
        )

    # The converse: a declared overlay package that ships nothing means the
    # build resolved it elsewhere, which is what this check exists to catch.
    unshipped = sorted(set(overlay_published) - set(overlay_attributed))
    if unshipped:
        failures.append(
            "declared overlay packages are absent from the shipped closure:\n  "
            + "\n  ".join(unshipped)
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
                # Named, not counted: these are the packages that do not come
                # from the distribution.
                "overlay_attributed": dict(sorted(overlay_attributed.items())),
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
