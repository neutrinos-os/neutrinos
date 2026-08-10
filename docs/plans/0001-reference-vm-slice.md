---
id: PLN-0001
title: Reference-VM evidence slice
status: active
owner: Jason Tarasovic
created: 2026-08-10
last_updated: 2026-08-10
gate: G1
depends_on: [PLN-0000]
---

# Reference-VM evidence slice

## Outcome

Produce one bounded, disposable, VM-only vertical slice that composes a
bootable deployment set from declared inputs, boots the literal artifact,
reports its deployment and input identities, retains evidence, and is
destroyed and reconstructed from the same declared inputs.

The claim this supports is narrow and worth stating in one sentence: the
accepted deployment-identity model can be realized end to end by direct
systemd/UAPI-oriented composition, and its identity and inspection path can be
observed rather than asserted.

This plan's acceptance satisfies PRE-003 through PRE-009. G1 additionally
requires PRE-017's CI evidence and PRE-018's recorded approval. It accepts no
mechanism, no package ecosystem, and no storage layout.

## Non-goals

- Any physical-host effect. This slice never leaves the VM.
- A general composition framework, fleet controller, installer, updater
  service, desktop, router, or microVM product.
- Selecting Fedora over Arch, selecting mkosi over bootc, or settling W-002,
  W-004, storage layout, or any role definition.
- Boot integrity, enrollment, secret custody, rollout, role availability, or
  state migration claims. The VM booting proves none of these.
- Performance, size, or boot-time optimization of any kind.

## Mutation and authority boundary

This plan inherits PLN-0000's boundary unchanged and does not restate it as a
new authority. It is reproduced here only where this slice narrows it.

May read and change:

- repository paths under `tools/` and a new `src/` tree for slice
  implementation, plus `docs/` records;
- build caches and artifacts in declared locations outside the checkout;
- disposable VM disks, firmware variables, vTPM state, and an isolated test
  network; and
- synthetic signing, enrollment, identity, and credential fixtures.

Must not, and no task in this plan may request an exception:

- touch `desktop-jason`, `router`, `misc`, or any other physical host beyond
  read-only inspection separately authorized by a task;
- use production Secure Boot, enrollment, recovery, or credential keys;
- publish or roll an artifact to any physical machine; or
- represent any output as a supported NeutrinOS release.

The slice's first network-reaching build is an acquisition phase bounded by
declared inputs, exactly as repository bootstrap is. It is not a licence for
undeclared resolution at any later step.

## Inputs and dependencies

| Input or dependency | Identity/status | Blocking behavior |
| --- | --- | --- |
| [ADR-0001](../adrs/0001-systemd-first.md) systemd-first | Accepted | Fail: an overlapping non-systemd mechanism requires recorded evidence first |
| [ADR-0003](../adrs/0003-bounded-fleet-intent-representation.md) bounded intent | Accepted | Fail: configuration must be bounded TOML plus exact native sources |
| [System requirements](../requirements/system.md) | Accepted | Per-requirement; see the trace below |
| [Validation contract](../project/validation-contract.md) | Accepted | Fail: slice tests register in the existing runner, not a parallel one |
| [Hygiene contract](../project/repository-hygiene.md) | Accepted | Fail: artifact size and binary bounds bind here first |
| Composition tool (mkosi leading) | Candidate fixture | Stop for review if it cannot express the deployment-set boundary without a general framework |
| Package snapshot (Fedora stable leading) | Candidate fixture | Stop for review if resolution cannot be declared and pinned |
| QEMU/KVM, UEFI firmware, vTPM | Development environment | Fail: no substitute host is authorized |

Candidate mechanisms used by this plan remain candidates. Nothing here accepts
mkosi, Fedora, or a storage layout, and an implementation that starts to depend
on one as though it were decided is a stop condition, not a shortcut.

## Decision and requirement trace

Per PLN-0000, this links what the slice exercises and classifies the rest by
family rather than copying 132 requirements forward.

