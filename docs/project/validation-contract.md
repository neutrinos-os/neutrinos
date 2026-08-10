---
status: accepted
last_updated: 2026-08-10
governing_plan: PLN-0000
readiness_criterion: PRE-015
amended_by: PR-0021
---

# Validation execution contract

## Decision scope

This policy defines the stable local and CI interface for running the accepted
[test and evidence strategy](test-strategy.md). It covers selection,
isolation, privileges, network and secrets, timeouts, flaky results, output,
redaction, cleanup, retention, and the initial CI gate.

It selects the repository task interface and initial validation language and
toolchain. It does not select an assertion framework, authorize product source
implementation, acquire package or build inputs, run physical-host trials, or
define long-term qualification-evidence storage. Repository layout and ignored
local state remain PRE-016 and PRE-017 work.

## Stable entry points

The repository exposes these canonical mise tasks:

```text
mise run check:fast
mise run check:complete
mise run check:list
mise run check:run TEST-ID...
```

- `fast`: every registered T0 check plus applicable deterministic T1 and T2
  checks that require no network, privilege, VM, or retained large artifact.
- `complete`: `fast` plus every other registered test currently applicable and
  authorized in the checkout's active plans, normally through T5 and any
  explicitly available T6 fixture.
- `list`: print test ID, level, profile membership, timeout, requirements or
  questions traced, and declared capabilities without executing tests.
- `run`: developer selection of exact test IDs. It is never evidence that the
  `fast` or `complete` gate passed.

The tasks delegate to one validation engine and any purpose-built native
runners. Mise owns task discovery and the locked tool environment; it does not
own test registration, selection, assertions, timeout enforcement, cleanup, or
result semantics. Callers and CI do not invoke the engine or native runners
directly. Changes behind the canonical tasks must preserve these meanings or
revise this policy first.

“Complete” means the complete applicable suite declared by the repository at
that revision. It never silently includes T7, a physical machine, production
authority, an undefined role, or a deferred test. The run manifest lists every
registered test as selected, not applicable, deferred, blocked, or excluded
with its reason.

## Toolchain and bootstrap boundary

The repository toolchain is declared by `mise.toml` and resolved exactly for
supported platforms by a committed `mise.lock`. It is not inferred from or
pinned to the current development host. Mise tasks remain small dispatchers;
substantial validation behavior lives in reviewable Python modules or the
native tools responsible for each assertion.

The initial validation engine uses the latest locked Python 3.14 patch release.
Python packages are declared in `pyproject.toml`, resolved by a committed
`uv.lock`, and executed with locked resolution. Mise owns Python, uv, and
non-Python tool versions; uv alone owns Python package dependency resolution.
The same dependency must not be independently pinned by both systems.

A lower Python version is permitted only when a named required tool or
dependency prohibits 3.14, supported by a reproducible failure or upstream
compatibility statement. The exception must name its owner, affected checks,
smallest viable fallback, and removal condition. Convenience, an older host
interpreter, or an unexamined transitive constraint is not sufficient.

Bootstrap is separate from validation. Mise is offline in repository context;
a local or CI acquisition phase may explicitly set `MISE_OFFLINE=0` only while
installing the pinned repository tools with `mise install --locked python uv`.
Locked uv dependency synchronization may then allow only its declared package
endpoints. Naming the repository-owned tools prevents an operator's unrelated
global mise configuration from entering project bootstrap. Mise task and shim
auto-install are disabled, and canonical dispatch resolves Python and uv
through `mise which`: after bootstrap, a missing tool or stale lock fails
preflight rather than downloading, resolving, or using an ambient same-named
binary. CI pins its mise bootstrap and third-party actions independently
because mise cannot bootstrap its own executable.

Mise declares a validation cache root under the invoking user's XDG cache
directory. Reconstructible test-framework metadata may persist there between
local runs, but canonical profiles do not use cache-dependent selection or
interpret cached state as a passing result. The cache is outside the checkout,
is never qualification evidence, and may be deleted when validation is not
running. CI starts with an empty validation cache and neither restores nor
uploads it. Dependency, tool, build, image, and VM caches remain separate
acquisition or future-plan concerns.

## Test registration and selection

Each test has a stable ID and declares:

