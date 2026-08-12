---
status: informative
last_updated: 2026-08-12
source_snapshot_revision: c163265
current_gate: G1
target_gate: G2
active_plan: PLN-0002 (accepted 2026-08-11; PLN-0001 complete 2026-08-11)
---

# Current project context

> Maintained, non-normative, self-contained cold-context artifact. For a
> read-only status/orientation/report task, rely on this file and do not open
> any path it cites. Exception: open one authority explicitly named by the
> user. Before edits, acceptance, or a high-risk claim, verify only the
> governing source. A conflicting source wins; correct this summary.

## Current position

NeutrinOS has an accepted architecture-policy baseline and **G1 is satisfied**:
approved by Jason Tarasovic on 2026-08-10 following PR-0029, which also
satisfies PRE-018 and completes PLN-0000
(`docs/plans/0000-pre-implementation-readiness.md`, status `complete`).

NeutrinOS source implementation is now **authorized, and only** for the
disposable VM/lab scope of accepted PLN-0002
(`docs/plans/0002-usr-artifact-format-spike.md`), which is the **active plan**
and the sole active implementation slice; PLN-0001 preceded it and is
complete. Both conditions of PLN-0000's mutation
boundary — G1 plus an accepted follow-on plan — now hold. Physical-host
mutation, production authority, and any mechanism ADR remain unauthorized, and
no candidate fixture became a decision.

Readiness history: EX-0016 passed at `c96fdbb`; PRE-012 and PRE-013 are
satisfied for the owner-approved Codex/Claude set. PRE-017 is satisfied
following PR-0028: the tracked baseline, licence, and secret scanning are
committed, the remote was force-pushed over an unrelated 2022 history and moved
to a ruleset requiring the `canonical profiles` check, and both profiles passed
on a hosted runner at `d0a2cc5`. Repeatability was then measured at `6ec625a`:
two independent green runs, `31420905770` and `31421167463`, both first-attempt
with no intervening fix, closing PR-0028 C-001.

PLN-0001-01 and PLN-0001-02 are complete. The slice declares its inputs in
bounded TOML validated by JSON Schema, and composes a bootable Fedora 44
deployment set unprivileged on `desktop-jason` with no host mutation, from a
single frozen repository enforced by mkosi's `LocalMirror`. The UKI, kernel,
initrd, package manifest, and the complete 7780-file tree are bit-identical
across builds. The disk image is not, and the cause is identified: the btrfs
chunk tree UUID is generated randomly and `mkfs.btrfs` offers no way to fix it,
so disk-image reproducibility is unreachable with a btrfs root regardless of
configuration. It is a goal, not a G1 requirement. An EROFS root would likely
be reproducible; that is a recorded hypothesis and not a reason to select
EROFS. See the [input declaration](slice-input-declaration.md) and
[composition record](slice-composition-record.md).

PLN-0001-03 is complete and **the artifact boots**: 26 targets reached, zero
failed units, virtual TPM found. It stopped at the interactive
`systemd-firstboot` prompt and never reached `multi-user.target`, so three
composition gaps were attributed back to PLN-0001-02 -- no first-boot
configuration, no kernel command line so no serial console, and no credential
or autologin. Booted under TCG: `/dev/kvm` is absent and loading `kvm-amd`
would mutate the build host. See the [boot record](slice-boot-record.md).

PLN-0001-04 is complete. The three gaps were **authorized by the owner and
fixed** in the composition fixture on 2026-08-10; the amendment changed
configuration only, leaving the package manifest and kernel digests and the
104-package closure unchanged. The machine now reaches `multi-user.target` with
no failed units, and **every identity it can report matches composition** --
kernel, systemd, distribution, command line, timezone, locale, hostname,
credentials -- with the UKI on its own ESP bit-identical to the composed
output. Three findings: the image carries **no package database**, so package
closure is not self-verifiable and rests on the builder's manifest alone; the
root filesystem is mounted `rw`, so **SYS-049 is not demonstrated** and the
plan's earlier read-only-root claim was never true -- owner-deferred to G2 on
2026-08-10, because the authenticated half needs a Verity substrate `S-004` has
not selected, a signature this slice has no authority to make, and a second
deployment to substitute; and systemd cannot use the
vTPM, because the tss2 runtime libraries are missing from the closure (systemd
itself is built `+TPM2`). A correction to PLN-0001-02's method is
recorded: `CleanPackageMetadata=auto` skips `directory` output, so the two
directory builds compared a tree that is not the shipped tree. See the
[identity report](slice-identity-report.md). mkosi and
Fedora remain candidate fixtures; one boot under emulation is not
qualification.

PLN-0001-05 is complete. Three slice tests are registered in the existing
runner: `T2-SLICE-001` validates the declared input set against its own schema
and reproduces the nine constructed rejections, closing the gap PLN-0001-01
recorded; `T3-SLICE-001` inspects the composed artifact and asserts the UKI on
the ESP is byte-identical to the composed UKI, which until now was a hand-made
claim; `T4-SLICE-001` boots the literal artifact under `snapshot=on` to a login
prompt whose hostname the harness supplied, with no failed units and the
artifact byte-identical afterwards, in 72 seconds under TCG. The runner gained
capability gating and `blocked` results, which it had no way to express. Two
consequences: `jsonschema` is now the repository's only runtime dependency, and
**`check:complete` fails with `blocked=1` unless `NEUTRINOS_SLICE_ARTIFACT_DIR`
names a composed artifact**, because composition needs the network and
canonical validation is offline. `check:fast` needs no artifact.

PLN-0001-06 is complete and produced the slice's first negative result. Seven
faults were injected, each into its own copy of `src/slice`; six failed closed
and named their responsible input, with the diagnostics recorded verbatim in the
[failure evidence](slice-failure-evidence.md). **The seventh did not fail.**
Replacing `LocalMirror=` with `Mirror=` in the composition fixture admitted
Fedora's `updates` repository -- which the declaration deliberately excludes as
inexact -- and built a complete artifact with 45 of its 104 packages from it.
`T3-SLICE-001` passed on that artifact. Two causes: no check asserts the
`LocalMirror=` construction is still present, and the retained manifest carries
no per-package repository attribution, so no check could verify sourcing even if
one wanted to. **SYS-059 is downgraded from demonstrated to partial and SYS-018
from demonstrated to partial; both were accepted at `Partial` by Jason
Tarasovic on 2026-08-11.** A second finding: the two mixed-branch faults fail closed on
Fedora's per-release GPG keys, not on anything in `src/slice` comparing an input
against its declaration -- an inherited guarantee, not an enforced one, and one
that does not survive a change of distribution. Two mitigations were proposed in
the evidence record and both were implemented on 2026-08-11; neither restores
SYS-059, because what the requirement asks for is per-package repository
attribution in the retained composition record and mkosi's manifest cannot
carry it.

PLN-0001-07 is complete and confirmed the identity claims while finding the
offline claim weaker than recorded. The artifact, both output directories, and
all six VM state directories were destroyed and the artifact rebuilt inside a
network namespace with loopback and nothing else, serving the declared
repository from a retained local copy. Every stable identity came back
byte-for-byte, the UKI read out of the reconstructed image's ESP matches the
standalone UKI, and trees extracted from two disk images compare **13240
entries with zero differences** -- which closes PLN-0001-04's correction that
the earlier comparison measured the composition process rather than the shipped
tree. `check:complete` `passing=10 failing=0` against the reconstructed
artifact, booting in 15.8 seconds. **Two findings.** Nothing in the fixture
retains the declared repository's metadata, so the first offline attempt could
not resolve at all and the retention had to be assembled by hand; **SYS-041 is
downgraded from demonstrated to partial in the plan trace and awaits owner
acceptance**, and only its acquisition half was exercised in any case. Second,
58 of the 179 RPMs in the shared package cache are not in the declared
repository -- `fc43` packages and `updates` builds left behind by PLN-0001-06's
injected faults -- so a cache shared across fault injection is not a retention
store. Nothing consumed them here. See the
[reconstruction record](slice-reconstruction-record.md).

Both findings, and the two F-RES-01 mitigations PLN-0001-06 had proposed, were
closed on 2026-08-11 at owner request. `compose.sh` now retains the declared
repository's metadata and the packages it resolved as a build step, into
`inputs/repository` under the build root, and **fails closed** on any package
that repository does not publish -- so retention is a check as well as a copy,
and the shared cache it used to draw from is out of the path. An offline
rebuild from that retention reproduced all four stable digests with one flag,
`--local-mirror=file://...`, and no assembled harness. Two tests were
registered: `T2-SLICE-002` asserts the composition mechanism still enforces the
declaration -- `LocalMirror=`, no `Mirror=` or `Repositories=`, matching branch,
and agreement of the values `compose.sh` duplicates -- and `T3-SLICE-002`
attributes every NEVRA in the shipped closure to the declared repository's own
published index, anchored to the declared `metadata_digest`. Both were verified
failure-sensitive, `T3-SLICE-002` against the exact `updates` package F-RES-01
admitted. `T4-SLICE-001` now records `accelerator_used`, read from the running
VM through QMP `query-kvm`, so a silent fallback to emulation is visible in the
evidence. `check:fast` is 8/0 and `check:complete` 12/0.