| ID | Applicability | Planned evidence |
| --- | --- | --- |
| SYS-001 | Demonstrated | Retained record binding source revision, pinned inputs, build configuration, and test results |
| SYS-002 | Demonstrated | The booted VM runs the exact deployment identity and closure that composition produced |
| SYS-008 | Demonstrated | Booted machine reports its exact deployment identity; inspection output retained |
| SYS-016 | Demonstrated | Fully resolved inputs and generated native configuration retained and compared across two builds |
| SYS-017 | Demonstrated | Deployment selects a previously built artifact; no machine-side evaluation |
| SYS-018 | Demonstrated | Injected configuration and composition failures identify the responsible input and generated output |
| SYS-041 | Demonstrated | Reconstruction from retained local inputs with the network removed |
| SYS-045 | Demonstrated | Immutable composition record with ordered inputs and tool identities |
| SYS-057 | Demonstrated | Declared distribution, branch, architecture, repositories, and precedence for every resolution |
| SYS-058 | Demonstrated | Complete resolved binary package closure with exact package bytes retained |
| SYS-059 | Demonstrated | Injected undeclared-repository and mixed-branch cases fail closed |
| SYS-065 | Demonstrated | Evidence records bind exact subject identities and literal formats |
| SYS-012 | Partial | Literal-artifact boot only; no emergency-release path exists |
| SYS-014, SYS-015 | Partial | Only the intent fields the slice requires; native escape hatch shown once |
| SYS-044 | Partial | `common < role < machine` precedence with a generic fixture role only |
| SYS-049 | Partial | Read-only root mount; authentication against a trust anchor is out of scope |
| SYS-026 | Partial | Diagnostics retained through failure; no rollback path exists to survive |
| SYS-066, SYS-067 | Partial | Build provenance for slice outputs only; no attestation chain |
| SYS-003, SYS-029, SYS-038, SYS-039, SYS-040 | Deferred to G2 | Lifecycle transition, staging, trial boot, blessing, and retention need a second deployment the slice does not build |
| SYS-030, SYS-036, SYS-037, SYS-053 | Not applicable to G1 | Production boot integrity and platform trust anchors are absent by construction; synthetic fixtures make no claim |
| SYS-025, SYS-032, SYS-033, SYS-035, SYS-047 | Not applicable to G1 | Authority, enrollment, and compromise recovery use synthetic values only |
| SYS-019 through SYS-024 | Deferred to a named later plan | State ownership, compatibility gating, and migration require persistent state the disposable VM does not keep |
| SYS-048, SYS-050 through SYS-056 | Deferred to G2 | Storage layout, encryption, capacity, and recovery environments are open |
| SYS-005, SYS-010, SYS-042, SYS-043 | Not applicable to G1 | The fixture is a generic qualification role, not a workstation or router |
| SYS-060 through SYS-064, SYS-068 through SYS-074 | Deferred to a named later plan | Supply-chain evidence, SBOM, reproducibility, and vulnerability processing exceed the slice |
| SYS-075 and later | Deferred to G2 | Rollout, fleet promotion, and withdrawal need more than one machine |

A requirement moving from deferred to demonstrated requires an update here, not
an implementation that quietly claims it.

## Work

At most one task is `active`.

| Task | Status | Depends on | Output/evidence | Next action |
| --- | --- | --- | --- | --- |
| PLN-0001-01 | complete | — | `src/slice/input-set.toml`, `src/slice/schema/input-set-v1.schema.json`, and [input declaration](../project/slice-input-declaration.md) recording what makes each input exact. Instance validates; schema rejects seven constructed violations | Complete 2026-08-10. No registered check guards these files until PLN-0001-05; the record states this. PLN-0001-02 is next |
| PLN-0001-02 | pending | 01 | Composition fixture producing a bootable deployment set | Compose the smallest bootable set and retain its composition record |
| PLN-0001-03 | pending | 02 | Boot of the literal artifact in a disposable VM | Boot the composed set unmodified and capture console and journal evidence |
| PLN-0001-04 | pending | 03 | Identity report from the running machine | Report booted deployment and input identities; compare against the composition record |
| PLN-0001-05 | pending | 03 | Registered slice tests in the existing runner | Register T2/T3 artifact and T4 VM tests; no parallel harness |
| PLN-0001-06 | pending | 04, 05 | Failure evidence for injected configuration, resolution, and composition faults | Inject each named failure and confirm it identifies its responsible input |
| PLN-0001-07 | pending | 04 | Destruction and offline reconstruction from declared inputs | Destroy the VM and rebuild with the network removed; compare identities |
| PLN-0001-08 | pending | 06, 07 | Evidence bundle and requirement-trace update | Retain the bundle outside the repository and update this trace with observed results |

