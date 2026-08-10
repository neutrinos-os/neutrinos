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
MISE_OFFLINE=0 mise install --locked python uv
mise exec --allow-net pypi.org --allow-net files.pythonhosted.org -- \
  uv sync --locked --python "$(mise which python)"
```

Naming `python uv` prevents unrelated tools in a developer's global mise
configuration from becoming repository bootstrap inputs. `MISE_OFFLINE=0` is
an explicit acquisition-phase exception to the repository default. Bootstrap
may use the network and tool caches. The canonical checks may not: mise itself
is offline, its tasks deny inherited environment and network access, its task
and shim auto-install paths are disabled, each dispatcher resolves both tools
through `mise which`, and uv runs with `--offline --locked --no-sync`.

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

The runner gives registered child tests one unique synthetic canary and scans
each log, result record, declared artifact, and the proposed manifest before
retention. It also recognizes a conservative set of private-key, AWS-key,
GitHub-token, and bearer-token markers. A finding fails the run, moves the raw
file into a private `neutrinos-validation-quarantine-*` directory outside the
run directory, and leaves only a content-free placeholder and finding metadata
in the uploadable result. `run.json` reports the quarantine path locally but
never the canary value or matched content. Symlinks and other non-regular
retained outputs are quarantined rather than followed.

Argument-validation, preflight, and selection failures also write a run
directory and report their failure stage. When no test began, `results.jsonl`
is present and empty. Diagnostics retain rejected environment names but never
their values, and arbitrary malformed argument values are not echoed. The
read-only `check:list` query does not create an execution result.

Pytest metadata persists at
`${XDG_CACHE_HOME:-$HOME/.cache}/neutrinos/validation/pytest`. Canonical
profiles never use `--last-failed`, `--failed-first`, or other cache-dependent
selection. The cache is reconstructible local state, not evidence; it may be
deleted while validation is not running. CI must begin with an empty cache and
must not restore or upload it. Do not redirect it into the checkout or merely
gitignore it: checkout-preservation checks intentionally include ignored state.
The task dispatcher declares the resolved path after mise establishes its
deny-environment sandbox, and the runner rejects an absent, relative, or
in-repository value.

## Current implementation boundary

The Python 3.14 runner implements named registration and selection, exact
runner and child environment allowlists, per-test process groups and timeouts,
live bounded output capture, interruption and descendant cleanup,
machine-readable results, synthetic-canary and conservative credential-marker
scanning, out-of-result quarantine, and before/after identities covering Git,
untracked, and ignored checkout state. Mise blocks inherited environment and
network syscalls around the complete task and prevents acquisition before task
launch. `T5-VAL-001` exercises these failure boundaries with synthetic
processes.

PRE-015 remains active. The empty-cache acquisition probe needs a repeatable
retained form; clean-checkout profile evidence and the pinned least-privilege
CI workflow remain required.
