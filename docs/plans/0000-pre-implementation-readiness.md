---
id: PLN-0000
title: Pre-implementation readiness
status: active
owner: Jason Tarasovic
created: 2026-08-10
last_updated: 2026-08-10
gate: G1
depends_on: [P-001, S-001, S-003, S-004, L-001, L-002, L-004, C-001]
---

# Pre-implementation readiness

## Outcome

Authorize one bounded, disposable, VM-only implementation slice that produces
evidence for NeutrinOS's deployment model without treating its candidate
package, storage, build, or update mechanisms as accepted product decisions.

Completing this plan satisfies G1. It does not satisfy G2, authorize physical
installation, or accept any mechanism ADR.

## Proposed first slice

The leading first slice is a vertical reference-VM loop:

```text
declared source + candidate package snapshot + minimal fleet intent
  -> direct systemd/UAPI-oriented image composition fixture
  -> exact bootable VM deployment set
  -> boot the literal artifact in a disposable VM
  -> report its deployment and input identities
  -> retain logs, measurements, artifact inventory, and failure evidence
  -> destroy and reconstruct the VM from declared inputs
```

The slice should prove the smallest end-to-end identity and inspection path. It
should not begin by building a general framework, fleet controller, installer,
desktop, router, microVM product, or production authority service.

## Mutation and authority boundary

Permitted after G1:

- repository implementation changes under an accepted follow-on plan;
- build caches and artifacts in declared development locations;
- disposable VM disks, firmware variables, virtual TPM state, and test networks;
- synthetic signing, enrollment, identity, and credential fixtures; and
- read-only inspection of current hosts when separately authorized by the task.

Not permitted by this plan:

- repartitioning, installing, enrolling, or changing ownership on
  `desktop-jason`, `router`, or `misc`;
- using production Secure Boot, enrollment, recovery, or credential keys;
- changing current boot entries, network service, firewall policy, container
  storage, user identity, sub-ID ranges, or backups;
- publishing or rolling an artifact to any physical machine; or
- representing a candidate fixture as a supported NeutrinOS release.

## Candidate fixture disposition

| Topic | G1 fixture | Decision status | Why it does not block G1 |
| --- | --- | --- | --- |
| Composition/update substrate | Direct systemd/UAPI-oriented composition, likely through mkosi | Leading, not selected; bootc remains challenger | The slice is evidence about the leading candidate and preserves replaceable boundaries |
| Package inputs | Declared Fedora stable snapshot fixture | Leading, not selected; Arch comparison remains required | A fixture can be exact and reproducible without deciding the product ecosystem |
| Storage | Disposable DDI-compatible VM layout sufficient to boot and retain test evidence | Exact production layout open | No physical preservation, capacity, encryption, or migration claim is made |
| Kernel | General package-universe kernel with normal initrd | Conservative fixture, not accepted W-004 policy | No specialized/no-initrd benefit is claimed |
| Configuration | Minimal bounded TOML/native-source path under ADR-0003 | Accepted boundary; implementation open | Only fields required by the slice need implementation |
| Identity | Synthetic VM machine/user identities | Policy accepted; exact production allocations open | No restored/shared production ownership is involved |
| Credentials | Synthetic test-only values | Policy accepted; custody mechanism open | No production confidentiality or entitlement is claimed |
| Role | Generic qualification fixture, not workstation/router role | Role definitions open | G1 proves lifecycle plumbing, not a role capability promise |
| VM versus microVM | Ordinary disposable test VM | W-002 remains open | A test harness VM is not a managed NeutrinOS microVM workload |

Any implementation shortcut that crosses one of these boundaries reopens G1
review before work continues.

## Repository and collaboration readiness

These tasks are part of G1 because unclear context, conflicting agent
instructions, an undefined test contract, and unmanaged generated output would
make the first implementation difficult to review or reproduce. They govern how
work is performed; they do not add NeutrinOS product requirements.

### Agent context contract

Define a small, tiered context path so a fresh human or agent does not need to
read the entire design archive before useful work:

1. a concise repository instruction file containing invariant working rules,
   safety boundaries, canonical commands, and where authority lives;
2. a current-context document containing the active gate and plan, accepted
   decisions relevant to current work, leading but unaccepted fixtures,
   prohibited actions, dirty-worktree expectations, and the next action;
3. a hard stop after those two files for read-only status/orientation/report
   work, except one authority explicitly named by the user;
4. the [work register](../project/work-register.md) only for aggregate status;
5. the active plan only for execution/edit scope and requirement trace; and
6. only the DES/ADR/SYS/EX sources governing the exact task.

The context summary must be explicitly non-normative, name its source records
and last verification point, and fail review if it promotes a candidate into a
decision or omits a safety boundary. Define update triggers for gate changes,
accepted/reopened decisions, active-plan changes, and mechanism-selection
changes. Evaluate a maintained summary first; generate derived indexes only
when generation demonstrably reduces drift without hiding the source.

Validate the contract by starting a clean session with no conversation history
in each supported agent and asking it to identify:

- the current gate, active plan, and next action;
- accepted versus leading versus open decisions;
- allowed and prohibited mutations;
- the authoritative document for a named decision; and
- the required validation and handoff behavior.

### Multi-agent repository contract

Maintain one canonical, tool-neutral instruction source. Provide the smallest
supported adapter for Codex, Claude Code, and GitHub Copilot, and test that each
client actually loads the intended guidance. Do not maintain three independent
copies of architecture or workflow rules.

The setup exercise should evaluate the current upstream discovery mechanisms:

