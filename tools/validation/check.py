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
import secrets
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Mapping, Sequence
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MAX_OUTPUT_BYTES = 1_048_576
MAX_ERROR_BYTES = 16_384
SCAN_CHUNK_BYTES = 65_536
SCAN_OVERLAP_BYTES = 512
VALIDATION_CACHE_ROOT_ENV = "NEUTRINOS_VALIDATION_CACHE_ROOT"
PYTHON_INSTALL_ENV = "NEUTRINOS_VALIDATION_PYTHON_INSTALL"
UV_INSTALL_ENV = "NEUTRINOS_VALIDATION_UV_INSTALL"
UV_CACHE_ENV = "NEUTRINOS_VALIDATION_UV_CACHE"
BETTERLEAKS_ENV = "NEUTRINOS_VALIDATION_BETTERLEAKS"
SYNTHETIC_CANARY_ENV = "NEUTRINOS_VALIDATION_CANARY"
SYNTHETIC_CANARY_PREFIX = "NEUTRINOS_SYNTHETIC_CANARY_"
UNSAFE_OUTPUT_PATTERNS = (
    ("private_key", re.compile(rb"-----BEGIN [A-Z0-9 ]{0,48}PRIVATE KEY-----")),
    ("aws_access_key", re.compile(rb"(?:AKIA|ASIA)[A-Z0-9]{16}")),
    (
        "github_token",
        re.compile(
            rb"(?:gh[pousr]_[A-Za-z0-9_]{20,255}|"
            rb"github_pat_[A-Za-z0-9_]{20,255})"
        ),
    ),
    (
        "bearer_token",
        re.compile(
            rb"(?i:authorization)[ \t]*:[ \t]*"
            rb"(?i:bearer)[ \t]+[^\s]{20,255}"
        ),
    ),
)
ALLOWED_RUNNER_ENVIRONMENT = frozenset(
    {
        "COLORTERM",
        "HOME",
        "LANG",
        "MISE_TASK_PGID_MANAGED",
        VALIDATION_CACHE_ROOT_ENV,
        PYTHON_INSTALL_ENV,
        UV_INSTALL_ENV,
        UV_CACHE_ENV,
        BETTERLEAKS_ENV,
        "PATH",
        "PWD",
        "SHELL",
        "SHLVL",
        "TERM",
        "USER",
        "UV",
        "UV_RUN_RECURSION_DEPTH",
        "VIRTUAL_ENV",
        "_",
    }
)


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


@dataclasses.dataclass(frozen=True)
class ProcessExecution:
    returncode: int
    detail: str | None
    output_bytes: int
    cleanup_ok: bool


@dataclasses.dataclass
class OutputSafety:
    canary: bytes
    quarantine_dir: Path | None = None
    findings: list[dict[str, str]] = dataclasses.field(default_factory=list)

    def _quarantine_root(self) -> Path:
        if self.quarantine_dir is None:
            self.quarantine_dir = Path(
                tempfile.mkdtemp(prefix="neutrinos-validation-quarantine-")
            )
            self.quarantine_dir.chmod(0o700)
        return self.quarantine_dir

    def _record(self, relative: Path, kinds: Sequence[str]) -> None:
        for kind in kinds:
            finding = {"kind": kind, "path": str(relative)}
            if finding not in self.findings:
                self.findings.append(finding)

    def _destination(self, relative: Path) -> Path:
        destination = self._quarantine_root() / relative
        if destination.exists() or destination.is_symlink():
            destination = (
                self._quarantine_root()
                / "duplicates"
                / f"{len(self.findings):06d}"
                / relative
            )
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        return destination

    def inspect_file(self, path: Path, run_dir: Path) -> bool:
        relative = path.relative_to(run_dir)
        try:
            kinds = unsafe_output_kinds(path, self.canary)
        except OSError:
            kinds = ["scan_error"]
        if not kinds:
            return False
        destination = self._destination(relative)
        os.replace(path, destination)
        if relative.parts[0] in {"logs", "artifacts"}:
            path.write_text(
                "unsafe output quarantined; content omitted\n", encoding="utf-8"
            )
            path.chmod(0o600)
        self._record(relative, kinds)
        return True

    def quarantine_bytes(
        self,
        storage_relative: Path,
        value: bytes,
        kinds: Sequence[str],
        *,
        finding_relative: Path | None = None,
    ) -> None:
        destination = self._destination(storage_relative)
        destination.write_bytes(value)
        destination.chmod(0o600)
        self._record(finding_relative or storage_relative, kinds)


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
    Test(
        id="T0-SEC-001",
        level="T0",
        profiles=("fast", "complete"),
        timeout_seconds=120,
        traces=("PLN-0000/PRE-017",),
        capabilities=("locked betterleaks",),
        fixtures=("repository checkout", "reachable Git history"),
        cleanup_owner="validation runner",
        function="check_secret_scan",
    ),
    Test(
        id="T5-VAL-001",
        level="T5@T1",
        profiles=("fast", "complete"),
        timeout_seconds=60,
        traces=("PLN-0000/PRE-015",),
        capabilities=(),
        fixtures=("synthetic hostile validation processes",),
        cleanup_owner="validation runner",
        function="check_runner_hostile_probes",
    ),
    Test(
        id="T5-VAL-002",
        level="T5@T1",
        profiles=("fast", "complete"),
        timeout_seconds=60,
        traces=("PLN-0000/PRE-015",),
        capabilities=(),
        fixtures=("isolated empty mise cache", "locked local Python and uv"),
        cleanup_owner="validation runner",
        function="check_empty_mise_cache",
    ),
    Test(
        id="T5-VAL-003",
        level="T5@T1",
        profiles=("complete",),
        timeout_seconds=600,
        traces=("PLN-0000/PRE-016",),
        capabilities=("populated uv cache",),
        fixtures=("clean clone of committed HEAD",),
        cleanup_owner="validation runner",
        function="check_clean_clone",
    ),
)
TEST_BY_ID = {test.id: test for test in TESTS}


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="milliseconds")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def bounded_error(value: object) -> str:
    encoded = str(value).encode("utf-8", errors="replace")
    if len(encoded) <= MAX_ERROR_BYTES:
        return encoded.decode("utf-8", errors="replace")
    suffix = b"... [truncated]"
    return (encoded[: MAX_ERROR_BYTES - len(suffix)] + suffix).decode(
        "utf-8", errors="replace"
    )