- test level, and paired level for T5;
- `fast`, `complete`, or both;
- requirements or experimental questions traced;
- exact capabilities: network, privilege, virtualization, storage, devices,
  time control, or other isolation needs;
- hard timeout and expected output bound;
- fixtures and retained inputs; and
- cleanup owner and resources.

A required selected test that cannot run is `blocked`, not `skipped` or
passing, and makes the profile fail. `Not applicable` and `deferred` are valid
only when already justified in the governing requirements-to-test trace.
Selection expressions may accelerate local diagnosis, but release, plan, and
gate evidence names an unmodified profile and repository revision.

## Execution boundary

Both profiles must:

- run without root and refuse effective UID 0;
- use a new private temporary work directory outside tracked source paths;
- confine persistent test-framework metadata to the declared external
  validation cache root;
- snapshot repository status before execution and fail if validation changes
  tracked, staged, untracked, or ignored repository state;
- isolate child processes in a killable process group and terminate it on
  exit, failure, timeout, or interruption;
- use only synthetic signing, enrollment, recovery, identity, credential, and
  machine fixtures;
- avoid physical devices, production networks, host firmware variables, host
  TPM state, and persistent host service configuration; and
- name every permitted writable path and verify cleanup of mounts, loop or
  network devices, VMs, firmware variables, vTPM state, sockets, and child
  processes it created.

The fast profile must work in a dirty checkout while preserving its exact
pre-run state. A result from a dirty checkout records the source revision and
diff identity and is development feedback, not qualification evidence. CI and
any qualification run require a clean checkout.

User-owned KVM and disposable VM state may be used by complete tests only when
the registered test declares them. Host-global virtualization, networking,
mount, or device mutation requires a separately accepted plan and is outside
the default entry points.

## Network, dependencies, and secrets

Validation is offline by default. Canonical check tasks must not download
dependencies, resolve mutable package sources, contact publication or discovery
services, or depend on current upstream state. Bootstrap, input acquisition,
and cache population are separate attributable operations with pinned inputs.

Tests receive an allowlisted environment and a temporary home. Agent tokens,
SSH agents, GPG agents, cloud credentials, GitHub write tokens, production
keys, host enrollment, machine identity, recovery material, and user credential
stores are absent. A required environment value is declared and synthetic; an
undeclared credential-like value fails preflight.

CI may use network access to check out the repository and obtain the locked
runner environment before a canonical check task starts. The validation
process itself runs with no network unless a future accepted test trace names
the exact endpoint, purpose, data exposure, and failure behavior. Such a test
is excluded from `fast` and may not use production authority.

## Timeouts and flaky results

Every test has a hard timeout enforced outside the test process. Initial
budgets are:

| Scope | Default | Maximum without plan-level justification |
| --- | --- | --- |
| T0 through T2 individual test | 60 seconds | 5 minutes |
| T3 individual test | 5 minutes | 20 minutes |
| T4 or T5 individual test | 15 minutes | 45 minutes |
| `fast` profile | 2 minutes | 5 minutes |
| `complete` profile | 60 minutes | 2 hours |

A timeout is a failing result and triggers normal cleanup. There are no
automatic assertion retries. A manual or infrastructure rerun creates a new
result and retains the first failure. A flaky test requires an owner, linked
work item, observed failure signature, claim impact, quarantine boundary, and
expiry. Quarantining a required test blocks the affected claim or gate; it does
not make the profile green.

## Result and artifact contract

Every profile or exact-test execution invocation, including one rejected during
argument validation, preflight, or selection, creates one run directory outside
the tracked checkout with:

- `run.json`: canonical JSON identifying repository revision and dirty-state
  identity, profile or selected IDs, registered-suite identity, environment,
  relevant tool versions, start/end, final result, omissions, and cleanup;
- `results.jsonl`: one append-only canonical JSON result per test, including
  its trace, exact subjects, assertions, duration, result, and diagnostic
  references;
- `logs/`: bounded native stdout, stderr, and tool diagnostics per test; and
- `artifacts/`: only outputs declared by the test registration, with identities
  and size recorded in `run.json`.

