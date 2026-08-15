---
status: active
last_updated: 2026-08-15
---

# Work register

## Purpose

This is the aggregate answer to “what is left?” It joins, but does not replace,
the authoritative status held by the decision backlog, requirements, designs,
ADRs, research exercises, and implementation plans.

The register deliberately keeps separate dimensions. An accepted policy is not
a selected mechanism; a selected mechanism is not completed evidence; completed
evidence is not an implementation; and an implementation is not a production
authorization.

## Authority and update rule

When this register conflicts with a source document, the source document wins
and this register must be corrected. Update the relevant row whenever a change:

- accepts, rejects, supersedes, or reopens a decision;
- selects or removes a leading mechanism;
- starts, completes, or invalidates an evidence exercise;
- starts or verifies an implementation milestone; or
- changes which phase gate a workstream blocks.

Do not update it for every exploratory commit. Plans and issues carry that
lower-level activity.

**Cells stay short and carry pointers.** A row states which dimension moved and
where the evidence lives; it does not restate the evidence. Restating it is how
this register went stale for two days while every fact in it existed correctly
elsewhere -- `P-010`'s duplicated-state failure, observed on this document. The
running record for the active plan is the
[current context](current-context.md); measurements live in the records the
plans name.

## Phase gates

| Gate | Meaning | Expansion authorized after satisfaction |
| --- | --- | --- |
| G0 | Architecture policy baseline | A bounded implementation plan may be reviewed; no code or mutation authority follows automatically |
| G1 | VM-only evidence prototype authorized | Disposable VM/lab implementation may begin under a named plan using candidate fixtures |
| G2 | Reference VM qualified | Reusable implementation foundation may advance; this does not authorize a physical-host install |
| G3 | Workstation trial authorized | Attended, recoverable trial on `desktop-jason` may proceed under a separate accepted plan |
| G4 | Router trial authorized | Attended router transition may proceed with independent service-continuity and recovery evidence |

Gates bound risk and mutation, not merely project maturity. Later laptop,
server/storage, microVM-guest, or public-release gates should be added only when
those targets become active.

## Status vocabulary by dimension

| Dimension | Values |
| --- | --- |
| Policy | open, in review, accepted, superseded |
| Mechanism | open, candidates, leading, selected, rejected |
| Evidence | not defined, proposed, active, complete, invalidated |
| Implementation | not started, active, verified, retired |
| Gate effect | blocking Gx, non-blocking through Gx, deferred to Gx |

Additional words in a cell qualify these states; they do not create a new
status system.

## Aggregate workstreams

