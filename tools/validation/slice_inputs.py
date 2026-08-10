"""T2 conformance check for the PLN-0001 declared input set.

Two assertions, and the second is the one that matters. The committed record
must validate against its declared schema, and the schema must reject every
constructed violation the input declaration claims it rejects. A schema that
has only ever been shown to accept is untested: it could be an empty object
and every acceptance would still pass.

The violations are expressed as mutations of the committed record rather than
as nine separate fixture files. A fixture file is a copy, and a copy drifts:
when the record gains a field, nine stale files keep passing for reasons that
no longer hold. A mutation is stated against the live record, so a change to
the record is a change to what each violation means.
"""

from __future__ import annotations

import copy
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
INPUT_SET = ROOT / "src" / "slice" / "input-set.toml"
SCHEMA_DIR = ROOT / "src" / "slice" / "schema"


def rolling_repository(record: dict[str, Any]) -> None:
    record["packages"]["repositories"][0]["frozen"] = False


def branch_as_source_revision(record: dict[str, Any]) -> None:
    record["source"]["revision"] = "main"


def unknown_top_level_field(record: dict[str, Any]) -> None:
    record["deployment"] = "slice"


def empty_repository_list(record: dict[str, Any]) -> None:
    record["packages"]["repositories"] = []


def git_commit_identity_holding_sha256(record: dict[str, Any]) -> None:
    record["tools"][0]["identity"] = "0" * 64


def undeclared_precedence_layer(record: dict[str, Any]) -> None:
    record["intent"]["layers"].append("site")


def unsupported_schema_version(record: dict[str, Any]) -> None:
    record["schema"]["version"] = 3


def tools_tree_pinned_by_tag(record: dict[str, Any]) -> None:
    record["tools_tree"]["base_image"] = "registry.fedoraproject.org/fedora:44"


def empty_tools_package_list(record: dict[str, Any]) -> None:
    record["tools_tree"]["packages"] = []


VIOLATIONS = (
    ("rolling repository", rolling_repository),
    ("branch name as source revision", branch_as_source_revision),
    ("unknown top-level field", unknown_top_level_field),
    ("empty repository list", empty_repository_list),
    ("git-commit identity holding a SHA-256", git_commit_identity_holding_sha256),
    ("undeclared precedence layer", undeclared_precedence_layer),
    ("unsupported schema version", unsupported_schema_version),
    ("tools tree pinned by tag", tools_tree_pinned_by_tag),
    ("empty tools package list", empty_tools_package_list),
)


def check_input_set() -> int:
    import jsonschema

    record = tomllib.loads(INPUT_SET.read_text(encoding="utf-8"))
    declared = record.get("schema", {})
    version = declared.get("version")
    if declared.get("id") != "neutrinos.slice.input-set" or not isinstance(version, int):
        print("record declares no usable schema identity or version", file=sys.stderr)
        return 1
    schema_path = SCHEMA_DIR / f"input-set-v{version}.schema.json"
    if not schema_path.is_file():
        # The record chooses its own validator by declaring a version, so a
        # version with no committed schema must fail rather than fall back to
        # whichever schema happens to be newest.
        print(f"no committed schema for declared version {version}", file=sys.stderr)
        return 1
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    validator_class = jsonschema.validators.validator_for(schema)
    validator_class.check_schema(schema)
    validator = validator_class(schema)

    failures: list[str] = []
    errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
    if errors:
        failures.extend(
            f"committed record rejected at {list(error.path)}: {error.message}"
            for error in errors
        )

    accepted: list[str] = []
    for label, mutate in VIOLATIONS:
        hostile = copy.deepcopy(record)
        mutate(hostile)
        if validator.is_valid(hostile):
            accepted.append(label)
    if accepted:
        failures.append("schema accepted constructed violations: " + ", ".join(accepted))

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "record": str(INPUT_SET.relative_to(ROOT)),
                "rejected_violations": [label for label, _ in VIOLATIONS],
                "result": "passing",
                "schema": str(schema_path.relative_to(ROOT)),
                "schema_dialect": schema.get("$schema"),
                "schema_version": version,
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0
