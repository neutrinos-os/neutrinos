#!/usr/bin/env python3
"""Provision the build root the composition resolves its inputs from.

The build root is not the artifact. It holds mkosi at its declared commit and
a tools tree carrying the package manager that resolves the image, and both
outlive any number of compositions. Separating them from `compose.sh` is what
lets each be rebuilt when its own declaration moves rather than when someone
remembers.

Both are read from `input-set.toml` rather than restated here, for the reason
`acquire-overlay.py` already gives: verifying against a copy of a declaration
checks that the copy is self-consistent, which is not the property anyone
wants. `compose.sh` carried a second copy of the base image, the repository
URL, the tools package list and the mkosi commit, and said so -- "sh cannot
validate TOML without a dependency this slice has not declared ... until then
a drift is unguarded." Python can read it, so the copy is gone and the drift
with it.

The tools tree is keyed by a digest of what it is built from. It was keyed by
existence, so adding a package to `[tools_tree] packages` left the previous
tree in place and the next composition resolved the image with it, reporting
success. That is the failure C-009 walks into: measuring the XFS arm needs
`xfsprogs` here, and by existence nothing would have rebuilt anything. The
declaration is the identity; a tree built from a different one is not the tree
the declaration names.

The digest deliberately covers only what the tree is built from. mkosi's commit
is not in it -- the checkout below is unconditional, so it already matches -- and
neither is the package overlay, which `acquire-overlay.py` verifies file by
file against its own declared digests.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

from declaration import load, repository

ROOT = Path(__file__).resolve().parent

# Not in the declaration, so not read from it. `[[tools]]` names mkosi and pins
# its commit, which is the identity that matters, but records no clone source.
# Adding one is a declared-input change to `input-set.toml` and its schema,
# which is the owner's call and not something to arrange from here.
MKOSI_REPOSITORY = "https://github.com/systemd/mkosi"

# The four subjects of the signing-material table in
# docs/project/artifact-parameter-declaration.md, generated into the build root
# and destroyed with it. Synthetic throughout: PLN-0002 forbids production
# material and needs none, since what is under test is whether the mechanism
# binds, not whose key signs.
#
# They were generated in two places -- three here and the platform key in
# enroll-fixture.sh -- under guards written twice and differing. The declaration
# holds them in one table because their distinctness is the measurement:
# T4-CONFEXT-001's entire content is which signer `db` carries, and a shared
# subject would make enrolling one enroll the other. One table there, one owner
# here.
#
# The verity subject is restated rather than read, which the declaration
# sanctions in as many words: "one subject" is not a value a build script can
# check itself against, so the literal is named there and guarded here.
VERITY_SUBJECT = "NeutrinOS verity, synthetic"

SIGNING_MATERIAL = (
    ("verity", VERITY_SUBJECT),
    ("verity-wrong", "NeutrinOS slice verity, synthetic, unenrolled"),
    ("secureboot", "NeutrinOS image, synthetic"),
    ("platform", "NeutrinOS slice platform key, synthetic"),
)


def tools_tree_identity(declaration: dict) -> str:
    """Digest what the tools tree is built from, not what it came out as.

    The tree itself cannot be digested: `input-set.toml` records that exporting
    it produces unstable timestamps, so its digest would move without any input
    moving. The recipe is stable and is what the declaration actually names.
    """
    tools_tree = declaration["tools_tree"]
    recipe = {
        "base_image": tools_tree["base_image"],
        # Sorted: the declaration's order is editorial, and reordering the list
        # is not a change to the tree it produces.
        "packages": sorted(tools_tree["packages"]),
        "repository": repository(declaration)["url"],
    }
    canonical = json.dumps(recipe, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def mkosi_commit(declaration: dict) -> str:
    for tool in declaration.get("tools", []):
        if tool["name"] == "mkosi":
            if tool["identity_kind"] != "git-commit":
                raise SystemExit(
                    f"input set declares mkosi by {tool['identity_kind']}; this "
                    "provisions a git checkout and can resolve a commit only"
                )
            return tool["identity"]
    raise SystemExit("input set declares no mkosi tool")


def provision_mkosi(build_root: Path, commit: str) -> None:
    """Clone once, check out every time.

    The checkout is unconditional because the commit is the input: a build root
    provisioned before the pin moved would otherwise keep the old tree and
    compose with a different mkosi than the one declared.
    """
    checkout = build_root / "mkosi"
    if not checkout.is_dir():
        subprocess.run(
            ["git", "clone", "--quiet", "--filter=blob:none", MKOSI_REPOSITORY, str(checkout)],
            check=True,
        )
    subprocess.run(["git", "-C", str(checkout), "checkout", "--quiet", commit], check=True)


def remove_tree(tree: Path) -> None:
    """Delete an exported root filesystem, which resists ordinary deletion.

    The Fedora base image ships thirteen directories at mode 0555 -- `/usr/bin`,
    `/usr/lib` and the rest -- and nothing can be unlinked inside a directory
    without write permission, so `rmtree` fails partway through. Suppressing
    that with `ignore_errors` leaves a half-deleted tree that the next step
    builds on top of: measured 2026-08-16, it left 1,527 files and no
    `etc/resolv.conf`. The modes are restored to writable first, and a failure
    after that is reported rather than ignored.
    """
    if not tree.exists():
        return
    for directory, _, _ in os.walk(tree):
        path = Path(directory)
        path.chmod(path.stat().st_mode | stat.S_IRWXU)
    shutil.rmtree(tree)


def build_tools_tree(build_root: Path, declaration: dict) -> None:
    """Build the tools tree from the frozen repository, not from the host.

    The host's rolling packages in this position would be an undeclared, moving
    input deciding what the image contains.
    """
    tree = build_root / "tools"
    archive = build_root / "tools.tar"
    log = build_root / "tools-build.log"

    container = subprocess.run(
        [
            "podman",
            "create",
            "--net=host",
            declaration["tools_tree"]["base_image"],
            "dnf5",
            "-y",
            f"--repofrompath=pin,{repository(declaration)['url']}",
            "--repo=pin",
            "--nogpgcheck",
            "install",
            *declaration["tools_tree"]["packages"],
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    try:
        with log.open("wb") as handle:
            result = subprocess.run(
                ["podman", "start", "--attach", container],
                stdout=handle,
                stderr=subprocess.STDOUT,
                check=False,
            )
        if result.returncode != 0:
            tail = log.read_text(encoding="utf-8", errors="replace").splitlines()[-20:]
            raise SystemExit(
                f"tools tree: package installation exited {result.returncode}; "
                f"last lines of {log}:\n  " + "\n  ".join(tail)
            )
        with archive.open("wb") as handle:
            subprocess.run(["podman", "export", container], stdout=handle, check=True)
    finally:
        subprocess.run(["podman", "rm", "--force", container], check=False, capture_output=True)

    # Extracted beside the tree and swapped into place, rather than over it: a
    # tree carrying files from a previous declaration is neither declaration's
    # tree, and an extraction that fails halfway must not leave one that looks
    # provisioned. Until the rename, the existing tree is untouched.
    staging = build_root / "tools.staging"
    remove_tree(staging)
    staging.mkdir(parents=True)
    subprocess.run(["tar", "-C", str(staging), "-xf", str(archive)], check=True)
    archive.unlink()

    # mkosi refuses a tools tree without this path; the sandbox supplies the
    # contents at build time.
    (staging / "etc" / "resolv.conf").touch()

    remove_tree(tree)
    staging.rename(tree)


def provision_tools_tree(build_root: Path, declaration: dict) -> bool:
    """Build the tools tree when it does not match the declaration.

    The stamp sits beside the tree rather than inside it: a file written into an
    exported root filesystem would be a file in the image's tools tree that no
    declaration accounts for.
    """
    tree = build_root / "tools"
    stamp = build_root / "tools.input-digest"
    declared = tools_tree_identity(declaration)

    if tree.is_dir() and stamp.is_file():
        if stamp.read_text(encoding="utf-8").strip() == declared:
            return False
        reason = "the declaration moved"
    elif tree.is_dir():
        # Provisioned before the tree was keyed at all. Rebuilt once, because
        # what it was built from cannot be established by looking at it.
        reason = "it predates the input digest"
    else:
        reason = "there is none"

    print(f"tools tree: building because {reason}")
    build_tools_tree(build_root, declaration)
    stamp.write_text(declared + "\n", encoding="utf-8")
    return True


def certificate_subject(certificate: Path) -> str:
    return subprocess.run(
        ["openssl", "x509", "-noout", "-subject", "-in", str(certificate)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def provision_signing_material(build_root: Path) -> list[str]:
    """Generate what is missing; never regenerate what exists.

    Every guard is on the certificate rather than the key: openssl writes the
    key first, and an interrupted run otherwise leaves a key with no certificate
    that a key-guarded check skips forever. Observed in the PLN-0002-01 spike.

    The verity subject is checked against the certificate rather than against a
    marker file. Changing the declared string alone would otherwise be a silent
    no-op on an existing build root, reading as satisfied while every artifact
    kept the old signer. It fails rather than regenerating, because regenerating
    would change the signature of artifacts already measured.
    """
    keys = build_root / "keys"
    keys.mkdir(parents=True, exist_ok=True)
    generated: list[str] = []

    verity = keys / "verity.crt"
    if verity.is_file():
        observed = certificate_subject(verity)
        if observed != f"subject=CN={VERITY_SUBJECT}":
            raise SystemExit(
                f"{verity} has {observed}, and the declaration names "
                f"'subject=CN={VERITY_SUBJECT}'. Artifacts signed by the old key "
                "keep it until they are rebuilt. To adopt the declared subject:\n"
                f"  rm -f {keys}/verity.key {keys}/verity.crt {keys}/verity.der"
            )

    for name, subject in SIGNING_MATERIAL:
        certificate = keys / f"{name}.crt"
        if not certificate.is_file():
            subprocess.run(
                [
                    "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                    "-days", "30", "-subj", f"/CN={subject}/",
                    "-keyout", str(keys / f"{name}.key"), "-out", str(certificate),
                ],
                check=True,
                capture_output=True,
            )
            generated.append(name)

        # UEFI db takes DER and openssl emits PEM. All four, so the negative
        # cases are enrollable too.
        der = keys / f"{name}.der"
        if not der.is_file():
            subprocess.run(
                ["openssl", "x509", "-outform", "DER", "-in", str(certificate),
                 "-out", str(der)],
                check=True,
                capture_output=True,
            )

    return generated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-set", type=Path, default=ROOT / "input-set.toml", help="declaration to read"
    )
    parser.add_argument("--build-root", required=True, type=Path, help="build root to provision")
    arguments = parser.parse_args()

    declaration = load(arguments.input_set)
    build_root = arguments.build_root
    build_root.mkdir(parents=True, exist_ok=True)

    generated = provision_signing_material(build_root)
    print(
        f"signing material: generated {', '.join(generated)}"
        if generated
        else f"signing material: {len(SIGNING_MATERIAL)} subjects already present"
    )

    commit = mkosi_commit(declaration)
    provision_mkosi(build_root, commit)
    print(f"mkosi: checked out {commit[:12]}")

    if not provision_tools_tree(build_root, declaration):
        print(f"tools tree: matches the declaration ({tools_tree_identity(declaration)[:12]})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