| Workstream | Policy | Mechanism | Evidence | Implementation | Gate and next action |
| --- | --- | --- | --- | --- | --- |
| Repository, agent, context, and test readiness ([PLN-0000](../plans/0000-pre-implementation-readiness.md)) | Accepted execution governance, [test strategy](test-strategy.md), and [validation contract](validation-contract.md); not product architecture | Root `AGENTS.md`, bounded current context, thin Claude/Copilot adapters, canonical mise-task execution | Complete: PRE-001 through PRE-018 satisfied, PR-0017 through PR-0029 accepted, [EX-0016](../research/exercises/0016-agent-context-and-instruction-loading.md) passed, CI passed both profiles on a hosted runner with repeatability confirmed at the time it was measured | Complete and verified | G1 satisfied 2026-08-10; the plan is complete and **its mutation boundary remains in force**. Copilot is owner-deferred and unverified, so it must not be relied on for autonomous repository work |
| Reference-VM evidence slice ([PLN-0001](../plans/0001-reference-vm-slice.md)) | Bounded by the PLN-0000 mutation boundary, ADR-0001, ADR-0003, and the validation and hygiene contracts; accepts no mechanism | Direct systemd/UAPI composition with mkosi and a frozen Fedora 44 repository, all candidate fixtures | Complete: declaration, [composition](slice-composition-record.md), [boot](slice-boot-record.md), [identity](slice-identity-report.md), [failure evidence](slice-failure-evidence.md), [reconstruction](slice-reconstruction-record.md), and [evidence bundle](slice-evidence-bundle.md) | Complete; five registered slice tests carried into PLN-0002 | **Accepted complete by Jason Tarasovic 2026-08-11**, with the qualification that exit criterion 5 is met for six of seven injected faults. **SYS-018, SYS-041, SYS-059 accepted at `Partial`** and carried into G2 as inherited obligations; the gate-evidence amendment is post-acceptance evidence in [PR-0029](reviews/0029-g1-gate-approval.md). Open and the owner's: whether G1 should be revisited against the corrected trace |
| Authenticated `/usr` artifact format comparison ([PLN-0002](../plans/0002-usr-artifact-format-spike.md)) | Bounded by the same mutation boundary, ADR-0001, ADR-0003, DES-0006 and DES-0005 as amended 2026-08-11; selects no ecosystem, layout, or mechanism and does not accept its own recommendation | None selected. EROFS and ext4 are the two compared `/usr` candidates; the confext carve and tooling task 03a drew are candidate and hand back to DES-0005 and ADR-0003 | Active. Tasks 01, 02 complete; 03a and 04 partial; 05 accepted 2026-08-12, implemented, and audited against the built artifacts 2026-08-14 with three corrections taken and its two open parameters ruled; 06 complete and accepted 2026-08-14, six artifacts built and digests retained ([artifact set](usr-artifact-set.md)); 07 complete and accepted 2026-08-15, five of C-007's eight criteria measured offline ([measurements](artifact-format-measurements.md)); 08 complete and accepted 2026-08-15, boot behaviour and memory measured over three boots per arm and both are ties ([boot records](artifact-boot-records.md)); 09 complete and accepted 2026-08-15, corruption behaviour measured over four injections and it is the **first criterion to separate the arms** ([corruption records](artifact-corruption-records.md)); 10 complete and accepted 2026-08-15, seven cells per arm over 32 boots, image substitution failing closed and signature substitution failing open on every cell ([substitution records](artifact-substitution-records.md)), which completes every measurement task; 11 complete and accepted 2026-08-15, the five registered slice tests audited true on both arms with `T3-SLICE-004` and `T4-SLICE-002` registered and `T2-SLICE-002` widened to the comparison's own premise ([check updates](slice-check-updates.md)), and, on the owner's ruling of the same date, `T4-SLICE-003` and `T4-SLICE-004` registered **deferred** so task 10's `/usr` signature fail-open keeps a registered obligation after this plan closes; 12 **complete and accepted 2026-08-15** ([disposition](artifact-recovery-disposition.md)), splitting the recovery criterion into a measured format layer -- eight injection sites, a tie on file data and **ext4 ahead on metadata diagnosis**, where `fsck.erofs` detects a corrupt superblock and exits 0 anyway and sees nothing below it -- and a system layer deferred to verification items 3 and 5 as an accepted amendment to item 2, resolving `crypttab` as unsatisfiable because the artifact contains none, and owing PLN-0002-07 a correction -- `fsck.erofs --extract=X --path=<file>` writes to `X` itself and does not fail open. Task states and standing findings are in the [current context](current-context.md); detail in the [early-boot record](spike-early-boot-record.md), [composition record](usr-artifact-composition.md), [carve record](etc-path-carve.md), and [parameter declaration](artifact-parameter-declaration.md) | Active, VM-only. `check:complete` run green at 16 of 16 on 2026-08-15 against the EROFS primary, after PLN-0002-11 registered two checks; 18 registered, 2 of them deferred and never selected | G1 satisfied; implementation authorized only within this plan's disposable-VM scope. **Next action: 13** (the C-007 recommendation) and 14 (evidence bundle and DES-0006 disposition). No measurement task remains, and four of C-007's eight criteria separate the formats not at all. **03b is deferred rather than sequenced ahead of the measurement tasks** (2026-08-14): the fail-open its 2026-08-12 sequencing was meant to keep out of the measurements is closed and registered, and the plan's text says no task depends on it. **One owner ruling still qualifies it**: the ParticleOS command-line ruling of 2026-08-12, unimplemented and contradicted by the accepted declaration's own measured argument. Three others were settled 2026-08-14 -- amendment 5 **accepted**, so 06 builds six artifacts; `systemd.image_filter=` **ruled absent**, the premise making it load-bearing having assumed two artifacts visible to one boot when task 10 substitutes the disk; and the initrd module list **accepted as measured, not tightened**, since no C-007 criterion needs the trim and kernel content is `W-004`. No parameter inside the signed UKI is open. Standing risks: PR-0030 C-006, and PR-0029 C-005 |
| Product invariant and deployment substrate ([P-001](decision-backlog.md), [S-001](decision-backlog.md), [L-004](decision-backlog.md)) | Accepted lifecycle and deployment-set boundaries; DES-0001 in review | Direct systemd/UAPI composition leads; bootc is the required challenger | EX-0005 complete; substrate conformance comparison open | Not started | Blocking G2; G1 may use the leading candidate as a non-accepted fixture |
| State ownership and migration ([S-002](decision-backlog.md), [L-005](decision-backlog.md)) | Accepted | Concrete migration and recovery mechanisms open | State fixtures in EX-0008 and later role exercises are proposed | Not started | Non-blocking through G1 with disposable state; blocking applicable G2/G3 claims |
| Fleet intent and configuration ([S-003](decision-backlog.md), [C-001](decision-backlog.md)) | Accepted in ADR-0003; DES-0005 accepted, and its 2026-08-11 amendment makes signed confexts the only configuration delivery mechanism | TOML records, JSON Schema validation, literal native sources, canonical JSON evidence selected; confext build tooling and the path carve remain open | EX-0006 and EX-0007 complete | Not started, beyond PLN-0002-03a's candidate carve and confext | Non-blocking policy dependency for G1; implement only the minimal reference-VM slice |
| Storage, integrity, and encryption ([S-004](decision-backlog.md)) | Accepted boundaries; DES-0006 in review. **Scope resolved 2026-08-11**: C-013 makes the authenticated artifact `/usr`, and C-008 puts `/var` on the machine-state volume | EROFS and ext4 are the compared candidates for the `/usr` image (C-007, open); the state filesystem, partitions, encryption, and recovery mechanisms remain open. The tmpfs root is a fixture, not a decision | PLN-0002 is the active evidence; [EX-0008](../research/exercises/0008-reference-storage-layouts.md) proposed | Not started outside PLN-0002's disposable fixture | Disposable layout non-blocking through G1; exact layout blocks G2 and physical-host gates |
| Threat, trust, authority, and recovery ([S-005](decision-backlog.md), [S-006](decision-backlog.md)) | Core policy accepted; residual threat design in review. **Open sub-question raised 2026-08-14**: an untrusted `/usr` verity signer does not stop the boot, by upstream design, and enforcement sits at the TPM unseal | Separate authorities selected in ADR-0002; concrete custody and ceremony mechanisms remain | EX-0001 through EX-0003 complete; later hostile mechanism tests proposed | Not started | Synthetic/no-production authority is mandatory for G1; physical trust/recovery blocks G3/G4 |
| Package inputs and snapshot policy ([L-001](decision-backlog.md)) | Accepted | Fedora stable leads, currently with a declared systemd overlay; literal Arch snapshot is the required challenger | [EX-0009](../research/exercises/0009-package-input-closure.md) proposed | Not started | G1 may use a declared Fedora fixture; ecosystem selection blocks G2 |
| Supply-chain and vulnerability evidence ([L-002](decision-backlog.md)) | Accepted. **Open sub-question**: retention covers the image closure and not the tools closure | Exact formats, producers, scanners, and cost open | [EX-0010](../research/exercises/0010-representative-evidence-graph.md) proposed; PLN-0001 and PLN-0002 retention is the working evidence | Retention implemented as a build step in the slice | Minimal input/artifact identity blocks G1; full selected evidence set blocks G2 |
| Installation and enrollment ([L-003](decision-backlog.md)) | Accepted | `systemd-sysinstall` leads; direct composition, Ignition, and bootc installation challenge; protocol/records open | [EX-0012](../research/exercises/0012-first-enrollment-and-replay-tabletop.md) proposed | Not started | Deferred through G2 because G1 is disposable VM-only; blocks G3/G4. Machine identity provisioning is directed here rather than to any PLN-0002 fixture |
| Fleet rollout ([L-006](decision-backlog.md)) | Accepted | Minimal immutable records lead; larger coordinators remain challengers | [EX-0011](../research/exercises/0011-personal-fleet-rollout-tabletop.md) proposed | Not started | Local single-VM lifecycle non-blocking through G2; coordinated rollout blocks G3/G4 as applicable |
| Maintenance policy ([L-007](decision-backlog.md)) | Accepted | Single current line and best-effort response selected | Policy review complete; mechanism evidence joins package/supply-chain exercises | Not started | Non-blocking through G1; component inventory and response path block G2 support claims |
| Secrets and credential delivery ([C-002](decision-backlog.md)) | Accepted | systemd credentials default last mile; custody, envelopes, issuers, recovery, and exceptions open | [EX-0013](../research/exercises/0013-representative-credential-flow.md) proposed | Not started | Synthetic values only through G1; selected custody/recovery blocks physical-host gates |
| Unix identity and rootless workloads ([W-001](decision-backlog.md)) | Accepted | UID/sub-ID, classic versus homed, mappings, and migration open | [EX-0014](../research/exercises/0014-identity-mapping-and-restore.md) proposed | Not started | Disposable VM identity non-blocking through G1; exact ownership/migration blocks G3 and affected workload claims |
| MicroVM lifecycle ([W-002](decision-backlog.md)) | Open | Open | Not defined | Not started | Deferred through G2 unless the first slice adopts microVMs as a product workload rather than a test harness |
| Software placement ([W-003](decision-backlog.md)) | Accepted | Native release packages, mise, Flatpak, exact OCI images, and guests lead in their classes; defaults open | [EX-0015](../research/exercises/0015-software-placement-and-shadowing.md) proposed | Not started | Minimal release-only fixture non-blocking through G1; concrete role placement blocks G3/G4 |
| Kernel specialization ([W-004](decision-backlog.md)) | Open | General distribution kernel with initrd is the conservative fixture, not an accepted decision | Not defined | Not started | Deferred through G2; role evidence must justify any specialized/no-initrd production variant |
| Repository change flow and CI ([P-008](decision-backlog.md), [P-009](decision-backlog.md), [P-010](decision-backlog.md)) | Open on all three | QEMU is a fixture chosen without comparison ([RES-0013](../research/comparisons/vm-test-harness.md)); no corpus-maintenance mechanism selected ([RES-0016](../research/comparisons/record-corpus-maintenance.md)) | RES-0013 and RES-0016 complete | Validation runner and both canonical profiles implemented | Non-blocking under G1. **`main` is pushed and current**, with owner bypass enabled as a deliberate temporary state. **CI is red on `main` and stays red until there is something to continuously integrate**; a hosted runner has no composed artifact, so `check:complete` cannot pass there. Not tracked further. `P-010` is deliberately left open until after G2, with its observed failure rate as the accepted cost |
| Workstation role ([R-001](decision-backlog.md)) | Open | Open | Not defined | Not started | Deferred through G2; accepted capabilities, health, and recovery block G3 |
| Laptop role ([R-002](decision-backlog.md)) | Open | Open | Not defined | Not started | Deferred beyond current G4 scope |
| Router role ([R-003](decision-backlog.md)) | Open | Open | Not defined | Not started | Deferred through G3; accepted service, availability, health, and recovery block G4 |
| Server/storage role including `misc` ([R-004](decision-backlog.md)) | Open | Open | Not defined | Not started | Deferred beyond G2; add a dedicated gate when `misc` becomes an active target |
| MicroVM guest role ([R-005](decision-backlog.md)) | Open | Open | Not defined | Not started | Deferred through G2 and dependent on W-002 |

