---
status: accepted
last_updated: 2026-08-15
governing_plan: PLN-0002
task: PLN-0002-11
accepted_by: Jason Tarasovic
accepted: 2026-08-15
---

# Slice checks under the `/usr` artifact

PLN-0002-11. The five registered slice tests were written for PLN-0001's
flattened root. This records what they assert now that the authenticated
artifact is `/usr`, what was added, and what each addition does **not**
establish. **Accepted 2026-08-15 by Jason Tarasovic**, including the two
deferred registrations, which are an extension of this task beyond the three
checks the plan named for it.

**Outcome. The five hold, and none of them was measuring the two properties
DES-0006 C-013 depends on.** A `/usr` artifact whose root hash the UKI does not
name, and a machine that writes durably to `/etc`, both passed every check this
repository had. Two new checks close that, and one existing check gained the
premise the whole C-007 comparison rests on.

## The five, audited

Each was run against **both arms** -- the EROFS and ext4 primaries of the
PLN-0002-06 set -- rather than against whichever arm the environment happened to
name.

| Check | What it reads | Status under `/usr` |
| --- | --- | --- |
| `T2-SLICE-001` | `input-set.toml` and its schema, 11 constructed violations | Unaffected. The declaration is format-independent and the artifact's shape is not in it |
| `T2-SLICE-002` | `mkosi.conf`, `compose.sh` | True, and **incomplete**: it knew nothing of the arm split. Extended below |
| `T3-SLICE-001` | Manifest, UKI sections, ESP/UKI digest identity | True on both arms, and blind to the verity partitions. `T3-SLICE-004` is the addition, not a rewrite |
| `T3-SLICE-002` | NEVRA attribution against the retained repository index | Unaffected. Attribution is about the closure, which the `/usr` split did not change |
| `T4-SLICE-001` | Readiness, unit failures, artifact immutability | True on both arms. It asserts nothing about `/usr` or `/etc`, which is what `T4-SLICE-002` is for |

`T3-SLICE-003` (signing material, PLN-0002-05) is not one of the five and was
audited with them: it passes on both arms. Its docstring reasons from EROFS
storing a small file contiguously and uncompressed; measured, the argument also
holds on ext4, where nothing is compressed at all.

## What was added

### `T2-SLICE-002` now asserts the arms differ in one variable

`mkosi.repart.erofs/10-usr.conf` states the premise in its own comment -- "the
diff between them is the whole of what PLN-0002 is measuring, and anything else
that drifts apart here is a second variable and voids the comparison" -- and
then asks the reader to enforce it by eye. Every other control in this
repository left to the eye has been caught failing: the superseded certificate,
the module list shipping 130 against 21 declared, the EROFS arm compared
uncompressed.

The permitted asymmetry is enumerated with a reason and a shape: `Format=` is
the variable, `Compression=`/`CompressionLevel=` may appear **on the EROFS arm
only** because ext4 cannot compress. Held constant, and now checked as such:
`Type`, `Label`, `CopyFiles`, `Verity`, `VerityMatchKey`, `Minimize`.

The shape is not decoration. The first draft expressed the permission as a bare
list of keys, and an injected `Compression=zstd` on the ext4 arm **passed** --
which would have turned the size and transfer-size criteria into a comparison of
two compressors.

### `T3-SLICE-004` -- root hash to UKI binding

Static, offline, no filesystem driver. Five links, each failing separately:

1. The UKI's signed `.cmdline` carries exactly one `usrhash=`.
2. Its halves are the `/usr` and `/usr`-verity partition UUIDs, which is how the
   Discovered Partition Specification binds a root hash to the partitions it
   covers.
3. The verity signature partition's payload names the same root hash.
4. Its `certificateFingerprint` is the certificate published beside the
   artifact, and the certificate embedded in the CMS blob is that same one.
5. The detached CMS signature over the root hash verifies against it.

Partitions are found by DPS **type** UUID, not by the labels this repository
gives them: the type is what systemd's dissection reads, and a check keyed on
our labels would keep passing after a rename that stops the machine finding the
partition at all.

**It does not verify the hash tree against the data.** An image whose `/usr` was
replaced and whose UUIDs, root hash and signature were all reissued consistently
passes. `veritysetup verify` is that assertion and lives in
`src/slice/measure-corruption.py`. **It does not establish trust**: the anchor is
the certificate shipped beside the artifact, so the claim is "signed by that
certificate", never "trusted by any machine" -- PLN-0002-10 measured that an
untrusted `/usr` verity signer does not stop the boot.

### `T4-SLICE-002` -- read-only `/usr`, nothing durable in `/etc`

One probe boot per run, on the `vm.boot` path, with the probe unit dropped in by
credential and pulled in by a `multi-user.target` drop-in. It runs under the
same two TPM masks as `T4-SLICE-001` and PLN-0002-08, and says so in its result.

