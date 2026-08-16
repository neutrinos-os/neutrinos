"""The four shared facts: where a build root is, digests, and deleting a tree."""

from __future__ import annotations

import hashlib
import os
import stat

import pytest

import common


def test_build_root_prefers_the_explicit_override(monkeypatch, tmp_path):
    monkeypatch.setenv("NEUTRINOS_SLICE_BUILD_ROOT", str(tmp_path / "elsewhere"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    assert common.default_build_root() == tmp_path / "elsewhere"


def test_build_root_falls_back_to_the_cache_directory(monkeypatch, tmp_path):
    monkeypatch.delenv("NEUTRINOS_SLICE_BUILD_ROOT", raising=False)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    assert common.default_build_root() == tmp_path / "cache" / "neutrinos" / "slice"


def test_build_root_falls_back_to_the_home_cache(monkeypatch, tmp_path):
    monkeypatch.delenv("NEUTRINOS_SLICE_BUILD_ROOT", raising=False)
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    monkeypatch.setattr(common.Path, "home", classmethod(lambda cls: tmp_path))
    assert common.default_build_root() == tmp_path / ".cache" / "neutrinos" / "slice"


def test_digest_reads_past_one_chunk(tmp_path):
    # Larger than the 1 MiB read, because a chunked hash that drops or repeats
    # a chunk still returns a plausible-looking hex string.
    payload = bytes(range(256)) * 8192
    path = tmp_path / "artifact"
    path.write_bytes(payload)
    assert len(payload) > (1 << 20)
    assert common.digest(path) == hashlib.sha256(payload).hexdigest()


def test_remove_tree_deletes_read_only_directories(tmp_path):
    """The measured fail-open: an extracted /usr carries mode-0555 directories."""
    tree = tmp_path / "usr"
    (tree / "lib" / "systemd").mkdir(parents=True)
    (tree / "lib" / "systemd" / "unit").write_text("x", encoding="utf-8")
    for directory in (tree / "lib" / "systemd", tree / "lib", tree):
        directory.chmod(0o555)

    common.remove_tree(tree)
    assert not tree.exists()


def test_remove_tree_is_silent_on_a_tree_that_is_not_there(tmp_path):
    common.remove_tree(tmp_path / "absent")


def test_remove_tree_raises_rather_than_leaving_a_half_deleted_tree(tmp_path):
    """Nothing here suppresses an error, which `ignore_errors=True` did."""
    parent = tmp_path / "parent"
    tree = parent / "usr"
    tree.mkdir(parents=True)
    (tree / "file").write_text("x", encoding="utf-8")
    # Unwritable parent: the chmod walk cannot help, because the entry being
    # unlinked lives in a directory this walk never touches.
    parent.chmod(0o555)
    try:
        if os.access(parent, os.W_OK):
            pytest.skip("running with privileges that ignore directory permissions")
        with pytest.raises(OSError):
            common.remove_tree(tree)
        assert tree.exists()
    finally:
        parent.chmod(parent.stat().st_mode | stat.S_IRWXU)


def test_run_mkosi_runs_the_provisioned_mkosi_against_the_tools_tree(monkeypatch, tmp_path):
    """Which mkosi and which tools tree are the two facts this owns."""
    seen = {}

    def record(command, **keywords):
        seen["command"] = command
        seen.update(keywords)

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(common.subprocess, "run", record)
    common.run_mkosi(tmp_path, ["--force"], cwd=tmp_path / "composition")

    assert seen["command"][1:3] == ["-m", "mkosi"]
    assert seen["command"][3] == f"--tools-tree={tmp_path / 'tools'}"
    assert seen["command"][-1] == "--force"
    assert seen["env"]["PYTHONPATH"] == str(tmp_path / "mkosi")
    assert seen["check"] is True
