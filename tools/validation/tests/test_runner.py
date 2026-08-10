from __future__ import annotations

import os
from pathlib import Path
import signal
import socket
import sys
import tempfile
import time

import pytest

from tools.validation import check


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
                directory, check.validation_cache_root()
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
    environment = check.child_environment(home, cache)
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
    }
    assert environment["HOME"] == str(home)
    assert environment[check.VALIDATION_CACHE_ROOT_ENV] == str(cache)


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
