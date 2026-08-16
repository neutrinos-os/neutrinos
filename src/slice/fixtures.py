#!/usr/bin/env python3
"""Build the configuration extension and stage it for composition.

PLN-0002-03a. The confext is built before the artifact that carries it, and it
resolves no repository, so it builds whether or not the declared repository is
reachable.

Two images from one source tree, differing only in who signed them.
T4-CONFEXT-001 measures whether an unenrolled signer is refused, and that
comparison means something only if the signature is the sole difference: a
second image built from a second source could be refused for being the wrong
image rather than the wrong signer. The enrolled one is staged into the
artifact; the unenrolled one is delivered from outside, as a substitution would
be.

Staging the signed image into `/usr/lib/confexts` is a declared fixture, not a
decision -- owner ruling 2026-08-11 on finding 1 option D. It fuses release and
configuration, which DES-0005's amendment separates, and PLN-0002-03b owns the
design.

The certificate travels in `/usr/lib/verity.d` because that is where systemd
looks. It is not sufficient for enforcement: measured 2026-08-11, the kernel
returns -ENOKEY for a key in no keyring and systemd merges unsigned anyway.
docs/project/etc-path-carve.md.

Nothing here reads the package declaration, and nothing here is
distribution-shaped: the extension is built by mkosi from a source tree, and
the signatures are openssl material the build root already holds. It is the one
part of the composition that an ecosystem change would leave alone.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from common import run_mkosi

ROOT = Path(__file__).resolve().parent

# The extension's name is its identity in three places -- the output file, the
# staged path under /usr/lib/confexts, and the fixture copies T4-CONFEXT-001
# consumes -- so it is named once.
CONFEXT = "neutrinos-network"

# The certificate's staged name. Fixed, because the artifact carries it and a
# name varying with the build root would make the guest guess.
VERITY_CERTIFICATE = "neutrinos-synthetic.crt"


def build(build_root: Path, source: Path, output: Path, signer: str) -> Path:
    """Compose one extension image, signed by the named build-root key.

    `--force` every time. mkosi declines to rebuild an existing output and exits
    0, which is the same silent no-op compose.sh refuses for the artifact; here
    the extension is cheap enough to rebuild unconditionally, so the question
    does not arise. Passing it is what keeps that true.
    """
    keys = build_root / "keys"
    output.mkdir(parents=True, exist_ok=True)

    run_mkosi(
        build_root,
        [
            f"--verity-key={keys / f'{signer}.key'}",
            f"--verity-certificate={keys / f'{signer}.crt'}",
            f"--output-directory={output}",
            "--force", "build",
        ],
        cwd=source,
    )

    image = output / f"{CONFEXT}.raw"
    if not image.is_file():
        raise SystemExit(f"confext: mkosi reported success but wrote no {image}")
    return image


def stage(build_root: Path, image: Path) -> Path:
    """Assemble the extra tree the composition merges into the artifact.

    Rebuilt from empty rather than copied over: a staging tree holding an
    extension from a previous build would put two images in
    `/usr/lib/confexts`, and the artifact would carry both.
    """
    staging = build_root / "confext-staging"
    if staging.exists():
        shutil.rmtree(staging)

    confexts = staging / "usr" / "lib" / "confexts"
    verity = staging / "usr" / "lib" / "verity.d"
    confexts.mkdir(parents=True)
    verity.mkdir(parents=True)

    shutil.copy2(image, confexts / image.name)
    shutil.copy2(build_root / "keys" / "verity.crt", verity / VERITY_CERTIFICATE)
    return staging


def build_all(build_root: Path, source: Path | None = None) -> None:
    """Both signings, the staging tree, and delivery to T4-CONFEXT-001."""
    source = source or ROOT / "confext" / CONFEXT

    # Signed by the key enrolled in the fixture's db. This is the one the
    # artifact carries.
    enrolled = build(build_root, source, build_root / "confext", "verity")
    staging = stage(build_root, enrolled)
    print(f"confext: staged {enrolled.name} signed by the enrolled key into {staging}")

    # Valid material, wrong signer, and enrolled in nothing. Generated from the
    # same source tree so the signature is the only difference.
    unenrolled = build(
        build_root, source, build_root / "confext-unenrolled", "verity-wrong"
    )
    print(f"confext: built {unenrolled.name} signed by the unenrolled key")

    # Delivered to T4-CONFEXT-001 here, with the build that produced them, and
    # not at the end of a composition as they were. Copying them there tied the
    # fixture's freshness to the artifact's: rebuilding the extensions without
    # composing left the check reading a previous build's images, and nothing
    # detected it. Whatever built them last is what the check now sees.
    fixture = build_root / "fixture"
    fixture.mkdir(parents=True, exist_ok=True)
    for image, name in ((enrolled, "confext-enrolled.raw"), (unenrolled, "confext-unenrolled.raw")):
        shutil.copy2(image, fixture / name)
    print(f"confext: delivered both images to {fixture}")
