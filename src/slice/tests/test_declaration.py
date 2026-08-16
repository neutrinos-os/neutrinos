"""The one-repository rule, and that it is a rule rather than a lookup."""

from __future__ import annotations

import pytest

import declaration

ONE = """
[packages]
[[packages.repositories]]
url = "https://example.invalid/one"
metadata_digest = "aa"
"""

TWO = """
[packages]
[[packages.repositories]]
url = "https://example.invalid/one"
metadata_digest = "aa"
[[packages.repositories]]
url = "https://example.invalid/two"
metadata_digest = "bb"
"""

NONE = """
[packages]
repositories = []
"""


def write(tmp_path, text):
    path = tmp_path / "input-set.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_load_reads_the_path_it_is_given(tmp_path):
    assert declaration.load(write(tmp_path, ONE))["packages"]["repositories"][0][
        "url"
    ] == "https://example.invalid/one"


def test_load_defaults_to_the_declaration_beside_it():
    assert declaration.load()["packages"]["repositories"]


def test_repository_returns_the_whole_entry(tmp_path):
    entry = declaration.repository(declaration.load(write(tmp_path, ONE)))
    # The URL alone is not an identity. A caller handed only the URL cannot
    # check which publication of it was declared, which is the whole reason
    # this returns the entry.
    assert entry == {
        "url": "https://example.invalid/one",
        "metadata_digest": "aa",
    }


@pytest.mark.parametrize("text", (TWO, NONE))
def test_repository_refuses_to_choose(tmp_path, text):
    with pytest.raises(SystemExit) as raised:
        declaration.repository(declaration.load(write(tmp_path, text)))
    assert "cannot choose" in str(raised.value)


def test_the_declared_input_set_satisfies_the_rule():
    entry = declaration.repository(declaration.load())
    assert entry["url"].startswith("https://")
    assert len(entry["metadata_digest"]) == 64
