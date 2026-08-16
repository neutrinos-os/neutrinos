"""What a selection means, and the refusal to report success without composing."""

from __future__ import annotations

import pytest

import compose

OVERLAYS = """
[packages]
[[packages.overlays]]
name = "systemd-261"
[[packages.overlays]]
name = "second-overlay"
"""


def test_primary_adds_nothing():
    assert compose.variant_arguments("primary", "workstation") == []


def test_content_adds_one_marker_tree():
    arguments = compose.variant_arguments("content", "workstation")
    assert arguments == [
        f"--extra-tree={compose.COMPOSITION / 'mkosi.extra.variant-content'}"
    ]


def test_seed_moves_only_the_identity():
    # A seed variant that boots means integrity did not bind the identity; a
    # content variant that boots means it did not bind the contents. Either
    # variant moving more than its one thing makes that distinction useless.
    assert compose.variant_arguments("seed", "workstation") == [
        f"--seed={compose.VARIANT_SEED}"
    ]


def test_state_adds_the_partitions_and_nothing_else():
    assert compose.variant_arguments("state", "workstation") == [
        f"--repart-directory={compose.COMPOSITION / 'state-partitions'}",
        f"--extra-tree={compose.COMPOSITION / 'mkosi.extra.state'}",
    ]


def test_session_includes_the_state_variant_rather_than_repeating_it():
    """A session composed without a home volume works exactly once."""
    state = compose.variant_arguments("state", "workstation")
    session = compose.variant_arguments("session", "workstation")
    assert session[: len(state)] == state
    assert f"--extra-tree={compose.COMPOSITION / 'mkosi.extra.session'}" in session


def test_session_packages_come_from_the_capability_declaration(monkeypatch):
    monkeypatch.setattr(
        compose.role_packages, "packages", lambda role, stages: [f"{role}-{stages[0]}"]
    )
    assert "--package=workstation-session" in compose.variant_arguments(
        "session", "workstation"
    )


def test_session_asks_for_the_session_stage_only(monkeypatch):
    """`workflow` is daily-use capability, and it is not what a first boot needs."""
    asked = {}

    def record(role, stages):
        asked["stages"] = stages
        return []

    monkeypatch.setattr(compose.role_packages, "packages", record)
    compose.variant_arguments("session", "workstation")
    assert asked["stages"] == ("session",)


def test_every_declared_overlay_gets_a_package_directory(tmp_path):
    """The regression: the overlay's name was a literal hidden inside a path."""
    path = tmp_path / "input-set.toml"
    path.write_text(OVERLAYS, encoding="utf-8")
    from declaration import load

    assert compose.overlay_arguments(load(path), tmp_path / "overlay") == [
        f"--package-directory={tmp_path / 'overlay' / 'systemd-261'}",
        f"--package-directory={tmp_path / 'overlay' / 'second-overlay'}",
    ]


def test_no_declared_overlay_asks_for_no_directory():
    assert compose.overlay_arguments({}, compose.ROOT) == []


def test_the_declared_input_set_names_its_overlay(tmp_path):
    from declaration import load

    arguments = compose.overlay_arguments(load(), tmp_path)
    assert arguments
    assert all(argument.startswith("--package-directory=") for argument in arguments)


def test_precheck_refuses_an_unknown_variant(tmp_path):
    with pytest.raises(SystemExit) as raised:
        compose.precheck("erofs", "nonesuch", tmp_path, [])
    assert "no variant" in str(raised.value)


def test_precheck_refuses_an_arm_with_no_partition_definitions(tmp_path):
    with pytest.raises(SystemExit) as raised:
        compose.precheck("xfs", "primary", tmp_path, [])
    assert "no arm 'xfs'" in str(raised.value)


def test_precheck_accepts_the_declared_arms(tmp_path):
    for arm in ("erofs", "ext4"):
        compose.precheck(arm, "primary", tmp_path / arm, [])


def test_precheck_refuses_a_build_that_would_be_a_silent_no_op(tmp_path):
    """mkosi declines to rebuild an existing output and exits 0."""
    (tmp_path / "neutrinos-slice.raw").write_bytes(b"")
    with pytest.raises(SystemExit) as raised:
        compose.precheck("erofs", "primary", tmp_path, [])
    assert "--force was not passed" in str(raised.value)


@pytest.mark.parametrize("flag", sorted(compose.FORCE_FLAGS))
def test_force_is_permitted_to_rebuild(tmp_path, flag):
    (tmp_path / "neutrinos-slice.raw").write_bytes(b"")
    compose.precheck("erofs", "primary", tmp_path, [flag])


@pytest.mark.parametrize("verb", ("summary", "clean", "cat-config"))
def test_read_only_verbs_are_not_refused(tmp_path, verb):
    """Only a build can be a silent no-op; refusing `summary` broke every read."""
    (tmp_path / "neutrinos-slice.raw").write_bytes(b"")
    compose.precheck("erofs", "primary", tmp_path, [verb])


def test_an_output_with_no_artifact_is_not_refused(tmp_path):
    compose.precheck("erofs", "primary", tmp_path, [])


def test_precheck_runs_before_anything_is_created(tmp_path):
    """A refused selection must not leave an output directory behind."""
    output = tmp_path / "out-xfs"
    with pytest.raises(SystemExit):
        compose.precheck("xfs", "primary", output, [])
    assert not output.exists()