The probe **writes**, rather than reading mount options and calling it a day:
`/usr` mounted `ro` is not the same claim as `/usr` cannot be written, and this
plan's recurring defect is a mechanism that is configured, runs, reports success
and gates nothing. Measured on both arms: the write is refused, `remount,rw`
fails with status 32, `/usr` is mounted `ro` from `/dev/mapper/usr` -- checked,
because a `/usr` mounted straight off `/dev/vda2` would satisfy every read-only
assertion with no verity underneath it.

## The `/etc` property is stronger than either draft assumed

Two drafts of the `/etc` assertion were wrong, and the boot corrected both.

1. "`/etc` is tmpfs" -- false. It is an `overlay`, because a confext merge is an
   overlay mount. DES-0005's mechanism, working.
2. "the overlay's upperdir is on tmpfs" -- also false. **Measured 2026-08-15:
   the `/etc` overlay is mounted `ro`, with lowerdirs only** -- the sysext
   metadata, the confext's own `/etc`, and `/sysroot/etc` from the initrd's
   factory replay -- **and no upperdir at all.** A write to `/etc` is refused
   outright.

So the rule is a disjunction covering this machine and one that merges no
confext: a write to `/etc` must be refused, **or** must land on a volatile
filesystem. Behind it sits the general statement, also checked: no block-backed
mount is writable anywhere, so there is no durable surface for anything to land
on. Asserting only the `/etc` case would let a writable partition mounted
elsewhere make the specific result true and the property it stands for false.

## Failure sensitivity

Established for every assertion, on both arms. A check that has only ever been
shown to accept is untested -- the rule `T2-SLICE-001` already states for the
schema.

`T3-SLICE-004`, against a copy of the EROFS primary, six injections, all
rejected, baseline passing before and after: one hex digit flipped in the UKI's
root hash; the signature payload naming a different root hash; the
wrong-but-valid certificate published beside the artifact; one bit flipped in
the CMS signature; the signature partition zeroed; the certificate absent.

**One injection was accepted by the first draft and is the finding of this
task's static half.** A bit flipped at offset 621 -- inside the certificate
embedded in the CMS structure -- verified successfully, while flips at 900,
1100, 1210 and 1241 all failed. OpenSSL matches the signer by issuer and serial
and reads the trusted copy from `-certfile`, so the embedded copy is never
consulted. Left uncovered, that is a region of a signed artifact that can be
changed with nothing noticing. The check now compares the embedded certificate
rather than trusting it, and the injection is rejected.

`T4-SLICE-002`, driving the shipped assertions with the guest's own console as
the baseline and mutating one observation at a time: `/usr` mounted `rw`, `/usr`
off the bare partition, a file created in `/usr`, `remount,rw` accepted, `/etc`
writable onto a durable upper layer, `/etc` writable directly onto a durable
filesystem, and a writable block-backed mount elsewhere -- **seven rejected on
both arms**. One case must be *accepted* and is: `/etc` writable onto tmpfs,
which is the machine that merges no confext. Rejecting it would make the check
assert the confext merge rather than durability.

The eighth injection is the one only a boot can make: the probe unit supplied
with nothing pulling it in. The guest runs to timeout with no marked report and
the check fails rather than reporting that nothing is wrong. This is the fault
`tools/validation/vm.py` records as already paid for once, and writing this
check re-paid it -- the first reconnaissance boot used `systemd.unit~`, which
does nothing, and sat at a login prompt for seven minutes.

## Validation

`mise run check:complete` ran **green at 16 of 16** on 2026-08-15 against the
EROFS primary, with the retained repository and the confext fixture declared:
`passing=16 failing=0 blocked=0 skipped=0 not_applicable=0 deferred=2`. That is
the profile required for any edit under `tools/validation/`, and the count rose
from 14 because this task registered two checks.

**18 tests are registered and 16 run.** The `deferred=2` is `T4-SLICE-003` and
`T4-SLICE-004`, and the run manifest is the check on that count rather than the
summary line: 16 IDs in `selected_ids`, neither deferred ID among them, and both
in `omissions` with `"state": "deferred"` and their declared justification.
Deferral does not fail the profile, and `final_result` is `passing`.

## Limits

- Both new checks run against the artifact directory the environment declares,
  one arm per run. They are written format-agnostic and were verified by hand
  against both primaries; nothing in the registered profile iterates the six.
- `T4-SLICE-002` says nothing about authentication. A successful mount is not a
  signature claim, which is the whole of PLN-0002-10's finding.
- `T3-SLICE-004` and `T4-SLICE-002` both trace `SYS-049`. Neither claims it
  satisfied; it stays `Partial`, and the requirement's substitution half is
  PLN-0002-10's.

## The registration question, settled

The plan asked this task to settle whether registering a check belongs here or
to the task that measures. **Ruled 2026-08-15 by Jason Tarasovic**, on the
argument below.