**None of this amends a requirement status.** SYS-018, SYS-059, and SYS-041
were **accepted at `Partial` by Jason Tarasovic on 2026-08-11**: the guards are
new, the measurements that produced the downgrades stand. SYS-018 cannot be
closed in a VM-only slice at all -- it needs a second role or machine -- and
SYS-059's gap is a limit of mkosi's manifest rather than of this configuration,
which makes it the first hard evidence bearing on mechanism selection and gives
it to `P-001`, `L-001`, and `L-004`. All three carry into G2 as inherited
obligations. The amendment to an approved gate's evidence basis is recorded as
post-acceptance evidence in [PR-0029](reviews/0029-g1-gate-approval.md); whether
G1's approval should be revisited against the corrected trace is left open
there. PLN-0001-08 is complete, and with it **all eight tasks of PLN-0001**. The
evidence bundle is retained outside the repository at
`~/.cache/neutrinos/slice/evidence/pln-0001-08/` -- 6310 KiB, 64 files, one
SHA-256 per file, scanned clean by canonical validation's own unsafe-output
patterns -- carrying the declaration, the mechanism, the resolved manifest, the
retention record, every output digest, three gzipped tree manifests, and both
profile runs in full. It carries no image: those are reconstructible from
declared inputs, and the commands that rebuild them are recorded instead. The
requirement trace is updated from planned to observed results. **Closing
measurement**: the shipped tree extracted from three separately produced disk
images -- the 2026-08-10 offline reconstruction, the 2026-08-11 networked
build, and the 2026-08-11 offline rebuild from retention -- is byte-identical
at 13240 entries with the same UKI on both ESPs. See the
[evidence bundle record](slice-evidence-bundle.md).

**S-004's scope half is decided.** On 2026-08-11 Jason Tarasovic accepted
DES-0006 C-013: the authenticated release artifact is **`/usr`**, not a
complete root. Configuration is delivered exclusively by dm-verity-signed
confexts under `image_policy_confext_strict` with mutable mode forbidden, and
the real `/etc` holds nothing durable, being regenerated at boot by
`systemd-tmpfiles` and `systemd-sysusers`. **No accepted requirement was
amended**: SYS-049 binds "release root content" without fixing its scope, and
both its evidence column and SYS-090 already treat configuration as a
deployment-set member distinct from root. SYS-123 now governs every confext.
Two things this does not settle: early-boot integrity, since the root
partition is unauthenticated state and anything read before `/usr` is verified
falls outside the boundary, and per-machine identity sourcing, which cannot
live in `/etc` and passes to L-003. The root *format* question (C-007, EROFS
versus ext4) stays open and is now measurable against the right artifact.
A side effect worth noting: the release artifact is no longer a disk image, so
the unreproducible btrfs and FAT bytes PLN-0001 identified move to state, where
reproducibility is not claimed -- a consequence of the decision, never a reason
for it.

**Two DES-0006 challenges are resolved**, both from RES-0014's review of
shipping A/B updaters, accepted by Jason Tarasovic on 2026-08-11 and now in the
design. C-014: the staging sequence
never marks the target slot ineligible before overwriting it, so on a second
update the retained eligible fallback becomes a partial image while still
selectable -- the outcome SYS-050 forbids, reached through ordinary operation.
C-015: the design carries only half of SYS-038, selecting a fallback on
exhaustion but never designing the "or stop with an attributable diagnosis"
half, so deployments that all fail assessment can alternate indefinitely.
Neither needs a requirement change. Two owner rulings on 2026-08-11 shaped
them, and neither accepts the amendments themselves. On C-014, durable
ineligibility targets surviving power loss, an unreadable ESP, **and** hostile
offline modification; surviving the first two is the accepted fallback, and
power loss alone is acceptable only with a recorded reason. On C-015, SYS-038
is read **narrowly** -- its bounded accounting governs each deployment's own
trial boots, not the cross-deployment loop -- so the loop breaker is a design
commitment beyond the requirement floor and must not be cited as satisfying
SYS-038. RES-0014 was extended with the terminal-state evidence behind it:
greenboot, MicroOS health-checker, Android Rescue Party, and ChromeOS converge
on stop selecting, keep running, be loud, and none halts the machine; MicroOS
additionally branches on whether the deployment was ever known-good, since a
previously-good deployment failing indicts the environment rather than the
image. A minimal ESP notification image was raised and rejected: it needs a
credential exactly when sealed state may be unavailable, and notification
belongs to the degraded running system. Both amendments are now in DES-0006:
C-014 as step 3 of "Staging and selection", C-015 as "When every eligible
deployment fails" in the same section, each with a failure-table row. The
spike inherits two cases from them -- the second-update overwrite of a retained
eligible fallback, and every eligible deployment failing assessment -- and owes
evidence on the strongest ineligibility durability level rather than the first
that works. Two questions are deliberately left unresolved: where the
exhaustion counter and known-good record live, given that state is what may be
damaged in the scenarios that trigger them, and what a machine running in an
unassessed condition is permitted to keep doing, router traffic in particular.

**C-008 is resolved and took the glossary with it**, accepted by Jason
Tarasovic on 2026-08-11. `/var` belongs to the machine-state volume, and every
remaining volume must name the custody, unlock, recovery, preservation, or
destruction difference that justifies it or be collapsed. Encryption scope was
never the question: `/usr` is public release content, dm-verity authenticated
and deliberately unencrypted, and `repart` cannot combine `Verity=` and
`Encrypt=` anyway. The actual defect was vocabulary -- C-013 left the word
**root** naming the superseded authenticated root, the new writable partition,
and the dm-verity root hash at once, and the glossary still defined only the
first. `root image` and `root slot` are retired in favor of release artifact
image and `/usr` slot, `root partition` is defined as the unauthenticated
writable filesystem holding the regenerated `/etc`, and bare **root** joins the
discouraged terms. A sweep followed and DES-0006's live prose is normalized,
with a note in the amendment explaining how to read the sections retained as
superseded record and why `root/Verity` is deliberate where recovery is
discussed -- the `/usr`-only scope was decided for normal deployments and was
never argued for recovery, which may still be a complete root. **Three surfaces
were deliberately left alone and are the owner's call.** Accepted requirements
SYS-030, SYS-049, and SYS-090 say "release-owned root content" and
"root/Verity"; C-013 already ruled that none needs amending because SYS-049
never fixed the scope, so editing their wording now would be a requirement
change dressed as a typo fix. DES-0001's artifact definition and DES-0008 use
`root image` generically, and rewriting another design's vocabulary from inside
a storage ruling is a scope crossing. Research, exercises, reviews, plans, and
slice records are evidence and history and keep the words they were written
with. One question is recorded rather than absorbed:
whether the root partition needs to persist at all, since a tmpfs would leave
nothing durable outside the ESP and the named state volumes and would enforce
the "nothing durable in `/etc`" rule by construction, against ParticleOS's
persistent encrypted `btrfs` root with `/var` as a subvolume. It changes the
partition count, so it is a decision, not a detail.

**DES-0005 now owns the confext lifecycle**, amended and accepted by Jason
Tarasovic on 2026-08-11. C-013 had made signed confexts the only configuration
delivery mechanism and named DES-0005 as the home of the SYS-123 lifecycle,
but DES-0005 contained no occurrence of confext, sysext, or extension and
covered three of nine obligations -- content identity, authorization, and
qualification. The other six were unowned for one coherent reason: the design
was written while configuration lived inside the deployment artifact, where
they cannot arise.

The accepted amendment settles all nine. **A deployment variant resolves to a
set of confexts, not one.** A 1:1 draft was rejected by the owner in the same
pass: it fused two costs, and while 1:1 is linear in fleet size rather than
combinatorial, binding each confext to an exact deployment identity forced
every machine's configuration to be rebuilt and re-signed on every `/usr`
release that changed nothing it contained, and made sharing impossible by
construction. Base compatibility is therefore a **guard**, not an identity
binding: `extension-release.d` declares a base level and blocks activation
against an incompatible `/usr`, while the deployment manifest continues to bind
the literal tuple, which is already C-001's answer to the hybrid problem. A
`/usr` release now requires re-qualification, not a rebuild.

