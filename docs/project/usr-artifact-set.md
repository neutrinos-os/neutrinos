---
status: accepted
last_updated: 2026-08-14
accepted_by: Jason Tarasovic
accepted_date: 2026-08-14
governing_plan: PLN-0002
task: PLN-0002-06
---

# The PLN-0002-06 artifact set

Six authenticated artifacts, built 2026-08-14 from one tree state, with their
digests retained outside the repository. This is task 06's deliverable and its
completion criterion. **Accepted 2026-08-14 by Jason Tarasovic**, with the
carried risks at the foot of this document accepted as part of it.

The count is six rather than four under [amendment
5](../plans/0002-usr-artifact-format-spike.md), accepted 2026-08-14: a primary
per arm, plus two substitution sources per arm that exist only for PLN-0002-10.

## What was built

| Directory | Arm | Role | `.raw` SHA-256 | Root hash |
| --- | --- | --- | --- | --- |
| `out-erofs` | EROFS | primary | `a7b610d38e686173…` | `d0f7f4118e5a260c…` |
| `out-erofs-content` | EROFS | content variant | `e1c284a492ab3ad0…` | `adc27deb06055914…` |
| `out-erofs-seed` | EROFS | seed variant | `6b713df475866294…` | `c5538f621ebc3847…` |
| `out-ext4` | ext4 | primary | `95ad53fce9f7b776…` | `d81cd4ba89a8ff36…` |
| `out-ext4-content` | ext4 | content variant | `7c59d27f77bd7131…` | `c5a3392c3f1e6462…` |
| `out-ext4-seed` | ext4 | seed variant | `074d5272a4672883…` | `2be0cc38e35498f0…` |

Full digests for every file of every artifact, with each UKI's command line, are
retained at `$NEUTRINOS_SLICE_BUILD_ROOT/evidence/pln0002-06/digests.json`,
written by `src/slice/retain-artifact-digests.py`. Digests, not bytes: the
images stay in the build root, which is what the hygiene contract's bounds mean
by evidence.

**Retention is a script, not a command someone ran.** The script names the six
rather than globbing them, because a glob retains five and reports success, and
the count is the criterion.

## The two facts that decide whether the digests mean anything

**The kernel command line is uniform across all six**, verified by reading the
`.cmdline` section of each built UKI rather than the configuration that produced
it -- reading the configuration would agree with itself by construction. Less
the necessarily-per-artifact `usrhash=`, every artifact carries exactly
`root=tmpfs rw systemd.image_policy=usr=signed`.

This is the defect the 2026-08-14 audit found and it is now closed: the ext4 arm
previously on disk had been built an hour before `systemd.image_policy=` landed,
carried no policy, and was therefore not a member of the declared set. The
retention script fails rather than records if the set is ever non-uniform again.

**The confext was rebuilt for all six.** `compose.sh`'s `NEUTRINOS_SKIP_CONFEXT`
reuses a previously built extension, and a determinism claim taken with it
skipped means something narrower than it says -- which is what the 2026-08-12
closure did. Recorded in the retained JSON as a field, not as prose here.

## The variants are the shapes task 10 needs

Both are validly signed by the **enrolled** verity key, exactly as the primaries
are. That is the point: a substitution that boots must mean integrity failed to
bind, never that a signature was missing.

Measured on the ext4 arm, where the filesystem is directly inspectable:

| | marker file | filesystem UUID | block count |
| --- | --- | --- | --- |
| primary | absent | `9fff0b98-…` | 112653 |
| content variant | **present** | `9fff0b98-…` (same) | **112656** |
| seed variant | absent | **`42bc6532-…`** (differs) | 112653 (same) |

Exactly one thing moves in each, which is what makes a task 10 failure
attributable:

- The **content variant** differs by one inert marker file under `/usr`
  (`src/slice/composition/mkosi.extra.variant-content/`) -- three more
  filesystem blocks, same UUID. A boot of it says integrity did not bind the
  **contents**.
- The **seed variant** has an identical tree and a second declared `Seed=`, so
  the partition UUIDs, filesystem UUID and verity salt move while the content
  does not. A boot of it says integrity did not bind the **identity**.

One artifact cannot show both, which is amendment 5's whole argument, and it is
now demonstrated rather than asserted.

## Build determinism, re-measured

The EROFS primary was rebuilt rather than carried forward, so that all six come
from one tree state. It reproduced its previous digest exactly:
`a7b610d38e686173…` before and after, **with the confext rebuilt**. That is a
stronger statement than the one this slice recorded on 2026-08-12 and it is
taken under the caveat that measurement was missing.

## Mechanism added by this task

- **`NEUTRINOS_SLICE_VARIANT`** selects `primary`, `content` or `seed`, beside
  the existing `NEUTRINOS_SLICE_ARM`. Environment-selected for the same reason
  the arm is: a variant that lives in an edited working tree is a variant no
  artifact can be traced back to.
- **Symmetric output naming**: six peer directories, `out-<arm>` and
  `out-<arm>-<variant>`, retiring the `out`/`out-ext4` asymmetry the composition
  carried from PLN-0001. **`out` survives as a symlink to `out-erofs`**, because
  PLN-0001's recorded digests name `out` and an operator may have
  `NEUTRINOS_SLICE_ARTIFACT_DIR` pointing at it. It is a compatibility path with
  an end: **PLN-0002-11 updates the registered checks and removes it.** The
  one-time migration refuses to guess if both `out/` and `out-erofs/` exist.
- `collect-evidence.py` discovers artifacts by scanning instead of the
  hardcoded `out`/`out-offline` pair that stopped describing the build root the
  moment a second arm existed.

## What this task does not claim

- **No measurement.** No size, boot, memory or build-time figure is taken here;
  that is tasks 07 and 08, and task 07 must measure filesystem bytes in use
  rather than partition size, for the `Minimize=guess` reason the
  [declaration](artifact-parameter-declaration.md) records.
- **No boot of the six.** Both arms booted to readiness on 2026-08-12 under the
  declared module list, and the artifacts here are not those artifacts. A boot
  of this set is task 08's.
- **Nothing about lazy verification.** dm-verity verifies per block on read, so
  a successful boot of any of these is not a statement about the artifact. This
  is why tasks 09 and 10 carry the plan's weight.
- **No format selection.** Six artifacts exist; C-007 is answered by task 13
  against measurements that do not exist yet.

## Carried risks

- **The synthetic signing material expires 2026-09-11.** All of it is generated
  `-days 30` and the current material dates from 2026-08-12. Tasks 07 through 10
  measure these artifacts afterwards; an enrollment fixture whose `db`
  certificate has expired is a different experiment. Regenerating invalidates
  this set, so the expiry is recorded rather than moved -- see the
  [declaration](artifact-parameter-declaration.md).
- **`systemd.image_filter=` is absent by ruling**, on the finding that the
  premise making it load-bearing assumed two artifacts visible to one boot while
  task 10 substitutes the disk. If task 10 shows a filter is needed, this set is
  rebuilt. That risk was accepted when the ruling was taken.
- **The ParticleOS command-line ruling is still open** and these artifacts
  freeze the implemented value, not the ruled one.
