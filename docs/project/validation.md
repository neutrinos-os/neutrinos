---
status: informative
last_updated: 2026-08-10
governed_by: PRE-015
---

# Repository validation usage

The accepted behavior is defined by the
[validation execution contract](validation-contract.md). This page records the
current operator interface; it is not a second policy source.

## Bootstrap

Install mise using the independently pinned method for the execution
environment, trust this repository after reviewing `mise.toml`, then run:

```sh
mise install --locked python uv
mise exec -- uv sync --locked --python "$(mise which python)"
```

Naming `python uv` prevents unrelated tools in a developer's global mise
configuration from becoming repository bootstrap inputs. Bootstrap may use the
network and tool caches. The canonical checks may not: they invoke uv with
`--offline --locked --no-sync`, and mise task auto-install is disabled.

## Checks

```sh
mise run check:fast
mise run check:complete
mise run check:list
mise run check:run T0-DOC-001 T0-DOC-002
```

`T0-DOC-001` is the former `git diff --check` validation.
`T0-DOC-002` is the former internal Markdown-link validation. Do not duplicate
their implementations in documentation or CI.

Each execution writes `run.json`, `results.jsonl`, and bounded per-test logs to
the printed temporary run directory outside the checkout. A dirty-checkout
pass is development feedback only.

## Current implementation boundary

The initial Python 3.14 runner implements named registration and selection,
per-test process groups and timeouts, an allowlisted child environment,
machine-readable results, bounded output detection, and before/after identities
covering Git, untracked, and ignored checkout state.

PRE-015 remains active. Hostile probes, stronger network and secret preflight,
interruption and live output-limit enforcement, cleanup-resource accounting,
clean-checkout profile evidence, and the pinned least-privilege CI workflow
remain required before the contract is satisfied.