If no test begins, `results.jsonl` exists and is empty. `run.json` records the
failure stage, bounded diagnostic, selected IDs (if any), and cleanup state.
Rejected environment values and unvalidated command-line values are not
retained. `check:list` is a read-only registration query, not an execution
result or evidence-producing invocation; the runner-private per-test command is
likewise represented by its parent result rather than a nested run directory.

`run.json` records the resolved validation cache path and that it neither
affects test selection nor belongs to retained evidence. Cache contents are
not copied into the run directory.

The terminal summary reports the run directory and counts for passing, failing,
blocked, skipped, not-applicable, and deferred tests. Exit zero means every
selected test passed and cleanup succeeded. Any other state, invalid
registration, output overflow, result-write failure, or cleanup failure exits
nonzero; the machine-readable result records the reason.

Local successful runs may remove bulky diagnostics after writing the summary
unless retention was requested. Failed, blocked, interrupted, or cleanup-
failed runs preserve bounded diagnostics and print their location. CI uploads
`run.json`, `results.jsonl`, and bounded logs on every result for 14 days.
Qualification evidence must be copied into its separately governed retained
evidence set before reliance; ephemeral CI retention is not qualification
retention.

## Redaction and output safety

The primary defense is absence of secrets. Redaction is not permission to
expose them. Tests use recognizable synthetic canaries and scan result files,
logs, crash output, VM serial output, and declared artifacts for undeclared
credential material before retention.

Registrations classify expected path, user, machine, network, topology, timing,
and failure data. Redaction produces a derived output and records the omitted
fields; it never silently edits the original evidence record. Unsafe raw output
is quarantined outside CI upload, reported without its sensitive content, and
makes the run fail.

## Cleanup and interruption

Cleanup runs after success, failure, timeout, signal, and runner error. It is
idempotent and limited to resources created under the run identity. It must not
use broad path deletion, ambiguous globs, or ownership of a shared host
resource.

Diagnostics needed to explain failure are copied to the bounded run directory
before disposable resources are removed. Cleanup then verifies absence of its
processes and resources. Incomplete cleanup is a test failure and the summary
names exact manual recovery steps; the runner does not continue into another
test that could reuse the leaked state.

## Initial CI contract

The first CI workflow bootstraps the locked repository toolchain and then runs
`mise run check:fast` in a clean checkout. It must:

- use a versioned runner label rather than a floating `latest` label, record
  the resolved runner-image identity, and pin third-party actions by immutable
  commit;
- grant read-only repository contents and no other token permissions;
- provide no environment secrets or production environment;
- set a five-minute job timeout and no automatic retry;
- upload the bounded run result on success and failure for 14 days; and
- fail on any nonzero entry-point result or unexpected checkout mutation.

`mise run check:complete` is initially a required local pre-G1 check and a
manual CI workflow. It becomes an automatic gate only when its retained inputs,
cache, virtualization, runtime, and cost are deterministic enough that CI
failure has a useful owner response. A CI badge, check mark, or workflow
conclusion is non-authoritative; plan and gate status change only in repository
records after owner review.

## Implementation sequence and exit

PRE-015 is satisfied when:

1. this contract, [PR-0018](reviews/0018-validation-contract.md), and
   [PR-0019](reviews/0019-mise-validation-interface.md) are accepted;
2. the four canonical mise tasks implement the contract for the tests then
   present using the locked Python 3.14 toolchain or an accepted exception;
3. the temporary commands in [validation.md](validation.md) are registered as
   named T0 tests rather than duplicated policy;
4. a clean local checkout passes both profiles and preserves repository state;
5. the initial pinned, least-privilege CI workflow passes
   `mise run check:fast` and retains its bounded result; and
6. hostile preflight, timeout, interruption, output, and cleanup probes verify
   that the runner fails closed.

Acceptance of this document alone does not satisfy PRE-015.

## Decision

Accepted by Jason Tarasovic on 2026-08-10 and amended through accepted PR-0019
on the same date. The canonical mise task interface, locked Python 3.14 and uv
toolchain policy, applicable-suite meaning of `complete`, offline/unprivileged/
secret-free defaults, initial budgets, result and cleanup contract, flaky-test
policy, ephemeral CI retention, and PR-0018/PR-0019 dispositions are project
validation policy. PRE-015 remains active until the entry points, hostile
probes, clean local runs, and initial CI result satisfy the implementation exit
criteria above.
