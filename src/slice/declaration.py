#!/usr/bin/env python3
"""Read `input-set.toml` and answer the questions more than one helper asks.

Three helpers now resolve their inputs from the declaration rather than from
copies restated in `compose.sh` -- `buildroot.py`, `acquire_overlay.py` and
`retain_repository.py` -- and two of them need the one declared repository.

"The one" is a rule, not a lookup. The declaration names exactly one repository
and records why a second cannot be an exact input, so a helper that reached for
`repositories[0]` would silently pick a winner the declaration never named. The
rule is enforced here, once, because a rule restated in three places is the
same drift the copies in `compose.sh` were, at a smaller scale.

This module holds no values. Anything it returns came out of the declaration on
this call.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUT_SET = ROOT / "input-set.toml"


def load(path: Path | None = None) -> dict:
    return tomllib.loads((path or INPUT_SET).read_text(encoding="utf-8"))


def repository(declaration: dict) -> dict:
    """The single declared repository, with its URL and metadata identity.

    Returns the whole entry rather than the URL: what makes the repository an
    input is the URL together with the `metadata_digest` that says which
    publication of it, and a caller handed only the URL cannot check the
    second.
    """
    repositories = declaration["packages"]["repositories"]
    if len(repositories) != 1:
        raise SystemExit(
            f"input set declares {len(repositories)} repositories; this slice "
            "resolves against the single declared repository and cannot choose"
        )
    return repositories[0]
