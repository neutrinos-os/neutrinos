---
id: PLN-0001
title: Reference-VM evidence slice
status: active
owner: Jason Tarasovic
created: 2026-08-10
last_updated: 2026-08-11
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
| SYS-018 | Partial | PLN-0001-06 injected seven faults; see the [failure evidence](../project/slice-failure-evidence.md). Responsible input, generated output, and lifecycle stage are identified at declaration, acquisition, resolution, composition, and artifact inspection. **Configuration scope is identified by none of them**: the slice has one machine, one role, and no precedence conflict, so no failure can attribute itself to a layer. No fault was injected after boot, because no later lifecycle stage exists |
| SYS-041 | Partial | **Downgraded from demonstrated by PLN-0001-07 measurement**, and awaiting owner acceptance. Reconstruction with the network removed succeeded and reproduced every stable identity, but only after a retention step the fixture does not perform: nothing retains the declared repository's metadata, so `--cache-only` cannot resolve and the offline claim held for this build root rather than for the slice. Only the acquisition half of the requirement was exercised in any case -- composition and boot need no publication service, discovery service, package repository, or WAN, while health recording, blessing, fallback, and deliberate rollback have no path here to test. See the [reconstruction record](../project/slice-reconstruction-record.md) |
| SYS-045 | Demonstrated | Immutable composition record with ordered inputs and tool identities |
| SYS-057 | Demonstrated | Declared distribution, branch, architecture, repositories, and precedence for every resolution |
| SYS-058 | Demonstrated by the builder only | Complete resolved binary package closure retained in `neutrinos-slice.manifest`. PLN-0001-04 found the running machine carries no package database and cannot verify this claim itself |
| SYS-059 | Partial | **Downgraded from demonstrated by PLN-0001-06 measurement.** Mixed branch fails closed: an `fc43` package under a `releasever=44` transaction, and a `Release=45` transaction over `fc44` packages, both fail GPG signature verification and name the offending package. The undeclared-repository half is **refuted**: replacing `LocalMirror=` with `Mirror=` admitted Fedora's `updates` repository, built a complete artifact with 45 of 104 packages from it, and passed `T3-SLICE-001`. Nothing checks that the enforcing construction is still present, and the retained manifest carries no per-package repository attribution to check against. See the [failure evidence](../project/slice-failure-evidence.md); two mitigations are proposed there and neither is accepted |
| SYS-065 | Demonstrated | Evidence records bind exact subject identities and literal formats |
| SYS-012 | Partial | Literal-artifact boot only; no emergency-release path exists |
| SYS-014, SYS-015 | Partial | Only the intent fields the slice requires; native escape hatch shown once |
| SYS-044 | Partial | `common < role < machine` precedence with a generic fixture role only |
| SYS-049 | Deferred to G2 | PLN-0001-04 measured the root filesystem mounted `rw`, and the earlier read-only-root claim was never true. **Owner decision 2026-08-10: out of scope for this plan.** Neither half is met and neither can be met here. The authenticated half needs an exact UKI-to-root/Verity binding whose substrate DES-0006 leaves open (`S-004`), so building it now would select a mechanism by implementation accident -- the failure [PR-0029](../project/reviews/0029-g1-gate-approval.md) C-005 names. A roothash in an unsigned UKI authenticates nothing, and the requirement's substitution clause needs a second deployment the slice does not build. The slice deliberately does not mount the root read-only either: that half alone is a two-line change and would make the requirement read as partly met while the half carrying the security value is absent |
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
| PLN-0001-01 | complete | — | `src/slice/input-set.toml`, `src/slice/schema/input-set-v2.schema.json`, and [input declaration](../project/slice-input-declaration.md) recording what makes each input exact. Instance validates; schema rejects nine constructed violations | Complete 2026-08-10. Now guarded by `T2-SLICE-001`, registered in PLN-0001-05; the record's unguarded-until-then caveat is discharged. PLN-0001-02 is next |
| PLN-0001-02 | complete | 01 | `src/slice/composition/mkosi.conf`, `src/slice/compose.sh`, and the [composition record](../project/slice-composition-record.md). 104-package closure from the single frozen repository; UKI, kernel, initrd, manifest, and file tree bit-identical across builds; disk image not reproducible, cause identified | Complete 2026-08-10. Built unprivileged with no host mutation. Disk-image variance traced to the randomly generated btrfs chunk tree UUID, for which `mkfs.btrfs` exposes no option, plus the FAT volume serial of the ESP; not fixable in configuration and not a requirement at this stage. Open: tools tree fetched with `--nogpgcheck`, no registered check. PLN-0001-03 is next |
| PLN-0001-03 | complete | 02 | [Boot record](../project/slice-boot-record.md). The unmodified artifact boots: 26 targets reached, zero failed units, vTPM found and `tpm2.target` reached. Console evidence by QMP screendump; journal recovered offline from the disk copy | Complete 2026-08-10. Stops at the interactive `systemd-firstboot` prompt and never reaches `multi-user.target`. Three composition gaps found and attributed to PLN-0001-02: no first-boot configuration, no kernel command line in the UKI so no serial console, no credential or autologin. Booted under TCG because loading `kvm-amd` would mutate the build host. Gaps authorized and fixed in PLN-0001-04 |
| PLN-0001-04 | complete | 03 | [Identity report](../project/slice-identity-report.md). Composition amended under owner authorization to close the three PLN-0001-03 gaps; the running machine reports kernel, systemd, distribution, command line, timezone, locale, hostname, and credentials matching composition, and the UKI on its ESP is bit-identical to the composed output | Complete 2026-08-10. `multi-user.target` reached, no failed units. Findings: the image has no package database, so package closure is not self-verifiable; the root filesystem is mounted `rw`, so SYS-049 is not demonstrated; systemd lacks TPM2 support. Correction recorded to PLN-0001-02's reproducibility method: `CleanPackageMetadata=auto` skips `directory` output, so the compared tree is not the shipped tree. PLN-0001-05 is next **Owner decision 2026-08-10: the composition amendment will be reverted once KVM works on the build host**, moving first-boot configuration, the console, and access to the harness via SMBIOS credentials and vsock ssh; PLN-0001-04 is re-run at that point. See [RES-0013](../research/comparisons/vm-test-harness.md). **Revert executed and re-run 2026-08-10** after SVM was enabled: `KernelCommandLine`, `Timezone`, `Locale`, `Hostname`, `RootPassword`, and `Autologin` removed; the rebuild reproduced the pre-amendment UKI `575c847d...`, initrd `e7061e25...`, kernel `4b37e4e5...`, and manifest `cb438999...` exactly, so the amendment was the only difference; `check:complete` `passing=10 failing=0` against the reverted artifact, with `T4-SLICE-001` reaching a login prompt under a harness-supplied hostname and no failed units. The vsock-ssh half is **not** done: nothing yet drives commands inside the guest |
| PLN-0001-05 | complete | 03 | `T2-SLICE-001`, `T3-SLICE-001`, and `T4-SLICE-001` registered in the existing runner, plus capability gating and `blocked` results the runner previously had no way to express | Complete 2026-08-10. `check:fast` 6/0 with no artifact; `check:complete` 9/0 with one declared. T2 reproduces the nine schema rejections the input declaration claims and closes the unguarded-record gap PLN-0001-01 recorded. T3 registers PLN-0001-04's central hand-made claim -- the UKI on the ESP is byte-identical to the composed UKI -- and was verified sensitive to a single flipped bit. T4 boots the literal artifact to a login prompt under a harness-supplied hostname, with no failed units and the artifact byte-identical afterwards, in 72s under TCG. **Consequence: `check:complete` fails with `blocked=1` unless `NEUTRINOS_SLICE_ARTIFACT_DIR` names a composed artifact**, because composition needs the network and canonical validation is offline. Guest-driven readiness over a notify vsock is deferred with the rest of the KVM-blocked work. **Open: the CI workflow runs `check:complete`, which a hosted runner cannot satisfy without a composed artifact.** Owner choice between composing in CI, running `fast` only in CI, or accepting a red `complete`; recorded with `P-008`. PLN-0001-06 is next |
| PLN-0001-06 | complete | 04, 05 | [Failure evidence](../project/slice-failure-evidence.md). Seven faults injected one at a time, each into its own copy of `src/slice`; the checkout was never mutated | Complete 2026-08-10. Six of seven failed closed and named their responsible input; diagnostics recorded verbatim. **Finding: the seventh did not fail.** Replacing `LocalMirror=` with `Mirror=` built a complete artifact with 45 of 104 packages from an undeclared repository and passed `T3-SLICE-001`. SYS-059 downgraded to partial and SYS-018 to partial above; both downgrades await owner acceptance. Second finding: the two mixed-branch fail-closed results come from Fedora's per-release GPG keys, not from anything in `src/slice` comparing an input to its declaration. Incidental: mkosi warns that `Seed=` is under `[Content]` and belongs under `[Output]`; not amended here. Evidence retained at `~/.cache/neutrinos/slice/evidence/pln-0001-06/`, 312 KiB. PLN-0001-07 is next |
| PLN-0001-07 | complete | 04 | [Reconstruction record](../project/slice-reconstruction-record.md). The artifact, both output directories, and all six VM state directories destroyed; rebuilt inside a network namespace with loopback only | Complete 2026-08-11. Every stable identity reproduced byte-for-byte -- UKI `575c847d...`, kernel `4b37e4e5...`, initrd `e7061e25...`, manifest `cb438999...` -- and the UKI read out of the reconstructed image's ESP matches the standalone UKI. Trees extracted from two disk images compare **13240 entries, zero differences**, which closes PLN-0001-04's "the compared tree is not the shipped tree" correction by measurement. `check:complete` `passing=10 failing=0` against the reconstructed artifact; `T4-SLICE-001` booted it in 15.8s, `READY=1` at 13.754s. **Two findings.** The fixture retains no repository metadata, so the first offline attempt failed to resolve and the retention had to be assembled by hand; SYS-041 downgraded to partial above. The shared package cache holds 58 RPMs that are not in the declared repository -- `fc43` packages and `updates` builds left by PLN-0001-06's faults -- so a cache shared across fault injection is not a retention store. The task's stated method was followed as written: the comparison is over the UKI, kernel, manifest, and a tree extracted from the disk image, not over the `.raw` digest and not over a `Format=directory` build. No exclusion for machine ID or boot ID was needed -- `etc/machine-id` ships as the literal `uninitialized`. PLN-0001-08 is next |
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
