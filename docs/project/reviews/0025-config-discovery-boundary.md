---
id: PR-0025
subject: Configuration-discovery boundary for bootstrap and canonical runs
reviewer: Claude implementation pass
date: 2026-08-10
status: proposed
---

# Configuration-discovery boundary review

## Decision scope

This review examines which mise configuration files can select repository
inputs, for bootstrap and for canonical task invocation. It extends the
`T5-VAL-002` C-003 residual recorded in
[PR-0023](0023-validation-empty-cache.md) beyond the probe's own subprocess. It
does not satisfy PRE-015, produce CI or qualification evidence, or authorize
NeutrinOS product implementation.

## Summary judgment

`T5-VAL-002` proves config isolation for the process it constructs. Nothing
carried that property to bootstrap or to an operator's ordinary
`mise run check:fast`. Both walked the operator's global configuration and
every ancestor directory.

The intended fix — declaring `ceiling_paths` in the repository `mise.toml` —
does not work, and the reason is structural rather than incidental: the
setting lives in a file mise must already have discovered, so it cannot
constrain the discovery that found it. No repository-level setting can exclude
the global config either, which is correct behavior; a checkout should not be
able to switch off an operator's global configuration from inside itself.

The boundary is therefore environment-scoped, not repository-scoped. Bootstrap
is now documented with the three config-only variables and is verified closed.
Canonical invocation remains open and belongs to CI and to the invoking
environment.

## Challenges

### C-001: A repository setting should express this, not documentation

- Severity: high
- Claim: a boundary that depends on an operator exporting variables is weaker
  than one declared in committed configuration, and `ceiling_paths` exists as
  a setting.
- Response: tested and falsified. With `ceiling_paths = ["{{ config_root }}"]`
  in a repository `mise.toml`, a parent-directory `mise.toml` was still loaded.
  The same fixture with `MISE_CEILING_PATHS` exported excluded the parent, and
  adding the global and system variables left only the repository config.
- Disposition: not resolvable at the declared layer
- Residual risk: the committed repository cannot enforce this. Any enforcement
  lives in the invoking environment, which the repository does not own.

### C-002: A documented bootstrap block does not bind agents or operators

- Severity: high
- Claim: prose and a copyable snippet are advisory. An operator or agent who
  runs `mise run check:fast` directly still admits ancestor and global
  configuration into resolution.
- Response: accepted. Bootstrap is closed because its documented procedure is
  now verified end to end, but canonical invocation is not, and this review
  does not claim otherwise. CI is the place where the variables can be set
  unconditionally, and CI is the remaining PRE-015 item.
- Disposition: open, deferred to the CI increment, which the owner moved to
  PRE-017 on 2026-08-10
- Residual risk: local canonical runs remain contamination-exposed until CI
  fixes the invocation environment, and local runs will not match CI until
  then.

### C-003: The observed contamination was only warnings

- Severity: medium
- Claim: the global-config tools failed to resolve and nothing was installed,
  so the exposure may be theoretical.
- Response: the observed instance was benign, but the mechanism is not. A
  global or ancestor config participating in resolution can declare tool
  families the repository never named, and repository lock coverage is
  asserted only for tools the repository declares. Treating a benign
  observation as a bound would repeat the PR-0024 error of documenting a
  boundary stronger than the mechanism.
- Disposition: recorded as mechanism, not severity
- Residual risk: no registered test asserts that canonical invocation resolves
  from the repository config alone.

### C-004: Isolating bootstrap could break tool acquisition

- Severity: medium
- Claim: applying the probe's isolation to bootstrap would redirect installs
  away from the operator's tool store, leaving canonical dispatch unable to
  find them.
- Response: only the config-only subset is documented. Data, installs, and
  cache directories are deliberately left at their operator defaults, which a
  clean-clone run confirms: bootstrap populated the real store and both
  profiles then passed.
- Disposition: resolved in the documented procedure
- Residual risk: a future contributor may copy the probe's full variable set
  into bootstrap and silently relocate the tool store.

## Probe observations

Fixture and clean clone at `6b9edf6`, mise 2026.7.17, Python 3.14.7,
uv 0.12.3:

- a parent `mise.toml` remained loaded with `ceiling_paths` declared in the
  child repository config;
- exporting `MISE_CEILING_PATHS` excluded the parent, and adding
  `MISE_GLOBAL_CONFIG_FILE` and `MISE_SYSTEM_CONFIG_DIR` reduced `mise config
  ls` to the repository config alone;
- the previously documented bootstrap admitted five global-config tool
  families into resolution, including `npm:bash-language-server`,
  `pipx:pyflakes`, and `actionlint`; and
- a fresh clone following the newly documented block produced no resolution
  warnings, resolved the locked Python and uv, passed `check:fast` and
  `check:complete` at `passing=4 failing=0`, and left the checkout clean with
  no stray directory.

These are development observations, not qualification or gate evidence.

## Required confirmations

1. Configuration-discovery isolation is environment-scoped; the committed
   repository cannot enforce it, and `ceiling_paths` in `mise.toml` is
   ineffective by construction.
2. Bootstrap isolates configuration only, never the data, installs, or cache
   directories.
3. Canonical local invocation remains contamination-exposed and is deferred to
   the CI increment rather than claimed closed here.
4. No registered test yet asserts repository-only config resolution for
   canonical invocation.
5. PRE-015 and G1 remain open.

## Owner decision

Pending. Acceptance would record the environment-scoped boundary, the
documented bootstrap procedure, and the deferral of canonical invocation to
the CI increment. It does not accept PRE-015 or G1.