- [Codex `AGENTS.md` discovery](https://developers.openai.com/codex/guides/agents-md);
- [Claude Code project memory and `AGENTS.md` import](https://code.claude.com/docs/en/memory); and
- [GitHub Copilot repository and agent instructions](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions).

The common contract must cover:

- source-of-truth and decision-authority order;
- user-only authority to accept designs, requirements, ADRs, gates, and plans;
- branch/worktree or other isolation per concurrent task;
- explicit task ownership and avoidance of overlapping file edits;
- preservation of dirty worktrees and unrelated changes;
- no production or physical-host mutation without plan-level authorization;
- atomic reviewable commits and no autonomous push/merge/release;
- standard validation commands and evidence expectations; and
- a handoff containing scope, changed files, tests, unresolved questions, and
  exact next action.

Tool-specific files may contain only discovery syntax or behavior genuinely
specific to that tool. Any duplicated common text needs a drift check.

### Test strategy and entry point

Define the testing model before choosing a framework. It must distinguish:

1. documentation structure, links, frontmatter, IDs, and cross-reference checks;
2. unit tests for parsers, composition, policy, and pure transformations;
3. schema, fixture, golden-output, and deterministic-reconstruction tests;
4. static artifact and deployment-closure inspection;
5. disposable VM boot and integration tests on literal artifacts;
6. lifecycle, interruption, corruption, substitution, offline, and recovery
   failure injection;
7. role qualification; and
8. separately authorized physical-host trials.

Select one documented top-level local/CI entry point for fast checks and one for
the complete applicable suite, regardless of the underlying runner. Define test
selection, isolation, privilege/network/secret policy, timeouts, retries and
flaky-test handling, logs/artifacts, redaction, cleanup, and retention. Every
implemented claim must trace to an accepted requirement or a deliberately
bounded experimental question; coverage percentages do not replace that trace.

### Repository hygiene contract

Before source implementation, define and enforce:

- the top-level layout and which directories own source, tests, fixtures,
  schemas, scripts, generated files, caches, artifacts, and retained evidence;
- naming, stable-ID, frontmatter, formatting, and cross-link conventions;
- which generated or golden outputs are committed and how their provenance and
  regeneration commands are recorded;
- ignored local state, build output, VM disks, firmware/vTPM state, credentials,
  logs, editor files, and agent-local memory;
- maximum practical repository artifact size and the external retention path
  for images and large evidence;
- supersession/archive rules for historical decisions and obsolete plans;
- dependency, lockfile, vendoring, and update ownership; and
- an automated check that a clean clone can run the documented fast validation
  without depending on undeclared local state.

Prefer a small stable layout over speculative directories. New top-level
directories require a named owner and lifecycle rather than becoming a misc
bucket.

### Baseline housekeeping

The repository now has canonical root agent instructions and thin Claude and
Copilot adapters. It still has no tracked root README, license, contributor
guide, `.gitignore`, `.editorconfig`, CI configuration, or canonical test
command. Before G1:

- add a root README that points to the project thesis, current gate, work
  register, active plan, bootstrap, test, and contribution paths;
- decide and record licensing before source code creates redistribution
  ambiguity;
- add `.gitignore` and `.editorconfig` from the accepted layout and toolchain,
  not a broad copied template;
- add canonical contributor/agent guidance and tested tool adapters;
- add the initial local validation entry point and CI job;
- establish secret scanning and synthetic-fixture rules before credentials or
  signing tests exist;
- define branch, worktree, issue, pull-request, review, commit, and handoff
  conventions appropriate to one human using multiple agents;
- decide how dependencies and agent-generated changes are reviewed and updated;
  and
- defer public contribution, security-reporting, release/versioning, and
  artifact-publication machinery explicitly if the repository remains private.

## Readiness checklist

| ID | Exit criterion | Status | Evidence or required disposition |
| --- | --- | --- | --- |
| PRE-001 | The first slice has an accepted outcome, non-goals, and mutation boundary. | Satisfied | Owner approval of this plan on 2026-08-10 |
| PRE-002 | Every decision relevant to the slice is classified as accepted, experimental fixture, blocking, or deferred. | Satisfied | Owner approval of the candidate fixture table and [work register](../project/work-register.md) on 2026-08-10 |
| PRE-003 | The exact source tree, candidate package snapshot, configuration inputs, build-tool identity, and expected output artifact set are named. | Pending | Follow-on reference-VM plan |
| PRE-004 | Applicable accepted system requirements are mapped to first-slice tests, with non-applicable requirements and reduced claims justified. | Pending | Requirements trace in follow-on plan |
| PRE-005 | At least one success path and representative substitution, corruption, interruption, reconstruction, and offline failure paths are specified. | Pending | Test matrix in follow-on plan |
| PRE-006 | Artifact, deployment, configuration, and package-input identities have a minimal inspectable representation before implementation defines filenames or schemas by accident. | Pending | Reference-VM output contract |
| PRE-007 | Build and test execution cannot access production signing, enrollment, recovery, fleet, machine, or secret authority. | Pending | Environment/credential allowlist and hostile-input test |
| PRE-008 | Build artifacts, caches, VM state, retained evidence, cleanup, capacity bounds, and failed-run handling are declared. | Pending | Follow-on plan storage and cleanup section |
| PRE-009 | The implementation plan names one next action, review increments, exit criteria, and conditions that stop or re-scope the work. | Pending | `PLN-0001` |
| PRE-010 | Open W-002, W-004, and role questions are visibly deferred without being encoded as accidental permanent architecture. | Satisfied | Owner approval of the work-register gate classifications on 2026-08-10 |
| PRE-011 | Documentation validation and incremental commit practice remain part of each completed plan step. | Satisfied | Existing repository workflow and commit history |
| PRE-012 | A concise agent context contract is documented, has explicit authority/update rules, and passes a clean-session comprehension exercise. | Satisfied | [EX-0016](../research/exercises/0016-agent-context-and-instruction-loading.md) passed Codex/Claude semantics, adversarial probes, freshness, and hard-bounded cold routing at `c96fdbb` |
| PRE-013 | Canonical tool-neutral repository instructions, minimal tool adapters, task isolation, concurrent-edit, commit, review, and handoff rules are defined and loading-tested. | Satisfied | Codex/Claude discovery and loading passed in [EX-0016 results](../research/results/0016-agent-context-and-instruction-loading.md) at `c96fdbb`; Copilot owner-deferred and remains unverified |
| PRE-014 | A layered test strategy maps requirements to documentation, unit, schema/fixture, artifact, VM, failure-injection, role, and physical-trial levels. | Satisfied | Owner acceptance of the [test and evidence strategy](../project/test-strategy.md), representative G1 trace, and [PR-0017](../project/reviews/0017-test-strategy.md) on 2026-08-10 |
| PRE-015 | Canonical fast and complete validation entry points define isolation, privileges, network/secrets, timeout, flaky, artifact, redaction, cleanup, and CI behavior. | Active | Accepted [validation execution contract](../project/validation-contract.md), [PR-0018](../project/reviews/0018-validation-contract.md), [PR-0019](../project/reviews/0019-mise-validation-interface.md), [PR-0020](../project/reviews/0020-validation-runner-hostile-probes.md), [PR-0021](../project/reviews/0021-validation-failed-invocation-results.md), [PR-0022](../project/reviews/0022-validation-output-safety.md), and [PR-0023](../project/reviews/0023-validation-empty-cache.md); four mise tasks, locked Linux-x64 Python 3.14/uv tooling, external XDG test cache, result-producing failed invocations, canary scanning and quarantine, named T0 checks, and registered hostile and retained empty-cache probes implemented; clean local evidence and passing initial CI job remain |
| PRE-016 | Repository layout, generated/committed content, ignored local state, large artifacts, stable IDs, formatting, dependency, supersession, and clean-clone rules are documented and checked. | Pending | Repository hygiene guide and clean-clone validation |
| PRE-017 | Root README, license decision, `.gitignore`, `.editorconfig`, contribution/agent guidance, secret scanning, and private/public deferrals are complete. | Pending | Tracked baseline files and CI evidence |
| PRE-018 | G1 approval is recorded explicitly; proposed-plan status alone grants no implementation authority. | Pending | Owner acceptance recorded in this plan |

## Requirements-trace expectations for PLN-0001

The follow-on reference-VM plan should not copy all system requirements into a
checklist. It should link the requirements exercised by the slice and classify
the remainder:

- **demonstrated**: the slice is intended to produce direct evidence;
- **partially exercised**: only a named aspect is in scope;
- **not applicable to G1**: the requirement governs a capability absent from
  the fixture; or
- **deferred to a named gate/exercise**: required later, with no current claim.

At minimum, the first slice should exercise the accepted deployment identity,
literal-artifact boot, deterministic configuration, package-input identity,
diagnostic, offline reconstruction, and evidence-separation boundaries. It
must not claim production boot integrity, enrollment, secret custody, rollout,
role availability, or state migration merely because the VM boots.

## Failure and stop conditions

Stop and return to design review if:

- the slice requires a production credential or physical-host mutation;
- direct systemd/UAPI composition cannot express the accepted deployment-set
  boundary without an unplanned general-purpose framework;
- a candidate package or tool forces undeclared mutable resolution;
- a fixture choice would silently settle Fedora versus Arch, storage layout,
  W-002, W-004, or a role definition;
- the build cannot identify or retain its exact inputs and outputs;
- VM state cannot be safely destroyed and reconstructed; or
- scope expands faster than requirements and tests can remain traceable.

A stop result is evidence, not plan failure. Update the relevant research note,
design, work-register row, and next action.

## G1 exit evidence

G1 is satisfied only when:

1. PRE-001 through PRE-018 are satisfied or carry an accepted later-gate
   deferral where the criterion allows one;
2. PLN-0001 exists and is accepted;
3. the work register identifies PLN-0001 as the sole active implementation
   slice;
4. the repository and VM-only mutation boundaries are explicit; and
5. the approval is recorded below.

## Decision

Accepted by Jason Tarasovic on 2026-08-10. PLN-0000 is active for repository
readiness, documentation, validation, and collaboration scaffolding only. The
approval accepts its readiness model and fixture/defer classifications; it does
not satisfy PRE-018, G1, or authorize NeutrinOS source implementation. G1 also
requires an accepted PLN-0001 and completion of this checklist.