def unsafe_bytes_kinds(value: bytes, canary: bytes) -> list[str]:
    kinds = []
    if canary in value:
        kinds.append("synthetic_canary")
    for name, pattern in UNSAFE_OUTPUT_PATTERNS:
        if pattern.search(value):
            kinds.append(name)
    return kinds


def unsafe_output_kinds(path: Path, canary: bytes) -> list[str]:
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode):
        return ["unsupported_file_type"]
    kinds: set[str] = set()
    overlap = b""
    with path.open("rb") as stream:
        while chunk := stream.read(SCAN_CHUNK_BYTES):
            value = overlap + chunk
            kinds.update(unsafe_bytes_kinds(value, canary))
            overlap = value[-SCAN_OVERLAP_BYTES:]
    return sorted(kinds)


def make_synthetic_canary() -> str:
    return SYNTHETIC_CANARY_PREFIX + secrets.token_hex(24)


def output_safe_error(value: object, safety: OutputSafety) -> str:
    error = bounded_error(value)
    encoded = error.encode("utf-8")
    kinds = unsafe_bytes_kinds(encoded, safety.canary)
    if not kinds:
        return error
    safety.quarantine_bytes(
        Path("raw-runner-error.txt"),
        encoded,
        kinds,
        finding_relative=Path("run.json"),
    )
    return "unsafe runner diagnostic quarantined; content omitted"


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *args),
        cwd=ROOT,
        env=git_environment(),
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def git_environment() -> dict[str, str]:
    return {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "HOME": os.environ.get("HOME", os.devnull),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH": os.environ["PATH"],
    }


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


def validation_cache_root(environment: Mapping[str, str] = os.environ) -> Path:
    raw = environment.get(VALIDATION_CACHE_ROOT_ENV)
    if not raw:
        raise ValueError(f"{VALIDATION_CACHE_ROOT_ENV} is not set")
    path = Path(raw)
    if not path.is_absolute():
        raise ValueError(f"{VALIDATION_CACHE_ROOT_ENV} must be an absolute path")
    path = path.resolve()
    repository = ROOT.resolve()
    if path == repository or repository in path.parents:
        raise ValueError(f"{VALIDATION_CACHE_ROOT_ENV} must be outside the repository")
    return path


def declared_directory(
    name: str, environment: Mapping[str, str] = os.environ
) -> Path:
    """An externally declared directory that must sit outside the checkout."""
    raw = environment.get(name)
    if not raw:
        raise ValueError(f"{name} is not set")
    path = Path(raw)
    if not path.is_absolute():
        raise ValueError(f"{name} must be an absolute path")
    path = path.resolve()
    if not path.is_dir():
        raise ValueError(f"{name} must identify an existing directory")
    repository = ROOT.resolve()
    if path == repository or repository in path.parents:
        raise ValueError(f"{name} must be outside the repository")
    return path