## Current critical path

The shortest safe path into implementation is:

```text
PLN-0000 complete 2026-08-10 (PRE-001 through PRE-018 satisfied)
  -> G1 approved 2026-08-10 (PRE-018, PR-0029)
  -> PLN-0001 accepted complete 2026-08-11: the bounded reference-VM slice
  -> PLN-0002 accepted 2026-08-11: the /usr artifact format comparison
  -> PLN-0002-06 complete 2026-08-14: six authenticated artifacts, digests retained
  -> PLN-0002-07 accepted 2026-08-15: five of C-007's eight criteria measured
  -> PLN-0002-08 accepted 2026-08-15: boot and memory measured, both a tie
  -> PLN-0002-09 accepted 2026-08-15: corruption measured, the arms separate
  -> PLN-0002-10 accepted 2026-08-15: substitution measured; the image binding
     holds and the signature binding is not a gate. The arms do not differ
  -> PLN-0002-11 accepted 2026-08-15: the registered checks audited against the
     /usr artifact, two added, and the signature fail-open registered deferred
  -> PLN-0002-12 accepted 2026-08-15: recovery ties on data, separates on
     metadata diagnosis, and is deferred at the system layer to items 3 and 5
  -> NOW: rule on 12, then 13 and 14; every measurement task is done
  -> collect substrate, package, storage, and identity evidence
  -> select mechanisms through ADRs
  -> G2: qualify the reference VM
  -> define and satisfy the workstation role gate
  -> G3: authorize an attended workstation trial
```

W-002, W-004 specialization, laptop, router, server/storage, and guest-role work
remain visible without falsely blocking the bounded G1 evidence prototype.

## Aggregate completion rule

The project is not “done” when every row says implemented; some workstreams are
intentionally deferred. A phase is complete when every row applicable to its
gate is either:

- satisfied with linked accepted decisions and evidence;
- explicitly non-blocking under the gate's bounded claims; or
- deferred to a named later gate with an accepted rationale.

No blank, merely old, or implicitly ignored row counts as a deferral.
