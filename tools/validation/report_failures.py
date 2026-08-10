"""Print the reason for each non-passing check in a validation run.

Run directories live outside the checkout and are discarded with the CI
runner, so a failing profile otherwise reports only a count. This reads the
run directories a profile left behind and prints each failing check's detail
and captured stderr.

This is a diagnostic reporter, not a check. It defines no result and decides
nothing: the runner has already classified every entry and has already scanned
and quarantined unsafe output by the time these files exist. Adding logic here
that changes what a result means would make the workflow a second definition
of validation behavior, which the execution contract forbids.
"""

from __future__ import annotations

import json
import pathlib
import sys

# Results the runner does not consider a defect. Anything else is reported.
NOT_A_FAILURE = frozenset(
    {"passing", "skipped", "not_applicable", "deferred"}
)


def report(search_root: pathlib.Path) -> int:
    reported = 0
    for results in sorted(search_root.glob("neutrinos-validation-*/results.jsonl")):
        run = results.parent
        for line in results.read_text(encoding="utf-8").splitlines():
            entry = json.loads(line)
            result = entry.get("result")
            if result in NOT_A_FAILURE:
                continue
            reported += 1
            print(f"::group::{entry['id']} ({result}) in {run.name}")
            if entry.get("detail"):
                print(entry["detail"])
            stderr = entry.get("diagnostics", {}).get("stderr")
            if stderr and (run / stderr).is_file():
                print((run / stderr).read_text(encoding="utf-8"), end="")
            print("::endgroup::")
    if not reported:
        print("no non-passing check was recorded in any run directory")
    return 0


if __name__ == "__main__":
    root = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("/tmp")
    raise SystemExit(report(root))