## Failure, interruption, and cleanup

PLN-0000's stop conditions apply unchanged and are the authority. In addition:

- VM disks, firmware variables, and vTPM state are disposable and are destroyed
  by the task that created them. A VM that cannot be destroyed and reconstructed
  is a stop condition, not a cleanup inconvenience.
- Build caches and artifacts live outside the checkout, as validation run
  directories already do. The hygiene contract's binary and 1 MiB bounds bind
  here first: no image, disk, or evidence bundle is committed. A document that
  depends on one records its identity and how to reconstruct it.
- A partial build is deleted rather than reused. Resuming from unidentified
  intermediate state defeats the identity claim this slice exists to make.
- Retained evidence is scanned by the same output-safety path canonical
  validation uses. Synthetic credentials are still credentials in a log.
- Interruption leaves declared inputs untouched; only derived state is removed.

## Risks and unknowns

| Risk or unknown | Effect | Disposition |
| --- | --- | --- |
| R-001 mkosi cannot express the deployment-set boundary without a general framework | Slice becomes framework-building, which is a stated non-goal | Stop for review; PLN-0000 names this exactly |
| R-002 A candidate tool performs undeclared mutable resolution | Input identity claim is void | Stop for review; the claim fails rather than weakens |
| R-003 Fixture choices drift into decisions through repetition | Fedora or mkosi becomes settled without an ADR | Every record repeats candidate status; review challenges any accepted-sounding language |
| R-004 vTPM or UEFI firmware differences make boot evidence environment-specific | Evidence does not generalize | Accept and record the exact environment; make no portability claim |
| R-005 Evidence bundles exceed practical local retention | Capacity pressure, temptation to commit artifacts | Bound retention and record identity plus reconstruction instead of bytes |
| R-006 The slice succeeds and is mistaken for a working OS | Premature G2 or physical-host expectations | The outcome statement and README both say what it is not |
| R-007 Offline reconstruction passes only because a cache was warm | Reconstruction claim is hollow | Reconstruct with the network removed and the cache cleared, as `T5-VAL-003` does for the clean clone |

## Exit criteria

1. Every task is satisfied, cancelled with rationale, or moved to a linked plan.
2. Every requirement marked demonstrated or partial has retained evidence, and
   every other row still classifies correctly after the work.
3. The literal composed artifact booted, reported its identities, and matched
   its composition record.
4. The VM was destroyed and reconstructed from declared inputs with the network
   removed, producing the same deployment identity.
5. Injected configuration, resolution, and composition failures each identified
   their responsible input.
6. Slice tests are registered in the existing validation runner and pass in a
   named profile.
7. Native diagnostics and failure evidence are retained outside the repository.
8. The work register, current context, and affected source records are updated.
9. Remaining unknowns are linked and assigned to a later gate or plan.

## Decision

Accepted by Jason Tarasovic on 2026-08-10 following
[PR-0027](../project/reviews/0027-reference-vm-slice-plan.md). PLN-0001 is
active; its bounded work may proceed.

This acceptance supplies the accepted follow-on plan that PLN-0000 requires.
It does not by itself authorize NeutrinOS source implementation. PLN-0000
permits repository implementation changes only **after G1**, and only under an
accepted follow-on plan: both conditions must hold. A plan carries bounded work
authority; it is not a gate and cannot grant itself one.

Work that is not repository implementation — records, declarations, and
research under `docs/` — may proceed now. Implementation tasks unlock when G1
is recorded under PRE-018, which additionally requires PRE-017's CI evidence.

It accepts no mechanism, package ecosystem, storage layout, or role definition;
authorizes no physical installation and no effect on `desktop-jason`, `router`,
or `misc`; and does not satisfy G2. It does not by itself satisfy PRE-018 or
G1, which additionally require PRE-017's CI evidence and a recorded G1
approval.

Per PR-0027 C-004, the first task that creates a top-level tree amends the
[hygiene contract](../project/repository-hygiene.md) table in the same commit.