def tool_install_path(
    name: str, environment: Mapping[str, str] = os.environ
) -> Path:
    raw = environment.get(name)
    if not raw:
        raise ValueError(f"{name} is not set")
    path = Path(raw)
    if not path.is_absolute():
        raise ValueError(f"{name} must be an absolute path")
    path = path.resolve()
    if not path.is_dir():
        raise ValueError(f"{name} must identify an installed tool directory")
    repository = ROOT.resolve()
    if path == repository or repository in path.parents:
        raise ValueError(f"{name} must be outside the repository")
    return path


def check_runner_hostile_probes() -> int:
    cache_dir = validation_cache_root() / "pytest"
    result = subprocess.run(
        (
            sys.executable,
            "-m",
            "pytest",
            "-o",
            f"cache_dir={cache_dir}",
            "-q",
            "tools/validation/tests",
        ),
        cwd=ROOT,
        check=False,
    )
    return result.returncode


def relative_files(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(
        str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()
    )


def check_empty_mise_cache() -> int:
    mise = shutil.which("mise")
    if mise is None:
        # Report the search path: this check resolves mise from PATH rather
        # than from a declared input, so where it looked is the whole answer
        # when it fails, and the path differs between a workstation and CI.
        print(
            "mise executable unavailable on PATH="
            f"{os.environ.get('PATH', '')}",
            file=sys.stderr,
        )
        return 1
    try:
        installs = {
            "python": tool_install_path(PYTHON_INSTALL_ENV),
            "uv": tool_install_path(UV_INSTALL_ENV),
            # The dispatcher declares the scanner executable rather than an
            # install root; aqua places the binary directly in the versioned
            # install directory, so its parent is that root.
            "betterleaks": declared_executable(BETTERLEAKS_ENV).parent,
        }
    except ValueError as error:
        print(bounded_error(error), file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="neutrinos-empty-mise-cache-") as raw:
        root = Path(raw)
        directories = {
            "cache": root / "xdg-cache" / "mise",
            "config": root / "xdg-config" / "mise",
            "data": root / "xdg-data" / "mise",
            "home": root / "home",
            "state": root / "xdg-state" / "mise",
        }
        for directory in directories.values():
            directory.mkdir(mode=0o700, parents=True)
        global_config = directories["config"] / "config.toml"
        global_config.touch()
        system_config = root / "system-config"
        system_config.mkdir(mode=0o700)
        for name, source in installs.items():
            target = directories["data"] / "installs" / name
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            target.symlink_to(source.parent, target_is_directory=True)

        environment = {
            "HOME": str(directories["home"]),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "MISE_CACHE_DIR": str(directories["cache"]),
            "MISE_CEILING_PATHS": str(ROOT.parent),
            "MISE_CONFIG_DIR": str(directories["config"]),
            "MISE_DATA_DIR": str(directories["data"]),
            "MISE_GLOBAL_CONFIG_FILE": str(global_config),
            "MISE_INSTALLS_DIR": str(directories["data"] / "installs"),
            "MISE_NO_HOOKS": "1",
            "MISE_STATE_DIR": str(directories["state"]),
            "MISE_SYSTEM_CONFIG_DIR": str(system_config),
            "PATH": os.pathsep.join(
                dict.fromkeys(
                    (str(Path(mise).parent), "/usr/local/bin", "/usr/bin", "/bin")
                )
            ),
            "XDG_CACHE_HOME": str(root / "xdg-cache"),
            "XDG_CONFIG_HOME": str(root / "xdg-config"),
            "XDG_DATA_HOME": str(root / "xdg-data"),
            "XDG_STATE_HOME": str(root / "xdg-state"),
        }
        trust = subprocess.run(
            (mise, "trust", "--yes", "--quiet", str(ROOT / "mise.toml")),
            cwd=ROOT,
            env=environment,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if trust.returncode != 0:
            print(
                "isolated mise trust setup failed: " + bounded_error(trust.stderr),
                file=sys.stderr,
            )
            return 1
        if relative_files(directories["cache"]):
            print("isolated mise cache was not empty before task execution", file=sys.stderr)
            return 1

        result = subprocess.run(
            (
                mise,
                "run",
                "--allow-env=MISE_*",
                "--allow-env=XDG_*",
                "check:list",
            ),
            cwd=ROOT,
            env=environment,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            print(
                "isolated empty-cache task failed: " + bounded_error(result.stderr),
                file=sys.stderr,
            )
            return 1
        resolved_tools: dict[str, str] = {}
        for name, source in installs.items():
            resolved = subprocess.run(
                (mise, "which", name),
                cwd=ROOT,
                env=environment,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            resolved_path = Path(resolved.stdout.strip()).resolve()
            if resolved.returncode != 0 or not resolved_path.is_relative_to(source):
                print(
                    f"isolated task did not resolve the locked {name} installation",
                    file=sys.stderr,
                )
                return 1
            resolved_tools[name] = str(resolved_path.relative_to(source))
        cache_files = relative_files(directories["cache"])
        allowed_bin_path_files = {
            (name, source.name) for name, source in installs.items()
        }
        unexpected = []
        for path in cache_files:
            parts = Path(path).parts
            if (
                len(parts) != 3
                or (parts[0], parts[1]) not in allowed_bin_path_files
                or not parts[2].startswith("bin_paths-")
                or not parts[2].endswith(".msgpack.z")
            ):
                unexpected.append(path)
        if "T5-VAL-002" not in result.stdout:
            print("isolated task did not execute the registered list query", file=sys.stderr)
            return 1
        if unexpected:
            print(
                "isolated task wrote non-local-resolution cache metadata: "
                + ", ".join(unexpected),
                file=sys.stderr,
            )
            return 1
        print(
            canonical_json(
                {
                    "cache_files": cache_files,
                    "cache_was_empty": True,
                    "nested_task": "check:list",
                    "remote_metadata_files": [],
                    "resolved_tools": resolved_tools,
                    "result": "passing",
                }
            )
        )
    return 0


def check_clean_clone() -> int:
    """A clean clone runs its own committed fast profile from declared inputs.

    The clone is driven through its committed runner rather than through
    ``mise run``: the nested runner enforces a strict environment allowlist,
    and the mise configuration isolation this probe needs cannot cross it
    without widening that allowlist. Mise task dispatch is therefore not
    exercised here; ``T5-VAL-002`` covers it.
    """
    git = shutil.which("git")
    if git is None:
        print("git executable unavailable", file=sys.stderr)
        return 1
    mise = shutil.which("mise")
    if mise is None:
        print(
            "mise executable unavailable on PATH="
            f"{os.environ.get('PATH', '')}",
            file=sys.stderr,
        )
        return 1
    try:
        python_install = tool_install_path(PYTHON_INSTALL_ENV)
        uv_install = tool_install_path(UV_INSTALL_ENV)
        uv_cache = declared_directory(UV_CACHE_ENV)
        scanner = declared_executable(BETTERLEAKS_ENV)
    except ValueError as error:
        print(bounded_error(error), file=sys.stderr)
        return 1
    python = python_install / "bin" / "python"
    candidates = sorted(uv_install.glob("*/uv")) + sorted(uv_install.glob("uv"))
    if not python.is_file() or not candidates:
        print("declared Python or uv installation is unusable", file=sys.stderr)
        return 1
    uv = candidates[0]

    with tempfile.TemporaryDirectory(prefix="neutrinos-clean-clone-") as raw:
        root = Path(raw)
        clone = root / "clone"
        home = root / "home"
        cache_root = root / "cache"
        for directory in (home, cache_root):
            directory.mkdir(mode=0o700)

        cloned = subprocess.run(
            (git, "clone", "--quiet", "--no-local", str(ROOT), str(clone)),
            cwd=root,
            env=git_environment(),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if cloned.returncode != 0:
            print(
                "clean clone failed: " + bounded_error(cloned.stderr),
                file=sys.stderr,
            )
            return 1

        # The clone runs its own committed runner, which enforces a strict
        # environment allowlist. Everything else is passed as a uv flag so no
        # undeclared variable reaches it.
        environment = {
            "HOME": str(home),
            "LANG": "C.UTF-8",
            # The clone's own fast profile includes T5-VAL-002, which resolves
            # mise from PATH. Include mise's directory explicitly: on a
            # workstation it is usually /usr/bin and was covered by accident,
            # but a CI runner installs it elsewhere and the clone then fails
            # for a reason that has nothing to do with the clone.
            "PATH": os.pathsep.join(
                dict.fromkeys(
                    (
                        str(Path(git).parent),
                        str(Path(mise).parent),
                        "/usr/bin",
                        "/bin",
                    )
                )
            ),
            VALIDATION_CACHE_ROOT_ENV: str(cache_root),
            PYTHON_INSTALL_ENV: str(python_install),
            UV_INSTALL_ENV: str(uv_install),
            UV_CACHE_ENV: str(uv_cache),
            BETTERLEAKS_ENV: str(scanner),
        }
        uv_flags = (
            "--offline",
            "--locked",
            "--cache-dir",
            str(uv_cache),
            "--no-managed-python",
            "--python",
            str(python),
        )

        bootstrap = subprocess.run(
            (str(uv), "sync", *uv_flags),
            cwd=clone,
            env=environment,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if bootstrap.returncode != 0:
            print(
                "clean clone could not build its declared environment offline; "
                "the declared uv cache must already hold the locked packages: "
                + bounded_error(bootstrap.stderr),
                file=sys.stderr,
            )
            return 1

        executed = subprocess.run(
            (
                str(uv),
                "run",
                *uv_flags,
                "--no-sync",
                "--no-env-file",
                "python",
                "tools/validation/check.py",
                "profile",
                "fast",
            ),
            cwd=clone,
            env=environment,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if executed.returncode != 0:
            print(
                # The clone's summary line and run directory are on stdout;
                # a preflight or selection failure writes only there, so
                # reporting stderr alone can produce an empty reason.
                "clean clone failed its own fast profile: "
                + bounded_error(executed.stderr)
                + " stdout: "
                + bounded_error(executed.stdout),
                file=sys.stderr,
            )
            return 1

        dirty = subprocess.run(
            (git, "status", "--porcelain"),
            cwd=clone,
            env=git_environment(),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        residue = [line for line in dirty.stdout.splitlines() if line.strip()]
        if dirty.returncode != 0 or residue:
            print(
                "clean clone was modified by its own validation: "
                + ", ".join(residue[:5]),
                file=sys.stderr,
            )
            return 1

        print(
            canonical_json(
                {
                    "clone_clean_after_run": True,
                    "nested_dispatch": "committed runner",
                    "nested_profile": "fast",
                    "offline": True,
                    "result": "passing",
                    "source": "committed HEAD",
                }
            )
        )
    return 0


def check_secret_scan() -> int:
    """No committed secret in the working tree or in reachable history.

    Runs the locked betterleaks against both sources. Scanning is offline and
    uses the pinned binary the dispatcher resolved, so this behaves the same
    locally and in CI: there is one definition of the check, not two.

    ``--redact`` is not optional. A finding must never widen exposure by
    printing the secret into a log, a result record, or a CI transcript.
    """
    scanner = declared_executable(BETTERLEAKS_ENV)
    config = ROOT / ".betterleaks.toml"
    if not config.is_file():
        print("secret-scanning configuration is missing", file=sys.stderr)
        return 1
    for source in ("dir", "git"):
        result = subprocess.run(
            (
                str(scanner),
                source,
                # A relative target keeps reported paths repository-relative,
                # which is what allowlist path patterns are written against.
                ".",
                "--config",
                str(config),
                "--redact",
                "--no-banner",
            ),
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        if result.returncode != 0:
            print(f"secret scan of {source} reported findings", file=sys.stderr)
            return result.returncode
    return 0


CHECKS: dict[str, Callable[[], int]] = {
    "check_git_diff": check_git_diff,
    "check_markdown_links": check_markdown_links,
    "check_runner_hostile_probes": check_runner_hostile_probes,
    "check_empty_mise_cache": check_empty_mise_cache,
    "check_clean_clone": check_clean_clone,
    "check_secret_scan": check_secret_scan,
}


def declared_executable(
    name: str, environment: Mapping[str, str] = os.environ
) -> Path:
    """An externally declared executable resolved by the task dispatcher."""
    raw = environment.get(name)
    if not raw:
        raise ValueError(f"{name} is not set")
    path = Path(raw)
    if not path.is_absolute():
        raise ValueError(f"{name} must be an absolute path")
    path = path.resolve()
    if not path.is_file():
        raise ValueError(f"{name} must identify an existing file")
    if not os.access(path, os.X_OK):
        raise ValueError(f"{name} must identify an executable file")
    repository = ROOT.resolve()
    if path == repository or repository in path.parents:
        raise ValueError(f"{name} must be outside the repository")
    return path


def preflight_errors(
    environment: Mapping[str, str] = os.environ,
    effective_uid: int | None = None,
) -> list[str]:
    errors = []
    if (os.geteuid() if effective_uid is None else effective_uid) == 0:
        errors.append("validation refuses to run as root")
    unexpected = sorted(set(environment) - ALLOWED_RUNNER_ENVIRONMENT)
    if unexpected:
        errors.append(f"undeclared environment variables: {', '.join(unexpected)}")
    try:
        validation_cache_root(environment)
    except ValueError as error:
        errors.append(str(error))
    for name in (PYTHON_INSTALL_ENV, UV_INSTALL_ENV):
        try:
            tool_install_path(name, environment)
        except ValueError as error:
            errors.append(str(error))
    try:
        declared_executable(BETTERLEAKS_ENV, environment)
    except ValueError as error:
        errors.append(str(error))
    try:
        declared_directory(UV_CACHE_ENV, environment)
    except ValueError as error:
        errors.append(str(error))
    return errors


def child_environment(home: Path, cache_root: Path, canary: str) -> dict[str, str]:
    environment = {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "HOME": str(home),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        VALIDATION_CACHE_ROOT_ENV: str(cache_root),
        "PATH": os.environ["PATH"],
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
        SYNTHETIC_CANARY_ENV: canary,
        PYTHON_INSTALL_ENV: os.environ[PYTHON_INSTALL_ENV],
        UV_INSTALL_ENV: os.environ[UV_INSTALL_ENV],
        UV_CACHE_ENV: os.environ[UV_CACHE_ENV],
        BETTERLEAKS_ENV: os.environ[BETTERLEAKS_ENV],
    }
    if "SYSTEMROOT" in os.environ:
        environment["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    return environment


def terminate_process_group(process_group: int, process: subprocess.Popen[bytes]) -> bool:
    try:
        os.killpg(process_group, signal.SIGTERM)
    except ProcessLookupError:
        return True

    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process_group, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()

    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        try:
            os.killpg(process_group, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.01)
    try:
        os.killpg(process_group, signal.SIGKILL)
    except ProcessLookupError:
        return True
    return False


def execute_process(
    command: Sequence[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    stdout_path: Path,
    stderr_path: Path,
    timeout_seconds: float,
    max_output_bytes: int = MAX_OUTPUT_BYTES,
) -> ProcessExecution:
    started = time.monotonic()
    detail: str | None = None
    output_bytes = 0
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=environment,
        start_new_session=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdout is not None
    assert process.stderr is not None
    selector = selectors.DefaultSelector()
    outputs = {
        process.stdout.fileno(): stdout_path.open("wb"),
        process.stderr.fileno(): stderr_path.open("wb"),
    }
    for stream in (process.stdout, process.stderr):
        os.set_blocking(stream.fileno(), False)
        selector.register(stream, selectors.EVENT_READ)

    try:
        while selector.get_map():
            remaining = timeout_seconds - (time.monotonic() - started)
            if remaining <= 0:
                detail = f"timed out after {timeout_seconds:g}s"
                break
            for key, _ in selector.select(timeout=min(remaining, 0.05)):
                chunk = os.read(key.fd, 65_536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                permitted = max_output_bytes - output_bytes
                if permitted > 0:
                    outputs[key.fd].write(chunk[:permitted])
                output_bytes += len(chunk)
                if output_bytes > max_output_bytes:
                    detail = f"output exceeded {max_output_bytes} bytes"
                    break
            if detail is not None:
                break
            if process.poll() is not None:
                # Descendants must not keep inherited output pipes or other
                # process-group resources alive after the registered command.
                terminate_process_group(process.pid, process)
        if detail is not None:
            terminate_process_group(process.pid, process)
    except BaseException:
        terminate_process_group(process.pid, process)
        raise
    finally:
        selector.close()
        for output in outputs.values():
            output.close()
        process.stdout.close()
        process.stderr.close()

    cleanup_ok = terminate_process_group(process.pid, process)
    returncode = process.poll()
    if returncode is None:
        returncode = -signal.SIGKILL
    if detail is None and returncode != 0:
        detail = f"exited {returncode}"
    return ProcessExecution(
        returncode=returncode,
        detail=detail,
        output_bytes=output_bytes,
        cleanup_ok=cleanup_ok,
    )


def execute_test(
    test: Test,
    run_dir: Path,
    home: Path,
    cache_root: Path,
    canary: str,
) -> dict[str, Any]:
    logs = run_dir / "logs"
    stdout_path = logs / f"{test.id}.stdout.log"
    stderr_path = logs / f"{test.id}.stderr.log"
    started = utc_now()
    start = time.monotonic()
    execution = execute_process(
        (sys.executable, str(Path(__file__).resolve()), "_execute", test.id),
        cwd=ROOT,
        environment=child_environment(home, cache_root, canary),
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout_seconds=test.timeout_seconds,
    )
    status = "passing" if execution.returncode == 0 and execution.detail is None else "failing"
    detail = execution.detail
    if not execution.cleanup_ok:
        status = "failing"
        detail = "process-group cleanup failed"

    return {
        "assertions": [test.function],
        "cleanup": {"process_group_absent": execution.cleanup_ok},
        "diagnostics": {
            "stderr": str(stderr_path.relative_to(run_dir)),
            "stdout": str(stdout_path.relative_to(run_dir)),
        },
        "detail": detail,
        "duration_seconds": round(time.monotonic() - start, 6),
        "ended_at": utc_now(),
        "id": test.id,
        "level": test.level,
        "output_bytes": execution.output_bytes,
        "result": status,
        "started_at": started,
        "subjects": list(test.fixtures),
        "traces": list(test.traces),
    }


def test_output_paths(test: Test, run_dir: Path) -> list[Path]:
    paths = [
        run_dir / "logs" / f"{test.id}.stdout.log",
        run_dir / "logs" / f"{test.id}.stderr.log",
    ]
    for path in sorted((run_dir / "artifacts").rglob("*")):
        if stat.S_ISDIR(path.lstat().st_mode):
            continue
        paths.append(path)
    return paths


def sanitized_unsafe_result(
    test: Test,
    result: Mapping[str, Any],
    findings: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    return {
        "assertions": ["retained_output_contains_no_unsafe_material"],
        "cleanup": result.get("cleanup", {"process_group_absent": False}),
        "diagnostics": {},
        "detail": "unsafe output quarantined; content omitted",
        "duration_seconds": result.get("duration_seconds", 0),
        "ended_at": result.get("ended_at", utc_now()),
        "id": test.id,
        "level": test.level,
        "output_bytes": result.get("output_bytes", 0),
        "output_safety_findings": list(findings),
        "result": "failing",
        "started_at": result.get("started_at", utc_now()),
        "subjects": [],
        "traces": list(test.traces),
    }


def tool_version(command: str, *args: str) -> str | None:
    executable = shutil.which(command)
    if executable is None:
        return None
    try:
        result = subprocess.run(
            (executable, *args),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError:
        return None
    return result.stdout.strip() or None


def select_tests(mode: str, values: Sequence[str]) -> tuple[str, list[Test]]:
    if mode == "profile":
        if len(values) != 1 or values[0] not in {"fast", "complete"}:
            raise ValueError("unknown validation profile")
        profile = values[0]
        return profile, [test for test in TESTS if profile in test.profiles]
    unknown = sorted(set(values) - TEST_BY_ID.keys())
    if unknown:
        safe = [value for value in unknown if re.fullmatch(r"[A-Z][A-Z0-9-]{0,63}", value)]
        if len(safe) == len(unknown):
            raise ValueError(f"unknown test ID(s): {', '.join(safe)}")
        raise ValueError(f"invalid test ID syntax ({len(unknown)} value(s))")
    return "selected", [TEST_BY_ID[value] for value in values]


def run(
    mode: str,
    values: Sequence[str],
    *,
    invocation_error: str | None = None,
) -> int:
    started = utc_now()
    run_dir = Path(tempfile.mkdtemp(prefix="neutrinos-validation-"))
    (run_dir / "artifacts").mkdir()
    (run_dir / "logs").mkdir()
    home = run_dir / "home"
    home.mkdir()
    results_path = run_dir / "results.jsonl"
    results_path.touch()
    canary = make_synthetic_canary()
    output_safety = OutputSafety(canary=canary.encode("utf-8"))

    before: dict[str, str] | None = None
    after: dict[str, str] | None = None
    cache_root: Path | None = None
    if invocation_error is not None:
        profile = "invalid"
    elif mode == "run":
        profile = "selected"
    elif mode == "profile" and values:
        profile = values[0]
    else:
        profile = mode
    selected: list[Test] = []
    results: list[dict[str, Any]] = []
    runner_error: str | None = None
    failure_stage: str | None = None
    output_safety_trigger_stage: str | None = None

    try:
        before = repository_snapshot()
    except BaseException as error:
        runner_error = output_safe_error(
            f"{type(error).__name__}: {error}", output_safety
        )
        failure_stage = "source_snapshot"

    if runner_error is None:
        errors = preflight_errors()
        if errors:
            runner_error = output_safe_error("; ".join(errors), output_safety)
            failure_stage = "preflight"
        else:
            cache_root = validation_cache_root()

    if runner_error is None and invocation_error is not None:
        runner_error = output_safe_error(invocation_error, output_safety)
        failure_stage = "invocation"

    if runner_error is None:
        try:
            profile, selected = select_tests(mode, values)
        except ValueError as error:
            runner_error = output_safe_error(error, output_safety)
            failure_stage = "selection"

    if runner_error is None:
        assert cache_root is not None
        try:
            with results_path.open("a", encoding="utf-8") as stream:
                for test in selected:
                    finding_start = len(output_safety.findings)
                    result = execute_test(test, run_dir, home, cache_root, canary)
                    for path in test_output_paths(test, run_dir):
                        output_safety.inspect_file(path, run_dir)
                    new_findings = output_safety.findings[finding_start:]
                    if new_findings:
                        result = sanitized_unsafe_result(test, result, new_findings)
                    encoded_result = canonical_json(result).encode("utf-8")
                    result_kinds = unsafe_bytes_kinds(
                        encoded_result, output_safety.canary
                    )
                    if result_kinds:
                        output_safety.quarantine_bytes(
                            Path("raw-results") / f"{test.id}.json",
                            encoded_result,
                            result_kinds,
                            finding_relative=Path("results.jsonl"),
                        )
                        result = sanitized_unsafe_result(
                            test,
                            result,
                            output_safety.findings[finding_start:],
                        )
                    results.append(result)
                    stream.write(canonical_json(result) + "\n")
                    stream.flush()
        except BaseException as error:
            runner_error = output_safe_error(
                f"{type(error).__name__}: {error}", output_safety
            )
            failure_stage = "execution"

    if before is not None:
        try:
            after = repository_snapshot()
        except BaseException as error:
            if runner_error is None:
                runner_error = output_safe_error(
                    f"{type(error).__name__}: {error}", output_safety
                )
                failure_stage = "cleanup_verification"

    cleanup_ok = before is not None and after is not None and before == after
    if before is not None and after is not None and not cleanup_ok:
        if runner_error is None:
            runner_error = "validation changed repository state"
            failure_stage = "cleanup_verification"

    if output_safety.findings:
        output_safety_trigger_stage = failure_stage
        if runner_error is None:
            runner_error = "unsafe output quarantined; content omitted"
        failure_stage = "output_safety"

    counts = {
        name: 0
        for name in (
            "passing",
            "failing",
            "blocked",
            "skipped",
            "not_applicable",
            "deferred",
        )
    }
    for result in results:
        counts[result["result"]] += 1
    success = (
        runner_error is None
        and len(results) == len(selected)
        and counts["failing"] == 0
    )
    revision: str | None = None
    dirty: bool | None = None
    if before is not None:
        try:
            revision = git("rev-parse", "HEAD").stdout.strip()
            status = git("status", "--porcelain=v2", "--untracked-files=all").stdout
            dirty = bool(status)
        except (OSError, subprocess.SubprocessError):
            pass
    manifest = {
        "cleanup": {"repository_preserved": cleanup_ok},
        "cache": {
            "affects_selection": False,
            "path": str(cache_root) if cache_root is not None else None,
            "retained_as_evidence": False,
        },
        "counts": counts,
        "dirty": dirty,
        "dirty_identity": before["git_identity"] if before is not None else None,
        "ended_at": utc_now(),
        "environment": {"platform": sys.platform, "python": sys.version.split()[0]},
        "error": runner_error,
        "failure_stage": failure_stage,
        "final_result": "passing" if success else "failing",
        "omissions": [
            {"id": test.id, "reason": "not selected by invocation"}
            for test in TESTS
            if test not in selected
        ],
        "output_safety": {
            "canary_configured": True,
            "findings": output_safety.findings,
            "passed": not output_safety.findings,
            "quarantine_path": (
                str(output_safety.quarantine_dir)
                if output_safety.quarantine_dir is not None
                else None
            ),
            "trigger_stage": output_safety_trigger_stage,
        },
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
        "worktree_identity": before["tree_identity"] if before is not None else None,
    }
    manifest_bytes = (canonical_json(manifest) + "\n").encode("utf-8")
    manifest_kinds = unsafe_bytes_kinds(manifest_bytes, output_safety.canary)
    if manifest_kinds:
        output_safety.quarantine_bytes(
            Path("raw-run.json"),
            manifest_bytes,
            manifest_kinds,
            finding_relative=Path("run.json"),
        )
        manifest["error"] = "unsafe manifest content quarantined; content omitted"
        manifest["failure_stage"] = "output_safety"
        manifest["final_result"] = "failing"
        manifest["output_safety"] = {
            "canary_configured": True,
            "findings": output_safety.findings,
            "passed": False,
            "quarantine_path": str(output_safety.quarantine_dir),
            "trigger_stage": failure_stage,
        }
        runner_error = manifest["error"]
        failure_stage = "output_safety"
        success = False
    (run_dir / "run.json").write_text(
        canonical_json(manifest) + "\n", encoding="utf-8"
    )

    print(f"run: {run_dir}")
    print(" ".join(f"{name}={count}" for name, count in counts.items()))
    if runner_error:
        print(runner_error, file=sys.stderr)
    if success:
        return 0
    return 2 if failure_stage in {"invocation", "preflight", "selection"} else 1


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


class InvocationArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise ValueError("invalid command-line invocation")


def parse_args() -> argparse.Namespace:
    parser = InvocationArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    profile = subparsers.add_parser("profile")
    profile.add_argument("name")
    exact = subparsers.add_parser("run")
    exact.add_argument("ids", nargs="+")
    subparsers.add_parser("list")
    internal = subparsers.add_parser("_execute")
    internal.add_argument("id", choices=tuple(TEST_BY_ID))
    return parser.parse_args()


def main() -> int:
    try:
        arguments = parse_args()
    except ValueError as error:
        return run("invalid", (), invocation_error=bounded_error(error))
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