**The split is by disjoint path ownership along consumer lines, never by
scope.** Splitting along `common`/`role`/`machine` would fail, because those
scopes overlap by construction -- machine scope exists to override role scope
for the same key -- so resolving them would need activation-time precedence,
which is the boot-time machine assembly DES-0005 already rejected and which
stays rejected. Precedence resolves at build time within each confext, and two
confexts claiming the same path is a composition-time error. Disjointness is
what makes merge order unable to change the effective result, so ordering
becomes a scheduling question rather than a semantic one. Reuse comes from two
machines legitimately having byte-identical subsystem configuration, which the
composition record can prove.

**Failure policy is declared per confext**, on owner direction, which is what
gives the split meaning beyond transport: required fails the trial boot,
optional marks the deployment degraded and unblessable, and neither may fall
back to `/usr/lib` defaults and report success. The declaration is authored in
the fleet inventory and only carried by the image, because an artifact
declaring its own criticality would authorize its own failure handling;
disagreement with the manifest is substitution and fails the gate. Unclassified
defaults to required. Rollback follows the deployment and never happens
independently. **Retention became a reference count** -- a confext lives while
any retained deployment names it -- and that is the one place sharing adds
machinery: collecting one because a single deployment was dropped could strip a
retained fallback that still needs it, which is C-014's SYS-050 violation
arriving through garbage collection instead of staging. Status enumerates every
merged confext and its declared policy rather than inferring them.

Left unsettled and named as such: confext build tooling, which belongs with the
ADR-0003 spike; per-machine identity and secrets, still `L-003`; the
unqualified-configuration test path, which genuinely conflicts with
`image_policy_confext_strict`; whether `Mutable=` could ever be argued back on
its own evidence; and **the actual path carve**, which is mechanically checkable
once drawn but which nobody has drawn. Verification items 11-19 were added,
including proving order-invariance by merging a set in several orders and
comparing effective configuration byte for byte.

**PLN-0001 is complete**, accepted by Jason Tarasovic on 2026-08-11 against
the exit-criteria assessment drafted in the plan, including its qualification
that criterion 5 is met for six of seven injected faults. One owner decision
stays open and is not taken by the drafter: whether G1's approval should be
revisited against the corrected trace.

**PLN-0002 is accepted** by Jason Tarasovic on 2026-08-11 and is the active
plan and the sole active implementation slice, succeeding PLN-0001. It answers
DES-0006 C-007 by measurement: the same package closure built as an EROFS
`/usr` artifact and an ext4 `/usr` artifact, each authenticated through
dm-verity with the root hash carried by a signed UKI, booted in a disposable
VM, measured against all eight criteria DES-0006 verification item 2 names,
plus a stated disposition for recovery behavior. It selects no package
ecosystem, no partition layout, and no mechanism, and it does not accept its
own recommendation. It runs under PLN-0000's mutation boundary, whose two
conditions -- G1 plus an accepted follow-on plan -- hold: disposable VM/lab
scope only, no physical-host mutation, no production authority, no mechanism
ADR. Task 01 is an early-boot spike with a hard stop-and-return gate, so the
`/usr`-only boot path C-013 accepted is proven or the plan returns to review
before anything else is built. Its first task order matters because the initrd
runs before the boot record the rest of the plan depends on.
[PR-0030](reviews/0030-usr-artifact-format-spike-plan.md) is accepted and
closed: twelve challenges found the first draft not fit to accept, the revision
resolved ten by restructuring, and two by owner ruling on 2026-08-11 -- a tmpfs
root for the fixture, and build determinism kept as one of eight criteria with
no single winner. **C-006 carries forward as the standing risk**: task 03a draws
the first confext path carve and builds the first confext tooling, both marked
candidate, and that protection is procedural rather than structural until
 DES-0005 takes the carve back.

**PLN-0002-01 is complete and the gate is not triggered.** The `/usr`-only boot
path C-013 accepted works: an EROFS `/usr` authenticated by dm-verity, its root
hash on a signed UKI's command line, mounted read-only onto a **tmpfs root with
no persistent storage at all**, reaching `multi-user.target`. The verity
generator derives both partition UUIDs from the root hash itself, so the command
line names a hash and the hash finds its own partitions.
`systemd-confext-sysroot.service` runs in the initrd, merges a confext into
`/sysroot/etc` before switch-root, and the merge survives. See the [early-boot
record](spike-early-boot-record.md). An inputs defect was found and ruled first:
Fedora 44 ships systemd 259.5 and stays on the 259.x series, while
`systemd-confext-sysroot.service` is new in 261, so the declared closure could
not exercise the mechanism C-013 names. **Owner ruling 2026-08-11**: take the
OBS `system:systemd` Fedora 44 build as a local package overlay, retained with
digests, so `LocalMirror=` keeps enforcing the single frozen repository by
construction; one fixture, no split. The overlay was verified to have landed in
both the manifest and pid 1 rather than assumed, F-RES-01 being the recorded
case of a substitution passing unnoticed. **Three findings are handed back and
none is taken by the drafter.** A tmpfs root leaves a separately delivered
signed confext nowhere to live, because the only search path that survives is
inside the authenticated artifact -- and a confext delivered beside the UKI
reaches only the initrd's `/etc`, which is discarded at switch-root. Read-only
`/etc` makes first-boot presets fail wholesale, so `dbus.socket` was never
enabled and four units failed; runtime unit enablement is therefore unavailable
and must move to composition or to a confext. And systemd announced `Missing
/etc/machine-id and /etc/ is read-only`, booting on a transient identity that
changes every boot, which is evidence for C-013's `L-003` deferral rather than a
resolution of it. The read-only `/etc` in all three is C-006 working as ruled --
and it holds **only while a confext is merged**, since without one `/etc` is an
ordinary writable tmpfs and the silent non-durability C-006 names would
return -- which was then measured directly, not argued: the refused-confext run
is the reference boot with one difference, and in it the write probe succeeded
and all twenty preset failures disappeared.

Failure capture is established for the rest of PLN-0002 (PR-0030 C-009), and
**two of three induced failures did not fail as the plan assumed**. A byte
flipped inside the authenticated `/usr` **booted normally**: dm-verity verifies
lazily, per block, on read, so nothing checked the block nothing read. The
diagnostic is precise once the block is touched -- `device-mapper: verity: 253:2:
data block 1000 is corrupted`, with `EIO` on the specific file -- but the
consequence is architectural: **a successful boot is not a statement about the
artifact**, for either format, so the harness now reads every file in `/usr` and
the reference does so cleanly. A refused confext, its base compatibility
declaring `ID=debian`, was correctly refused and **failed silently**: the unit
reported `Finished`, nothing failed, and the machine booted unconfigured, so
DES-0005's per-confext required/optional policy needs a mechanism that does not
exist in what was observed. Withholding the modules initrd fails closed in the
initrd at `Timed out waiting for device dev-mapper-usr.device`; an
EROFS-specific exclusion could not be expressed through mkosi v26's module
patterns in two attempts, both of which booted clean, so that case carries to
PLN-0002-09. Emergency mode is reached but unusable (`the root account is
locked`), and notify-vsock readiness does not apply to a pre-`/usr` failure,
which is why the harness treats a timeout as a result. Evidence retained outside
the repository at 416 KiB across 8 files with one SHA-256 each, unsafe-output
scan clean; the synthetic keys are deliberately kept for PLN-0002-10.

**PLN-0002-02 is done as work and blocked on evidence.** The composition now
produces a `/usr`-only tree: 1352 entries left `/etc`, which is where every one
of the PLN-0001 closure's release defaults landed and where a `/usr`-only
artifact would have lost them. A finalize script classifies each into one of
three dispositions and fails if it cannot -- relocated where the release
already has a `/usr` search path, so `*.wants` enablement moves to
`/usr/lib/systemd/system` and stops depending on the writable `/etc`
PLN-0002-01 found unavailable; discarded where the content configures building
rather than running; and otherwise moved to a generated tmpfiles factory that
replays it into `/etc` at boot. `/etc` is empty afterwards and the script
asserts it, so a package that later installs there fails the build instead of
vanishing from the artifact. Two defects were found by measurement rather than
review: a relative symlink that escaped its relocated tree shipped silently
broken, and merging into `/usr/share/factory/etc` silently overwrote four
package-owned files the closure itself ships there, so this task's content now
lives in `/usr/share/factory/neutrinos-etc` and every replay line names its
source. Measured after the fix, 1906 symlinks resolve and the two that do not
were already dangling in the flattened root. The systemd 261 overlay became a
**declared input**: schema version 3 adds `packages.overlays`, pinned file by
file with a SHA-256 and carrying a required `reason`, and acquisition reads
that declaration rather than a copy of it and fails closed before the build.
Retention keeps the two sources apart rather than mixing an overlay package
into the repository copy. See the [composition
record](usr-artifact-composition.md). **What is not verified is the artifact**:
`dl.fedoraproject.org` began returning 403 for the declared repository on
2026-08-11, and the tools tree -- rebuilt to gain `createrepo_c` -- can only be
built from it, so no build has resolved the closure and the overlay together.
The retained repository copy is what made the day's measurements possible at
all, which is the second time retention has been the difference between a
stalled afternoon and a stalled plan. Handed back: a factory-replayed `/etc` is
a populated tmpfs and still does not satisfy C-006.

