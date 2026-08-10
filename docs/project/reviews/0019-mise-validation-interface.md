---
id: PR-0019
subject: Mise validation interface and Python toolchain
reviewer: Codex adversarial pass
date: 2026-08-10
status: accepted
---

# Mise validation interface and Python toolchain review

## Decision scope

This review challenges the amendment replacing the proposed root `./check`
executable with canonical mise tasks and selecting locked Python 3.14 plus uv
for the initial validation engine. It does not select a product mechanism,
place mise in a NeutrinOS host role, or authorize NeutrinOS source work.

## Summary judgment

The amendment removes a redundant wrapper and makes the selected repository
tool manager the discoverable command surface. It is suitable if mise remains
the bootstrap and dispatch layer rather than becoming a second validation
framework, and if automatic installation cannot cross the offline validation
boundary.

The strongest reason to reject it is circular dependence on a tool that the
repository must first obtain. That dependence is acceptable for development
tooling when mise itself is pinned outside its lockfile, bootstrap is explicit,
and validation fails rather than acquiring a missing tool.

## Challenges

### C-001: Mise becomes an opaque test framework

- Severity: high
- Claim: profiles, test registration, result joins, and cleanup could migrate
  into task dependencies and embedded TOML commands.
- Required response: use mise for task discovery, locked tools, and dispatch
  only; keep validation semantics in reviewable Python and native tools.
- Disposition: resolved in amendment
- Residual risk: implementation review must reject substantial task DSL logic.

### C-002: Task auto-install violates offline validation

- Severity: critical
- Claim: invoking a check can resolve or download a missing tool and silently
  mix acquisition with evidence production.
- Required response: disable task auto-install, perform `mise install --locked`
  in an attributable bootstrap phase, and fail preflight when inputs are absent.
- Disposition: resolved in amendment
- Residual risk: hostile probes must prove an empty cache cannot trigger network
  resolution after validation begins.

### C-003: Repository results depend on the current workstation

- Severity: high
- Claim: generating versions from installed tools would reproduce one host's
  accidental state and break as soon as that host pivots.
- Required response: declare supported tool lines in `mise.toml`, commit exact
  platform resolutions in `mise.lock`, and reconstruct from those records.
- Disposition: resolved in amendment
- Residual risk: PRE-016 must assign lock update and supported-platform policy.

### C-004: Python 3.14 is too new for a required dependency

- Severity: medium
- Claim: an essential validation or system tool may not yet support 3.14,
  blocking the suite for no product benefit.
- Required response: default to the latest locked 3.14 patch; permit only an
  evidenced, named, temporary fallback with an owner and removal condition.
- Disposition: accepted conditional escape
- Residual risk: avoid selecting dependencies merely because they lag 3.14 when
  a maintained compatible alternative exists.

### C-005: Mise use accidentally selects product software placement

- Severity: high
- Claim: repository adoption could be cited as acceptance that every
  NeutrinOS role ships, exposes, or supports mise.
- Required response: classify this decision as repository development tooling
  only; retain W-003 placement and role defaults as separate decisions.
- Disposition: resolved in amendment
- Residual risk: implementation plans must not turn developer bootstrap into a
  host-role promise.

### C-006: Removing `./check` harms portability

- Severity: medium
- Claim: callers now need to know and install mise instead of invoking a
  repository-native executable.
- Required response: make mise installation and pinning part of the documented
  bootstrap, use full `mise run` commands in automation, and keep task names
  stable under the validation contract.
- Disposition: accepted tradeoff
- Residual risk: revisit only if a supported environment cannot bootstrap mise
  or another CI provider requires a tool-neutral entry point.

## Required confirmations

1. The four `mise run check:*` tasks are canonical.
2. Mise owns locked tools and task dispatch, not validation semantics.
3. Python 3.14 is the default; fallback requires concrete incompatibility
   evidence and an explicit temporary exception.
4. uv alone owns Python package resolution and locking.
5. Bootstrap may acquire pinned inputs; validation may not auto-install or
   resolve them.
6. Repository mise use does not decide NeutrinOS role software placement.

## Decision

Accepted by Jason Tarasovic on 2026-08-10. All six confirmations are approved.
PRE-015 remains active until implementation, hostile probes, clean local
profiles, and the initial CI result satisfy the amended validation contract.
