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
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MAX_OUTPUT_BYTES = 1_048_576
MAX_ERROR_BYTES = 16_384
SCAN_CHUNK_BYTES = 65_536
SCAN_OVERLAP_BYTES = 512
MAXIMUM_TRACKED_BYTES = 1_048_576
# Git's empty tree. Diffing the index against it lists every tracked blob as an
# addition, which is how a whole-repository classification is obtained from a
# command that otherwise reports only changes.
EMPTY_TREE_OBJECT = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
VALIDATION_CACHE_ROOT_ENV = "NEUTRINOS_VALIDATION_CACHE_ROOT"
PYTHON_INSTALL_ENV = "NEUTRINOS_VALIDATION_PYTHON_INSTALL"
UV_INSTALL_ENV = "NEUTRINOS_VALIDATION_UV_INSTALL"
UV_CACHE_ENV = "NEUTRINOS_VALIDATION_UV_CACHE"
BETTERLEAKS_ENV = "NEUTRINOS_VALIDATION_BETTERLEAKS"
SLICE_ARTIFACT_ENV = "NEUTRINOS_SLICE_ARTIFACT_DIR"
SLICE_REPOSITORY_ENV = "NEUTRINOS_SLICE_REPOSITORY_DIR"
CONFEXT_FIXTURE_ENV = "NEUTRINOS_CONFEXT_FIXTURE_DIR"
STATE_ARTIFACT_ENV = "NEUTRINOS_STATE_ARTIFACT_DIR"
SESSION_ARTIFACT_ENV = "NEUTRINOS_SESSION_ARTIFACT_DIR"
# The declared build outputs a check may be pointed at, keyed by the name the
# operator types. One mapping, used by three things that must agree: the
# `--artifact` invocation option, the environment handed to the child process
# that runs a check, and the evidence record. They disagreed once already.
#
# These are declarations, not discoveries. Nothing here searches for an
# artifact: composition writes outputs too large for the checkout, and which
# one a check is pointed at is the operator's statement, recorded as such.
ARTIFACT_DECLARATIONS = {
    "slice": SLICE_ARTIFACT_ENV,
    "state": STATE_ARTIFACT_ENV,
    "session": SESSION_ARTIFACT_ENV,
    "repository": SLICE_REPOSITORY_ENV,
    "confext": CONFEXT_FIXTURE_ENV,
}
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
        # Optional. Its absence blocks the tests that declare it rather than
        # failing preflight, so a checkout with no composed artifact still runs
        # every test that does not need one.
        SLICE_ARTIFACT_ENV,
        # Optional on the same terms: the retained repository subset that
        # composition writes, against which the shipped closure is attributed.
        SLICE_REPOSITORY_ENV,
        # Optional on the same terms: the enrolled artifact and the pair of
        # confexts T4-CONFEXT-001 compares signers with.
        CONFEXT_FIXTURE_ENV,
        # Optional on the same terms: the state variant, which is a separate
        # artifact from the six PLN-0002-06 members and must never be pointed at
        # them -- it carries partitions they do not have.
        STATE_ARTIFACT_ENV,
        # Optional on the same terms: the session variant, which is the state
        # variant plus the role's session-stage packages and units.
        SESSION_ARTIFACT_ENV,
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
    # Registered and not run. The contract admits `deferred` "only when already
    # justified in the governing requirements-to-test trace", so this text is
    # the declaration: it names that trace and is what the manifest reports as
    # the reason. Enforced by selection rather than by the test body, so a
    # deferred test can never produce a passing result.
    deferred: str | None = None


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
        id="T0-DOC-003",
        level="T0",
        profiles=("fast", "complete"),
        timeout_seconds=60,
        traces=("P-010/RES-0016",),
        capabilities=(),
        fixtures=("repository Markdown files",),
        cleanup_owner="validation runner",
        function="check_derived_indexes",
    ),
    Test(
        id="T0-DOC-004",
        level="T0",
        profiles=("fast", "complete"),
        timeout_seconds=60,
        traces=("P-010/RES-0016",),
        capabilities=(),
        fixtures=("repository Markdown files",),
        cleanup_owner="validation runner",
        function="check_bounded_and_frozen_documents",
    ),
    Test(
        id="T0-HYG-001",
        level="T0",
        profiles=("fast", "complete"),
        timeout_seconds=60,
        traces=("PLN-0000/PRE-016",),
        capabilities=(),
        fixtures=("repository index",),
        cleanup_owner="validation runner",
        function="check_tracked_artifacts",
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
        id="T2-SLICE-001",
        level="T2",
        profiles=("fast", "complete"),
        timeout_seconds=60,
        traces=("PLN-0001/PLN-0001-05", "SYS-057", "SYS-058", "SYS-016"),
        capabilities=(),
        fixtures=(
            "src/slice/input-set.toml",
            # By declared version, not by file name. This read v2 while the
            # declaration had said 3 since v3 landed, and the check itself
            # resolves the path from the version, so the label named a schema
            # the check had stopped reading.
            "src/slice/schema/input-set-v<declared version>.schema.json",
            "constructed schema violations",
        ),
        cleanup_owner="validation runner",
        function="check_slice_input_set",
    ),
    Test(
        id="T2-ROLE-001",
        level="T2",
        profiles=("fast", "complete"),
        timeout_seconds=60,
        traces=("CH-003", "CH-006", "ADR-0003"),
        capabilities=(),
        fixtures=(
            "src/roles/*/capabilities.toml",
            "src/roles/*/schema/capabilities-v1.schema.json",
            "constructed schema violations",
        ),
        cleanup_owner="validation runner",
        function="check_role_capabilities",
    ),
    Test(
        id="T2-STATE-001",
        level="T2",
        profiles=("fast", "complete"),
        timeout_seconds=60,
        traces=("ADR-0005", "C-009"),
        capabilities=(),
        fixtures=(
            "tools/validation/slice_boot.py",
            "src/slice/composition/state-partitions/",
        ),
        cleanup_owner="validation runner",
        function="check_state_volumes",
    ),
    Test(
        id="T4-SESSION-001",
        level="T4",
        profiles=("complete",),
        timeout_seconds=600,
        traces=("CH-003", "CH-006", "ADR-0001"),
        capabilities=("declared session artifact", "user-owned disposable VM"),
        fixtures=(
            "composed session-variant disk image",
            "src/roles/workstation/capabilities.toml",
        ),
        cleanup_owner="validation runner",
        function="check_session_boot",
    ),
    Test(
        id="T4-STATE-001",
        level="T4",
        profiles=("complete",),
        timeout_seconds=300,
        traces=("ADR-0005", "CH-003"),
        capabilities=("declared state artifact", "user-owned disposable VM"),
        fixtures=(
            "composed state-variant disk image",
            "src/slice/composition/mkosi.extra.state/",
        ),
        cleanup_owner="validation runner",
        function="check_state_boot",
    ),
    Test(
        id="T2-SLICE-002",
        level="T2",
        profiles=("fast", "complete"),
        timeout_seconds=60,
        traces=("PLN-0001/PLN-0001-06", "SYS-059", "SYS-057", "SYS-018"),
        capabilities=(),
        fixtures=(
            "src/slice/composition/mkosi.conf",
            "src/slice/compose.sh",
            "src/slice/input-set.toml",
            # Read too, because the values compose.sh used to restate now live
            # in the helpers that resolve them, and the check asserts they are
            # resolved rather than recopied.
            "src/slice/declaration.py",
            "src/slice/buildroot.py",
            "src/slice/retain_repository.py",
        ),
        cleanup_owner="validation runner",
        function="check_slice_composition",
    ),
    Test(
        id="T3-SLICE-002",
        level="T3",
        profiles=("complete",),
        timeout_seconds=300,
        traces=("PLN-0001/PLN-0001-06", "SYS-059", "SYS-058", "SYS-041"),
        capabilities=(
            "declared slice artifact",
            "retained declared repository",
            "zstd reader",
        ),
        fixtures=(
            "composed package manifest",
            "retained repository metadata",
            "src/slice/input-set.toml",
        ),
        cleanup_owner="validation runner",
        function="check_slice_repository_attribution",
    ),
    Test(
        id="T3-SLICE-001",
        level="T3",
        profiles=("complete",),
        timeout_seconds=300,
        traces=("PLN-0001/PLN-0001-05", "SYS-002", "SYS-008", "SYS-045", "SYS-058"),
        capabilities=("declared slice artifact", "FAT reader"),
        fixtures=(
            "composed disk image, UKI, and manifest",
            "src/slice/input-set.toml",
        ),
        cleanup_owner="validation runner",
        function="check_slice_artifact",
    ),
    Test(
        id="T3-SLICE-003",
        level="T3",
        profiles=("complete",),
        timeout_seconds=300,
        # PLN-0002-05 because the verity signer's subject is a declared
        # parameter of that task, and amendment 4 is what this protects.
        traces=("PLN-0002/PLN-0002-05", "SYS-002", "SYS-045"),
        capabilities=("declared slice artifact",),
        fixtures=(
            "composed disk image",
            "verity certificate published beside the artifact",
        ),
        cleanup_owner="validation runner",
        function="check_slice_signing_material",
    ),
    Test(
        id="T3-SLICE-004",
        level="T3",
        profiles=("complete",),
        timeout_seconds=300,
        # SYS-049 for the half of it this can reach offline: an exact identity
        # carried by the selected boot artifact. The read-only half is
        # T4-SLICE-002's, and neither claims SYS-049 satisfied.
        traces=("PLN-0002/PLN-0002-11", "SYS-049", "SYS-002", "SYS-045"),
        capabilities=("declared slice artifact", "openssl"),
        fixtures=(
            "composed disk image and UKI",
            "verity certificate published beside the artifact",
        ),
        cleanup_owner="validation runner",
        function="check_slice_usr_verity_binding",
    ),
    Test(
        id="T4-SLICE-001",
        level="T4",
        profiles=("complete",),
        # The contract's T4 default is 15 minutes. A TCG boot of this artifact
        # takes about half a minute of guest time and several minutes of wall
        # clock; KVM, once available, makes the budget generous rather than
        # tight.
        timeout_seconds=900,
        traces=("PLN-0001/PLN-0001-05", "SYS-002", "SYS-008", "SYS-017", "SYS-012"),
        capabilities=("declared slice artifact", "user-owned disposable VM"),
        fixtures=(
            "composed disk image",
            "software TPM",
            "disposable firmware variable store",
            "synthetic first-boot credentials",
        ),
        cleanup_owner="validation runner",
        function="check_slice_boot",
    ),
    Test(
        id="T4-SLICE-002",
        level="T4",
        # One boot, and the probe powers the guest off rather than waiting for
        # a login prompt. Sized for TCG like its neighbours.
        timeout_seconds=900,
        profiles=("complete",),
        # SYS-049's read-only half. T3-SLICE-004 covers the identity half;
        # neither claims the requirement satisfied, which stays Partial.
        traces=("PLN-0002/PLN-0002-11", "SYS-049", "SYS-002", "SYS-017"),
        capabilities=("declared slice artifact", "user-owned disposable VM"),
        fixtures=(
            "composed disk image",
            "disposable firmware variable store",
            "harness-supplied probe unit",
        ),
        cleanup_owner="validation runner",
        function="check_slice_runtime_boundaries",
    ),
    # Both deferred, for one reason: PLN-0002-10 measured that the `/usr` verity
    # signature is verified and gates nothing, and the measurement lives in
    # `src/slice/measure-substitution.py`, which is not registered. Without
    # these the fail-open becomes invisible when PLN-0002 closes.
    #
    # They register what SYS-049 requires, not the observed behaviour, which
    # would pass because the mechanism is broken and go red when it is fixed.
    # That is why they are deferred rather than failing.
    Test(
        id="T4-SLICE-003",
        level="T4",
        timeout_seconds=1800,
        profiles=("complete",),
        traces=("PLN-0002/PLN-0002-10", "SYS-049", "SYS-002"),
        capabilities=(
            "declared slice artifact",
            "user-owned disposable VM",
            "Secure Boot firmware",
        ),
        fixtures=(
            "composed disk image",
            "donor artifact of the same format",
            "enrolled verity signer in db",
        ),
        cleanup_owner="validation runner",
        function="check_slice_signature_root_hash_binding",
        deferred=(
            "SYS-049 is accepted Partial with the unenforced /usr verity "
            "signature recorded as an open sub-question under S-005, and "
            "PLN-0002-10's sig-foreign cell measured the gap: a signature by "
            "the enrolled signer over a root hash this image does not carry "
            "boots to running with zero failed units, on both arms and under "
            "both firmware states. Deferred until the mechanism that would "
            "make this refusable is decided under S-005; the assertion is not "
            "implemented, so lifting the deferral fails the profile until the "
            "task that closes S-005 writes it."
        ),
    ),
    Test(
        id="T4-SLICE-004",
        level="T4",
        timeout_seconds=1800,
        profiles=("complete",),
        traces=("PLN-0002/PLN-0002-10", "SYS-049", "SYS-002"),
        capabilities=(
            "declared slice artifact",
            "user-owned disposable VM",
            "Secure Boot firmware",
        ),
        fixtures=(
            "composed disk image",
            "signature by an unenrolled authority",
            "enrolled verity signer in db",
        ),
        cleanup_owner="validation runner",
        function="check_slice_signature_authority",
        deferred=(
            "The same S-005 sub-question, in its authority dimension. "
            "PLN-0002-10's sig-wrong-key cell measured a valid signature by an "
            "authority the firmware does not trust booting to running with "
            "zero failed units, under firmware whose db carries the verity "
            "signer. Registered separately from T4-SLICE-003 because it is a "
            "distinct substitution with a distinct diagnostic, and a single "
            "check would hide whichever half was fixed first. Not implemented, "
            "on the same terms."
        ),
    ),
    Test(
        id="T4-CONFEXT-001",
        level="T4",
        # Five boots, four of them measured. Each is well under a minute with
        # KVM and a few minutes under TCG, and the budget is sized for TCG.
        timeout_seconds=1800,
        profiles=("complete",),
        traces=("PLN-0002/PLN-0002-10", "SYS-123", "SYS-002", "SYS-012"),
        capabilities=(
            "user-owned disposable VM",
            "Secure Boot firmware",
            "confext signature fixture",
        ),
        fixtures=(
            "artifact copy with the verity signer enrolled in UEFI db",
            "confext signed by the enrolled key",
            "confext signed by a valid but unenrolled key",
            "disposable firmware variable store",
        ),
        cleanup_owner="validation runner",
        function="check_confext_signature_policy",
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


def git(
    *args: str, check: bool = True, input: str | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *args),
        cwd=ROOT,
        env=git_environment(),
        check=check,
        input=input,
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
    """Identify both Git state and all worktree bytes, including ignored files.

    Ignored files are hashed on purpose -- a check writing an image, a key or a
    run directory into the checkout is what this catches, and all of those are
    in `.gitignore`. The exclusion below is deliberately not "whatever Git
    ignores".

    Bytecode is the exception: the interpreter derives it from source already
    hashed here, and writing it is a side effect of running the checks. Hashing
    it made the first `check:complete` after any edit under `tools/validation/`
    report "validation changed repository state" against the tree the runner had
    just compiled. Measured 2026-08-12, twice, misattributed once.
    """
    git_parts = []
    for args in (
        ("status", "--porcelain=v2", "--branch", "--untracked-files=all", "--ignored=matching"),
        ("diff", "--no-ext-diff", "--binary"),
        ("diff", "--no-ext-diff", "--binary", "--cached"),
    ):
        result = git(*args)
        # Same exclusion as the tree walk, for the same reason. `--ignored`
        # lists the `__pycache__` directory, so on a checkout that has never
        # been run this half would flip when the first run creates it.
        git_parts.append(
            "\n".join(
                line for line in result.stdout.splitlines()
                if "__pycache__" not in line
            )
        )

    tree = hashlib.sha256()
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if relative.parts and relative.parts[0] == ".git":
            continue
        if "__pycache__" in relative.parts or path.suffix in (".pyc", ".pyo"):
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


def _frontmatter_field(document: Path, field: str) -> str | None:
    """Read one top-level frontmatter scalar, without a YAML dependency.

    Only the leading `---` block is scanned, so a matching line in the body
    cannot masquerade as metadata.
    """
    lines = document.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            return None
        name, separator, value = line.partition(":")
        if separator and name.strip() == field:
            return value.strip()
    return None


def check_derived_indexes() -> int:
    """Hold hand-maintained indexes to the files they claim to describe.

    An index is a derived view, and `P-010` records that derived views in this
    corpus rot: the work register went stale in two days while every fact in it
    existed correctly elsewhere. RES-0016 recommends exactly one first step
    against that failure class, a validator, because it costs no dependencies
    and fits the `check:fast` contract. This is that step, scoped to the two
    indexes that carry conclusions rather than prose.

    Status is checked as well as presence, because a row that lists a decision
    as proposed after it was accepted is the duplicated-state failure rather
    than the referential one, and both were observed on the same day.
    """
    failures: list[str] = []

    adr_dir = ROOT / "docs" / "adrs"
    adr_index = (adr_dir / "README.md").read_text(encoding="utf-8")
    # `| [ADR-0004](0004-....md) | **Proposed** | ...`
    rows = dict(
        re.findall(
            r"^\|\s*\[ADR-\d+\]\(([^)]+)\)\s*\|\s*([^|]+?)\s*\|",
            adr_index,
            re.MULTILINE,
        )
    )
    for record in sorted(adr_dir.glob("[0-9]*.md")):
        name = record.name
        if name not in rows:
            failures.append(f"ADR not in docs/adrs/README.md index: {name}")
            continue
        declared = _frontmatter_field(record, "status")
        listed = rows[name].replace("*", "").strip().lower()
        # The index may qualify a status ("Accepted; amended 2026-08-11"); the
        # frontmatter word must lead it.
        if declared and not listed.startswith(declared.lower()):
            failures.append(
                f"ADR status disagrees with the index: {name} "
                f"frontmatter={declared!r} index={rows[name].strip()!r}"
            )

    comparisons = ROOT / "docs" / "research" / "comparisons"
    comparison_index = (comparisons / "README.md").read_text(encoding="utf-8")
    linked = set(re.findall(r"\]\(([^)#]+)\)", comparison_index))
    for study in sorted(comparisons.glob("*.md")):
        if study.name == "README.md":
            continue
        if study.name not in linked:
            failures.append(
                f"comparison not in docs/research/comparisons/README.md: {study.name}"
            )

    if failures:
        print("\n".join(failures))
        return 1
    return 0


# Documents whose job is to route a reader somewhere. A historical record may
# describe a frozen document; an index must not send anyone to one.
LIVE_ROUTING_DOCUMENTS = (
    "AGENTS.md",
    "docs/README.md",
    "docs/project/*.md",
    "docs/adrs/*.md",
    "docs/research/comparisons/README.md",
)


def check_bounded_and_frozen_documents() -> int:
    """Enforce two rules the corpus states about itself and never checked.

    The word bound is read from the document rather than hardcoded, so the
    check and the rule cannot disagree: whatever `current-context.md` declares
    is what it is held to. It grew to 5,350 words under a maintenance note
    telling it to stay a summary, which is what an unenforced rule is worth.

    The frozen rule is general. Any document whose frontmatter says
    `status: frozen` must not be linked from a document whose job is routing,
    because a frozen file is not maintained and a reader sent there is being
    sent to decay. Historical records may still cite it; that is what they are
    for.
    """
    failures: list[str] = []

    context = ROOT / "docs" / "project" / "current-context.md"
    text = context.read_text(encoding="utf-8")
    declared = re.search(r"under ([\d,]+) words", text)
    if declared is None:
        failures.append(
            "docs/project/current-context.md no longer declares a word bound; "
            "the bound is the document's own and must stay stated in it"
        )
    else:
        cap = int(declared.group(1).replace(",", ""))
        actual = len(text.split())
        if actual > cap:
            failures.append(
                f"docs/project/current-context.md is {actual} words against its "
                f"declared bound of {cap}; move detail to the owning record"
            )

    frozen = {
        document.resolve()
        for document in ROOT.rglob("*.md")
        if ".git" not in document.relative_to(ROOT).parts
        and _frontmatter_field(document, "status") == "frozen"
    }
    if frozen:
        routing: list[Path] = []
        for pattern in LIVE_ROUTING_DOCUMENTS:
            routing.extend(sorted(ROOT.glob(pattern)))
        for document in routing:
            if document.resolve() in frozen:
                continue
            for raw in re.findall(
                r"\]\(([^)#]+)", document.read_text(encoding="utf-8")
            ):
                if re.match(r"^(?:https?|mailto):", raw):
                    continue
                target = (document.parent / raw).resolve()
                if target in frozen:
                    failures.append(
                        f"{document.relative_to(ROOT)} links to frozen "
                        f"{target.relative_to(ROOT)}; cite it only from a "
                        f"historical record"
                    )

    if failures:
        print("\n".join(failures))
        return 1
    return 0


def check_tracked_artifacts() -> int:
    """Enforce the hygiene contract's two artifact bounds.

    Both bounds were reviewer-applied policy with no check -- PR-0026's accepted
    limitation C-002 -- and a tracked bytecode cache then survived twenty-six
    commits and a gate review before anyone noticed.

    The index is the subject, not `HEAD`: the bounds are about what a commit
    would contain, and `HEAD` reports the breach only after it landed.

    Binary classification is Git's own. `--numstat` prints `-` for both counts
    exactly when Git considers a blob binary, so this honors `.gitattributes`
    and the NUL heuristic instead of re-deciding what "binary" means.
    """
    failures: list[str] = []

    # Each -z record is one NUL-terminated `added TAB deleted TAB path`. Only
    # renames split the path into further fields, and a diff against the empty
    # tree is all additions, so there are none.
    numstat = git("diff", "--numstat", "-z", "--cached", EMPTY_TREE_OBJECT)
    for record in numstat.stdout.split("\0"):
        if not record:
            continue
        added, deleted, path = record.split("\t", 2)
        if added == "-" and deleted == "-":
            failures.append(f"tracked binary artifact: {path}")

    listing = git("ls-files", "--cached", "--stage", "-z")
    blobs: dict[str, str] = {}
    for record in listing.stdout.split("\0"):
        if not record:
            continue
        metadata, path = record.split("\t", 1)
        blobs[path] = metadata.split()[1]

    sizes = git(
        "cat-file",
        "--batch-check=%(objectsize)",
        input="".join(f"{sha}\n" for sha in blobs.values()),
    )
    measured = sizes.stdout.split()
    for (path, _), size in zip(blobs.items(), measured, strict=True):
        if int(size) > MAXIMUM_TRACKED_BYTES:
            failures.append(f"tracked file exceeds {MAXIMUM_TRACKED_BYTES} bytes: {path} is {size}")

    if failures:
        print("\n".join(sorted(failures)))
        return 1
    print(f"tracked blobs checked: {len(blobs)}")
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
            # Declared executables only; see declared_path_directory.
            "PATH": str(declared_path_directory(root, (mise,))),
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


def declared_path_directory(root: Path, executables: Sequence[str]) -> Path:
    """Build a PATH directory containing only the named executables.

    A probe that admits a system directory admits everything in it, so an
    undeclared dependency resolves and the probe passes for a reason it never
    stated. Linking each declared executable into a directory of its own makes
    the declaration exact: anything not named here fails to resolve rather than
    being satisfied by whatever the host happens to install.
    """
    directory = root / "declared-bin"
    directory.mkdir(mode=0o700)
    for executable in executables:
        (directory / Path(executable).name).symlink_to(executable)
    return directory


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
            # PATH is a directory of symlinks to exactly the executables this
            # probe declares, not a list of system directories. Directory
            # granularity cannot express the constraint: on a workstation git
            # and mise usually live in /usr/bin, so admitting their directory
            # admits every other binary beside them, and a check that resolves
            # an undeclared executable then passes locally and fails wherever
            # the host is arranged differently. That is what happened to this
            # check. Here an undeclared executable does not resolve anywhere.
            "PATH": str(declared_path_directory(root, (git, mise))),
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


def check_slice_input_set() -> int:
    # Imported here rather than at module scope: the runner's own preflight,
    # selection, and listing paths must not depend on a third-party package.
    # The child executes this file as a script, so the repository root is not
    # on the import path until it is put there.
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.validation.slice_inputs import check_input_set

    return check_input_set()


def check_role_capabilities() -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.validation.role_capabilities import check_role_capabilities as run

    return run()


def check_session_boot() -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.validation.session_boot import check_session_boot as run

    return run()


def check_state_boot() -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.validation.state_boot import check_state_boot as run

    return run()


def check_state_volumes() -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.validation.state_volumes import check_state_volumes as run

    return run()


def check_slice_composition() -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.validation.slice_composition import check_composition_fixture

    return check_composition_fixture()


def check_slice_repository_attribution() -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.validation.slice_composition import check_repository_attribution

    return check_repository_attribution()


def check_slice_artifact() -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.validation.slice_artifact import check_artifact

    return check_artifact()


def check_slice_signing_material() -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.validation.slice_artifact import check_signing_material_current

    return check_signing_material_current()


def check_slice_usr_verity_binding() -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.validation.slice_artifact import check_usr_verity_binding

    return check_usr_verity_binding()


def check_slice_boot() -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.validation.slice_boot import check_boot

    return check_boot()


def check_slice_runtime_boundaries() -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.validation.slice_runtime import check_runtime_boundaries

    return check_runtime_boundaries()


def check_slice_signature_root_hash_binding() -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.validation.slice_signature import check_signature_root_hash_binding

    return check_signature_root_hash_binding()


def check_slice_signature_authority() -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.validation.slice_signature import check_signature_authority

    return check_signature_authority()


def check_confext_signature_policy() -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.validation.confext_policy import check_confext_signature_policy as run

    return run()


CHECKS: dict[str, Callable[[], int]] = {
    "check_role_capabilities": check_role_capabilities,
    "check_slice_input_set": check_slice_input_set,
    "check_session_boot": check_session_boot,
    "check_state_boot": check_state_boot,
    "check_state_volumes": check_state_volumes,
    "check_slice_composition": check_slice_composition,
    "check_slice_repository_attribution": check_slice_repository_attribution,
    "check_slice_artifact": check_slice_artifact,
    "check_slice_signing_material": check_slice_signing_material,
    "check_slice_usr_verity_binding": check_slice_usr_verity_binding,
    "check_slice_boot": check_slice_boot,
    "check_slice_runtime_boundaries": check_slice_runtime_boundaries,
    "check_slice_signature_root_hash_binding": check_slice_signature_root_hash_binding,
    "check_slice_signature_authority": check_slice_signature_authority,
    "check_confext_signature_policy": check_confext_signature_policy,
    "check_git_diff": check_git_diff,
    "check_markdown_links": check_markdown_links,
    "check_derived_indexes": check_derived_indexes,
    "check_bounded_and_frozen_documents": check_bounded_and_frozen_documents,
    "check_tracked_artifacts": check_tracked_artifacts,
    "check_runner_hostile_probes": check_runner_hostile_probes,
    "check_empty_mise_cache": check_empty_mise_cache,
    "check_clean_clone": check_clean_clone,
    "check_secret_scan": check_secret_scan,
}

# A test names its function as a string, so the registry and this table are two
# places one check must appear. Registering in only the first produced a
# `KeyError` at dispatch time, reported as `failing` after the profile had
# already started -- and a direct call to the function passed, because it
# bypassed this table. Bind them at import instead, so the omission cannot reach
# a run at all.
_undispatchable = sorted({test.function for test in TESTS} - set(CHECKS))
if _undispatchable:
    raise AssertionError(
        f"registered test function(s) missing from CHECKS: {', '.join(_undispatchable)}"
    )


SLICE_ARTIFACT_MEMBERS = (
    "neutrinos-slice.raw",
    "neutrinos-slice.efi",
    "neutrinos-slice.manifest",
)
OVMF_CODE_CANDIDATES = (
    "/usr/share/edk2/x64/OVMF_CODE.4m.fd",
    "/usr/share/edk2/ovmf/OVMF_CODE.fd",
    "/usr/share/OVMF/OVMF_CODE.fd",
    "/usr/share/edk2-ovmf/x64/OVMF_CODE.fd",
)


def capability_slice_artifact(
    environment: Mapping[str, str] = os.environ,
) -> str | None:
    """A composed slice artifact, declared outside the checkout.

    Composition needs the network and a package repository, so it is not part
    of offline canonical validation. The artifact is therefore an input the
    operator declares, exactly as the locked tool installations are, and its
    absence blocks the tests that inspect or boot it.
    """
    if not environment.get(SLICE_ARTIFACT_ENV):
        return f"{SLICE_ARTIFACT_ENV} is not set"
    try:
        directory = declared_directory(SLICE_ARTIFACT_ENV, environment)
    except ValueError as error:
        return str(error)
    missing = [name for name in SLICE_ARTIFACT_MEMBERS if not (directory / name).is_file()]
    if missing:
        return f"declared slice artifact is missing {', '.join(missing)}"
    return None


def capability_state_artifact(
    environment: Mapping[str, str] = os.environ,
) -> str | None:
    """A composed state-variant artifact, declared outside the checkout.

    Separate from the slice artifact capability rather than sharing it: they are
    different disks. The state variant carries /var and /home partitions the six
    PLN-0002-06 members do not, so a check pointed at a member would fail for
    the right reason but the wrong cause, reading as a defect in the mount units
    rather than as a misdeclared fixture.
    """
    if not environment.get(STATE_ARTIFACT_ENV):
        return f"{STATE_ARTIFACT_ENV} is not set"
    try:
        directory = declared_directory(STATE_ARTIFACT_ENV, environment)
    except ValueError as error:
        return str(error)
    if not (directory / "neutrinos-slice.raw").is_file():
        return "declared state artifact is missing neutrinos-slice.raw"
    return None


def capability_session_artifact(
    environment: Mapping[str, str] = os.environ,
) -> str | None:
    """A composed session-variant artifact, declared outside the checkout.

    Distinct from the state artifact for the same reason that one is distinct
    from the slice artifact: they are different disks, and a check pointed at
    the wrong one fails for the right reason with the wrong cause.
    """
    if not environment.get(SESSION_ARTIFACT_ENV):
        return f"{SESSION_ARTIFACT_ENV} is not set"
    try:
        directory = declared_directory(SESSION_ARTIFACT_ENV, environment)
    except ValueError as error:
        return str(error)
    if not (directory / "neutrinos-slice.raw").is_file():
        return "declared session artifact is missing neutrinos-slice.raw"
    return None


def capability_retained_repository(
    environment: Mapping[str, str] = os.environ,
) -> str | None:
    """The retained subset of the declared repository, produced by composition.

    `compose.sh` writes this; it is declared to validation the same way the
    artifact is, because it is the same kind of thing -- a build output too
    large to live in the checkout. Attribution has nothing to check against
    without it, so its absence blocks rather than skips.
    """
    if not environment.get(SLICE_REPOSITORY_ENV):
        return f"{SLICE_REPOSITORY_ENV} is not set"
    try:
        directory = declared_directory(SLICE_REPOSITORY_ENV, environment)
    except ValueError as error:
        return str(error)
    if not (directory / "repodata" / "repomd.xml").is_file():
        return "retained repository has no repodata/repomd.xml"
    return None


def capability_zstd_reader() -> str | None:
    """Decompression for the declared repository's published primary index.

    Fedora publishes it zstd-compressed. Python's standard library has no zstd
    before 3.14's `compression.zstd`, and adding a third-party dependency to
    read one file would widen the repository's only runtime dependency for the
    sake of a decompressor the host already has.
    """
    if shutil.which("zstd") is None:
        return "zstd unavailable on PATH"
    return None


def capability_virtualization() -> str | None:
    """A user-owned disposable VM, with no host-global mutation.

    `/dev/kvm` is deliberately not required: the contract permits user-owned
    KVM when a test declares it, and TCG is slower but produces the same
    evidence. What is required is a VMM, a software TPM, and firmware the
    harness can copy, because a test that silently used host firmware
    variables would violate the execution boundary rather than fail.
    """
    missing = [name for name in ("qemu-system-x86_64", "swtpm") if shutil.which(name) is None]
    if missing:
        return f"executables unavailable on PATH: {', '.join(missing)}"
    if not any(Path(candidate).is_file() for candidate in OVMF_CODE_CANDIDATES):
        return "no OVMF firmware found at any known path"
    return None


def capability_openssl() -> str | None:
    """CMS verification and DER conversion for the verity signature.

    Declared rather than assumed. Python's standard library cannot verify a
    detached CMS signature, and the alternative is a cryptography dependency
    where the host already ships the tool that produced the signature.
    """
    if shutil.which("openssl") is None:
        return "openssl unavailable on PATH"
    return None


def capability_fat_reader() -> str | None:
    """Unprivileged read access to the ESP inside the image.

    mtools reads a FAT filesystem at a byte offset in a plain file, so the
    image is never attached to a loop device or mounted. Mounting would need
    privilege the execution boundary refuses and would mutate host state.
    """
    missing = [name for name in ("mdir", "mtype") if shutil.which(name) is None]
    if missing:
        return f"mtools unavailable on PATH: {', '.join(missing)}"
    return None


def capability_confext_fixture(
    environment: Mapping[str, str] = os.environ,
) -> str | None:
    """The enrolled artifact and the two confexts, produced by composition.

    Built by `src/slice/enroll-fixture.sh` and declared to validation the same
    way the artifact is. Absence blocks rather than skips: a signature check
    with nothing to compare signers against would report the same shape as a
    passing run.
    """
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.validation.confext_policy import FIXTURE_MEMBERS

    if not environment.get(CONFEXT_FIXTURE_ENV):
        return f"{CONFEXT_FIXTURE_ENV} is not set"
    try:
        directory = declared_directory(CONFEXT_FIXTURE_ENV, environment)
    except ValueError as error:
        return str(error)
    missing = [name for name in FIXTURE_MEMBERS if not (directory / name).is_file()]
    if missing:
        return f"confext fixture is missing {', '.join(missing)}"
    return None


def capability_secure_boot_firmware() -> str | None:
    """Firmware compiled *with* Secure Boot support, which is not the default.

    `OVMF_CODE.4m.fd` and `OVMF_CODE.fd` are built without it. A guest boots
    fine on them and simply has no SetupMode, no SecureBoot, no db and an empty
    platform keyring -- so a signature test runs green against a mechanism that
    is absent rather than working. The PLN-0002-01 spike did exactly that for
    its whole duration. This blocks rather than skips for the same reason.
    """
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.validation.vm import SECBOOT_CODE_CANDIDATES

    if not any(Path(candidate).is_file() for candidate in SECBOOT_CODE_CANDIDATES):
        return "no Secure Boot OVMF build found at any known path"
    return None


# Capabilities with no probe are established by preflight, which fails the
# whole run when they are absent. Only capabilities that may legitimately be
# missing from an otherwise valid checkout are probed here.
CAPABILITY_PROBES: dict[str, Callable[[], str | None]] = {
    "declared slice artifact": capability_slice_artifact,
    "declared session artifact": capability_session_artifact,
    "declared state artifact": capability_state_artifact,
    "retained declared repository": capability_retained_repository,
    "zstd reader": capability_zstd_reader,
    "user-owned disposable VM": capability_virtualization,
    "FAT reader": capability_fat_reader,
    "openssl": capability_openssl,
    "confext signature fixture": capability_confext_fixture,
    "Secure Boot firmware": capability_secure_boot_firmware,
}


def blocking_reason(test: Test) -> str | None:
    for capability in test.capabilities:
        probe = CAPABILITY_PROBES.get(capability)
        if probe is None:
            continue
        reason = probe()
        if reason is not None:
            return f"{capability}: {reason}"
    return None


def blocked_result(test: Test, reason: str) -> dict[str, Any]:
    """A declared capability was absent, so the test did not run.

    Per the validation execution contract this is `blocked` rather than
    `skipped`, and it fails the profile. A profile that reported green while
    silently omitting its VM evidence would be worse than one that fails.
    """
    now = utc_now()
    return {
        "assertions": [],
        "cleanup": {"process_group_absent": True},
        "diagnostics": {},
        "detail": reason,
        "duration_seconds": 0.0,
        "ended_at": now,
        "id": test.id,
        "level": test.level,
        "output_bytes": 0,
        "result": "blocked",
        "started_at": now,
        "subjects": list(test.fixtures),
        "traces": list(test.traces),
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
    # Every declared artifact, not a hand-kept subset. The state and session
    # variants were missing here while being present in
    # ALLOWED_RUNNER_ENVIRONMENT and in their capability functions, so the
    # capability evaluated in this process saw the declaration and the child
    # that actually runs the check did not: T4-STATE-001 and T4-SESSION-001
    # would raise KeyError inside the child rather than run. Driving both from
    # one mapping is what stops the two lists from disagreeing again.
    for declared in ARTIFACT_DECLARATIONS.values():
        if declared in os.environ:
            environment[declared] = os.environ[declared]
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
        # Contract: "complete" never silently includes a deferred test. The
        # exclusion is here rather than in the test body so that a deferred
        # test cannot produce a result of any kind, passing least of all.
        return profile, [
            test
            for test in TESTS
            if profile in test.profiles and test.deferred is None
        ]
    unknown = sorted(set(values) - TEST_BY_ID.keys())
    if unknown:
        safe = [value for value in unknown if re.fullmatch(r"[A-Z][A-Z0-9-]{0,63}", value)]
        if len(safe) == len(unknown):
            raise ValueError(f"unknown test ID(s): {', '.join(safe)}")
        raise ValueError(f"invalid test ID syntax ({len(unknown)} value(s))")
    # A deferred ID named explicitly is a selection error, not a quiet run. The
    # ID is registered, so reporting it unknown would be a lie; running it would
    # defeat the deferral.
    deferred = [value for value in values if TEST_BY_ID[value].deferred is not None]
    if deferred:
        raise ValueError(f"deferred test ID(s) cannot be run: {', '.join(deferred)}")
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
                    reason = blocking_reason(test)
                    if reason is not None:
                        result = blocked_result(test, reason)
                    else:
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
    # From the registry rather than from results, since deferred tests never
    # execute: what this profile would have selected had they not been
    # deferred. `check:run` cannot name one, so a selected run reports zero.
    deferred_tests = [
        test
        for test in TESTS
        if test.deferred is not None and profile in test.profiles
    ]
    counts["deferred"] = len(deferred_tests)
    success = (
        runner_error is None
        and len(results) == len(selected)
        and counts["failing"] == 0
        # Contract: a required selected test that cannot run is blocked, and
        # blocked fails the profile.
        and counts["blocked"] == 0
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
        # Contract: every registered test listed as selected, not applicable,
        # deferred, blocked or excluded, with its reason. A deferred test's
        # reason is the justification its registration declares, not a generic
        # string.
        "omissions": [
            {
                "id": test.id,
                "reason": (
                    test.deferred
                    if test.deferred is not None
                    else "not selected by invocation"
                ),
                "state": "deferred" if test.deferred is not None else "excluded",
            }
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
    # STATE is beyond the contract's listed columns and is not optional in
    # practice: a deferred test that listed identically to a running one would
    # read as coverage the profile does not have.
    print("ID\tLEVEL\tPROFILES\tTIMEOUT\tTRACES\tCAPABILITIES\tSTATE")
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
                    "deferred" if test.deferred is not None else "registered",
                )
            )
        )
    return 0


class InvocationArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise ValueError("invalid command-line invocation")


def declare_artifacts(
    declarations: Sequence[str], environment: MutableMapping[str, str]
) -> None:
    """Put `--artifact KIND=DIR` declarations into the environment.

    The runner reads artifact locations from the environment, and `mise` sets
    `sandbox.deny_env`, so a task cannot forward one from the caller's shell.
    Without this option there is no supported way to run an artifact-dependent
    check at all, and every such run was assembled by hand -- which is where the
    guessed variable names and malformed interpreter invocations came from.

    The declaration is rejected rather than merged when the variable is already
    set. A check pointed at two different disks by two different routes is the
    ambiguity these checks exist to prevent, and silently preferring one of them
    would decide it invisibly.
    """
    for declaration in declarations:
        kind, separator, value = declaration.partition("=")
        if not separator or not kind or not value:
            raise ValueError(f"--artifact takes KIND=DIR, not {declaration!r}")
        name = ARTIFACT_DECLARATIONS.get(kind)
        if name is None:
            expected = ", ".join(sorted(ARTIFACT_DECLARATIONS))
            raise ValueError(f"no artifact kind {kind!r}; expected one of {expected}")
        if name in environment:
            raise ValueError(f"{kind} artifact is declared twice")
        environment[name] = value


def parse_args() -> argparse.Namespace:
    parser = InvocationArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    profile = subparsers.add_parser("profile")
    profile.add_argument("name")
    profile.add_argument("--artifact", action="append", default=[], metavar="KIND=DIR")
    exact = subparsers.add_parser("run")
    exact.add_argument("ids", nargs="+")
    exact.add_argument("--artifact", action="append", default=[], metavar="KIND=DIR")
    single = subparsers.add_parser("one")
    single.add_argument("id")
    single.add_argument("--artifact", action="append", default=[], metavar="KIND=DIR")
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
    if arguments.command in {"profile", "run", "one"}:
        try:
            declare_artifacts(arguments.artifact, os.environ)
        except ValueError as error:
            return run("invalid", (), invocation_error=bounded_error(error))
    if arguments.command == "profile":
        return run("profile", (arguments.name,))
    if arguments.command in {"run", "one"}:
        ids = (arguments.id,) if arguments.command == "one" else arguments.ids
        # No separate result handling for `one`: a selected test that cannot run
        # is blocked, and blocked already fails the run. Asking for one test and
        # being told it was skipped must not exit 0.
        return run("run", ids)
    test = TEST_BY_ID[arguments.id]
    # The runner-private path, closed for the same reason selection is: a
    # deferred test must not be reachable by any route that could report it
    # passing.
    if test.deferred is not None:
        print(f"{test.id} is deferred and does not execute", file=sys.stderr)
        return 2
    return CHECKS[test.function]()


if __name__ == "__main__":
    raise SystemExit(main())