**PLN-0002-04 is partial and PLN-0002-03 was blocked, both on the same
unruled question.** The disposable layout is promoted from the spike into the
slice composition and recorded as a fixture at creation: ESP, `/usr`, and the
verity partition, with the tmpfs root expressed as `root=tmpfs` on a kernel
command line that PLN-0001 had deliberately stripped -- structural, since
without it the artifact cannot mount its own `/usr`, and not a reversal of the
first-boot amendments that were reverted on reachability grounds. The
verity-signature partition is deferred to task 06 with the signing material it
needs. **The confext partition is not placed**, because placing it decides
where a separately delivered confext lives, and on a tmpfs root the only
surviving search path is inside the authenticated `/usr` -- which fuses release
and configuration and contradicts what DES-0005's amendment separates. Task 03
hits the same wall. Options for all three task-01 findings are now drafted for
owner ruling, with arguments and with what each would unblock, and none is
taken: see the [early-boot findings](early-boot-findings-for-decision.md).
Finding 2 is partly overtaken -- PLN-0002-02 moved release enablement into the
vendor `*.wants` path, so the presets that failed in the spike are enabled by
construction, which closes the symptom and not the general question.

**Prior art was surveyed while the repository outage blocked everything else,
and it weakened the drafted recommendation**
([RES-0015](../research/comparisons/stateless-etc-configuration-delivery.md),
2026-08-11). The crux question was stated before the survey ran: does anyone
mount a discovered partition into a confext search path inside the initrd,
before the merge? **No.** No surveyed image-based system delivers configuration
as a separately signed artifact into a stateless `/etc`; each gives `/etc` a
persistent writable backing instead. ParticleOS -- systemd's own reference
distribution, same authors as the mechanism -- has a persistent TPM-encrypted
btrfs root with `/var` as a subvolume, keeps `/etc` writable, presets units at
first boot, and **uses no confexts at all**. Upstream names `/var/lib/confexts`
as the primary install location, endorses `/run/confexts` for symlinks to
images held elsewhere, and on medium-confidence evidence validates confexts
against the same key as the EFI binaries -- which would buy independent
delivery and not independent signing. So a separate confext partition is novel
work rather than adoption, and the drafted argument was revised from "B for the
design" to "A or the `/run` variant for the design", D for this plan unchanged.
Extended the same day with a second question: a stateless `/etc` **is** run in
the field -- NixOS impermanence, and systemd's own `systemd.volatile=yes`,
which replaces the root with a tmpfs and mounts only `/usr` into it read-only,
almost exactly what `root=tmpfs` produces by another spelling -- but always
populated from a *generated* source rather than a delivered artifact. **No
deployment was found running a stateless `/etc` fed by confexts.** The pairing
NeutrinOS is building is unattested, which makes PLN-0002-01's early-boot
record the primary source rather than confirmation of a pattern. NixOS's
`system.etc.overlay.mutable = false` is the closest analogue and is marked
experimental; what breaks there is the same failure NeutrinOS's finding 2
records -- `systemctl enable` returning "Read-only file system", sysusers and
`mutableUsers` forced to match `/etc`'s mutability. The answer that community
gives adds a mechanism finding 2 did not have: **systemd generators**, writing
unit symlinks into `/run/systemd/generator*` with no writable `/etc` at all.
Two further things the survey found and NeutrinOS has no position on:
`systemd.image_policy=` states per-partition integrity requirements on the
signed command line, and ParticleOS's tmpfiles factory uses `L` symlinks rather
than the `C` copies PLN-0002-02 generates, on the stated grounds that copies do
not propagate across a `/usr` update. Both are in front of the owner and
neither is taken.

**Owner ruling 2026-08-11 on finding 1: option D for this plan.** The confext
lives at `/usr/lib/confexts` as a declared measurement fixture; PLN-0002
measures formats and not delivery. The design question is explicitly not
settled and moves to the proposed PLN-0002-03b. The fixture must be declared in
the task text of the task that builds it, and any later task whose argument
depends on where the confext lives stops and returns to the finding.

**PLN-0002-03 is split, accepted by Jason Tarasovic on 2026-08-11**:
`03a` builds and carves on a delivery path declared a fixture in the task text
and is unblocked once the repository is reachable; `03b` takes the delivery
question with RES-0015 as its evidence and is on no other task's path. The task table and every downstream
reference are updated; the reasoning is kept in the plan's amendment section.

**A second amendment is accepted the same day: PLN-0002-05 is widened to the
kernel command line.** Task 05 is the plan's declaration gate, and its
enumerated parameter set is filesystem parameters only -- so the command line,
which affects boot behavior and memory and which lives *inside the signed UKI*,
would stay an inherited fixture through the measurements that decide C-007. It
declares `root=tmpfs` against `systemd.volatile=yes`,
`systemd.image_policy=`, `systemd.image_filter=`, `systemd.confext=`, and the
`usrhash=` mkosi injects, each with the alternative not chosen and the reason.
`systemd.image_policy=` matters most: NeutrinOS currently asserts `/usr`
integrity by having mounted it, which PLN-0002-01 already showed to be the
unsafe claim when a corrupt artifact booted normally because dm-verity is lazy.
**Deadline before PLN-0002-06**, since a command-line change after 06 voids
tasks 07 through 10.

**`C` versus `L` is ruled: owner ruling 2026-08-11, the default is `L` and the
exceptions stay open.** `mkosi.finalize` now states a disposition per path --
60 linked against 8 copied on the retained closure -- so the paths a confext or
a machine must contribute *into* rather than replace can be completed in
PLN-0002-03a as a data change. Leaving the whole question open would not have
been neutral: the script emitted `C` for everything, so copy would have won by
inaction. The `C` exceptions are `machine-id`, the six `systemd-sysusers` files,
`adjtime`, and `ld.so.cache`, each because a running system writes them. This
partly overtakes the C-006 handback: a linked path resolves into read-only
`/usr`, so the write fails on the artifact's integrity boundary rather than only
while a confext is merged -- for 60 of 68 entries, and reasoned rather than
measured until a build confirms it. The drafting found that ParticleOS's
stated reason -- copies go stale against a later `/usr` -- **does not transfer**,
because NeutrinOS regenerates `/etc` from the current factory at every boot. The
two arguments that do apply are stronger: under `L` a write to `/etc` fails on
the read-only verity boundary, which makes C-006 a property of the artifact
rather than of the current overlay state, and copies occupy tmpfs while
symlinks do not, which touches a measured criterion. The costs are granularity
-- `L` on a directory forecloses per-machine contribution into it, which ties
the decision to PLN-0002-03a's carve -- and the paths that must remain real
files, `machine-id` above all -- which is why the exception list is expressed
and left incomplete rather than closed. Confirmation waits on the repository.

**The repository outage stopped blocking builds on 2026-08-11**, without
changing a declared input. The composition now builds **entirely offline** from
three things already on disk: the retained repository copy as
`--local-mirror=file://`, the retained systemd 261 overlay, and the tools tree
the PLN-0002-01 spike built before the outage. That last is a *reuse* of a
declared input rather than a rebuild, and it is justified by a declaration
rather than a comparison: the tools-tree package list and pinned base-image
digest in `compose.sh` and `spike.sh` are byte-identical, because PLN-0002-02
added `createrepo_c` to the slice recipe and thereby removed the spike's stated
reason for a separate tree. It was not rebuilt, so it is not verified
byte-for-byte, and the repository was unreachable to check at the time.
Switching `LocalMirror=` to the `download.fedoraproject.org` redirector, which
served the path with a 200, was **not** taken: it would change a declared input
to route around an outage. **Both open ends are now closed** -- the outage
ended on 2026-08-12 with the declared repository serving `repomd.xml` again at
the same revision as the retained copy, and the reuse question is ruled the
same day: consolidate on the slice tree, confirmed by a rebuild rather than by
the identical declarations alone.

