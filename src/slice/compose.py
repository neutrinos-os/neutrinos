#!/usr/bin/env python3
"""Compose one artifact: the selected arm and variant, built by mkosi.

Per artifact, which is what separates this from its neighbours. buildroot.py
runs once per input set, fixtures.py once per set of test material, and
retain-repository.py once per retained release set; this runs once per artifact
and produces exactly one.

Selection -- which arm, which variant, which role -- is decided by the caller
and arrives as arguments. What a selection *means* is decided here: which
repart directory an arm names, which extra trees and packages a variant adds.
compose.sh holds no list of arms or variants, so adding one is an edit to this
file and not to two.

The one thing this refuses to do is report success without composing. mkosi
declines to rebuild an existing output and exits 0, so a caller that trusted
the exit code would verify the previous artifact against a change it never
built -- measured 2026-08-16, on a rebuild meant to prove a deleted file was
gone.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from common import run_mkosi
from declaration import load

ROOT = Path(__file__).resolve().parent
COMPOSITION = ROOT / "composition"

# Declared, not derived, and deliberately not the composition's own `Seed=`.
# Deriving one from the other would make the relationship between two artifacts
# an algorithm nobody wrote down.
VARIANT_SEED = "8c1e5b47-2d93-4f60-a1e8-7d4c2f0b93a5"

VARIANTS = ("primary", "content", "seed", "state", "session")

# mkosi's verbs, other than `build`. Only a build can be a silent no-op:
# `summary`, `clean` and the rest produce no artifact, so refusing them for an
# output that already exists would break every read-only use -- measured
# 2026-08-16, when the first form of the guard exited 1 on `compose.sh summary`.
READ_ONLY_VERBS = frozenset(
    {
        "summary", "clean", "shell", "boot", "vm", "qemu", "ssh", "journalctl",
        "coredumpctl", "serve", "burn", "sysupdate", "sandbox", "documentation",
        "genkey", "dependencies", "completion", "cat-config", "box",
    }
)

FORCE_FLAGS = frozenset({"--force", "-f", "-ff"})


def refuse_silent_noop(output: Path, arguments: list[str]) -> None:
    """Stop rather than let mkosi decline the rebuild and exit 0.

    The pre-existing mitigation was downstream and indirect: the verity
    certificate is copied unconditionally so T3-SLICE-003 fails later. That
    makes the state visible to validation but leaves this script's exit code
    meaningless, and a build tool whose exit code does not mean "built" is one
    every caller has to work around.
    """
    if any(argument in FORCE_FLAGS for argument in arguments):
        return
    if any(argument in READ_ONLY_VERBS for argument in arguments):
        return
    artifact = output / "neutrinos-slice.raw"
    if artifact.exists():
        raise SystemExit(
            f"compose: {artifact} exists and --force was not passed; mkosi would "
            "decline to rebuild it and this script would report success without "
            "composing anything. Pass --force to rebuild, or remove the output "
            "directory."
        )


def variant_arguments(variant: str, role: str) -> list[str]:
    """What the selected variant adds. Each moves exactly one thing.

    PLN-0002 amendment 5. `primary` is what everything measures; `content` and
    `seed` are PLN-0002-10 substitution sources, and they exist because the
    build is bit-reproducible, so substituting a rebuild is vacuous. Task 10
    needs a substitute validly signed by the enrolled key carrying a root hash
    the UKI does not name:

      content  one declared marker file under /usr, so the image differs
      seed     identical tree, different Seed=, so the identities differ

    Two routes because they fail differently -- a content variant that boots
    means integrity did not bind the contents, a seed variant that boots means
    it did not bind the identity. Anything a variant moves beyond its one thing
    would make a task 10 failure unattributable.
    """
    if variant == "primary":
        return []
    if variant == "content":
        return [f"--extra-tree={COMPOSITION / 'mkosi.extra.variant-content'}"]
    if variant == "seed":
        return [f"--seed={VARIANT_SEED}"]

    # `state` and `session` are not substitution sources. `state` adds the
    # machine-state and home partitions, so it is the first artifact this
    # project has built with anything writable on it. It rides the variant axis
    # because that axis already guarantees the one thing that matters here: a
    # non-primary variant writes to its own output directory and therefore
    # cannot overwrite the six retained PLN-0002-06 members, whose rebuild would
    # void PLN-0002's tally.
    #
    # A second definitions directory rather than partitions added to the shared
    # composition/mkosi.repart/. RepartDirectories= is a list and the CLI
    # appends to it, so repart receives the shared directory, the arm directory
    # and this one; nothing in the shared set is edited, so a `primary` build is
    # byte-identical to what it produced before this variant existed.
    arguments = [
        f"--repart-directory={COMPOSITION / 'state-partitions'}",
        f"--extra-tree={COMPOSITION / 'mkosi.extra.state'}",
    ]
    if variant == "state":
        return arguments

    # State plus a graphical session. It includes the state variant's partitions
    # and mount units rather than repeating them, because the session needs a
    # home volume to put a home directory on: a session composed without one
    # works exactly once, which is the failure shape T4-STATE-001 exists to
    # catch.
    #
    # The package list comes from the role's capability declaration, which is
    # what makes that file a mechanism rather than a description. A package no
    # capability declares does not enter the image, and a capability whose
    # packages change moves the artifact.
    #
    # Only the `session` stage. The `workflow` stage is daily-use capability
    # that follows once a session exists, and pulling it in now would make the
    # first graphical boot depend on twenty packages whose failures are
    # unrelated to whether a session comes up.
    packages = subprocess.run(
        [sys.executable, str(ROOT / "role-packages.py"), f"--role={role}", "--stage=session"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    arguments.append(f"--extra-tree={COMPOSITION / 'mkosi.extra.session'}")
    arguments.extend(f"--package={package}" for package in packages)
    return arguments


def overlay_arguments(declaration: dict, overlay_root: Path) -> list[str]:
    """One package directory per declared overlay, named by the declaration.

    The overlay's name was written here as a literal, which made it the last
    value restated from `input-set.toml` after the others had moved -- and it
    survived the sweep that claimed to remove them, because a name embedded in a
    path does not look like a restated value. Declaring a second overlay would
    have silently left it out of the build.
    """
    return [
        f"--package-directory={overlay_root / overlay['name']}"
        for overlay in declaration.get("packages", {}).get("overlays", [])
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-set", type=Path, default=ROOT / "input-set.toml", help="declaration to read"
    )
    parser.add_argument("--build-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="output directory")
    parser.add_argument("--overlay", required=True, type=Path, help="verified overlay root")
    parser.add_argument("--arm", required=True, help="the /usr filesystem format under test")
    parser.add_argument("--variant", required=True, choices=VARIANTS)
    parser.add_argument("--role", required=True, help="role whose capabilities select packages")
    parser.add_argument(
        "--precheck",
        action="store_true",
        help=(
            "validate the selection and refuse a silent no-op, then exit without "
            "composing. compose.sh runs this before provisioning the build root and "
            "rebuilding the extension fixtures, so a build that will be refused is "
            "refused in a second rather than after a minute of work. The build path "
            "runs the same two checks again: a guard a caller has to remember to ask "
            "for is one a caller can forget."
        ),
    )
    parser.add_argument("mkosi", nargs="*", help="arguments passed through to mkosi")
    arguments = parser.parse_args()

    build_root: Path = arguments.build_root
    output: Path = arguments.output

    repart = COMPOSITION / f"mkosi.repart.{arguments.arm}"
    if not repart.is_dir():
        raise SystemExit(
            f"compose: no arm {arguments.arm!r}; expected a partition definition "
            f"directory at {repart}"
        )

    refuse_silent_noop(output, arguments.mkosi)
    if arguments.precheck:
        return 0

    keys = build_root / "keys"

    # --initrd is passed rather than declared because mkosi has no specifier for
    # the output directory: %C, %P, %D, %F, %I is the whole set. Setting it makes
    # want_default_initrd() return False, so the composition owns an initrd
    # instead of adding to a synthesized one -- PLN-0002-05's ruling of
    # 2026-08-12, and why mkosi.finalize.d/10-initrd-etc-factory no longer
    # exists.
    #
    # Only the arm directory is passed. mkosi picks up the shared
    # composition/mkosi.repart/ by path suffix and appends this to it -- verified
    # against `mkosi summary`. Passing both hands repart the same --definitions
    # twice.
    #
    # The variant's arguments come first so the caller's `--force` or `summary`
    # still reaches mkosi last.
    arguments_to_mkosi = [
        # Package cache inside this build root, not the user's shared mkosi cache: PLN-0001-07
        # found 58 RPMs there that the declared repository does not contain, left
        # by injected faults. A build resolving from a shared cache cannot say
        # where its inputs came from.
        f"--package-cache-directory={build_root / 'pkgcache'}",
        *overlay_arguments(load(arguments.input_set), arguments.overlay),
        f"--extra-tree={build_root / 'confext-staging'}",
        f"--repart-directory={repart}",
        f"--output-directory={output}",
        f"--initrd={output / 'initrd'}",
        f"--secure-boot-key={keys / 'secureboot.key'}",
        f"--secure-boot-certificate={keys / 'secureboot.crt'}",
        f"--verity-key={keys / 'verity.key'}",
        f"--verity-certificate={keys / 'verity.crt'}",
        *variant_arguments(arguments.variant, arguments.role),
        *arguments.mkosi,
    ]
    run_mkosi(build_root, arguments_to_mkosi, cwd=COMPOSITION)

    # Every run, whether or not mkosi rebuilt anything. Regenerating signing
    # material and re-running otherwise leaves a new key beside an artifact
    # carrying the old signature -- measured 2026-08-12, and it read as success.
    # Copying unconditionally makes that state visible: T3-SLICE-003 fails
    # because the bytes it searches for are no longer inside the image.
    certificate = keys / "verity.crt"
    if certificate.is_file():
        shutil.copy2(certificate, output / "neutrinos-slice.verity.crt")

    return 0


if __name__ == "__main__":
    sys.exit(main())
