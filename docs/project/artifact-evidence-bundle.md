---
status: accepted
last_updated: 2026-08-15
governing_plan: PLN-0002
task: PLN-0002-14
accepted_by: Jason Tarasovic
accepted: 2026-08-15
---

# `/usr` artifact spike evidence bundle and DES-0006 disposition

PLN-0002-14, the plan's last task. Three things: what was gathered into one
retained bundle, what PLN-0002 hands back to DES-0006, and what the plan's
requirement trace looks like against measured results rather than planned
evidence.

**Accepted 2026-08-15 by Jason Tarasovic**, with the requirement trace and the
exit-criteria assessment it produced. **The acceptance does not accept EROFS,
close C-007, amend an accepted record, or declare PLN-0002 complete** -- the
last of those is a separate owner decision. The trace update and the assessment
live in [PLN-0002](../plans/0002-usr-artifact-format-spike.md) itself, where
PLN-0001-08 put them.

The same ruling **moved PLN-0002-03b out of the plan** (amendment 6): confext
delivery is now an open sub-question under `S-004`, owned by DES-0005, and
PLN-0002-04's unplaced confext partition travels with it. That is what met exit
criterion 1.

## The bundle

Same terms as [PLN-0001's](slice-evidence-bundle.md): the bundle is **not in the
repository**, because the hygiene contract's binary and 1 MiB bounds bind here,
so it records identity and reconstruction rather than bytes.

| Property | Value |
| --- | --- |
| Location | `~/.cache/neutrinos/slice/evidence/pln-0002-14/` |
| Size | 9343 KiB, 130 files |
| Collected at | 2026-08-15, source revision `6a75f20` |
| Collector | `src/slice/collect-evidence.py` |
| Integrity | `MANIFEST.sha256`, one SHA-256 per file |
| Unsafe-output scan | Clean, zero findings |

### What it contains

- **`composition/`** — the declaration and every mechanism that produced a
  figure, as committed: `input-set.toml`, `compose.sh`, `mkosi.conf`, the three
  `mkosi.repart` definitions, the confext's `mkosi.conf`, `enroll-fixture.sh`,
  `retain-repository.py`, `retain-artifact-digests.py`, and the five
  `measure-*.py` scripts. Plus the resolved package manifest, the retention
  record, and the declared repository's `repomd.xml`. The measurement scripts
  are collected on the same ground `compose.sh` is: a record that cites one by
  path stops being checkable the moment the checkout moves on.
- **`measurements/`** — the six per-task evidence directories verbatim,
  `pln0002-06` through `pln0002-12`: the artifact digests, the offline
  measurements, boot, corruption, substitution and recovery JSON, and the serial
  console of every boot behind them. **This is the one place the bundle keeps
  bytes rather than identity**, because a measurement's JSON and the console it
  was read from are the evidence and are reconstructible from nothing.
- **`identity/`** — `digests.json`: every output digest of all six PLN-0002-06
  artifacts, the UKI read out of each artifact's own ESP, and PLN-0001's
  networked and offline builds beside them.
- **`validation/`** — both canonical profile runs in full, results and logs:
  `fast` at 8 passing, `complete` at 16 passing, zero failing, zero blocked,
  **two deferred**. The deferred pair is not in `results.jsonl` because it is
  never selected; it is in the run manifest's `omissions` with its
  justification, which is the mechanism [validation](validation.md#deferred-checks)
  describes.
- **`index.json`** — the above as one machine-readable record, with the source
  revision and the scan result.

### What it does not contain, and why

Disk images, UKIs, kernels and initrds are named by digest only, for PLN-0001's
reason: they are reconstructible from the declared inputs, and carrying six
artifacts' worth of bytes to prove it would contradict the claim rather than
support it. The retained repository is identified by `retained.json` and the
repository's own signed metadata.

Two things are absent for a stronger reason than size:

- **VM disks, firmware variables and vTPM state.** Destroyed at task end, which
  PLN-0002's boundary requires. What survives them is the serial console of
  every boot, which is what the records are read from.
- **The synthetic signing material.** Generated into the build root and
  destroyed with it. The subjects are declared in the [parameter
  declaration](artifact-parameter-declaration.md); the keys are not collected
  and never were.

## DES-0006 disposition

What this plan hands back, item by item. **None of it accepts anything**: C-007
stays open, EROFS and ext4 remain candidate fixtures, and the mechanism
questions below go to the design and the backlog rather than to an ADR.

### Verification item 2 is answered, with one accepted amendment

Item 2 asked for `/usr` artifacts in both formats authenticated through the
exact signed UKI and dm-verity path, with early boot exercised, compared on
eight criteria plus recovery behaviour. Against that:

| Item 2 clause | Disposition |
| --- | --- |
| Both formats authenticated through a signed UKI and dm-verity | **Done.** Six artifacts, one tree state, [artifact set](usr-artifact-set.md); the root hash binding is asserted by `T3-SLICE-004` |
| Early boot exercised | **Done**, and it is where the plan's first finding came from: [early-boot record](spike-early-boot-record.md), [carve record](etc-path-carve.md) |
| `fstab`, `crypttab`, initrd-stage configuration | **Unsatisfiable as written.** No `crypttab`, `fstab` or `veritytab` exists anywhere in the initrd while the generators that would read them ship in both arms. Goes to item 6 and `S-004` ([disposition](artifact-recovery-disposition.md)) |
| Eight criteria measured | **Done.** Five offline ([measurements](artifact-format-measurements.md)), boot and memory ([boot records](artifact-boot-records.md)), corruption ([corruption records](artifact-corruption-records.md)) |
| Recovery behaviour disposition | **Split, and the split is an accepted amendment to item 2** (2026-08-15): format layer measured over eight injection sites, system layer deferred to items 3 and 5, which need the A/B slots this plan excludes |
| "Absent that, EROFS would be selected by having been tried first" | **Answered on the record, not noted.** ext4 was built, booted and measured as a full arm and won or tied seven of nine rows, including two results that contradict the naive prior ([recommendation](artifact-format-recommendation.md)) |

### C-007 has a recommendation and stays open

**EROFS, conditional on the update mechanism not being whole-image-only**,
accepted 2026-08-15 together with the weighing rule that produced it. The
acceptance is of the recommendation and the rule, **not of EROFS**: a format is
accepted by an ADR, and none exists. The design's open question should record
the recommendation and remain open.

Four things an ADR would still need, carried here from the recommendation so
they are not lost when this plan closes:

1. **The workload read comparison**, which is DES-0006 verification item 9's and
   is the single measurement that could reverse the recommendation. Memory is a
   tie measured on an idle guest; EROFS pays its compression cost on read.
2. **A selected update mechanism**, which resolves the recommendation's
   condition and settles criterion 6 one way or the other.
3. **The ParticleOS command-line ruling** of 2026-08-12, unimplemented and
   contradicted by the accepted declaration's own measured argument. Settling it
   in its own favour rebuilds the artifact set and voids every figure measured
   against it.
4. **A capacity budget from C-002**, without which the deciding magnitude —
   111.4 MiB per slot — has no requirement to be measured against.

### What DES-0006 gains that it did not ask for

Four results belong to the design rather than to C-007, and each has a home:

- **The signature fail-open.** A valid signature by the enrolled signer over a
  root hash the image does not carry boots to `running` with zero failed units,
  enrolled or not, identically on both arms ([substitution
  records](artifact-substitution-records.md)). Upstream's enforcement point is
  the TPM unseal rather than the mount. Recorded as an open sub-question under
  `S-005`, and kept in the check registry past this plan by `T4-SLICE-003` and
  `T4-SLICE-004`, registered **deferred**.
- **`systemd.image_policy=usr=signed` is a structural predicate, not an
  enforcement mechanism.** Satisfied by both enrolment arms, evaluated after the
  initrd already mounted `/usr`, and non-fatal. It must not be cited as what
  makes substitution fail closed.
- **The manifest is not a delivered release member.** `neutrinos-slice.manifest`
  is on no partition of any artifact and nothing at boot reads it, so its
  substitution cell is answered by reasoning rather than by a boot. If C-013
  intends it as release-owned, it is not currently delivered as one. That is
  DES-0006's question.
- **The verity partitions are 95% empty**, 62.6 MiB wasted per artifact on both
  arms. It cancels between the arms, so it is not C-007 evidence — but it is
  over half the size advantage the recommendation rests on, and it is a layout
  question for `S-004`.

### What is handed back unchanged

The confext path carve and the confext build tooling remain **candidate** and
return to DES-0005 and the ADR-0003 spike; PR-0030 C-006's protection is still
procedural rather than structural. The tmpfs root remains a fixture and DES-0006's
"does the root partition need to persist at all" stays open. The `/usr` slot
count is one per arm, so every C-001 cell needing A/B slots, finalization, or
power loss is uncovered and goes to items 3 and 4.

## What this bundle does not establish

- **Retention is not durability.** One user's cache directory on one host,
  nothing replicating it. R-005's bound is respected by keeping identity rather
  than bytes; where evidence must live long-term is not this plan's question.
- **A green profile is not qualification.** Twenty-four passing results across
  two profiles record that the checks this slice defines pass on this host. Two
  further checks are registered and deferred and therefore assert nothing today.
- **A boot is not a statement about the artifact.** The plan's standing finding
  holds through its last task: dm-verity is lazy, four corrupted copies booted
  to `running`, and every signature substitution booted clean. What the bundle
  retains is the console of those boots, not a claim drawn from them.
- **Nothing physical.** Disposable VMs, synthetic signing material, plain OVMF
  and one enrolment fixture. SYS-030 stays not applicable, and C-001's residual
  firmware-variable and FAT-ordering risk is untouched.
- **The signing material expires 2026-09-11.** Anything re-measured afterwards
  measures expired enrolment material.

## Reconstructing what the bundle only names

```sh
# The six artifacts, from the declared inputs. Retention runs as part of it.
./src/slice/compose.sh --force build

# Evidence, after both canonical profiles have been run.
python3 src/slice/collect-evidence.py \
    --build-root="$HOME"/.cache/neutrinos/slice \
    --fast-run=/tmp/neutrinos-validation-XXXX \
    --complete-run=/tmp/neutrinos-validation-YYYY \
    --task-evidence="$HOME"/.cache/neutrinos/slice/evidence/pln0002-07 \
    --destination="$HOME"/.cache/neutrinos/slice/evidence/pln-0002-14
```

`--task-evidence` is repeatable and was passed once per retained task
directory. The measurement scripts in `composition/` reproduce the JSON under
`measurements/`; each states its own repetition count and accelerator state, and
`retain-artifact-digests.py` records whether the confext was rebuilt, which any
determinism claim from this slice must state.
