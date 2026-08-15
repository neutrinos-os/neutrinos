"""SYS-049's signature clauses: registered, deferred, not implemented.

`T4-SLICE-003` and `T4-SLICE-004` are never selected, so neither function is
reached by `check:fast` or `check:complete`. They exist so the registration
names a real callable and so **lifting a deferral cannot produce a green
profile by itself**: remove the `deferred=` declaration and the check runs and
fails, naming the assertion still owed.

The direction is deliberate. This plan's recurring defect is a mechanism that
is configured, runs, reports success and gates nothing -- eight instances. A
deferred registration whose body returned zero would be the ninth and the
worst, sitting in the registry looking like coverage of the one requirement the
artifact does not meet.

What is owed, when S-005 decides the mechanism:

- `T4-SLICE-003` -- a `/usr` verity signature by the enrolled authority over a
  root hash this image does not carry must not reach a running system.
  PLN-0002-10's `sig-foreign` cell is the substitution; the measurement path is
  `src/slice/measure-substitution.py`, and the recorded outcome is `running`
  with zero failed units.
- `T4-SLICE-004` -- a `/usr` verity signature by an authority the firmware does
  not trust must not reach a running system. `sig-wrong-key`, same measurement
  path, same recorded outcome.

Neither is implementable today: there is no mechanism whose refusal could be
asserted, since the kernel refuses a signature it has no key for,
`systemd-veritysetup` retries without it, and enrolling the signer changes the
code path and no outcome. A boot harness written now would be several hundred
lines of never-executed code asserting a refusal nothing performs. These
registrations carry the obligation, not a second copy of the measurement.
"""

from __future__ import annotations

import json
import sys

RECORDS = "docs/project/artifact-substitution-records.md"
MEASUREMENT = "src/slice/measure-substitution.py"


def _not_implemented(check_id: str, clause: str, cell: str) -> int:
    print(
        json.dumps(
            {
                "check": check_id,
                "result": "not implemented",
                "clause": clause,
                "measured_instead": {
                    "cell": cell,
                    "outcome": "boots to running with zero failed units",
                    "record": RECORDS,
                    "harness": MEASUREMENT,
                },
                "reason": (
                    "registered deferred against SYS-049's open sub-question "
                    "under S-005. If this ran, the deferral was lifted without "
                    "the assertion being written."
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )
    print(
        f"{check_id}: deferral lifted but the assertion is not implemented",
        file=sys.stderr,
    )
    return 1


def check_signature_root_hash_binding() -> int:
    return _not_implemented(
        "T4-SLICE-003",
        "a /usr verity signature over a root hash the image does not carry "
        "must not reach a running system",
        "sig-foreign",
    )


def check_signature_authority() -> int:
    return _not_implemented(
        "T4-SLICE-004",
        "a /usr verity signature by an authority the firmware does not trust "
        "must not reach a running system",
        "sig-wrong-key",
    )


if __name__ == "__main__":
    raise SystemExit(check_signature_root_hash_binding())