**PLN-0002-02's blocker is therefore closed**: the `/usr`-only artifact exists
and the systemd 261 overlay is in its manifest, which is the exact thing task 02
was waiting on. The artifact is a 246.7M EROFS `neutrinos-usr` with a 64M
`neutrinos-usr-verity` and a 512M ESP, `/etc` empty and asserted so, and a
generated factory fragment of **68 entries, 59 `L` and 9 `C`** -- correcting the
ruling record's pre-build estimate of 60 and 8.

**PLN-0002-03a drew the carve, found two collisions, and both were ruled and
then measured the same day**: see the [carve record](etc-path-carve.md).

The carve is provisionally accepted: one confext, `neutrinos-network`, owning
`/etc/systemd/network/`, with machine identity deliberately excluded because
giving `/etc/machine-id` to a confext would resolve `L-003` by task convenience.
It collides with nothing, and the reason is a correction worth keeping: the
first analysis reasoned from the retained repository's file list, which
describes systemd **259.5**, while the artifact ships the **261 overlay**, and
261 keeps its defaults in `/usr/lib/systemd` so `/etc/systemd` never reaches the
factory at all. The declared repository's index is not the artifact's file list
wherever an overlay replaces a package.

**Collision 1**, that `L` links a whole directory so a confext owning a path
inside one silently replaces it, is **ruled A** -- emit factory lines deeper
where a carve enters -- and is **not implemented**, because this carve does not
enter a factory directory. It binds the next carve; `/etc/ssh` is the nearest
case and goes live the moment the closure gains an sshd.

**Collision 2 is the substantial one and is now measured across four boots.**
With a confext merged under stock ordering, the factory replay **fails
wholesale**: `/etc` holds 2 entries instead of 74, there is no `/etc/passwd`, no
`/etc/os-release`, no `/etc/machine-id`, no D-Bus, sysusers is skipped, and 8
units fail -- while `systemd-tmpfiles-setup.service` reports `Result=success`
having exited 65, the same silent-failure shape PLN-0002-01 recorded for a
refused confext. The cause is architectural rather than an ordering slip:
`systemd-confext.service` declares `Before=sysinit.target
systemd-tmpfiles-setup.service`, so **systemd's model is that `/etc` is already
populated when a confext merges**, which is true of every system RES-0015
surveyed and false of NeutrinOS. That is the mechanical reason nobody runs the
pairing RES-0015 could not find in the field. **Owner ruling 2026-08-11: A, with
B measured alongside.** B was measured and fails -- ordering the merge after the
replay produces an ordering cycle that systemd breaks by *deleting the merge
job*, so the machine boots with nothing merged and reports nothing wrong. A was
measured and works: an initrd unit running `systemd-tmpfiles --root=/sysroot
--create` before `systemd-confext-sysroot.service` yields the confext merged,
59 factory symlinks replayed, `/etc/os-release` readable, sysusers finished,
`/etc` read-only, and one failed unit. A is also the option that does not fight
upstream, which is a better argument than the one originally drafted for it and
was only available after B failed. Two residuals: the replay unit exits non-zero
on partial tmpfiles failures and needs a stated success criterion, and the entry
count is 73 against the baseline's 74, unattributed.

**A defect in PLN-0002-02 was found by the baseline boot**: five release paths
shipped as **dangling symlinks**, `/etc/os-release` among them, because the
finalize script applied its `retarget` fix to relocated entries and never to
factory entries. `head /etc/os-release` failed on the running machine. The fix
calls the existing function, and the rebuild resolves all seven. Two things
carry: the composition record's "1906 resolve, 2 do not" measurement missed it
because it encoded the same assumption as the bug, and systemd's own
`etc.conf` handles four of these paths correctly while the generated fragment
sorts first and silently overrode it. Whether the fragment should skip paths
upstream already owns is open and belongs to task 02.

**Both of 03a's remaining deliverables have since landed, and each found
something.**

The confext is now a **signed 3-partition DDI**, built by `compose.sh` from
`src/slice/confext/neutrinos-network/` and staged into `/usr/lib/confexts` with
its certificate in `/usr/lib/verity.d`. It merges. **Its signature is not
enforced**: dm-verity resolves the signing key through the *kernel keyring*, not
a file, a synthetic key is in no keyring, the kernel returns `-ENOKEY`, and
systemd retries unsigned and merges. `--image-policy=root=signed` did not close
it. This is the **third mechanism in this plan to fail open silently**, after
lazy dm-verity booting a corrupt `/usr` and a refused confext reporting
`Finished`, and it predicts **PLN-0002-10's confext substitution will pass**.
Enforcement needs a synthetic key enrolled in the disposable VM's own firmware,
which the plan permits and nobody has done.

The **initrd replay unit is now repository content** --
`src/slice/composition/initrd/`, packed into a cpio by
`mkosi.finalize.d/10-initrd-etc-factory` and handed to mkosi through
`$ARTIFACTDIR/io.mkosi.initrd`, because mkosi offers no way to put a file in its
default initrd (`ExtraTrees=` is not inherited by the synthesized
`default-initrd` image). Shipping it exposed three defects the credential probe
could not: `--root=` does not redirect NSS, so a full `--create` exits 65 on
group lookups against the initrd's own database; a positional config path is not
`--root=`-relative, so the fragment must be named `/sysroot`-prefixed; and a
`RemainAfterExit` oneshot survives switch-root as `not-found failed` unless it
conflicts with `initrd-switch-root.target`. It now boots with **zero failed
units**, `/etc` at 70 entries, read-only, `os-release` readable.

