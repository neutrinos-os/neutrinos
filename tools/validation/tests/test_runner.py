from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator
from typing import Any

import pytest

from tools.validation import check


@contextmanager
def runner_invocation(
    *arguments: str,
    extra_environment: dict[str, str] | None = None,
) -> Iterator[tuple[subprocess.CompletedProcess[str], Path, dict[str, Any]]]:
    environment = {
        name: value
        for name, value in os.environ.items()
        if name in check.ALLOWED_RUNNER_ENVIRONMENT
    }
    if extra_environment:
        environment.update(extra_environment)
    result = subprocess.run(
        (sys.executable, str(Path(check.__file__).resolve()), *arguments),
        cwd=check.ROOT,
        env=environment,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    run_lines = [line for line in result.stdout.splitlines() if line.startswith("run: ")]
    assert len(run_lines) == 1, result
    run_dir = Path(run_lines[0].removeprefix("run: "))
    try:
        manifest = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        yield result, run_dir, manifest
    finally:
        shutil.rmtree(run_dir)


def process_exists(process_id: int) -> bool:
    try:
        os.kill(process_id, 0)
    except ProcessLookupError:
        return False
    return True


def execution(command: tuple[str, ...], timeout: float = 2, limit: int = 4096):
    with tempfile.TemporaryDirectory(prefix="neutrinos-runner-probe-") as raw:
        directory = Path(raw)
        result = check.execute_process(
            command,
            cwd=directory,
            environment=check.child_environment(
                directory,
                check.validation_cache_root(),
                check.make_synthetic_canary(),
            ),
            stdout_path=directory / "stdout.log",
            stderr_path=directory / "stderr.log",
            timeout_seconds=timeout,
            max_output_bytes=limit,
        )
        return result, (directory / "stdout.log").read_bytes()


def test_preflight_rejects_root_and_undeclared_environment() -> None:
    cache = "/synthetic/cache"
    assert check.preflight_errors(
        {check.VALIDATION_CACHE_ROOT_ENV: cache}, effective_uid=0
    ) == ["validation refuses to run as root"]
    assert check.preflight_errors(
        {
            "PATH": "/synthetic",
            "AWS_SECRET_ACCESS_KEY": "synthetic",
            check.VALIDATION_CACHE_ROOT_ENV: cache,
        },
        effective_uid=1000,
    ) == ["undeclared environment variables: AWS_SECRET_ACCESS_KEY"]


def test_cache_root_must_be_absolute_and_external() -> None:
    name = check.VALIDATION_CACHE_ROOT_ENV
    assert check.preflight_errors({}, effective_uid=1000) == [f"{name} is not set"]
    assert check.preflight_errors({name: "relative"}, effective_uid=1000) == [
        f"{name} must be an absolute path"
    ]
    assert check.preflight_errors(
        {name: str(check.ROOT / ".pytest_cache")}, effective_uid=1000
    ) == [f"{name} must be outside the repository"]


def test_child_environment_is_allowlisted() -> None:
    home = Path("/synthetic/home")
    cache = Path("/synthetic/cache")
    canary = check.make_synthetic_canary()
    environment = check.child_environment(home, cache, canary)
    assert set(environment) == {
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_NOSYSTEM",
        "HOME",
        "LANG",
        "LC_ALL",
        check.VALIDATION_CACHE_ROOT_ENV,
        "PATH",
        "PYTHONDONTWRITEBYTECODE",
        "PYTHONIOENCODING",
        check.SYNTHETIC_CANARY_ENV,
    }
    assert environment["HOME"] == str(home)
    assert environment[check.VALIDATION_CACHE_ROOT_ENV] == str(cache)
    assert environment[check.SYNTHETIC_CANARY_ENV] == canary


def test_canary_and_credential_markers_are_detected() -> None:
    canary = check.make_synthetic_canary().encode()
    assert check.unsafe_bytes_kinds(b"prefix " + canary + b" suffix", canary) == [
        "synthetic_canary"
    ]
    assert "private_key" in check.unsafe_bytes_kinds(
        b"-----BEGIN PRIVATE KEY-----", canary
    )
    assert "aws_access_key" in check.unsafe_bytes_kinds(
        b"AKIAIOSFODNN7EXAMPLE", canary
    )
    assert "github_token" in check.unsafe_bytes_kinds(
        b"github_pat_" + (b"a" * 30), canary
    )
    assert "bearer_token" in check.unsafe_bytes_kinds(
        b"Authorization: Bearer " + (b"a" * 30), canary
    )


def test_unsafe_files_are_quarantined_outside_retained_results() -> None:
    with tempfile.TemporaryDirectory(prefix="neutrinos-output-probe-") as raw:
        run_dir = Path(raw) / "run"
        log = run_dir / "logs" / "probe.stdout.log"
        artifact = run_dir / "artifacts" / "probe.bin"
        log.parent.mkdir(parents=True)
        artifact.parent.mkdir(parents=True)
        canary = check.make_synthetic_canary().encode()
        log.write_bytes(
            (b"x" * (check.SCAN_CHUNK_BYTES - 10)) + canary + b" safe suffix"
        )
        artifact.write_bytes(b"-----BEGIN PRIVATE KEY-----")
        safety = check.OutputSafety(canary=canary)

        assert safety.inspect_file(log, run_dir)
        assert safety.inspect_file(artifact, run_dir)
        assert safety.quarantine_dir is not None
        assert run_dir not in safety.quarantine_dir.parents
        assert canary not in log.read_bytes()
        assert b"PRIVATE KEY" not in artifact.read_bytes()
        assert (safety.quarantine_dir / "logs" / log.name).read_bytes().endswith(
            canary + b" safe suffix"
        )
        assert (
            safety.quarantine_dir / "artifacts" / artifact.name
        ).read_bytes() == b"-----BEGIN PRIVATE KEY-----"
        shutil.rmtree(safety.quarantine_dir)


def test_run_fails_when_registered_output_contains_canary(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    snapshot = {"git_identity": "synthetic-git", "tree_identity": "synthetic-tree"}
    monkeypatch.setattr(check, "repository_snapshot", lambda: snapshot)
    monkeypatch.setattr(check, "preflight_errors", lambda: [])
    monkeypatch.setattr(
        check, "validation_cache_root", lambda: Path("/synthetic/cache")
    )

    def unsafe_test(
        test: check.Test,
        run_dir: Path,
        _home: Path,
        _cache_root: Path,
        canary: str,
    ) -> dict[str, Any]:
        stdout = run_dir / "logs" / f"{test.id}.stdout.log"
        stderr = run_dir / "logs" / f"{test.id}.stderr.log"
        stdout.write_text(canary, encoding="utf-8")
        stderr.write_bytes(b"")
        return {
            "cleanup": {"process_group_absent": True},
            "duration_seconds": 0,
            "ended_at": check.utc_now(),
            "id": test.id,
            "output_bytes": len(canary),
            "result": "passing",
            "started_at": check.utc_now(),
        }

    monkeypatch.setattr(check, "execute_test", unsafe_test)
    status = check.run("run", ("T0-DOC-001",))
    output = capsys.readouterr()
    run_dir = Path(
        next(
            line.removeprefix("run: ")
            for line in output.out.splitlines()
            if line.startswith("run: ")
        )
    )
    quarantine: Path | None = None
    try:
        manifest = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        quarantine = Path(manifest["output_safety"]["quarantine_path"])
        retained = b"".join(
            path.read_bytes() for path in run_dir.rglob("*") if path.is_file()
        )
        assert status == 1
        assert manifest["failure_stage"] == "output_safety"
        assert manifest["output_safety"]["passed"] is False
        assert manifest["counts"]["failing"] == 1
        assert check.SYNTHETIC_CANARY_PREFIX.encode() not in retained
        assert check.SYNTHETIC_CANARY_PREFIX not in output.out
        assert check.SYNTHETIC_CANARY_PREFIX not in output.err
        assert (quarantine / "logs" / "T0-DOC-001.stdout.log").is_file()
    finally:
        shutil.rmtree(run_dir)
        if quarantine is not None:
            shutil.rmtree(quarantine)


def test_source_identification_environment_is_allowlisted() -> None:
    environment = check.git_environment()
    assert set(environment) == {
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_NOSYSTEM",
        "HOME",
        "LANG",
        "LC_ALL",
        "PATH",
    }
    assert "AWS_SECRET_ACCESS_KEY" not in environment


def test_failed_preflight_writes_bounded_result_without_environment_value() -> None:
    canary = "DO_NOT_RECORD_THIS_SYNTHETIC_VALUE"
    with runner_invocation(
        "profile",
        "fast",
        extra_environment={"AWS_SECRET_ACCESS_KEY": canary},
    ) as (result, run_dir, manifest):
        assert result.returncode == 2
        assert manifest["failure_stage"] == "preflight"
        assert manifest["final_result"] == "failing"
        assert manifest["cleanup"]["repository_preserved"] is True
        assert manifest["selected_ids"] == []
        assert (run_dir / "results.jsonl").read_bytes() == b""
        retained = b"".join(
            path.read_bytes() for path in run_dir.rglob("*") if path.is_file()
        )
        assert canary.encode() not in retained
        assert canary not in result.stdout
        assert canary not in result.stderr
        assert "AWS_SECRET_ACCESS_KEY" in manifest["error"]


def test_invalid_selection_writes_bounded_result() -> None:
    unknown = "X" * 20_000
    with runner_invocation("run", unknown) as (result, run_dir, manifest):
        assert result.returncode == 2
        assert manifest["failure_stage"] == "selection"
        assert manifest["profile"] == "selected"
        assert manifest["selected_ids"] == []
        assert manifest["error"] == "invalid test ID syntax (1 value(s))"
        assert unknown not in result.stdout
        assert unknown not in result.stderr
        assert (run_dir / "results.jsonl").read_bytes() == b""


def test_invalid_invocation_writes_result() -> None:
    with runner_invocation("profile") as (result, run_dir, manifest):
        assert result.returncode == 2
        assert manifest["failure_stage"] == "invocation"
        assert manifest["profile"] == "invalid"
        assert manifest["selected_ids"] == []
        assert (run_dir / "results.jsonl").read_bytes() == b""


def test_error_details_are_bounded() -> None:
    error = check.bounded_error("x" * (check.MAX_ERROR_BYTES * 2))
    assert len(error.encode()) <= check.MAX_ERROR_BYTES
    assert error.endswith("... [truncated]")


def test_network_syscalls_are_denied() -> None:
    with pytest.raises(PermissionError):
        socket.socket()


def test_timeout_fails_and_removes_process_group() -> None:
    result, _ = execution((sys.executable, "-c", "import time; time.sleep(60)"), timeout=0.1)
    assert result.detail == "timed out after 0.1s"
    assert result.returncode != 0
    assert result.cleanup_ok


def test_output_is_bounded_and_fails() -> None:
    limit = 4096
    result, stdout = execution(
        (sys.executable, "-c", "import sys; sys.stdout.write('x' * 1000000)"),
        limit=limit,
    )
    assert result.detail == f"output exceeded {limit} bytes"
    assert len(stdout) <= limit
    assert result.cleanup_ok


def test_descendant_is_removed_after_leader_exits() -> None:
    program = (
        "import subprocess,sys; "
        "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
        "print(child.pid, flush=True)"
    )
    result, stdout = execution((sys.executable, "-c", program))
    child = int(stdout.strip())
    assert result.cleanup_ok
    assert not process_exists(child)


def test_interruption_removes_process_group() -> None:
    with tempfile.TemporaryDirectory(prefix="neutrinos-interrupt-probe-") as raw:
        process_id_file = Path(raw) / "pid"
        program = (
            "import os,pathlib,time; "
            f"pathlib.Path({str(process_id_file)!r}).write_text(str(os.getpid())); "
            "time.sleep(60)"
        )

        def interrupt(_signal: int, _frame: object) -> None:
            raise KeyboardInterrupt

        previous = signal.signal(signal.SIGALRM, interrupt)
        signal.setitimer(signal.ITIMER_REAL, 0.1)
        try:
            with pytest.raises(KeyboardInterrupt):
                execution((sys.executable, "-c", program))
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)

        deadline = time.monotonic() + 1
        while not process_id_file.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert process_id_file.exists()
        assert not process_exists(int(process_id_file.read_text()))
