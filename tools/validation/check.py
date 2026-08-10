#!/usr/bin/env python3
"""NeutrinOS repository validation entry point.

Mise owns tool selection and task dispatch. This module owns registration,
selection, execution, result recording, and checkout-preservation checks.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Sequence
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MAX_OUTPUT_BYTES = 1_048_576


@dataclasses.dataclass(frozen=True)
class Test:
    id: str
    level: str
    profiles: tuple[str, ...]
    timeout_seconds: int
    traces: tuple[str, ...]
    capabilities: tuple[str, ...]
    fixtures: tuple[str, ...]
    cleanup_owner: str
    function: str


TESTS = (
    Test(
        id="T0-DOC-001",
        level="T0",
        profiles=("fast", "complete"),
        timeout_seconds=60,
        traces=("PLN-0000/PRE-011", "PLN-0000/PRE-015"),
        capabilities=(),
        fixtures=("repository checkout",),
        cleanup_owner="validation runner",
        function="check_git_diff",
    ),
    Test(
        id="T0-DOC-002",
        level="T0",
        profiles=("fast", "complete"),
        timeout_seconds=60,
        traces=("PLN-0000/PRE-011", "PLN-0000/PRE-015"),
        capabilities=(),
        fixtures=("repository Markdown files",),
        cleanup_owner="validation runner",
        function="check_markdown_links",
    ),
)
TEST_BY_ID = {test.id: test for test in TESTS}


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="milliseconds")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *args),
        cwd=ROOT,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def repository_snapshot() -> dict[str, str]:
    """Identify both Git state and all worktree bytes, including ignored files."""
    git_parts = []
    for args in (
        ("status", "--porcelain=v2", "--branch", "--untracked-files=all", "--ignored=matching"),
        ("diff", "--no-ext-diff", "--binary"),
        ("diff", "--no-ext-diff", "--binary", "--cached"),
    ):
        result = git(*args)
        git_parts.append(result.stdout)

    tree = hashlib.sha256()
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if relative.parts and relative.parts[0] == ".git":
            continue
        metadata = path.lstat()
        tree.update(os.fsencode(str(relative)))
        tree.update(b"\0")
        tree.update(str(stat.S_IMODE(metadata.st_mode)).encode())
        tree.update(b"\0")
        if path.is_symlink():
            tree.update(b"link\0")
            tree.update(os.fsencode(os.readlink(path)))
        elif path.is_file():
            tree.update(b"file\0")
            with path.open("rb") as source:
                while chunk := source.read(1024 * 1024):
                    tree.update(chunk)
        elif path.is_dir():
            tree.update(b"dir\0")
        else:
            tree.update(b"special\0")

    git_identity = hashlib.sha256("\0".join(git_parts).encode()).hexdigest()
    return {"git_identity": git_identity, "tree_identity": tree.hexdigest()}


def check_git_diff() -> int:
    result = git("diff", "--check", check=False)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    return result.returncode


def check_markdown_links() -> int:
    link = re.compile(r"\[[^]]*\]\(([^)]+)\)")
    failures: list[str] = []
    for document in ROOT.rglob("*.md"):
        relative = document.relative_to(ROOT)
        if ".git" in relative.parts:
            continue
        fenced = False
        for line in document.read_text(encoding="utf-8").splitlines():
            if line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            if fenced:
                continue
            for match in link.finditer(line):
                raw = match.group(1)
                target = raw.split("#", 1)[0].removeprefix("<").removesuffix(">")
                if not target or re.match(r"^(?:https?|mailto):", target):
                    continue
                if not (document.parent / target).exists():
                    failures.append(f"{relative} -> {raw}")
    if failures:
        print("\n".join(failures))
        return 1
    return 0


CHECKS: dict[str, Callable[[], int]] = {
    "check_git_diff": check_git_diff,
    "check_markdown_links": check_markdown_links,
}


def child_environment(home: Path) -> dict[str, str]:
    environment = {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "HOME": str(home),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH": os.environ["PATH"],
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
    }
    if "SYSTEMROOT" in os.environ:
        environment["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    return environment


def terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=2)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()


def execute_test(test: Test, run_dir: Path, home: Path) -> dict[str, Any]:
    logs = run_dir / "logs"
    stdout_path = logs / f"{test.id}.stdout.log"
    stderr_path = logs / f"{test.id}.stderr.log"
    started = utc_now()
    start = time.monotonic()
    status = "failing"
    detail: str | None = None

    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(
            (sys.executable, str(Path(__file__).resolve()), "_execute", test.id),
            cwd=ROOT,
            env=child_environment(home),
            start_new_session=True,
            stdout=stdout,
            stderr=stderr,
        )
        try:
            returncode = process.wait(timeout=test.timeout_seconds)
            status = "passing" if returncode == 0 else "failing"
            if returncode != 0:
                detail = f"exited {returncode}"
        except subprocess.TimeoutExpired:
            terminate_process_group(process)
            status = "failing"
            detail = f"timed out after {test.timeout_seconds}s"
        except BaseException:
            terminate_process_group(process)
            raise

    output_bytes = stdout_path.stat().st_size + stderr_path.stat().st_size
    if output_bytes > MAX_OUTPUT_BYTES:
        status = "failing"
        detail = f"output exceeded {MAX_OUTPUT_BYTES} bytes"

    return {
        "assertions": [test.function],
        "diagnostics": {
            "stderr": str(stderr_path.relative_to(run_dir)),
            "stdout": str(stdout_path.relative_to(run_dir)),
        },
        "detail": detail,
        "duration_seconds": round(time.monotonic() - start, 6),
        "ended_at": utc_now(),
        "id": test.id,
        "level": test.level,
        "result": status,
        "started_at": started,
        "subjects": list(test.fixtures),
        "traces": list(test.traces),
    }


def tool_version(command: str, *args: str) -> str | None:
    executable = shutil.which(command)
    if executable is None:
        return None
    result = subprocess.run(
        (executable, *args),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip() or None


def select_tests(mode: str, values: Sequence[str]) -> tuple[str, list[Test]]:
    if mode == "profile":
        profile = values[0]
        return profile, [test for test in TESTS if profile in test.profiles]
    unknown = sorted(set(values) - TEST_BY_ID.keys())
    if unknown:
        raise ValueError(f"unknown test ID(s): {', '.join(unknown)}")
    return "selected", [TEST_BY_ID[value] for value in values]


def run(mode: str, values: Sequence[str]) -> int:
    if os.geteuid() == 0:
        print("validation refuses to run as root", file=sys.stderr)
        return 2

    try:
        profile, selected = select_tests(mode, values)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2

    started = utc_now()
    before = repository_snapshot()
    run_dir = Path(tempfile.mkdtemp(prefix="neutrinos-validation-"))
    (run_dir / "artifacts").mkdir()
    (run_dir / "logs").mkdir()
    home = run_dir / "home"
    home.mkdir()
    results_path = run_dir / "results.jsonl"
    results: list[dict[str, Any]] = []
    runner_error: str | None = None

    try:
        with results_path.open("a", encoding="utf-8") as stream:
            for test in selected:
                result = execute_test(test, run_dir, home)
                results.append(result)
                stream.write(canonical_json(result) + "\n")
                stream.flush()
    except BaseException as error:
        runner_error = f"{type(error).__name__}: {error}"

    after = repository_snapshot()
    cleanup_ok = before == after
    if not cleanup_ok and runner_error is None:
        runner_error = "validation changed repository state"

    counts = {name: 0 for name in ("passing", "failing", "blocked", "skipped", "not_applicable", "deferred")}
    for result in results:
        counts[result["result"]] += 1
    success = runner_error is None and len(results) == len(selected) and counts["failing"] == 0
    revision = git("rev-parse", "HEAD").stdout.strip()
    status = git("status", "--porcelain=v2", "--untracked-files=all").stdout
    manifest = {
        "cleanup": {"repository_preserved": cleanup_ok},
        "counts": counts,
        "dirty": bool(status),
        "dirty_identity": before["git_identity"],
        "ended_at": utc_now(),
        "environment": {"platform": sys.platform, "python": sys.version.split()[0]},
        "error": runner_error,
        "final_result": "passing" if success else "failing",
        "omissions": [
            {"id": test.id, "reason": "not selected by invocation"}
            for test in TESTS
            if test not in selected
        ],
        "profile": profile,
        "registered_suite_identity": hashlib.sha256(
            canonical_json([dataclasses.asdict(test) for test in TESTS]).encode()
        ).hexdigest(),
        "repository_revision": revision,
        "selected_ids": [test.id for test in selected],
        "started_at": started,
        "tools": {
            "mise": tool_version("mise", "--version"),
            "python": tool_version("python", "--version"),
            "uv": tool_version("uv", "--version"),
        },
        "worktree_identity": before["tree_identity"],
    }
    (run_dir / "run.json").write_text(canonical_json(manifest) + "\n", encoding="utf-8")

    print(f"run: {run_dir}")
    print(" ".join(f"{name}={count}" for name, count in counts.items()))
    if runner_error:
        print(runner_error, file=sys.stderr)
    return 0 if success else 1


def list_tests() -> int:
    print("ID\tLEVEL\tPROFILES\tTIMEOUT\tTRACES\tCAPABILITIES")
    for test in TESTS:
        print(
            "\t".join(
                (
                    test.id,
                    test.level,
                    ",".join(test.profiles),
                    f"{test.timeout_seconds}s",
                    ",".join(test.traces),
                    ",".join(test.capabilities) or "none",
                )
            )
        )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    profile = subparsers.add_parser("profile")
    profile.add_argument("name", choices=("fast", "complete"))
    exact = subparsers.add_parser("run")
    exact.add_argument("ids", nargs="+")
    subparsers.add_parser("list")
    internal = subparsers.add_parser("_execute")
    internal.add_argument("id", choices=tuple(TEST_BY_ID))
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    if arguments.command == "list":
        return list_tests()
    if arguments.command == "profile":
        return run("profile", (arguments.name,))
    if arguments.command == "run":
        return run("run", arguments.ids)
    test = TEST_BY_ID[arguments.id]
    return CHECKS[test.function]()


if __name__ == "__main__":
    raise SystemExit(main())