The PLN-0002-05 declaration 03a owed for this change is **drafted as PLN-0002
amendment 3, accepted 2026-08-11 by Jason Tarasovic**. Acceptance binds the
*obligation to declare* and selects no route or module list; the declaration
itself is task 05's, still due **before PLN-0002-06** because
the initrd is inside the signed UKI. Drafting it enlarged it. mkosi's default
initrd **is** `mkosi-initrd` -- `finalize_default_initrd()` parses
`resources/mkosi-initrd` in place, so it is package-based, not dracut -- and
its `KernelModules=` list ships **both `erofs` and `ext4`**. So each arm
currently carries the other arm's driver, which is PR-0030 C-003's named
outcome ("both drivers ship in both arms and neither artifact is the one that
would ship") measured rather than predicted. The additive
`$ARTIFACTDIR/io.mkosi.initrd` route cannot express a per-arm module list, so
task 05 now carries a route question: keep it and declare a shared list, or
move to a `mkosi.images/initrd/` subimage with `Include=mkosi-initrd`. The
drafter recommends the subimage and does not rule.

The four paths the narrowed replay no longer establishes before the merge
(`/etc/mtab`, `/etc/pam.d`, `/etc/credstore`, `/etc/credstore.encrypted`) are
**ruled 2026-08-11 by Jason Tarasovic**: they become the first named entries of
the `C`/`L` exception list and the general case passes to PLN-0002-03b and
DES-0005. They stay absent meanwhile -- `/etc` at 70 entries, zero failed
units -- and the replay is deliberately **not** widened to systemd's own
`etc.conf`, which would re-open the exit-65 NSS failure. Whether the two
credstore paths are separable from the other two, being C-002/DES-0011
territory, is carried as a named sub-question rather than dropped.

**Still owed by 03a**: signature enforcement, now under way. The keyring
question is **verified offline** against the kernel under test
(`kernel-core 6.19.10-300.fc44`, matched to the artifact manifest):
`CONFIG_DM_VERITY_VERIFY_ROOTHASH_SIG_PLATFORM_KEYRING=y` with
`CONFIG_LOAD_UEFI_KEYS=y`, so a certificate enrolled in the disposable VM's own
UEFI `db` reaches the keyring dm-verity reads. **Owner ruling 2026-08-11: db
enrollment, both keys built now.** MOK is not needed and is worse here, since
`CONFIG_INTEGRITY_CA_MACHINE_KEYRING_MAX=y` admits only CA certificates to
`.machine`. Both synthetic keys now exist outside the repository and are
generated by `compose.sh` -- the signer, and a second valid-but-unenrolled key
so PLN-0002-10 can tell a substitution failure from a signature failure. Secure
**Measured 2026-08-11 in a disposable VM, four boots**, artifact digest
unchanged throughout. Two harness defects were found first and the first is
material beyond the probe: `src/spike/pln0002-01/boot.sh` boots
`OVMF_CODE.4m.fd`, **the firmware build with no Secure Boot support**, so no
`db`, `SetupMode` or `SecureBoot` variable exists and no certificate could ever
have reached the kernel. Every earlier signature statement in this plan was
measured where the mechanism was structurally absent. On
`OVMF_CODE.secboot.4m.fd`, **mkosi auto-enrolls its own Secure Boot keys** from
`\loader\keys\auto` on the ESP and Secure Boot comes on by itself
(`SecureBoot=1`) -- undocumented in the plan and relevant to PLN-0002-05.

**Fixed 2026-08-11.** `boot.sh` now boots the Secure Boot firmware, takes a
warm-up boot first (auto-enrolment reboots, and `-no-reboot` would otherwise
end qemu before the report unit runs), and **reports `SecureBoot` and the
`.platform` keyring in the report itself** -- the defect hid because the
harness could not say whether the mechanism was present. Re-measured on the
unchanged PLN-0002-01 artifact: `SecureBoot=1`, `.platform: 1`, and every other
line of the early-boot report unchanged, so the record in
[spike early boot](spike-early-boot-record.md) stands as written. **The
firmware state is now asserted, not just printed** -- `boot.sh` fails if the
report does not show `SecureBoot=1` and a `.platform` keyring, since a printed
fact nothing checks is how this was lost. Verified by injection: restoring the
old firmware path exits 1 with `SecureBoot is 'unreported'`. The assertion is
skipped when no report ran, because a boot that never reaches userspace is a
result `faults.sh` exists to produce; a firmware regression is still caught,
because the non-secboot build boots fine and runs the report. What the
spike claims about verity, the confext merge, and `/etc` writability did not
depend on the firmware; only the signature statements did.

With that firmware the keyring route is confirmed: `db` loads into
`.platform`, `.machine` stays empty as the CA restriction predicted, and
rebuilding the ESP's `db.auth` as a two-certificate list puts the verity
certificate in `.platform` alongside mkosi's.

**Enforcement is still not demonstrated, and the evidence now says it is
absent.** Control and enrolled boots differ only in whether the confext's
signer is in `db`, and the confext **merges in both**, with no `ENOKEY` either
way. A merge indifferent to whether its signer is trusted is not a validated
merge: this is the **fourth** fail-open observation in this plan and the first
with the trust anchor present rather than missing. Secure Boot being on by
default removes the question of whether to enable it.

**The negative control has since been run and settles it.** Two confexts from
one source differing only in signer -- one signed by the certificate in `db`,
one by the valid-but-unenrolled second key -- delivered through `/run/confexts`
into the same artifact, so this measures the **system** merge. The enrolled
signer produces no kernel error; the unenrolled one produces
`device-mapper: table: verity: Root hash verification failed (-ENOKEY)` and
`error adding target to table`. **Both then merge**, `systemd-confext refresh`
exits 0 in both, and `/etc/systemd/network/10-neutrinos-default.network` is
present in both. So signature validation *does* happen once a key is enrolled
and the kernel *does* discriminate -- and systemd falls back to unsigned verity
and applies the untrusted configuration anyway. The mechanism is **available,
working, and not enforcing**; the fallback is the defect, not the key. The plan
now also has a harness that discriminates, so any candidate fix (image policy,
dissect option, systemd version) can be tested against a pair known to differ
only in signer.

**That fix has now been found: `--image-policy=root=signed`.** Eight boots, one
policy per fresh boot, everything else held. Passed on the `systemd-confext`
command line it admits the enrolled signer and refuses the unenrolled one --
exit 1, nothing merged, `/etc/systemd/network/` absent. `root=verity` merges
both, so `signed` is the flag that reaches the validation result; `=signed`
refuses **both**, including the correct artifact, so the designator has to be
named and the broad spelling is an outage rather than a control. Two limits,
both recorded in [the /etc carve](etc-path-carve.md): this is the system merge
through the CLI, not the initrd merge, and **the drop-in form of the same flag
was measured earlier as not closing** -- the contradiction is unresolved, and
the unit-configured form is the one NeutrinOS would ship. So PLN-0002-10 now
injects against a *configuration* rather than a missing mechanism, and the plan
should say which.

**The slice was recomposed 2026-08-12 with the repository back up**, and the
run produced two failures and one defect, none of them in the artifact itself.

The composition succeeded: 103-package closure, UKI `848fb8ea...` matching its
ESP copy byte-for-byte, both confexts built -- the enrolled one and the one
signed by the unenrolled key -- and retention of 121 packages plus repository
metadata. `T2-SLICE-001`, `T2-SLICE-002` and `T3-SLICE-001` pass against it.

**`T3-SLICE-002` fails**: the six systemd 261 packages in the shipped closure
are "not published by the declared repository". They are the declared OBS
overlay, so this is not an undeclared input -- it is the attribution check
having no model of overlay provenance. Retention records
`overlay_package_count: 0` because it matches names against the package cache
and the overlay arrives through `--package-directory` instead, so the overlay
is never attributed to anything. This is the **first complete-profile run since
the 261 overlay entered the slice composition**; PLN-0001-07's 12/0 predates
it. Failing closed is the right direction, but the check currently cannot pass
on a legitimate declared input, which makes it unusable as a gate until either
retention covers the overlay or attribution learns about it. **Open, unowned.**

**`T4-SLICE-001` fails**: two units, `systemd-pcrproduct.service` (TPM NvPCR
Product ID Measurement) and `systemd-tpm2-setup-early.service`. Both are
systemd 261 additions and both are consistent with PLN-0001-04's standing
finding that the tss2 runtime libraries are absent from the closure while
systemd itself is built `+TPM2`. So the boot regression is the known TPM gap
surfacing through new units rather than a new defect -- but the artifact no
longer boots with zero failed units, which is what that check asserts. **Open,
unowned.**

**A defect of mine, found and fixed by this run.** `compose.sh` staged the
T4-CONFEXT-001 fixture *before* retention; the fixture step failed, `set -eu`
aborted, and **retention silently did not run** -- the step that makes the next
offline rebuild possible at all. Reordered after retention, and verified on the
re-run. A step added for a new check must not be able to take out an
established one.

**The slice-side fixture is blocked on PLN-0002-06, not on the outage.**
Enrollment needs an image-signing certificate to keep in `db` beside the verity
signer, and **the slice composition declares no `SecureBoot=` at all**, so the
UKI is unsigned and there is nothing to keep. Enrolling regardless produces a
machine whose firmware refuses its own UKI. `compose.sh` now says so and
continues; the fixture's absence still **blocks** `T4-CONFEXT-001`, which is
the same signal in the place that reads it.

**The canonical runner cannot reach any of these checks locally.** Two
independent causes, both pre-existing: `sandbox.deny_env = true` strips the
declared-directory variables under `mise run`, and running the runner directly
fails its own environment rule because `uv run` injects `LC_CTYPE`. The results
above were obtained by invoking the check functions in-process, which is
**evidence, not a canonical run**.

**PLN-0002-10 is started out of order**, on the owner ruling that this check
belongs to it: `T4-CONFEXT-001` covers the **confext-substitution cell, for the
signature dimension only**. The rest of task 10's row -- `/usr`, Verity, and
manifest substitution, a wrong-but-valid key against the artifact rather than
the confext, and the C-001 cross-product enumeration -- still needs task 06's
four artifacts, and task 06 needs task 05's declaration. **The declared Fedora
repository is reachable again** (checked 2026-08-12, `repomd.xml` HTTP 200) and
its revision `1776864872` is identical to the retained copy, so the outage no
longer blocks composition and the unrun slice-side fixture can be built.

**`T4-CONFEXT-001` is registered and landed, 2026-08-11**, in the `complete`
profile: `tools/validation/confext_policy.py`, five boots of which four are
measured, asserting the 2x2 rather than the happy path. Verified by injection
as well as by passing -- swapping the unenrolled confext for the enrolled one
fails it, and restoring the non-secboot firmware fails it in all four cells.
`src/slice/enroll-fixture.sh` builds the enrolled artifact copy as a declared
build step; the artifact itself is never written. Two limits: it is
**unreachable through `mise run`** because `sandbox.deny_env` strips the
declared fixture directory -- pre-existing and shared with `T3-SLICE-001`,
governed by the validation contract -- and the **slice-side fixture is unrun**,
since this host has no slice tools tree, so it was exercised against the
PLN-0002-01 spike artifact instead and the `compose.sh` wiring is written but
not executed.

**Ruled 2026-08-11 by Jason Tarasovic**, on the draft registration of
`T4-CONFEXT-001`: the check tests the **unit** form, and it lands **as part of
PLN-0002-10** rather than before it. The ruling landed on the form previously
recorded as not closing, so it was measured before being recorded as settled --
three boots, digest unchanged, policy applied as a drop-in overriding
`systemd-confext.service`'s `ExecStart` and confirmed in effect by
`systemctl show`. **It closes**: `success/0` and merged for the enrolled
signer, `exit-code/1` and nothing merged for the unenrolled one. The unit form
is strictly stronger than the CLI form, because the failure is a *unit* failure
visible to the rest of the transaction rather than an exit code inside a
script. The contradiction with the earlier drop-in attempt is **attributed, not
proven** -- that attempt targeted the sysroot merge, on non-secboot firmware,
with no key enrolled anywhere, and was not re-run. Note also that the `Requires=`
guard on the replay is fail-closed for the **initrd** merge only -- a failing
replay still ends with `/etc` overmounted by the post-switch-root merge.

**Three backlog questions were ruled on 2026-08-12 by Jason Tarasovic**, none
of them on the critical path, all recorded in the
[carve record](etc-path-carve.md)'s question table.

Question 9, the tools tree: **consolidate on the slice tree.** PLN-0002-02 added
`createrepo_c` to the slice recipe and thereby removed the spike's stated reason
for a separate tree, so the two declarations are now identical in package list
and pinned base digest and two build roots is duplication rather than
independence. The reuse that raised the question was never verified
byte-for-byte, because the repository was unreachable; it is reachable now, so
consolidation is confirmed by a rebuild rather than by the declaration alone.

Question 8, the factory fragment against systemd's own `etc.conf`: **skip the
paths upstream owns.** The argument is the defect's own history -- upstream
handled four of the five dangling release paths correctly while the generated
fragment, sorting first, silently overrode it with a broken target. The
implementation belongs to PLN-0002-02 and must be measured, since both the entry
count and the resolve/dangle counts move.

Question 6, collision 1's option A: **implement when the first carve needs it.**
Writing it against no failing case would add a path nothing exercises. The
trigger is named rather than left to memory -- the first carve that enters a
factory directory, `/etc/ssh` being the nearest, live the moment the closure
gains an sshd. Until then the question row is itself the guard.

**Three more were ruled the same day, and two of them land on PLN-0002-03b.**
Question 5b, the replay's fail-open residual, is **recorded and carried to
03b**: it is a property of the delivery design rather than of the carve. The
cost is carried openly -- a known fail-open stays live through tasks 06 to 10,
so a green boot in that range is not evidence the replay ran, and any result
depending on it must say so. The credstore sub-question of 5a is **deferred to
03b** with the general exception-list question, rather than answered where
answering it would settle credential delivery as a side effect of a tmpfiles
list. Both rulings raise 03b's weight: it now owns the delivery design, the
exception list, the credstore paths, and a live fail-open, while remaining off
every other task's critical path. It is therefore **sequenced the same day:
after 05 and 06, before 07 through 10**. A scheduling ruling, not a dependency
-- and the reason is the fail-open, which running 03b before 07 confines to
task 06 instead of carrying it through every measurement task.

The **verity certificate subject** is ruled a task 05 parameter: one subject
for the verity signer across every build root, accepted as
[PLN-0002 amendment 4](../plans/0002-usr-artifact-format-spike.md). It looked
cosmetic while the build roots were independent and stopped being cosmetic when
enforcement became real -- the subject is what is enrolled in `db` and what
sits in `/usr/lib/verity.d`. The image signer, the unenrolled second key, and
the platform key stay distinct, because `T4-CONFEXT-001`'s entire content is
which signer `db` holds.

**Early-boot findings 2 and 3 are ruled the same day**, both narrower than the
options put up, and both recorded in the
[findings](early-boot-findings-for-decision.md).

Finding 2, runtime unit enablement: **A now, with B and D both left open.**
Composition owns enablement today, which is already true after PLN-0002-02 and
needs no change. The drafter's "B as the design" was **not** taken -- B is
blocked behind finding 1 and D arrived from RES-0015 a day earlier, so ranking
them now would be ranking a blocked candidate against a new one. The standing
guard is unchanged and now covers all three: B, C, or D arriving implicitly as
a task's convenience is a stop condition.

Finding 3, `/etc/machine-id`: **the direction only.** Machine identity is
persistent and provisioned at install; the mechanism belongs to `L-003` and is
not decided, so not even A's persistent volume is committed to. B and D are
excluded by the direction. C is excluded only as a substitute for provisioning
-- not as a transport -- which is precisely the accident the ruling exists to
prevent. PLN-0002 is unaffected: its fixture boots transient, says so, and
measures nothing depending on machine continuity.

Question 7 is **answered by measurement** rather than ruled, and closes: the
enrollment exists, the control is the unit-form image policy above, and
`T4-CONFEXT-001` registers it. Its prediction -- that task 10's substitution
would pass -- was correct for the mechanism as it stood.

A hygiene breach was found and closed alongside it.
`tools/validation/__pycache__/check.cpython-314.pyc` had been tracked since
`f54c217`, committed in the forty-minute window before `.gitignore` existed,
and survived twenty-six commits and the G1 review because the contract's
"no tracked binary artifact" bound was policy a reviewer applies and no
reviewer applied it. The file is untracked and `T0-HYG-001` now enforces both
artifact bounds against the index in both profiles, closing PR-0026 C-002.
**It is deliberately left in history**: `f54c217` is an ancestor of both
published refs, and rewriting would invalidate seven cited commit identities
including `6ec625a`, the commit G1 was approved at, and `874e9c7`, the source
revision `src/slice/input-set.toml` declares. `check:fast` is now 7/0.

**Open and unresolved: this makes the CI `check:complete` job fail.** The
workflow runs both profiles, and a hosted runner has no composed artifact, so
the three-way choice is CI composing the slice itself, CI running `fast` only
with `complete` becoming a local qualification profile, or accepting a red
`complete` in CI. Nothing has been pushed, so nothing is currently broken. The
choice is the owner's and belongs with `P-008`. **Explicitly punted 2026-08-12
by Jason Tarasovic**, and the reason is worth keeping because it rejects the
three-way framing rather than declining to choose within it: CI needs a full
answer that includes how qualification runs a VM at all, and taking one of
these three now would settle that by picking the cheapest arm under no
pressure. Nothing is pushed, so nothing is red; the constraint is that this
must be answered **before** the workflow's `complete` job runs anywhere.

`P-009` is newly open and blocks nothing under G1: QEMU became the VM harness in
PLN-0001-03 without a comparison, so [RES-0013](../research/comparisons/vm-test-harness.md)
records one. QEMU alone offers a writable firmware varstore and a TCG fallback;
cloud-hypervisor and `test.thing` offer neither, and `test.thing` is
GPL-3.0-or-later, so its code cannot be copied into this Apache-2.0 repository.
Four of its techniques should still be adopted independently -- guest-driven
readiness over a notify vsock, SMBIOS Type 11 credentials, ssh over vsock with
ephemeral keys, and `snapshot=on` disposability. Three are now adopted; ssh
over vsock is the one held back, and for a reason recorded below. Two were measured working
under TCG against the literal pre-amendment artifact: `snapshot=on` leaves it
byte-identical, and SMBIOS credentials plus
`io.systemd.stub.kernel-cmdline-extra` take it from a blocking prompt to a
login prompt without changing a byte. **All three PLN-0001-04 composition
amendments are therefore unnecessary for reachability**. **Owner decision
2026-08-10: revert them, but not until KVM works**, so the revert and the move
to vsock ssh happen in one motion; where first-boot configuration belongs on a
physical host, which has no harness, remains an open `C-002`/`L-003` question.

**SVM was enabled in firmware setup on 2026-08-10 and the revert was executed.**
KVM is live -- `svm` present, `kvm_amd` loaded, QMP `query-kvm` reporting
`enabled` on the harness's own flag set -- and `T4-SLICE-001` runs at 18 seconds
against 72 under TCG with identical evidence fields. The six settings were
removed from the composition fixture and the rebuild reproduced the
pre-amendment UKI, initrd, kernel, and manifest digests **exactly**, which is
what establishes the amendment was the only difference. `check:complete` is
`passing=10 failing=0` against the reverted artifact.

**Notify-vsock readiness landed the same day.** `T4-SLICE-001` now waits for
`READY=1` from pid 1 over a vsock rather than for a `login:` string in the
serial log -- 13.2 seconds against 15.4, and a stronger claim, since a prompt
is a getty starting while `READY=1` is the boot transaction completing. The
hostname is read from `X_SYSTEMD_HOSTNAME`. It adds nothing to the image: the
guest side is stock systemd reading the `vmm.notify_socket` credential. Hosts
without `/dev/vhost-vsock` fall back to the serial marker and say so in
`readiness_source`.

Two things remain open and should not be read as closed. **ssh over vsock is
not done and is now a question rather than a task**: it needs `openssh-server`
in the image, which changes the closure and every pinned digest, and it is the
same shape as the amendment just reverted -- the artifact carrying something it
does not need so a test can drive it. Nothing currently depends on it. And the
retained `T4-SLICE-001` result still records `accelerator_requested` but not
which accelerator was obtained, so a silent fallback to TCG would report
passing; the vsock fallback deliberately does not have that defect.
`W-002` no longer blocks `P-009` on hardware grounds.

`P-008` is open and blocks nothing under G1: the required `canonical profiles`
check cannot report on an unpushed commit, so direct pushes to `main` are
rejected and `main` is pull-request-only in effect, and the only enabled merge
method replaces owner-signed commits with one signed by GitHub's `web-flow`
key. Work continues locally by owner decision; local `main` is ahead of the
remote and pull request 7 is open and green but unmerged. The four canonical tasks, Linux-x64 tool locks, failed invocations,
output-safety quarantine, named T0 checks, secret scanning, and registered
hostile, empty-cache, and clean-clone probes are implemented. Copilot remains
unverified and must not be relied on for autonomous repository work.

PR-0029 C-005 is the standing risk for the duration of G1: mkosi, the Fedora
snapshot, EROFS/Btrfs, `systemd-sysinstall`, and the general distribution
kernel will now be used repeatedly and successfully, and repeated success is
how a candidate becomes a decision without an ADR. The test is whether the
required challengers — bootc, a literal Arch snapshot — are ever actually run.

`docs/project/work-register.md` is the aggregate view. Question state lives in
`docs/project/decision-backlog.md`. Neither is architecture authority. Do not
open either for a cold status report.

## Accepted decisions relevant now

- The project name is **NeutrinOS** in prose, **`neutrinos`** in machine-facing
  identifiers, and **`neutrinos-os`** for the GitHub organization
  (`docs/project/naming.md`).
- The repository is licensed **Apache-2.0** and is **public**, resolving
  `P-007` (`docs/project/scope.md`). Public visibility limits nothing in scope:
  "not a public distribution" governs support and compatibility promises, not
  source visibility.
- NeutrinOS is systemd-first; an overlapping non-systemd mechanism carries a
  documented burden of proof (`docs/adrs/0001-systemd-first.md`, ADR-0001).
- Routine, exceptional, machine, and data authorities remain separate, with an
  independently usable recovery path
  (`docs/adrs/0002-separate-authority-and-recovery.md`, ADR-0002).
- Fleet intent uses bounded TOML records and exact native configuration, JSON
  Schema validation, and canonical JSON evidence
  (`docs/adrs/0003-bounded-fleet-intent-representation.md`, ADR-0003).
- Accepted system policy covers deployment lifecycle, configuration, storage
  boundaries, package inputs, supply-chain evidence, rollout, installation,
  credentials, Unix identity, and software-placement boundaries
  (`docs/requirements/system.md`). Exact mechanisms remain open where no ADR
  accepts them.
- Test policy uses the T0-through-T7 taxonomy, cross-cutting `T5@Tn` failure
  notation, exact requirements-to-test traces, and explicit claim boundaries
  (`docs/project/test-strategy.md`).
- Validation policy uses the canonical `mise run check:fast`, `check:complete`,
  `check:list`, and `check:run` tasks, with a locked Python 3.14/uv engine by
  default. Applicable-suite, offline/unprivileged/secret-free, result, timeout,
  cleanup, and CI rules are accepted (`docs/project/validation-contract.md`).
  The Linux-x64 task/runner/T0 slice, external XDG test cache, and registered
  environment, cache-boundary, network, timeout, interruption, output, and
  process-cleanup probes are implemented.
  Canary scanning and quarantine are accepted and implemented, as is the
  retained empty-cache acquisition-boundary probe. Bootstrap is an unfiltered
  acquisition phase bounded by pinned hash-checked locks, not by endpoint
  restriction, which the locked platform cannot enforce. Clean-clone profiles
  pass, and the pinned least-privilege CI job runs both profiles on a hosted
  runner. `T5-VAL-002` and `T5-VAL-003` now build `PATH` as a directory of
  symlinks to exactly the executables they declare, closing PR-0028 C-002 for
  both known instances: a system directory admits everything beside the tool
  that justified it, so an undeclared dependency resolves and the probe passes
  for a reason it never stated. Repository mise use does not select
  host-role software placement.
- PLN-0000's readiness model and fixture/defer classifications are accepted.
  PRE-001 through PRE-018 are satisfied and the plan is complete.
- **G1 is approved** (2026-08-10, PR-0029). It authorizes disposable VM/lab
  implementation under an accepted follow-on plan and nothing else -- PLN-0001,
  now complete, and currently PLN-0002. PRE-018 records an authority
  act rather than evidence; the gate is a readiness gate, not a capability
  gate. Seven review challenges are carried open, not closed: PR-0026 C-003 and
  C-005, PR-0027 C-002 and C-006, PR-0028 C-002's residual class, C-003, and
  C-006.

## Leading but unaccepted fixtures

These may support a bounded experiment. They are not permanent architecture:

- direct systemd/UAPI-oriented image composition, likely using mkosi, with
  bootc retained as the required deployment-substrate challenger;
- a declared Fedora stable package snapshot, with a literal Arch snapshot as
  the required package-ecosystem challenger;
- an EROFS root and Btrfs mutable state for later evaluation; the exact storage
  layout, encryption, and recovery mechanism remain open;
- `systemd-sysinstall` as the leading installation mechanism;
- a general distribution kernel with a normal initrd for the first VM fixture;
  and
- an ordinary disposable VM as a test harness, not an accepted microVM product
  model or role.

W-002 microVM lifecycle, W-004 kernel specialization, and workstation, laptop,
router, server/storage, and guest role contracts remain open or explicitly
deferred to later gates. Do not encode their fixture shapes as permanent
architecture.

## Allowed and prohibited work

Currently allowed:

- NeutrinOS source implementation and reference-VM work within the bounded
  scope of active PLN-0002, under its named tasks, using disposable VM disks,
  firmware variables, virtual TPM state, and test networks;
- synthetic signing, enrollment, identity, and credential fixtures;
- build caches and artifacts in declared development locations;
- documentation, repository guidance, and validation scaffolding;
- read-only repository and host inspection when the specific task authorizes
  it; and
- documentation-only evaluation with synthetic inputs.

Currently prohibited:

- implementation outside PLN-0002's accepted task scope, or any work reaching
  for G2 qualification claims;
- mutation of `desktop-jason`, `router`, `misc`, or another physical host;
- use of production credentials, signing keys, enrollment state, recovery
  material, or machine authority;
- treating a candidate fixture, successful probe, or agent summary as an
  accepted decision; and
- autonomous push, merge, release, or publication.

The exact mutation-changing authority and stop conditions live in
`docs/plans/0000-pre-implementation-readiness.md` (mutation boundary, retained
after completion) and `docs/plans/0001-reference-vm-slice.md` (task scope and
stop conditions). Do not open either for a
read-only status report; the current boundary above is complete for that task.

## Working-tree and validation expectations

Assume a dirty worktree may contain user or another task's work. Before editing,
inspect it, preserve unrelated changes, and name them in the handoff.
Concurrent work requires explicit ownership and isolated worktrees under root
`AGENTS.md`.

Read-only task: do not run validation. Report only this requirement: after
edits, run `mise run check:fast`; a successful terminal result is a pass.
Bootstrap and the additional canonical profiles are documented in
`docs/project/validation.md`. PRE-015 is satisfied; a passing run is not by
itself G1 or qualification evidence.

## Context path for a fresh task

1. Read root `AGENTS.md`.
2. Read this file.
3. Read-only status/orientation/report: hard stop. Cite paths from this file
   without opening them. Open only one authority explicitly named by the user.
4. Execution/edit: read only the active-plan sections and sources governing the
   exact change or risk.
5. Aggregate analysis: `docs/project/work-register.md` on demand.
6. History/provenance only: `docs/background/design-session-summary.md`, then
   the transcript only if necessary.

## Maintenance and verification

Update this file whenever any of the following changes:

- the active gate or active plan;
- an accepted, rejected, superseded, or reopened decision relevant to current
  work;
- a leading mechanism or experimental fixture relevant to current work;
- the allowed or prohibited mutation boundary;
- the canonical validation commands; or
- the one next action.

Set `source_snapshot_revision` to the source revision against which the summary
was checked. This names its inputs, not this file's containing commit, and may
therefore precede HEAD. EX-0016
(`docs/research/exercises/0016-agent-context-and-instruction-loading.md`) is
complete for the owner-approved Codex/Claude set; rerun it before expanding the
supported autonomous-client set or when instruction discovery materially
changes.
