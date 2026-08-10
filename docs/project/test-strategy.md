---
status: accepted
last_updated: 2026-08-10
governing_plan: PLN-0000
readiness_criterion: PRE-014
---

# Test and evidence strategy

## Decision scope

This policy defines how NeutrinOS maps requirements and bounded experimental
questions to tests. It establishes a common test-level taxonomy, evidence and
trace rules, and the minimum escalation needed for a claim.

It does not select a test framework, command runner, CI service, file format,
artifact-retention service, timeout, or retry policy. PRE-015 owns those
choices. It also grants no physical-host mutation authority and does not turn
a successful fixture into an accepted product mechanism.

## Testing invariant

Every implemented claim must map to a falsifiable check over exact subjects in
a declared environment, with an explicit oracle, retained result, and claim
boundary. A passing check supports only that boundary. It does not transfer to
another artifact, deployment identity, role, platform, failure, or mechanism.

An accepted requirement can require evidence at several test levels. A lower
level should provide fast and precise fault localization; it cannot replace
the closest practical environment in which the claimed behavior exists.
Coverage percentages and a generic “tests pass” result do not replace the
requirement-to-test trace.

## Test levels

The identifiers are a taxonomy, not a confidence ranking. In particular,
failure injection is a cross-cutting activity recorded with the level whose
subject is manipulated, such as `T5@T2` or `T5@T4`.

| ID | Test level | Primary subjects and checks | Does not establish |
| --- | --- | --- | --- |
| T0 | Documentation contract | Structure, frontmatter, stable IDs, links, status vocabulary, required sections, authority references, and trace completeness | Executable semantics or runtime behavior |
| T1 | Pure logic | Parsers, validators, policy decisions, canonicalization, graph and closure operations, selectors, and other deterministic transformations | Generated native configuration, artifact contents, or integration behavior |
| T2 | Data contract and reconstruction | Schemas, valid and hostile fixtures, native-input pass-through, golden outputs, repeated composition, and reconstruction from declared retained inputs | That an artifact contains the result or that a machine boots it |
| T3 | Static artifact inspection | Literal deployment artifacts, deployment closure, manifests, identities, permissions, ownership, configuration, package inventory, signatures, and evidence joins | Boot, runtime health, firmware behavior, or recovery under interruption |
| T4 | Disposable VM integration | Boot of the literal artifact, on-machine identity, services, lifecycle transitions, offline operation, diagnostics, and destroy/reconstruct behavior using synthetic authority | Role qualification on a supported platform or physical hardware behavior |
| T5 | Controlled failure injection | Substitution, corruption, interruption, power loss, unavailable dependencies, hostile inputs, full storage, clock faults, and loss of synthetic authority at named transition boundaries | A broader claim than the paired subject and environment |
| T6 | Role qualification | An exact deployment variant and role configuration evaluated against named functional, security, availability, maintenance, and externally observable health criteria | Unexercised platforms, other roles, or production authorization |
| T7 | Separately authorized physical-host trial | Firmware, boot chain, TPM, storage, networking, devices, power behavior, performance, recovery media, and operator procedure on one exact platform | Fleet-wide hardware support, architecture acceptance, or permission to mutate another host |

T0 through T4 are the normal pre-merge progression when applicable. T5 pairs
with any level at which a failure invariant exists. T6 is required before a
role-support claim. T7 is required for claims that depend on real firmware,
hardware trust facilities, devices, power behavior, or performance, but only
under an accepted plan naming the host, mutations, backup or recovery path,
stop conditions, and cleanup.

## Selection and escalation rules

For each claim:

1. Decompose the governing requirement or experimental question into the
   smallest observable properties that can independently pass or fail.
2. Select the lowest applicable level for fast feedback and the closest
   practical level for the actual claim. Record both when they differ.
3. Name the exact input, artifact, deployment identity, configuration identity,
   role, platform, transition, and authority fixture that bound the result.
4. State the oracle before implementation. Prefer independently observable
   state and native diagnostics over a component asserting its own success.
5. Add a negative control for identity, authorization, precedence, isolation,
   or trust-boundary claims. A happy path alone cannot establish rejection of
   a substituted or lower-authority input.
6. For lifecycle failures, inject at every transition boundary material to the
   claim and assert the required post-failure invariant and recovery path, not
   merely an error code.
7. Retain failures, skips, unsupported cases, and coverage gaps as results. A
   skipped or flaky check never becomes passing evidence through retry.

Use these minimum escalation rules:

- source and schema behavior: T0 through T2 as applicable;
- a claim about shipped bytes or complete deployment membership: T3;
- a claim about boot, runtime, offline lifecycle, or recovery: T4;
- a claim about behavior under a failure: T5 paired with the applicable level;
- a claim about a supported role: T6; and
- a claim that materially depends on physical hardware or firmware: T7.

A higher level does not excuse missing lower-level observability. A physical
trial that boots successfully, for example, cannot establish package-input
identity or deterministic configuration if those properties were not traced
and inspected.

## Requirements-to-test trace contract

Every implementation plan must maintain a trace for its exact claim set. A
trace row contains:

- accepted requirement ID or explicitly non-authoritative experimental
  question;
- plan-local claim classification: `demonstrated`, `partially exercised`,
  `not applicable`, or `deferred` to a named gate or exercise;
