---
status: active
last_updated: 2026-08-12
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
| Repository, agent, context, and test readiness ([PLN-0000](../plans/0000-pre-implementation-readiness.md)) | Accepted execution governance, [test and evidence strategy](test-strategy.md), and [validation execution contract](validation-contract.md); not product architecture | Root `AGENTS.md`, hard-bounded current context, thin Claude/Copilot adapters; test taxonomy and canonical mise-task execution/evidence/CI contract accepted; four tasks, Linux-x64 Python 3.14/uv locks, runner, failed-invocation result recording, output-safety quarantine, named T0 checks, and registered hostile/empty-cache probes implemented; repository conventions open | [EX-0016](../research/exercises/0016-agent-context-and-instruction-loading.md) passed Codex/Claude semantics, adversarial probes, freshness, discovery, and cold routing at `c96fdbb`; `T5-VAL-001` passed seventeen environment, result, cache-boundary, network, timeout, interruption, output-safety, and cleanup probes; `T5-VAL-002` passed with an empty isolated mise cache and no remote metadata on Python 3.14.7; PR-0017 through PR-0028 accepted; clean-clone profiles passed at `42f23b9`; pinned least-privilege CI passed both profiles at `d0a2cc5` in run `31418770417`, and repeatability was confirmed at `6ec625a` in runs `31420905770` and `31421167463`; PR-0029 accepted; Copilot owner-deferred and unverified | Complete | G1 satisfied 2026-08-10; PRE-001 through PRE-018 satisfied and the plan is complete. Its mutation boundary remains in force |
| Reference-VM evidence slice ([PLN-0001](../plans/0001-reference-vm-slice.md)) | Bounded by accepted PLN-0000 mutation boundary, ADR-0001, ADR-0003, and the validation and hygiene contracts; accepts no mechanism | Direct systemd/UAPI composition leads with mkosi v26 as candidate fixture; Fedora 44 frozen release repository candidate; all remain candidates | [Composition record](slice-composition-record.md): 104-package closure, reproducible UKI, unreproducible disk image, built with no host mutation; its two-build comparison measures the composition process, not the shipped tree. Planned evidence is the composition record, literal-artifact boot, identity report, injected-failure diagnostics, and offline reconstruction | Accepted and active on 2026-08-10 following [PR-0027](reviews/0027-reference-vm-slice-plan.md); the sole active implementation slice. `PLN-0001-01` through `PLN-0001-04` complete 2026-08-10: declared input set with schema, a deployment set composed unprivileged from one frozen repository, a [boot record](slice-boot-record.md) for the unmodified artifact, and an [identity report](slice-identity-report.md) from the running machine. The three composition gaps the boot found were owner-authorized and fixed; the machine now reaches `multi-user.target` with no failed units and every reportable identity matches composition, the UKI on its ESP bit-identically. Open findings: no package database in the image so closure is not self-verifiable; root mounted `rw` so SYS-049 is not demonstrated and is owner-deferred to G2; no systemd TPM2 support. `PLN-0001-05` complete 2026-08-10: `T2-SLICE-001`, `T3-SLICE-001`, and `T4-SLICE-001` registered in the existing runner, with capability gating and `blocked` results added to it. `check:complete` now requires a declared composed artifact and fails `blocked` without one. `PLN-0001-06` complete 2026-08-10: seven injected faults, [failure evidence](slice-failure-evidence.md) recorded. Six failed closed and named their responsible input; **the undeclared-repository fault did not fail at all** -- it built a complete artifact with 45 of 104 packages from a repository the declaration excludes, and passed `T3-SLICE-001`. SYS-059 and SYS-018 downgraded to partial in the plan trace, awaiting owner acceptance. The deferred composition revert was executed 2026-08-10 once SVM was enabled: the six PLN-0001-04 amendments removed, the pre-amendment UKI, initrd, kernel, and manifest digests reproduced exactly, `check:complete` `passing=10 failing=0`, and `T4-SLICE-001` down from 72 seconds under TCG to 18 under KVM. Notify-vsock readiness implemented the same day: `T4-SLICE-001` waits for `READY=1` from pid 1 at 13.2 seconds instead of a serial `login:` string at 15.4, reads the hostname from `X_SYSTEMD_HOSTNAME`, adds nothing to the image, and falls back legibly where `/dev/vhost-vsock` is absent. ssh over vsock is **not** done and is reopened as a question: it requires `openssh-server` in the image, changing the closure and every pinned digest, which is the shape of the amendment just reverted. `PLN-0001-07` complete 2026-08-11: the artifact, both output directories, and all six VM state directories destroyed, then rebuilt inside a network namespace with loopback only against a retained local copy of the declared repository. Every stable identity reproduced byte-for-byte, the UKI on the reconstructed ESP matches the standalone UKI, and trees extracted from two disk images compare 13240 entries with zero differences -- closing the correction that the earlier comparison measured the composition process rather than the shipped tree. `check:complete` `passing=10 failing=0` against the reconstructed artifact. **Two findings**: nothing in the fixture retains the declared repository's metadata, so the offline build was impossible until retention was assembled by hand, and **SYS-041 is downgraded to partial awaiting owner acceptance**; and 58 of 179 RPMs in the shared package cache come from outside the declared repository, left by PLN-0001-06's faults, so that cache is not a retention store. See the [reconstruction record](slice-reconstruction-record.md). Both findings were closed 2026-08-11 at owner request, together with the two F-RES-01 mitigations PLN-0001-06 proposed: `compose.sh` retains the declared repository's metadata and resolved packages as a build step, failing closed on anything that repository does not publish, and an offline rebuild from that retention reproduced all four digests with one flag; `T2-SLICE-002` asserts the mechanism still enforces the declaration and `T3-SLICE-002` attributes every NEVRA in the shipped closure to the declared repository's published index. `T4-SLICE-001` now records `accelerator_used` from QMP `query-kvm`, closing the gap where a silent TCG fallback left evidence indistinguishable from a KVM run. `check:fast` 8/0, `check:complete` 12/0. **The three downgrades were accepted at `Partial` by Jason Tarasovic on 2026-08-11** and none is amended by the mitigations: SYS-018, SYS-059, and SYS-041, all carried into G2 as inherited obligations, with the gate-evidence amendment recorded as post-acceptance evidence in [PR-0029](reviews/0029-g1-gate-approval.md). `PLN-0001-08` complete 2026-08-11: [evidence bundle](slice-evidence-bundle.md) retained outside the repository at 6310 KiB across 64 files, one SHA-256 per file, unsafe-output scan clean, and the requirement trace updated from planned to observed results. Closing measurement: the shipped tree extracted from three separately produced disk images -- one networked build and two offline reconstructions a day apart -- is byte-identical at 13240 entries. **All eight tasks are complete, and PLN-0001 was accepted as complete by Jason Tarasovic on 2026-08-11** against its exit-criteria assessment, including the qualification that criterion 5 is met for six of seven injected faults. Whether G1 should be revisited against the corrected trace stays open and is not taken by the drafter | G1 satisfied 2026-08-10 ([PR-0029](reviews/0029-g1-gate-approval.md)); implementation is authorized within this plan's bounded VM-only scope. Now blocking G2 |
| Authenticated `/usr` artifact format comparison ([PLN-0002](../plans/0002-usr-artifact-format-spike.md)) | Bounded by the same accepted PLN-0000 mutation boundary, ADR-0001, ADR-0003, DES-0006 as amended 2026-08-11, and DES-0005 as amended 2026-08-11; selects no package ecosystem, no partition layout, and no mechanism, and does not accept its own recommendation | None selected. EROFS and ext4 are the two compared candidates; the confext path carve and confext tooling task 03 draws are candidate and hand back to DES-0005 and ADR-0003 | Planned: an early-boot spike gating the rest, declared free parameters gating the builds, two artifacts measured against all eight DES-0006 verification item 2 criteria -- image size, build time, build determinism, boot behavior, memory, update transfer size, inspectability, corruption behavior -- plus a stated recovery-behavior disposition, negative evidence, and registered checks | **Accepted by Jason Tarasovic on 2026-08-11** following [PR-0030](reviews/0030-usr-artifact-format-spike-plan.md), and now the sole active implementation slice. PR-0030 found the first draft not fit to accept across twelve challenges; ten were resolved by restructuring and two by owner ruling on 2026-08-11 -- a tmpfs root for the fixture, and build determinism retained as one of eight criteria with no single winner. Task 01 is an early-boot spike with a hard stop-and-return gate, so the `/usr`-only boot path DES-0006 C-013 accepted is proven or the plan returns to review before anything further is built. Inherited from PLN-0001 as partial and carried into G2: SYS-018, SYS-041, SYS-059. SYS-049 stays partial and its demonstration is not claimed on substitution alone. Standing risk: PR-0030 C-006, since task 03 draws the first confext path carve and the first confext tooling, both candidate, with protection that is procedural rather than structural until DES-0005 takes the carve back | G1 satisfied ([PR-0029](reviews/0029-g1-gate-approval.md)); implementation authorized within this plan's bounded disposable-VM scope. **This cell is the aggregate view and deliberately does not restate the detail**: the running record is the [current context](current-context.md), with the `/etc` work in the [carve record](etc-path-carve.md) and the composition in the [composition record](usr-artifact-composition.md). Restating them here is what made this row stale for two days, which is `P-010`'s duplicated-state failure observed on this row. **Tasks 01 and 02 are complete**, 02 with a defect found and fixed; **03a, 04 and 10 are partial**, 10 having started out of order on an owner ruling; the rest are pending. **Task 01's stop-gate is not triggered**: an EROFS `/usr` authenticated by dm-verity, its root hash on a signed UKI, boots read-only to `multi-user.target` on a tmpfs root with no persistent storage, and a confext merges into `/sysroot/etc` before switch-root. **The finding that governs everything since is that this plan's mechanisms fail open silently**, now four times: lazy dm-verity booted a corrupt `/usr` normally, a refused confext left the machine unconfigured with no failed unit, an unenrolled confext signer merged anyway, and the initrd replay's fail-closed guard covers the initrd merge only. Three are closed and the fourth is carried to 03b by ruling. A successful boot is therefore not a statement about the artifact, which is why the negative evidence in tasks 09 and 10 carries the plan's weight rather than the positive boots. **Signature enforcement is closed and registered**: `--image-policy=root=signed` applied as a drop-in on `systemd-confext.service` admits the enrolled signer and refuses the valid-but-unenrolled one, measured across a 2x2 in a disposable VM with synthetic keys, registered as `T4-CONFEXT-001` and verified by injection. It covers the confext-substitution cell of task 10 for the signature dimension only. **Declared inputs are unchanged by the outage** that ran 2026-08-11 to 2026-08-12: `dl.fedoraproject.org` returned 403 for the declared repository and the retained copy composed offline rather than a declared URL being repointed at a mirror. The repository is reachable again and its revision matches the retained copy byte for byte. The systemd 261 overlay remains a declared local package overlay under input-set schema version 3, taken because Fedora 44 stays on systemd 259.x. Inherited from PLN-0001 as partial and carried into G2: SYS-018, SYS-041, SYS-059. SYS-049 stays partial and its demonstration is not claimed on substitution alone. Standing risk unchanged: PR-0030 C-006, the first confext carve and confext tooling are candidate, with protection that is procedural rather than structural until DES-0005 takes the carve back. **Two checks are open and unowned against the composed artifact**: `T3-SLICE-002` fails because attribution has no model of overlay provenance, so a legitimate declared input reads as unpublished and the `complete` profile cannot pass as a gate; and `T4-SLICE-001` fails on two systemd 261 TPM units, the known tss2 gap surfacing through new units. **Next action: PLN-0002-05's declaration**, which is the critical path -- 06 depends on it and 07 through 10 depend on 06 -- and which carries four accepted amendments: the kernel command line, the initrd, the initrd route question, and the verity signer's subject.
| Product invariant and deployment substrate ([P-001](decision-backlog.md), [S-001](decision-backlog.md), [L-004](decision-backlog.md)) | Accepted lifecycle and deployment-set boundaries; DES-0001 remains in review | Direct systemd/UAPI composition leads; bootc is the required challenger | EX-0005 complete; substrate conformance comparison remains open | Not started | Blocking G2; G1 may use the leading candidate as a non-accepted fixture |
| State ownership and migration ([S-002](decision-backlog.md), [L-005](decision-backlog.md)) | Accepted | Concrete migration and recovery mechanisms open | State fixtures in EX-0008 and later role exercises are proposed | Not started | Non-blocking through G1 with disposable state; blocking applicable G2/G3 claims |
| Fleet intent and configuration ([S-003](decision-backlog.md), [C-001](decision-backlog.md)) | Accepted in ADR-0003 | TOML records, JSON Schema validation, literal native sources, canonical JSON evidence selected | EX-0006 and EX-0007 complete | Not started | Non-blocking policy dependency for G1; implement only the minimal reference-VM slice |
| Storage, integrity, and encryption ([S-004](decision-backlog.md)) | Accepted boundaries; DES-0006 in review | EROFS root and Btrfs mutable state lead; exact partitions, encryption, and recovery mechanisms open | [EX-0008](../research/exercises/0008-reference-storage-layouts.md) proposed | Not started | Disposable layout non-blocking through G1; exact layout blocks G2 and physical-host gates |
| Threat, trust, authority, and recovery ([S-005](decision-backlog.md), [S-006](decision-backlog.md)) | Core policy accepted; residual threat design remains in review | Separate authorities selected in ADR-0002; concrete custody and ceremony mechanisms remain | EX-0001 through EX-0003 complete; later hostile mechanism tests proposed | Not started | Synthetic/no-production authority is mandatory for G1; physical trust/recovery blocks G3/G4 |
| Package inputs and snapshot policy ([L-001](decision-backlog.md)) | Accepted | Fedora stable leads; literal Arch snapshot is required challenger | [EX-0009](../research/exercises/0009-package-input-closure.md) proposed | Not started | G1 may use a declared Fedora fixture; ecosystem selection blocks G2 |
| Supply-chain and vulnerability evidence ([L-002](decision-backlog.md)) | Accepted | Exact formats, producers, scanners, and cost open | [EX-0010](../research/exercises/0010-representative-evidence-graph.md) proposed | Not started | Minimal input/artifact identity blocks G1; full selected evidence set blocks G2 |
| Installation and enrollment ([L-003](decision-backlog.md)) | Accepted | `systemd-sysinstall` leads; direct composition, Ignition, and bootc installation challenge; protocol/records open | [EX-0012](../research/exercises/0012-first-enrollment-and-replay-tabletop.md) proposed | Not started | Deferred through G2 because G1 is disposable VM-only; blocks G3/G4 |
| Fleet rollout ([L-006](decision-backlog.md)) | Accepted | Minimal immutable records lead; larger coordinators remain challengers | [EX-0011](../research/exercises/0011-personal-fleet-rollout-tabletop.md) proposed | Not started | Local single-VM lifecycle non-blocking through G2; coordinated rollout blocks G3/G4 as applicable |
| Maintenance policy ([L-007](decision-backlog.md)) | Accepted | Single current line and best-effort response selected | Policy review complete; mechanism evidence joins package/supply-chain exercises | Not started | Non-blocking through G1; component inventory and response path block G2 support claims |
| Secrets and credential delivery ([C-002](decision-backlog.md)) | Accepted | systemd credentials default last mile; custody, envelopes, issuers, recovery, and exceptions open | [EX-0013](../research/exercises/0013-representative-credential-flow.md) proposed | Not started | Synthetic values only through G1; selected custody/recovery blocks physical-host gates |
| Unix identity and rootless workloads ([W-001](decision-backlog.md)) | Accepted | UID/sub-ID, classic versus homed, mappings, and migration open | [EX-0014](../research/exercises/0014-identity-mapping-and-restore.md) proposed | Not started | Disposable VM identity non-blocking through G1; exact ownership/migration blocks G3 and affected workload claims |
| MicroVM lifecycle ([W-002](decision-backlog.md)) | Open | Open | Not defined | Not started | Deferred through G2 unless the first slice adopts microVMs as a product workload rather than a test harness |
| Software placement ([W-003](decision-backlog.md)) | Accepted | Native release packages, mise, Flatpak, exact OCI images, and guests lead in their classes; defaults open | [EX-0015](../research/exercises/0015-software-placement-and-shadowing.md) proposed | Not started | Minimal release-only fixture non-blocking through G1; concrete role placement blocks G3/G4 |
| Kernel specialization ([W-004](decision-backlog.md)) | Open | General distribution kernel with initrd is the conservative fixture, not an accepted decision | Not defined | Not started | Deferred through G2; role evidence must justify any specialized/no-initrd production variant |
| Workstation role ([R-001](decision-backlog.md)) | Open | Open | Not defined | Not started | Deferred through G2; accepted capabilities, health, and recovery block G3 |
| Laptop role ([R-002](decision-backlog.md)) | Open | Open | Not defined | Not started | Deferred beyond current G4 scope |
| Router role ([R-003](decision-backlog.md)) | Open | Open | Not defined | Not started | Deferred through G3; accepted service, availability, health, and recovery block G4 |
| Server/storage role including `misc` ([R-004](decision-backlog.md)) | Open | Open | Not defined | Not started | Deferred beyond G2; add a dedicated gate when `misc` becomes an active target |
| MicroVM guest role ([R-005](decision-backlog.md)) | Open | Open | Not defined | Not started | Deferred through G2 and dependent on W-002 |

## Current critical path

The shortest safe path into implementation is:

```text
PLN-0000 complete 2026-08-10 (PRE-001 through PRE-018 satisfied)
  -> PLN-0001 accepted 2026-08-10: the bounded reference-VM slice
  -> G1 approved 2026-08-10 (PRE-018, PR-0029)
  -> PLN-0001-01..06 complete 2026-08-10: inputs, composition, boot, identity,
     registered slice tests, injected-failure evidence
  -> PLN-0001-01..08 complete; PLN-0001 accepted complete 2026-08-11
  -> PLN-0002 accepted 2026-08-11: the /usr artifact format comparison
  -> NOW: G2 evidence -- substrate, package, storage, identity
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
