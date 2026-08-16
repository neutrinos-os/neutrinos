"""T2 conformance check for role capability declarations.

Same shape and the same reasoning as slice_inputs: a declaration must validate
against the schema it names, and the schema must reject every constructed
violation the declaration relies on it rejecting. A schema shown only to accept
is untested -- it could be an empty object and every acceptance would pass.

Two obligations here are not expressible in JSON Schema and are asserted
directly: the directory a declaration sits in must be the role it names, and
the requirement it serves must exist. Both are the ways a role declaration
silently stops describing anything.

What this does NOT check, deliberately: whether a named package exists in any
declared closure, and whether any predicate is implemented by a qualification
check. Both need artifacts and a booted machine. Asserting them here would
make a structural check look like evidence of a working role.
"""

from __future__ import annotations

import copy
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ROLES_DIR = ROOT / "src" / "roles"


def unknown_top_level_field(record: dict[str, Any]) -> None:
    record["deployment"] = "workstation"


def unknown_capability_field(record: dict[str, Any]) -> None:
    next(iter(record["capability"].values()))["priority"] = "high"


def capability_without_an_assert(record: dict[str, Any]) -> None:
    next(iter(record["capability"].values())).pop("assert")


def capability_without_an_origin(record: dict[str, Any]) -> None:
    next(iter(record["capability"].values())).pop("origin")


def undeclared_stage(record: dict[str, Any]) -> None:
    next(iter(record["capability"].values()))["stage"] = "someday"


def empty_capability_set(record: dict[str, Any]) -> None:
    record["capability"] = {}


def duplicate_package_selection(record: dict[str, Any]) -> None:
    entry = next(
        value for value in record["capability"].values() if value["packages"]
    )
    entry["packages"] = entry["packages"] + [entry["packages"][0]]


def assert_stated_as_a_command(record: dict[str, Any]) -> None:
    # An assert must be an observation, not a shell line. The schema enforces
    # only a minimum length, so this violation is what that bound is for.
    next(iter(record["capability"].values()))["assert"] = "true"


def unsupported_schema_version(record: dict[str, Any]) -> None:
    record["schema"]["version"] = record["schema"]["version"] + 1


def requirement_outside_the_requirement_tree(record: dict[str, Any]) -> None:
    record["role"]["requirement"] = "docs/designs/0006-storage-layout-and-encryption/README.md"


VIOLATIONS = (
    ("unknown top-level field", unknown_top_level_field),
    ("unknown capability field", unknown_capability_field),
    ("capability with no assert", capability_without_an_assert),
    ("capability with no stated origin", capability_without_an_origin),
    ("undeclared stage", undeclared_stage),
    ("empty capability set", empty_capability_set),
    ("duplicate package selection", duplicate_package_selection),
    ("assert stated as a command", assert_stated_as_a_command),
    ("unsupported schema version", unsupported_schema_version),
    ("requirement outside the requirement tree", requirement_outside_the_requirement_tree),
)


def _check_one(path: Path, failures: list[str]) -> dict[str, Any] | None:
    import jsonschema

    role = path.parent.name
    record = tomllib.loads(path.read_text(encoding="utf-8"))

    declared = record.get("schema", {})
    version = declared.get("version")
    if declared.get("id") != "neutrinos.role.capabilities" or not isinstance(
        version, int
    ):
        failures.append(f"{role}: declares no usable schema identity or version")
        return None

    schema_path = path.parent / "schema" / f"capabilities-v{version}.schema.json"
    if not schema_path.is_file():
        # The record chooses its own validator by declaring a version, so a
        # version with no committed schema must fail rather than fall back to
        # whichever schema happens to be newest.
        failures.append(f"{role}: no committed schema for declared version {version}")
        return None
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    validator_class = jsonschema.validators.validator_for(schema)
    validator_class.check_schema(schema)
    validator = validator_class(schema)

    errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
    failures.extend(
        f"{role}: rejected at {list(error.path)}: {error.message}" for error in errors
    )
    if errors:
        return None

    # Not expressible in the schema: the declaration must describe the
    # directory it lives in, and must serve a requirement that exists.
    declared_role = record["role"]["name"]
    if declared_role != role:
        failures.append(
            f"{role}: declaration names role {declared_role!r}, directory says {role!r}"
        )
    requirement = ROOT / record["role"]["requirement"]
    if not requirement.is_file():
        failures.append(
            f"{role}: requirement {record['role']['requirement']} does not exist"
        )

    accepted = [
        label
        for label, mutate in VIOLATIONS
        if _accepts(validator, record, mutate)
    ]
    if accepted:
        failures.append(
            f"{role}: schema accepted constructed violations: " + ", ".join(accepted)
        )

    stages: dict[str, int] = {}
    for entry in record["capability"].values():
        stages[entry["stage"]] = stages.get(entry["stage"], 0) + 1
    return {
        "capabilities": len(record["capability"]),
        "record": str(path.relative_to(ROOT)),
        "role": role,
        "schema": str(schema_path.relative_to(ROOT)),
        "schema_version": version,
        "stages": stages,
    }


def _accepts(validator: Any, record: dict[str, Any], mutate: Any) -> bool:
    hostile = copy.deepcopy(record)
    mutate(hostile)
    return bool(validator.is_valid(hostile))


def check_role_capabilities() -> int:
    if not ROLES_DIR.is_dir():
        print("no src/roles directory", file=sys.stderr)
        return 1

    records = sorted(ROLES_DIR.glob("*/capabilities.toml"))
    if not records:
        # A silent pass over zero declarations is how this check would stop
        # meaning anything after a directory move.
        print("no role capability declarations found under src/roles", file=sys.stderr)
        return 1

    failures: list[str] = []
    reports = [report for path in records if (report := _check_one(path, failures))]

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "rejected_violations": [label for label, _ in VIOLATIONS],
                "result": "passing",
                "roles": reports,
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(check_role_capabilities())
