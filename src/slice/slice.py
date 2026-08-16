#!/usr/bin/env python3
"""Build the PLN-0001 reference-VM slice. One entry point, one step per bucket.

`compose.sh` used to sequence this. It was 174 lines of shell that read three
environment variables, assembled an output path, and ran six subprocesses in
order -- nothing that needed a shell, and nothing a test could reach. What it
sequences has four lifetimes, and each subcommand below is one of them:

  buildroot   once per input set      mkosi, the tools tree, signing material
  acquire     once per input set      the declared package overlays
  fixtures    once per test material  both extension signings, delivered
  compose     once per artifact       the arm and variant, built by mkosi
  retain      once per release set    the declared repository, by digest
  enroll      once per test material  the T4-CONFEXT-001 enrolled artifact

`build` runs all six in the order their dependencies require, which is the
whole of what the shell script did.

Selection -- arm, variant, role -- is orthogonal to those four and is passed
through. It reads from the environment when an argument is absent, because
every record and every measurement tool invokes this with NEUTRINOS_SLICE_ARM
and NEUTRINOS_SLICE_VARIANT set, and those invocations are evidence of what was
run rather than a preference to be updated. New callers should pass arguments:
`mise.toml` sets `sandbox.deny_env`, so a mise task cannot pass an environment
variable through at all.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import acquire_overlay
import buildroot
import compose
import enroll
import fixtures
import retain_repository
from common import default_build_root

ROOT = Path(__file__).resolve().parent

# The harness machine-id is deliberately not here. It is delivered to the guest
# by tools/validation/slice_boot.py and derives the /var partition UUID; a build
# script was never its home, and T2-STATE-001 read it out of one.


def output_directory(build_root: Path, arm: str, variant: str) -> Path:
    """Six peer directories, no arm holding a privileged name (PLN-0002-06).

    `out` survives as a symlink because the PLN-0001 records name it and an
    operator's NEUTRINOS_SLICE_ARTIFACT_DIR may point at it.
    """
    name = f"out-{arm}" if variant == "primary" else f"out-{arm}-{variant}"
    return build_root / name


def selection(arguments: argparse.Namespace) -> tuple[str, str, str]:
    arm = arguments.arm or os.environ.get("NEUTRINOS_SLICE_ARM") or "erofs"
    variant = arguments.variant or os.environ.get("NEUTRINOS_SLICE_VARIANT") or "primary"
    role = arguments.role or os.environ.get("NEUTRINOS_SLICE_ROLE") or "workstation"
    return arm, variant, role


def run_build(arguments: argparse.Namespace) -> int:
    build_root: Path = arguments.build_root
    arm, variant, role = selection(arguments)
    output = output_directory(build_root, arm, variant)
    overlay = build_root / "inputs" / "overlay"
    passthrough = list(arguments.mkosi)

    # Before anything below does work, so a build that will be refused costs a
    # second rather than a build root and two extension rebuilds. compose runs
    # the same two checks again: a guard a caller has to remember to ask for is
    # one a caller can forget.
    #
    # Before the mkdir too. An unknown arm used to be rejected before any
    # directory existed, and creating the output first left `out-xfs` behind for
    # a selection that was then refused.
    compose.precheck(arm, variant, output, passthrough)

    build_root.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    compatibility = build_root / "out"
    if not compatibility.exists():
        compatibility.symlink_to("out-erofs")

    buildroot.provision(build_root, arguments.input_set)
    # Before the build, not after -- an overlay that cannot be verified must
    # stop the composition rather than be discovered in the artifact.
    acquire_overlay.acquire_all(overlay, arguments.input_set)

    # NEUTRINOS_SKIP_CONFEXT keeps its name and its meaning: measure-build-time
    # sets it, retain-artifact-digests reports on it, and the artifact-parameter
    # and format-measurement records cite it as a condition of measurements
    # already taken.
    if not os.environ.get("NEUTRINOS_SKIP_CONFEXT"):
        fixtures.build_all(build_root)

    compose.compose(
        build_root, output, overlay, arm, variant, role, passthrough, arguments.input_set
    )

    # Retention is a build step, not something to remember afterwards; without
    # it the declared repository is a URL whose bytes survive only as a side
    # effect of the last build's cache, which is what made PLN-0001-07's first
    # offline rebuild impossible.
    #
    # Only when a build produced an image: `clean`, `--help` and the other verbs
    # have nothing to retain, and fetching metadata for them would put a network
    # dependency on operations that have none.
    if not (output / "neutrinos-slice.manifest").is_file():
        return 0

    retain_repository.retain(
        cache=build_root / "pkgcache",
        overlay=overlay,
        destination=build_root / "inputs" / "repository",
        input_set=arguments.input_set,
    )

    # The T4-CONFEXT-001 fixture. After retention, and that ordering is a fix:
    # this step failed on its first real run, the shell aborted, and retention
    # silently did not happen. A step added for a new check must not take out an
    # established one.
    #
    # It needs an image-signing certificate to keep in `db` beside the verity
    # signer, since enrolling without one produces a machine whose firmware
    # refuses its own UKI. buildroot generates that certificate, so its absence
    # is a damaged build root rather than an incomplete one -- reported, not
    # fatal, because the fixture's absence blocks T4-CONFEXT-001, which is the
    # same signal in the place that reads it.
    if os.environ.get("NEUTRINOS_SKIP_CONFEXT"):
        return 0
    if not (build_root / "keys" / "secureboot.crt").is_file():
        print(
            f"slice: no image-signing certificate at {build_root}/keys/secureboot.crt, "
            "so the T4-CONFEXT-001 fixture was not built. buildroot generates that "
            "certificate, so its absence means the build root is damaged rather "
            "than incomplete.",
            file=sys.stderr,
        )
        return 0
    enroll.enroll(build_root)
    return 0


def run_buildroot(arguments: argparse.Namespace) -> int:
    buildroot.provision(arguments.build_root, arguments.input_set)
    return 0


def run_acquire(arguments: argparse.Namespace) -> int:
    acquire_overlay.acquire_all(
        arguments.build_root / "inputs" / "overlay", arguments.input_set
    )
    return 0


def run_fixtures(arguments: argparse.Namespace) -> int:
    fixtures.build_all(arguments.build_root)
    return 0


def run_compose(arguments: argparse.Namespace) -> int:
    build_root: Path = arguments.build_root
    arm, variant, role = selection(arguments)
    compose.compose(
        build_root,
        output_directory(build_root, arm, variant),
        build_root / "inputs" / "overlay",
        arm,
        variant,
        role,
        list(arguments.mkosi),
        arguments.input_set,
    )
    return 0


def run_retain(arguments: argparse.Namespace) -> int:
    retain_repository.retain(
        cache=arguments.build_root / "pkgcache",
        overlay=arguments.build_root / "inputs" / "overlay",
        destination=arguments.build_root / "inputs" / "repository",
        input_set=arguments.input_set,
    )
    return 0


def run_enroll(arguments: argparse.Namespace) -> int:
    enroll.enroll(arguments.build_root)
    return 0


def main(argv: list[str] | None = None) -> int:
    # Line-buffered, because mkosi writes to the same file descriptor from a
    # subprocess. Python block-buffers stdout when it is redirected, so the
    # steps' own progress lines were flushed at exit and a captured log showed
    # the build root being provisioned after the build that used it.
    sys.stdout.reconfigure(line_buffering=True)

    parser = argparse.ArgumentParser(prog="slice", description=__doc__)
    # Declared once, on the parent, rather than in each of six programs. That
    # repetition was most of what the split into separate scripts cost.
    parser.add_argument("--build-root", type=Path, default=default_build_root())
    parser.add_argument("--input-set", type=Path, default=ROOT / "input-set.toml")
    steps = parser.add_subparsers(dest="step", required=True)

    def selected(sub: argparse.ArgumentParser) -> argparse.ArgumentParser:
        sub.add_argument("--arm", help="/usr filesystem format; NEUTRINOS_SLICE_ARM")
        sub.add_argument("--variant", choices=compose.VARIANTS, help="NEUTRINOS_SLICE_VARIANT")
        sub.add_argument("--role", help="capability declaration; NEUTRINOS_SLICE_ROLE")
        sub.add_argument("mkosi", nargs="*", help="passed through to mkosi")
        return sub

    selected(steps.add_parser("build", help="the whole pipeline")).set_defaults(run=run_build)
    selected(steps.add_parser("compose", help="the artifact only")).set_defaults(run=run_compose)
    steps.add_parser("buildroot", help="mkosi, tools tree, keys").set_defaults(run=run_buildroot)
    steps.add_parser("acquire", help="declared package overlays").set_defaults(run=run_acquire)
    steps.add_parser("fixtures", help="both extension signings").set_defaults(run=run_fixtures)
    steps.add_parser("retain", help="the declared repository").set_defaults(run=run_retain)
    steps.add_parser("enroll", help="the enrolled-artifact fixture").set_defaults(run=run_enroll)

    # parse_known_args, because everything after the step is mkosi's: `--force`,
    # `summary`, `-ff`. argparse rejects unknown options otherwise, and the
    # shell script this replaces separated them with `--`, which no operator
    # typing `slice.py build --force` would think to do. An option this parser
    # does not know is therefore mkosi's to reject, and mkosi does reject it
    # loudly -- verified by passing a misspelled flag.
    arguments, passthrough = parser.parse_known_args(argv)
    if hasattr(arguments, "mkosi"):
        arguments.mkosi = [*arguments.mkosi, *passthrough]
    elif passthrough:
        parser.error(f"unrecognized arguments: {' '.join(passthrough)}")
    return arguments.run(arguments)


if __name__ == "__main__":
    sys.exit(main())
