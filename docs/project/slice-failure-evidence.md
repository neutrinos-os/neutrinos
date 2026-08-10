---
status: active
last_updated: 2026-08-10
governing_plan: PLN-0001
---

# Reference-VM slice failure evidence

PLN-0001-06. Every prior slice record asks what happens when composition
works. This one asks what happens when it does not, because a pipeline that
only demonstrates success has demonstrated nothing about whether it fails
closed.

Seven faults were injected, one at a time, each into its own copy of
`src/slice`. The checkout was never mutated: the harness copies the tracked
sources, applies exactly one change, and composes from the copy.

**Result: six of seven faults failed closed and named their responsible input.
The seventh did not fail at all.** Substituting mkosi's `Mirror=` for
`LocalMirror=` silently admitted an undeclared repository, built a complete
artifact from it, and passed `T3-SLICE-001`. SYS-059's undeclared-repository
half is therefore **not demonstrated**, and this record downgrades it.

## What SYS-018 asks for

SYS-018 requires a failure to identify four things: the responsible input, the
configuration scope, the generated output, and the lifecycle stage. The table
below records each separately rather than collapsing them into "the error was
good", because the slice scores differently on each. In particular
**configuration scope is never identified by any fault**, for a structural
reason recorded under [Limits](#limits) rather than a defect in any one
diagnostic.

## Injected faults

| ID | Stage | Injected change | Outcome |
| --- | --- | --- | --- |
| F-CFG-01 | Declaration | `[intent].layers` gains `"site"` | Rejected before any tool runs |
| F-CFG-02 | Resolution | `mkosi.conf` `Release=45`, declaration still `44` | Failed closed on trust domain |
| F-CFG-03 | Artifact inspection | Declaration `release = "45"`, artifact built at `44` | Rejected by `T3-SLICE-001` |
| F-RES-01 | Resolution | `LocalMirror=` replaced by `Mirror=` | **Did not fail.** Built from an undeclared repository |
| F-RES-02 | Resolution | Repository URL moved to `releases/43`, `Release` still `44` | Failed closed on trust domain |
| F-CMP-01 | Composition | Unresolvable package added to `Packages=` | Failed closed, named the package |
| F-CMP-02 | Acquisition | One hex digit changed in the tools-tree base image digest | Failed closed, named the digest |

### F-CFG-01 — undeclared precedence layer

```
path: ['intent', 'layers', 3] | keyword: enum
message: 'site' is not one of ['common', 'role', 'machine']
```

The best diagnostic of the seven, and the only one that names the input by its
location in the declaration rather than by a value that happens to appear in a
downstream command. It names the field path, the offending value, and the
permitted set. It costs nothing: no network, no build, no tools tree. This is
the same rejection `T2-SLICE-001` already reproduces as one of its nine
constructed violations; what is new here is the recorded text.

- Responsible input: `src/slice/input-set.toml`, `[intent].layers[3]`
- Generated output: none — the fault is caught before generation
- Lifecycle stage: declaration

### F-CFG-02 — mechanism drifts from declaration

`mkosi.conf` is the mechanism; `input-set.toml` is the declaration. Nothing
compares them before a build. Setting `Release=45` while the declaration and
the repository URL still say `44` produced a build that ran for 6.6 seconds and
then failed:

```
Importing OpenPGP key 0xF577861E:
 UserID     : "Fedora (45) <fedora-45-primary@fedoraproject.org>"
Transaction failed: Signature verification failed.
OpenPGP check for package "filesystem-3.18-52.fc44.x86_64" ... from repo
"fedora" has failed: Import of the key didn't help, wrong key?
```

**It failed closed, but not for the reason it was injected.** Nothing detected
that the mechanism disagreed with the declaration. What caught it was that
`releasever=45` selects the Fedora 45 signing key while the packages carry
Fedora 44 signatures — a trust-domain mismatch, which is SYS-059's territory
and not SYS-018's. A drift to a release whose signing key still matched would
not have been caught here at all; it would have built successfully and reached
`T3-SLICE-001`, which is where F-CFG-03 picks the thread up.

This is the drift `src/slice/compose.sh` flags in its own comments, where the
declared values are duplicated into shell variables. It remains unguarded at
composition time.

- Responsible input: named only indirectly, as `--releasever=45` in the echoed
  command; the file that set it is not named
- Generated output: the full `dnf5` invocation, quoted verbatim
- Lifecycle stage: resolution

### F-CFG-03 — declaration drifts from artifact

The inverse of F-CFG-02, and the one that is guarded. With the declaration
changed to `release = "45"` and the good artifact unchanged:

```
manifest release is '44', declaration says '45'
```

`T3-SLICE-001` names both sides of the disagreement and which source each value
came from. It is a post-build check: it establishes that a retained artifact
matches its declaration, not that a build was correctly configured before it
started.

- Responsible input: both sides named — the manifest and the declaration
- Generated output: `neutrinos-slice.manifest`
- Lifecycle stage: artifact inspection

### F-RES-01 — undeclared repository (fail-open finding)

`LocalMirror=` is the entire mechanism by which the single declared repository
is the only repository. `mkosi.conf` says so in its own comments. Replacing it
with `Mirror=` restores mkosi's default Fedora repository set, which includes
`updates` — a continuously republished repository the declaration deliberately
excludes because it cannot be an exact input.

Composition **succeeded** in 45.3 seconds and produced a complete artifact:
disk image, UKI, kernel, initrd, and manifest.

Comparing the resulting manifest against the declared closure:

- 104 packages before, 104 after
- **45 of 104 came from the undeclared repository**, at versions newer than GA:
  `glibc 2.43-2.fc44` → `2.43-8.fc44`, `systemd 259.5-1.fc44` → `259.8-1.fc44`,
  `coreutils 9.10-3.fc44` → `9.10-5.fc44`, and 42 others

`T3-SLICE-001` was then run against this artifact and reported
`passing=1 failing=0`.

Two distinct gaps produce this:

1. **No check asserts the construction is still in place.** The declaration is
   enforced by `LocalMirror=` and by nothing else. Deleting that one line is a
   silent, complete defeat of the exactness claim.
2. **The manifest cannot attribute a package to a repository.** Its entries
   carry only `name`, `version`, `architecture`, and `type`. Even a check that
   wanted to verify every package came from the declared repository has no field
   to read. `T3-SLICE-001`'s "fully identified" assertion is satisfied by an
   entry sourced from anywhere.

Neither is fixable by improving a diagnostic, because there was no diagnostic:
nothing failed.

- Responsible input: not identified
- Generated output: produced and retained, but indistinguishable from correct
- Lifecycle stage: none reached a failure

### F-RES-02 — mixed branch

Repository URL moved to `releases/43` with `Release=44` unchanged. Failed
closed in 7.8 seconds:

```
OpenPGP check for package "filesystem-3.18-50.fc43.x86_64" ... from repo
"fedora" has failed: Import of the key didn't help, wrong key?
```

The diagnostic names the mixing precisely — an `fc43` package under a
`releasever=44` transaction — and identifies it by the artifact the wrong input
produced rather than by the URL that was changed. As in F-CFG-02, the enforcing
mechanism is per-release GPG key separation, not any comparison against the
declaration. That is a genuine guarantee and it is Fedora's, not this project's;
a distribution without per-release keys would fail open here.

- Responsible input: named by consequence (`...fc43.x86_64`), not by location
- Generated output: the `dnf5` invocation, quoted verbatim
- Lifecycle stage: resolution

### F-CMP-01 — unresolvable package

```
No match for argument: neutrinos-absent-package
‣ "dnf5 --assumeyes --best --releasever=44 --installroot=/buildroot ...
   install dbus-broker kernel-core neutrinos-absent-package systemd
   systemd-boot systemd-udev util-linux-core" returned non-zero exit code 1.
```

Failed in 15.6 seconds. The exact injected token is quoted, and the fully
generated native command is echoed alongside it, which is the "generated
output" half of SYS-018 satisfied literally. The declaring file and stanza
(`mkosi.conf`, `[Content] Packages=`) are not named.

The output directory held `initrd` and `initrd.cpio.zst` afterwards: a failed
composition leaves partial outputs behind. They are not a complete deployment
set and no manifest was written, so nothing here could be mistaken for a usable
artifact, but a consumer that globbed the output directory would find files.

- Responsible input: named by value, not by location
- Generated output: the `dnf5` invocation, quoted verbatim
- Lifecycle stage: composition

### F-CMP-02 — tools-tree base image digest

One hex digit changed in the pinned base image digest. Failed in 0.7 seconds,
before any resolution:

```
Error: unable to copy from source docker://registry.fedoraproject.org/fedora@sha256:...e919:
reading manifest sha256:...e919 in registry.fedoraproject.org/fedora: manifest unknown
```

The registry cannot serve a digest it does not have, so this fault cannot fail
open by construction. The full digest is quoted. This is the cheapest and most
certain of the seven.

- Responsible input: named exactly, by value
- Generated output: none — the fault precedes generation
- Lifecycle stage: acquisition

## Limits

**Configuration scope is not identified by any of the seven.** The slice has
one machine, one role, and one set of declared layers, so no failure can
attribute itself to a layer because no layer ever loses a precedence contest.
This is not evidence that scope attribution works or that it does not; it is
evidence that the slice cannot exercise it. SYS-018's scope clause needs a
deployment set with a real precedence conflict.

**Two of the three fail-closed resolution results are Fedora's guarantee, not
this project's.** F-CFG-02 and F-RES-02 are both caught by per-release GPG key
separation. Nothing in `src/slice` compares an input against its declaration
during resolution. That is worth stating plainly because it is the difference
between an enforced property and an inherited one, and only the first survives
a change of distribution — which remains open, since Fedora is a candidate
fixture and not an accepted mechanism.

**No failure was injected into boot, staging, selection, or health
assessment.** SYS-018 names those stages; the slice reaches only boot, and the
lifecycle stages after it do not exist yet. They stay deferred with the rest of
G2.

## Incidental finding

mkosi warns on every build of the tracked composition:

```
mkosi.conf: Setting Seed should be configured in [Output], not [Content].
```

`Seed=` sits under `[Content]` in `src/slice/composition/mkosi.conf`. mkosi
accepts it anyway, and PLN-0001-02 measured the effect it was added for — a
stable btrfs filesystem UUID across builds — so the setting works today. It
depends on mkosi tolerating a misplaced key, which the warning says will not
last. Moving it to `[Output]` is a one-line correction; it is not made here
because PLN-0001-06 injects faults and does not amend composition.

## Recommendation, not decision

The F-RES-01 fail-open has a cheap mitigation and an expensive one, and neither
is taken here.

- **Cheap**: assert in `T3-SLICE-001` — or a new T2 — that
  `src/slice/composition/mkosi.conf` still sets `LocalMirror=` to the declared
  URL and sets neither `Mirror=` nor `Repositories=`. This guards the
  construction that does the real work. It checks the mechanism file, not the
  artifact, so it would not catch an artifact built elsewhere.
- **Expensive**: require per-package repository attribution in the retained
  composition record, and check every entry against the declared repository
  set. This is what SYS-059 actually asks for. mkosi's JSON manifest does not
  carry the field, so this needs another source — an `rpm -qi`-level query
  against the closure, or a different composition mechanism.

Both are proposed. Neither is accepted, and the requirement trace below reports
the measured state rather than the intended one.

## Requirement trace effect

- **SYS-018** — demonstrated for responsible input, generated output, and
  lifecycle stage at declaration, acquisition, resolution, composition, and
  artifact inspection. Not demonstrated for configuration scope, and not
  demonstrated at any stage after boot.
- **SYS-059** — **downgraded from demonstrated to partial.** The mixed-branch
  half is demonstrated (F-RES-02, F-CFG-02). The undeclared-repository half is
  refuted by measurement: F-RES-01 built a complete artifact from an undeclared
  repository and passed every registered check.

Both changes are drafted in [PLN-0001](../plans/0001-reference-vm-slice.md) and
await owner acceptance.

## Retained evidence

Outside the repository at
`~/.cache/neutrinos/slice/evidence/pln-0001-06/`, 312 KiB: the injection
harness, and per fault the mutated sources, the captured `stderr`, and the exit
code and wall-clock time. F-RES-01 additionally retains the manifest of the
artifact built from the undeclared repository, which is the finding's primary
evidence.
