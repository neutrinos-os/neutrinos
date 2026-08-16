"""The entry point: where an artifact lands, what selects it, what mkosi receives."""

from __future__ import annotations

import pytest

import slice as entry


def test_the_primary_arm_holds_no_privileged_name(tmp_path):
    # PLN-0002-06: six peer directories. `out-erofs`, not `out`.
    assert entry.output_directory(tmp_path, "erofs", "primary") == tmp_path / "out-erofs"
    assert entry.output_directory(tmp_path, "ext4", "primary") == tmp_path / "out-ext4"


def test_a_variant_writes_to_its_own_directory(tmp_path):
    """What keeps a variant build from overwriting a retained PLN-0002-06 member."""
    for variant in ("content", "seed", "state", "session"):
        assert entry.output_directory(tmp_path, "erofs", variant) == (
            tmp_path / f"out-erofs-{variant}"
        )


def namespace(**values):
    import argparse

    return argparse.Namespace(**{"arm": None, "variant": None, "role": None, **values})


def test_arguments_win_over_the_environment(monkeypatch):
    monkeypatch.setenv("NEUTRINOS_SLICE_ARM", "ext4")
    monkeypatch.setenv("NEUTRINOS_SLICE_VARIANT", "seed")
    monkeypatch.setenv("NEUTRINOS_SLICE_ROLE", "router")
    assert entry.selection(namespace(arm="erofs", variant="state", role="workstation")) == (
        "erofs",
        "state",
        "workstation",
    )


def test_the_environment_is_read_when_an_argument_is_absent(monkeypatch):
    # Every record and every measurement tool invokes this with these set, and
    # those invocations are evidence of what was run.
    monkeypatch.setenv("NEUTRINOS_SLICE_ARM", "ext4")
    monkeypatch.setenv("NEUTRINOS_SLICE_VARIANT", "seed")
    monkeypatch.delenv("NEUTRINOS_SLICE_ROLE", raising=False)
    assert entry.selection(namespace()) == ("ext4", "seed", "workstation")


def test_the_defaults_are_the_measured_selection(monkeypatch):
    for name in ("ARM", "VARIANT", "ROLE"):
        monkeypatch.delenv(f"NEUTRINOS_SLICE_{name}", raising=False)
    assert entry.selection(namespace()) == ("erofs", "primary", "workstation")


def stub(monkeypatch):
    """Replace the step that would do work, and capture what it was asked for."""
    captured = {}

    def run(arguments):
        captured["arguments"] = arguments
        return 0

    monkeypatch.setattr(entry, "run_build", run)
    monkeypatch.setattr(entry, "run_buildroot", run)
    return captured


@pytest.mark.parametrize(
    "argv",
    (
        ["build", "--force"],
        ["build", "summary"],
        ["build", "-ff"],
    ),
)
def test_unknown_arguments_are_mkosi_s(monkeypatch, argv):
    """`slice.py build --force` is the invocation sixteen records document."""
    captured = stub(monkeypatch)
    assert entry.main(argv) == 0
    assert captured["arguments"].mkosi == argv[1:]


def test_selection_arguments_are_not_passed_to_mkosi(monkeypatch):
    captured = stub(monkeypatch)
    entry.main(["build", "--arm", "ext4", "--variant", "state", "--force"])
    assert captured["arguments"].mkosi == ["--force"]
    assert entry.selection(captured["arguments"])[:2] == ("ext4", "state")


def test_a_step_with_no_passthrough_still_rejects_what_it_does_not_know(monkeypatch):
    stub(monkeypatch)
    with pytest.raises(SystemExit) as raised:
        entry.main(["buildroot", "--nonsense"])
    assert raised.value.code == 2


def test_an_unknown_variant_is_refused_by_the_parser(monkeypatch):
    stub(monkeypatch)
    with pytest.raises(SystemExit) as raised:
        entry.main(["build", "--variant", "nonesuch"])
    assert raised.value.code == 2


def test_the_build_root_is_declared_once_for_every_step(monkeypatch, tmp_path):
    captured = stub(monkeypatch)
    entry.main(["--build-root", str(tmp_path), "buildroot"])
    assert captured["arguments"].build_root == tmp_path
    entry.main(["--build-root", str(tmp_path), "build"])
    assert captured["arguments"].build_root == tmp_path


def test_a_step_is_required(monkeypatch):
    stub(monkeypatch)
    with pytest.raises(SystemExit) as raised:
        entry.main([])
    assert raised.value.code == 2
