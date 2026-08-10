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
environment, then run the following from the repository root after reviewing
`mise.toml`:

```sh
mise trust "$PWD/mise.toml"
export MISE_GLOBAL_CONFIG_FILE=/dev/null
export MISE_SYSTEM_CONFIG_DIR="$PWD/.mise-no-system-config"
export MISE_CEILING_PATHS="$(dirname "$PWD")"
MISE_OFFLINE=0 mise install --locked python uv
uv sync --locked --python "$(mise which python)"
```

The three exported variables exclude the operator's global mise configuration,
any system configuration, and every config file above the repository, so only
this checkout's `mise.toml` selects bootstrap inputs. They are the config-only
subset of the isolation `T5-VAL-002` constructs; bootstrap deliberately does
not isolate the data, installs, or cache directories, because it must populate
the operator's real tool store. Without them, tools declared in a developer's
global configuration enter version resolution. Equivalent `mise.toml` settings
do not work: `ceiling_paths` is read from a config file that mise has already
discovered, so it cannot prevent that discovery, and no repository-level
setting can exclude the global config.

Trust is required before the first command: an untrusted `mise.toml` makes
`mise which python` fail, and `uv sync --python ""` then silently selects an
interpreter other than the locked one.

Bootstrap is an unfiltered acquisition phase. Per-host network filtering is not
available: pinned mise rejects `--allow-net=<host>` on Linux, the only locked
platform, so no endpoint restriction is enforced here. What bounds bootstrap is
the pinned input set, not the network path: `mise.lock` fixes the tool
versions, `uv.lock` with `--locked` fixes every package and hash, and a lock
mismatch fails rather than resolving.

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
`T5-VAL-001` runs the hostile validation-runner probes. `T5-VAL-002` starts
with an isolated empty mise cache and runs the registered `check:list` task
using only the already-installed locked Python and uv inputs.

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
in-repository value. It likewise declares the exact resolved Python and uv
installation roots; the runner rejects missing, relative, non-directory, or
in-repository roots.

`T5-VAL-002` never deletes or substitutes the operator cache. It creates
private HOME, XDG, mise cache/config/data/state, system-config, and trust-state
directories; prevents config discovery above the repository; links only the
local Python and uv installation families; and runs nested `check:list` under
the repository's offline and no-auto-install settings. Its retained log records
that the cache began empty, the exact locked executables resolved beneath the
declared installations, and every cache file created. Only mise's local
per-version `bin_paths-*.msgpack.z` resolution record is permitted; any other
cache file fails the test. This is repeatable development/CI result evidence,
not qualification retention.

## Current implementation boundary

The Python 3.14 runner implements named registration and selection, exact
runner and child environment allowlists, per-test process groups and timeouts,
live bounded output capture, interruption and descendant cleanup,
machine-readable results, synthetic-canary and conservative credential-marker
scanning, out-of-result quarantine, and before/after identities covering Git,
untracked, and ignored checkout state. Mise blocks inherited environment and
network syscalls around the complete task and prevents acquisition before task
launch. `T5-VAL-001` exercises these failure boundaries with synthetic
processes. `T5-VAL-002` retains the empty-mise-cache acquisition-boundary
result.

PRE-015 is satisfied. The empty-cache and bootstrap-boundary increments are
accepted. Clean-checkout profile evidence is obtained: a fresh clone at
`42f23b9`, bootstrapped exactly as documented above, passed `check:fast` and
`check:complete` at `passing=4 failing=0` and left the checkout clean. The
pinned least-privilege CI workflow is deferred to PRE-017. When written it must
set the bootstrap configuration variables above for canonical invocation too:
config-discovery isolation cannot be declared in `mise.toml`, so canonical
local runs still admit ancestor and global configuration. That boundary is
proposed in
[PR-0025](reviews/0025-config-discovery-boundary.md) and awaits review.