- exact claim boundary and explicit non-claims;
- applicable test levels and named success, negative, and failure scenarios;
- oracle and independently observed outputs;
- fixture and input identities, including synthetic-authority boundaries;
- retained evidence records and coverage gaps;
- result state: `planned`, `passing`, `failing`, `blocked`, or `skipped`; and
- the plan or authorization governing destructive, privileged, networked, or
  physical execution.

`Not applicable` and `deferred` require a reason. They do not satisfy the
requirement outside the plan's declared claim boundary. An experimental
question can justify a test and evidence record, but its result cannot accept
an architecture decision.

## Evidence rules

Each retained result must identify the test definition revision, exact
subjects and inputs, environment and relevant tool versions, start and end,
result, assertions, and raw diagnostic locations. It must distinguish observed
facts from derived verdicts and record redaction, omissions, and cleanup.

Passing, failing, and skipped executions are append-only observations. A rerun
creates a new result; it does not rewrite the earlier one. Qualification is an
evaluation of exact subjects against a named policy and environment, not a
synonym for test success. PRE-015 will define concrete result formats,
locations, retention, redaction, and local/CI commands.

## Representative G1 trace

This is a strategy check and seed for PLN-0001, not the final implementation
trace. “Demonstrated” below means only within the disposable reference-VM
boundary proposed by PLN-0000.

| Source | G1 classification | Levels | Representative check and evidence | Explicit boundary or non-claim |
| --- | --- | --- | --- | --- |
| SYS-001 | Demonstrated | T0, T2, T3, T4 | Join source revision, pinned inputs, build configuration, literal outputs, and VM result in one traversable fixture record | No production provenance or release authorization |
| SYS-002 | Demonstrated | T3, T4, T5@T4 | Inspect the complete deployment closure, boot those literal identities, and reject one substituted member | VM fixture only; no physical boot-integrity claim |
| SYS-008 | Demonstrated | T4 | Query the booted deployment identity and follow its references back to the fixture manifest and qualification result | Minimal inspection path, not the final machine-status model |
| SYS-014 | Partially exercised | T0, T2 | Review minimal bounded TOML and native inputs without executing a user language; retain parsed and rendered forms | No workstation or router configuration-completeness claim |
| SYS-016 | Partially exercised | T1, T2 | Repeat composition, exercise precedence conflicts, and compare resolved inputs and native outputs | Only fields and native inputs needed by the first slice |
| SYS-017 | Demonstrated | T3, T4, T5@T4 | Boot a previously built artifact while source, build tooling, and upstream repositories are unavailable | Does not select the permanent deployment substrate |
| SYS-018 | Partially exercised | T1, T2, T4, T5 | Malformed, conflicting, substituted, and boot-failing inputs identify their input, scope, output, and lifecycle stage | Only stages implemented by the slice |
| SYS-027 | Partially exercised | T0, T5 | Bind each security or isolation claim in the slice to assets, attacker action, assumptions, guarantee, non-guarantee, and recovery observation | No production-role security claim |
| SYS-036 | Demonstrated | T3, T5@T3 | An attributable but unqualified or subject-substituted build fails the synthetic qualification/promotion join | Synthetic authority only; no release publication |
| SYS-041 | Partially exercised | T4, T5@T4 | After required local inputs are retained, deny all named external dependencies and exercise boot, result recording, and a bounded return path | Reference VM only; workstation and router remain deferred |
| SYS-045 | Partially exercised | T2, T3 | Trace ordered configuration inputs and decisions both forward to rendered artifact bytes and backward from those bytes | Minimal composition record, not the final schema |
| SYS-057 | Partially exercised | T2, T5@T2 | Resolve a declared package snapshot twice and reject mutated metadata, undeclared sources, or solver-identity drift | Candidate package fixture; no Fedora-versus-Arch decision |
| SYS-058 | Demonstrated | T2, T3, T5@T2 | Reconstruct package inputs from retained exact bytes with upstream unavailable and trace packages to deployment files | Fixture reconstruction, not bit-reproducibility |
| SYS-065 | Partially exercised | T2, T3, T5@T3 | Validate typed evidence records and reject subject, producer, schema, or content substitution | Minimal evidence types only; record identity does not establish truth |
| SYS-010 | Deferred to role work | T6 | PLN-0001 records no role-support claim; later role plans define externally observable health and acceptance criteria | Generic VM fixture is not a role |
| SYS-030 | Not applicable to G1; deferred to authorized physical qualification | T3, T5@T7, T7 | Preserve the requirement and name the later authenticated-boot and substitution matrix | Disposable VM success makes no production physical boot-integrity claim |

PLN-0001 must replace these representative descriptions with exact test cases,
fixtures, expected outputs, evidence locations, and disposition for every
requirement applicable to its reduced claim.

## Review and change control

Review this policy adversarially against false confidence, fixture
ossification, VM-to-hardware claim transfer, golden-output drift, shallow
failure injection, unsafe authority access, and unbounded test matrices. The
initial review is [PR-0017](reviews/0017-test-strategy.md).

Changing the taxonomy or trace contract requires updating active plans and
traces that rely on it. Adding a runner or CI implementation belongs under
PRE-015 and must not silently redefine these claim boundaries.

## Decision

Accepted by Jason Tarasovic on 2026-08-10. The taxonomy, `T5@Tn` notation,
trace contract, evidence rules, representative G1 boundaries, and PR-0017
dispositions are project testing policy. This acceptance satisfies PRE-014; it
does not satisfy PRE-015, authorize source implementation or a physical-host
trial, or accept any experimental fixture as product architecture.
