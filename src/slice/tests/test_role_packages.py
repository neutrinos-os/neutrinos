"""A role's packages come from its capability declaration, or the build stops."""

from __future__ import annotations

import pytest

import role_packages

DECLARATION = """
[capability.graphical-session]
stage = "session"
packages = ["gnome-shell", "gdm"]

[capability.terminal]
stage = "session"
packages = ["gdm", "foot"]

[capability.editing]
stage = "workflow"
packages = ["helix"]
"""


@pytest.fixture
def role(monkeypatch, tmp_path):
    path = tmp_path / "src" / "roles" / "fixture" / "capabilities.toml"
    path.parent.mkdir(parents=True)
    path.write_text(DECLARATION, encoding="utf-8")
    monkeypatch.setattr(role_packages, "ROOT", tmp_path)
    return "fixture"


def test_packages_are_sorted_and_de_duplicated(role):
    # Two capabilities may legitimately want the same package, and an
    # artifact's contents must not depend on TOML iteration order.
    assert role_packages.packages(role) == ["foot", "gdm", "gnome-shell", "helix"]


def test_a_stage_selects_only_its_own_capabilities(role):
    assert role_packages.packages(role, ("session",)) == ["foot", "gdm", "gnome-shell"]
    assert role_packages.packages(role, ("workflow",)) == ["helix"]


def test_a_missing_declaration_stops_rather_than_composing_nothing(monkeypatch, tmp_path):
    monkeypatch.setattr(role_packages, "ROOT", tmp_path)
    with pytest.raises(SystemExit) as raised:
        role_packages.packages("absent")
    assert "no capability declaration" in str(raised.value)


def test_a_stage_that_declares_nothing_stops(monkeypatch, tmp_path):
    path = tmp_path / "src" / "roles" / "empty" / "capabilities.toml"
    path.parent.mkdir(parents=True)
    path.write_text(
        '[capability.editing]\nstage = "workflow"\npackages = ["helix"]\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(role_packages, "ROOT", tmp_path)
    with pytest.raises(SystemExit) as raised:
        role_packages.packages("empty", ("session",))
    assert "no packages declared" in str(raised.value)


def test_the_declared_workstation_role_resolves_a_session():
    assert role_packages.packages("workstation", ("session",))