**Registration belongs to whichever task first needs the assertion enforced.**
Authoring a check belongs with whoever holds the fixture and the evidence, which
is always the measuring task; writing `T4-SLICE-002` from scratch here re-paid a
lesson `vm.py` already records, at the cost of a seven-minute boot into a login
prompt. A dedicated task keeps the narrower obligation this one actually
discharged: **audit that every registered check is still true of the current
artifact**. That is the part no measuring task can do, because it is
cross-cutting and time-varying -- the five PLN-0001 tests were written for a
flattened root and the artifact changed under them.

Registration is admitted against a stated standard, which is where
`T4-CONFEXT-001`'s early registration actually went wrong. It was correct in
placement and verified failure-sensitive, and it still spent a period
*registered and not running*: unreachable through `mise run` because
`sandbox.deny_env` stripped its fixture directory, with its slice-side fixture
exercised against the PLN-0002-01 spike artifact instead. Neither limit was
found by the task that registered it. The standard is in
[validation](validation.md#admission-standard-for-a-new-check); the accepted
[validation contract](validation-contract.md) is untouched, because it governs
what a registration declares and has never spoken to who registers or when.

This is a convention and is revisable on evidence, which is the basis it was
ruled on.

## Task 10's fail-open, registered deferred

**Ruled 2026-08-15 by Jason Tarasovic: add the checks as deferred.** This is
beyond the three checks the plan named for this task and is recorded here as an
extension of it; the plan row says so, and acceptance is the owner's.

The problem it closes: `/usr` signature substitution fails open -- a valid
signature by the enrolled signer over a root hash the image does not carry
boots to `running` with zero failed units -- and no registered check asserted
anything about it. It lived only in the
[substitution records](artifact-substitution-records.md) and in
`src/slice/measure-substitution.py`, which is not in the registry, so it would
have stopped being carried when PLN-0002 closes.

Asserting the observed behaviour was rejected: a check that encodes the
fail-open passes because the mechanism is broken and goes red when it is fixed.
What is registered is what SYS-049 requires, which fails today and correctly so.
The contract's state for that is `deferred`, "valid only when already justified
in the governing requirements-to-test trace" -- and SYS-049 is accepted at
`Partial` with the upstream reason recorded as an open sub-question under
`S-005`, so the justification exists and each registration states it.

**Two, not one.** `T4-SLICE-003` is the enrolled signer over a foreign root hash
(`sig-foreign`); `T4-SLICE-004` is the unenrolled authority (`sig-wrong-key`).
Distinct substitutions, distinct diagnostics, and one combined check would hide
whichever half was fixed first.

The mechanism is described in
[validation](validation.md#deferred-checks). Four routes by which a deferred
check could have reported success are closed -- profile selection, `check:run`,
the runner-private `_execute` path, and the manifest -- and the failure
direction is set so that **lifting a deferral without writing the assertion
turns the profile red**, because the registered bodies report "not implemented"
and return nonzero. A deferred registration whose body returned zero would have
been this plan's ninth fail-open, and the worst of them: coverage in name of the
one requirement the artifact does not meet.

Verified by hand, 2026-08-15, before running the profile: `check:list` shows
both as `deferred`; `mise run check:run T4-SLICE-003` fails selection with
`deferred test ID(s) cannot be run` rather than executing or reporting the ID
unknown; `_execute T4-SLICE-003` exits 2; the run manifest carries both under
`omissions` with `"state": "deferred"` and the justification as the reason; and
each body returns 1 when called directly, which is the lifted-deferral case.

**The implementation cost was the reason this was a decision rather than an
obvious yes.** A first reading of `check.py` called the three always-zero counts
an unplumbed gap; checked against the contract and against a real `run.json`,
that was wrong and is retracted:

- the contract requires the terminal summary to report all six counts, so a zero
  for `skipped` is an assertion that nothing was skipped rather than a stub;
- `skipped` is deliberately unreachable, because the contract says a required
  selected test that cannot run is `blocked`, "not `skipped` or passing" --
  `blocked_result`'s docstring records exactly that;
- every registered test is accounted for in the manifest, which the 2026-08-15
  `check:fast` run confirms: eight in `selected_ids` and eight in `omissions`
  with `"reason": "not selected by invocation"`; and
- `not_applicable` and `deferred` read zero because nothing currently is either,
  which is honest.

What was true is narrower, and is what this change implemented: the `Test`
registration carried nine fields and none declared a deferral or its
justification, so deferring a check needed a new field, a path that reports the
state, and the guarantee that it does not count as a pass. It now carries ten.

## Open

Nothing carried by this task. The registration question and task 10's fail-open
are both ruled, and this record is accepted.

**Raised for a later task, not deferred by this one**: a deferral justification
is free text, and nothing validates that it names a trace that exists. These two
say `S-005` because they were written to. Making that structural -- a field
resolved against the [decision backlog](decision-backlog.md) -- would apply to
every future deferral, so it is a registration-shape question rather than a
PLN-0002 one.
