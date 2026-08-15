---
status: informative
last_updated: 2026-08-11
governed_by: PRE-015
---

# Repository validation usage

The accepted behavior is defined by the
[validation execution contract](validation-contract.md). This page records the
current operator interface; it is not a second policy source.

## Bootstrap

Bootstrap below covers the tools mise and uv install from the lock files. The
**system** tools the composition and the VM harnesses call are not in any lock
file; `python3 tools/host-tools.py` checks for them and names what each missing
one would break, and `--packages` prints the package list for provisioning a
container, VM, or replacement machine. It is a preflight, not a canonical check:
it installs nothing, pins nothing, and is not registered in a profile.

Install mise using the independently pinned method for the execution
environment, then run the following from the repository root after reviewing
`mise.toml`:

```sh
mise trust "$PWD/mise.toml"
export MISE_GLOBAL_CONFIG_FILE=/dev/null
export MISE_SYSTEM_CONFIG_DIR="$PWD/.mise-no-system-config"
export MISE_CEILING_PATHS="$(dirname "$PWD")"
MISE_OFFLINE=0 mise install --locked python uv betterleaks
uv sync --locked --python "$(mise which python)"
```

The three exported variables exclude the operator's global mise configuration,
any system configuration, and every config file above the repository, so only
this checkout's `mise.toml` selects bootstrap inputs. They are the config-only
subset of the isolation `T5-VAL-002` constructs; bootstrap deliberately does
not isolate the data, installs, or cache directories, because it must populate
the operator's real tool store. Without them, tools declared in a developer's
global configuration enter version resolution. Equivalent `mise.toml` settings
do not work: `ceiling_paths` is read from a config file that mise has already
discovered, so it cannot prevent that discovery, and no repository-level
setting can exclude the global config.

Trust is required before the first command: an untrusted `mise.toml` makes
`mise which python` fail, and `uv sync --python ""` then silently selects an
interpreter other than the locked one.

Bootstrap is an unfiltered acquisition phase. Per-host network filtering is not
available: pinned mise rejects `--allow-net=<host>` on Linux, the only locked
platform, so no endpoint restriction is enforced here. What bounds bootstrap is
the pinned input set, not the network path: `mise.lock` fixes the tool
versions, `uv.lock` with `--locked` fixes every package and hash, and a lock
mismatch fails rather than resolving.

Naming the tools explicitly prevents unrelated tools in a developer's global mise
configuration from becoming repository bootstrap inputs. `MISE_OFFLINE=0` is
an explicit acquisition-phase exception to the repository default. Bootstrap
may use the network and tool caches. The canonical checks may not: mise itself
is offline, its tasks deny inherited environment and network access, its task
and shim auto-install paths are disabled, each dispatcher resolves both tools
through `mise which`, and uv runs with `--offline --locked --no-sync`.

## Checks

```sh
mise run check:fast
mise run check:complete
mise run check:list
mise run check:run T0-DOC-001 T0-DOC-002
```

`T0-DOC-001` is the former `git diff --check` validation.
`T0-DOC-002` is the former internal Markdown-link validation. Do not duplicate
their implementations in documentation or CI.
`T0-SEC-001` scans the working tree and all reachable history for committed
secrets using the locked betterleaks, always with `--redact` so a finding never
widens exposure. It is registered in both profiles and runs the same way
locally and in CI: there is one definition of the check, not a local one and a
separate CI one. Scoped exceptions live in `.betterleaks.toml`.
`T0-HYG-001` enforces the [hygiene contract](repository-hygiene.md)'s two
artifact bounds -- no tracked binary and no tracked file over 1 MiB -- which
were reviewer-applied policy with no check until a committed bytecode cache
survived twenty-six commits and a gate review. It classifies the index, not
`HEAD`, so a breach fails before it is committed, and it takes Git's own binary
classification from `git diff --numstat` rather than re-deciding what binary
means.
`T2-SLICE-001` validates `src/slice/input-set.toml` against the schema its own
`[schema]` block declares, and reproduces the eleven constructed rejections the
[input declaration](slice-input-declaration.md) claims. It uses the locked
`jsonschema` package -- the repository's only runtime dependency, added because
the schema uses `$ref`, `allOf`, and `if`/`then`, and a hand-rolled subset
checker that misread any of them would report a record as valid that the schema
rejects.
Two of those eleven arrived with PLN-0002-02's schema version 3, which added
declared package overlays: an overlay file with no digest, and an overlay with
no stated reason. The same change moved the `unsupported schema version`
violation from 3 to 4, because version 3 became real and the violation would
otherwise have been a record the schema accepts.

`T2-SLICE-002` and `T3-SLICE-002` are the two mitigations PLN-0001-06 proposed
for the injected fault that did not fail, registered 2026-08-11.

`T2-SLICE-002` asserts that the composition mechanism still enforces the
declaration: `LocalMirror=` is set to the declared repository URL, neither
`Mirror=` nor `Repositories=` appears, `Distribution=` and `Release=` match the
declaration, and the values `compose.sh` duplicates -- repository URL, mkosi
commit, tools-tree base image -- agree with it. The mixed-branch faults
previously failed closed on Fedora's per-release GPG keys, an inherited
guarantee that would not survive a change of distribution; the branch assertion
makes it an enforced one. The `compose.sh` half closes the drift PLN-0001-02
recorded as possible and unguarded. It reads the fixture, not the artifact, so
it cannot speak for an image built somewhere else -- which is what
`T3-SLICE-002` is for. Verified failure-sensitive against three injections: the
literal `LocalMirror=`-to-`Mirror=` fault, a `Release=45` branch drift, and a
`compose.sh` mkosi commit that disagrees with the declaration.

PLN-0002-11 widened it to the premise of the C-007 comparison: the two arm
directories must differ **only** in the variable under test. `Format=` is that
variable and must match the arm directory's own name; `Compression=` and
`CompressionLevel=` are permitted on the EROFS arm alone, because ext4 cannot
compress; `Type`, `Label`, `CopyFiles`, `Verity`, `VerityMatchKey` and
`Minimize` are held constant and now checked as such. A `10-usr.conf` in the
shared `mkosi.repart/` fails, because it would make masking order between
definition directories decide which `/usr` definition wins. Verified
failure-sensitive against five injections. One of them exposed a defect in the
first draft: with the permitted asymmetry expressed as a list of keys rather
than as a shape, an injected `Compression=zstd` on the **ext4** arm passed,
which would have turned two measured criteria into a comparison of two
compressors.

`T3-SLICE-002` attributes the shipped closure. Every package in the retained
manifest must exist, at its exact NEVRA, in the declared repository's own
published index. mkosi's manifest carries no per-package repository field, so
attribution is by content rather than by a label the builder wrote about
itself. The index comes from the repository subset `compose.sh` now retains,
declared to validation the same way the artifact is:

```sh
export NEUTRINOS_SLICE_REPOSITORY_DIR=/path/to/build-root/inputs/repository
```

The same directory is what an offline rebuild resolves against:
`./src/slice/compose.sh --local-mirror=file://<build root>/inputs/repository`
with the network removed. Measured 2026-08-11: all four stable digests
reproduced.

Its absence blocks rather than skips, on the same terms as the artifact. Two
anchors keep the test honest: the retained metadata's SHA-256 must equal the
`metadata_digest` the input set declares, and the retention record's source URL
must be the declared repository, so attribution cannot be satisfied by whatever
repository happens to sit in that directory. Verified failure-sensitive by
adding a real `updates` package (`coreutils-9.10-5.fc44`) to a copied manifest,
which is the exact signature of the fault that fail-opened, and by tampering
with both anchors. **Its limit**: an identical NEVRA rebuilt and published
elsewhere would pass, because the manifest carries no per-package checksum to
compare.

`T3-SLICE-001` inspects a composed artifact without booting it: the manifest's
distribution, release, architecture, and output format must match the declared
input set, every closure entry must be fully identified, the UKI must carry its
required sections, its `.uname` must be the closure's `kernel-core`, and the
UKI stored on the ESP inside the disk image must be **byte-identical** to the
standalone UKI composition emitted. Those two files have different names, so
only their content can establish that the machine boots what was built. The ESP
is read through mtools at a byte offset in the plain file, so the image is
never attached to a loop device or mounted, and the ESP's location is read from
the GPT rather than assumed.

`T3-SLICE-003` asks a narrower question about the same artifact: was it built
with the signing material published beside it. The failure it exists for is an
artifact that outlived its own key. Key generation is guarded on the certificate
existing and mkosi declines to rebuild when the output exists, so regenerating
the verity key and re-running the composition leaves a new certificate beside an
image still carrying the old signature -- measured 2026-08-12 while implementing
amendment 4, where it read as success because every check then available looked
at the build root rather than at the image. `compose.sh` therefore publishes the
certificate on **every** run, whether or not mkosi rebuilt: that is what makes
the divergence visible instead of silent.

The assertion is by content and needs no filesystem driver. The certificate is
staged into `/usr/lib/verity.d`, and EROFS stores a file that small contiguously
and uncompressed, so its exact bytes appear in the image; measured, the current
certificate appears once and a superseded one not at all. Verified
failure-sensitive against two injections: publishing the superseded certificate,
and removing it. The second fails rather than passing quietly, because an
artifact directory that cannot answer this question must not report that nothing
is wrong.

It **finds bytes; it does not verify a signature**. `T3-SLICE-004`, registered
by PLN-0002-11 now that the verity signature partition exists, is the check that
does.

`T3-SLICE-004` binds the root hash to the UKI, statically and offline. The UKI's
signed `.cmdline` must carry exactly one `usrhash=`; its two halves must be the
`/usr` and `/usr`-verity partition UUIDs, which is how the Discovered Partition
Specification binds a root hash to the partitions it covers; the verity
signature partition's payload must name the same root hash; its
`certificateFingerprint` and the certificate embedded in the CMS blob must both
be the certificate published beside the artifact; and the detached CMS signature
over that root hash must verify against it. Partitions are found by DPS **type**
UUID rather than by this repository's labels, because the type is what systemd's
dissection reads. Verified failure-sensitive against six injections.

Its boundaries are stated in its own report. It **does not verify the hash tree
against the data** -- an image whose `/usr` was replaced and whose UUIDs, root
hash and signature were reissued consistently passes, and `veritysetup verify`
in `src/slice/measure-corruption.py` is that assertion -- and it **anchors trust
on the certificate shipped beside the artifact**, so it says the signature is by
that certificate, never that any machine trusts it.

`T4-SLICE-002` boots the artifact and asserts the two runtime properties
DES-0006 C-013 depends on: `/usr` is read-only, and nothing in `/etc` is
durable. The probe writes rather than reading mount options, because `/usr`
mounted `ro` is not the same claim as `/usr` cannot be written. It also checks
that `/usr` comes from a device-mapper device: mounted straight off the
partition, every read-only assertion would still pass with no verity underneath.
Durability is a disjunction -- a write to `/etc` must be refused outright, or
must land on a volatile filesystem -- with the general form checked behind it:
no block-backed mount is writable anywhere. Measured on both arms, the `/etc`
overlay is mounted `ro` with lowerdirs only and no upperdir, so writes are
refused. It runs under the same two TPM masks as `T4-SLICE-001` and names them
in its result. It says nothing about authentication; a successful mount is not a
signature claim. Verified failure-sensitive against seven mutated observations
and one boot in which the probe never ran; details and the accepted-by-design
case are in the [check updates](slice-check-updates.md).

Composition needs the network, and canonical validation is offline, so the
artifact is an operator-declared input:

There are three such declarations, and `sandbox.deny_env` means each must be
passed through explicitly -- it strips everything otherwise, including mise's
own `[env]`. A complete run with every fixture available therefore needs all
three named, which is what an earlier reading of this section missed by naming
only the first:

```sh
export NEUTRINOS_SLICE_ARTIFACT_DIR=/path/to/mkosi/output
export NEUTRINOS_SLICE_REPOSITORY_DIR=/path/to/retained/repository
export NEUTRINOS_CONFEXT_FIXTURE_DIR=/path/to/confext/fixture
mise run \
  --allow-env=NEUTRINOS_SLICE_ARTIFACT_DIR \
  --allow-env=NEUTRINOS_SLICE_REPOSITORY_DIR \
  --allow-env=NEUTRINOS_CONFEXT_FIXTURE_DIR \
  check:complete
```

**Without them, `check:complete` fails with `blocked=1` or more.** That is deliberate and
follows the contract: a required test that cannot run is blocked, not skipped,
and blocked fails the profile. A complete run that reported green while
silently omitting its artifact evidence would be worse than one that fails.
`check:fast` is unaffected and needs no artifact.
`T4-SLICE-001` boots that artifact in a disposable VM and asserts three things:
it signals readiness under a hostname the **harness** supplied, so the
first-boot configuration demonstrably arrived from outside the image; no unit
failed on the way, read from the serial log; and the artifact is byte-identical
afterwards. It is booted directly under `snapshot=on` with no copy made, so a
mutation would be a real defect rather than an artefact of the harness. First
boot configuration and the kernel command line are supplied as SMBIOS Type 11
credentials, so nothing is baked into the image to make this pass. QEMU is
asked for `accel=kvm:tcg`: KVM where the host offers it, TCG where it does not,
with the same evidence either way. Measured at 72 seconds wall clock under TCG,
and at 18 seconds under KVM once SVM was enabled in firmware setup on
2026-08-10. The evidence fields were identical across both; only the clock
changed. The result records `accelerator_used` alongside `accelerator_requested`, read
from the running VM through QMP `query-kvm` rather than inferred from the host,
because `/dev/kvm` being present does not mean this guest used it. Emulation
remains a permitted outcome and is recorded rather than asserted; what is no
longer possible is a run that fell back to TCG and left evidence
indistinguishable from a KVM run.

Readiness is guest-driven over a notify vsock, implemented 2026-08-10. The
harness reserves a guest CID, listens on an ephemeral vsock port, and passes
the address to the guest as the `vmm.notify_socket` credential; stock systemd
connects back and says `READY=1`. **Nothing is added to the image** -- no
agent, no notify client, no extra package -- so the artifact whose digests the
composition record pins is the artifact that runs. Measured at 13.2 seconds
against the serial `login:` marker's 15.4, and it asserts something stronger:
a prompt is a getty having started, `READY=1` is pid 1 declaring the boot
transaction complete. The hostname is now read from the notify stream's
`X_SYSTEMD_HOSTNAME` rather than pattern-matched out of the login banner.

Each sd_notify is its own connection, so the listener accepts in a loop;
accepting once yields only systemd's early handshake and never the readiness
message. Where `/dev/vhost-vsock` is unavailable -- a container, a locked-down
CI runner -- the test falls back to the serial marker and records
`readiness_source: serial-marker`, so a degraded run is legible as one. Both
paths and both new assertions were verified failure-sensitive. Driving commands
inside the guest, the ssh-over-vsock half of the RES-0013 decision, remains
unimplemented and would require adding a package to the image; see
[RES-0013](../research/comparisons/vm-test-harness.md).
`T5-VAL-001` runs the hostile validation-runner probes. `T5-VAL-002` starts
with an isolated empty mise cache and runs the registered `check:list` task
using only the already-installed locked Python and uv inputs. `T5-VAL-003`
clones committed `HEAD`, builds the clone's declared environment offline, runs
the clone's own fast profile, and asserts the clone is unmodified afterward.

`T5-VAL-003` is registered in the complete profile only. Registering it in the
fast profile would make that profile clone and re-run itself, and the fast
profile must stay fast. It requires the declared uv cache to already hold the
locked packages, because canonical validation is offline; a cold cache fails
the test with that reason rather than reaching the network.

Each execution writes `run.json`, `results.jsonl`, and bounded per-test logs to
the printed temporary run directory outside the checkout. A dirty-checkout
pass is development feedback only.

The runner gives registered child tests one unique synthetic canary and scans
each log, result record, declared artifact, and the proposed manifest before
retention. It also recognizes a conservative set of private-key, AWS-key,
GitHub-token, and bearer-token markers. A finding fails the run, moves the raw
file into a private `neutrinos-validation-quarantine-*` directory outside the
run directory, and leaves only a content-free placeholder and finding metadata
in the uploadable result. `run.json` reports the quarantine path locally but
never the canary value or matched content. Symlinks and other non-regular
retained outputs are quarantined rather than followed.

Argument-validation, preflight, and selection failures also write a run
directory and report their failure stage. When no test began, `results.jsonl`
is present and empty. Diagnostics retain rejected environment names but never
their values, and arbitrary malformed argument values are not echoed. The
read-only `check:list` query does not create an execution result.

Pytest metadata persists at
`${XDG_CACHE_HOME:-$HOME/.cache}/neutrinos/validation/pytest`. Canonical
profiles never use `--last-failed`, `--failed-first`, or other cache-dependent
selection. The cache is reconstructible local state, not evidence; it may be
deleted while validation is not running. CI must begin with an empty cache and
must not restore or upload it. Do not redirect it into the checkout or merely
gitignore it: checkout-preservation checks intentionally include ignored state.
The task dispatcher declares the resolved path after mise establishes its
deny-environment sandbox, and the runner rejects an absent, relative, or
in-repository value. It likewise declares the exact resolved Python and uv
installation roots; the runner rejects missing, relative, non-directory, or
in-repository roots.

`T5-VAL-002` never deletes or substitutes the operator cache. It creates
private HOME, XDG, mise cache/config/data/state, system-config, and trust-state
directories; prevents config discovery above the repository; links only the
local Python and uv installation families; and runs nested `check:list` under
the repository's offline and no-auto-install settings. Its retained log records
that the cache began empty, the exact locked executables resolved beneath the
declared installations, and every cache file created. Only mise's local
per-version `bin_paths-*.msgpack.z` resolution record is permitted; any other
cache file fails the test. This is repeatable development/CI result evidence,
not qualification retention.

## Admission standard for a new check

Ruled 2026-08-15 by Jason Tarasovic, under PLN-0002-11. A convention, revisable
on evidence; the accepted [validation contract](validation-contract.md) governs
what a registration *declares* and has never spoken to who registers or when.

**Registration belongs to whichever task first needs the assertion enforced**,
which in practice is the task that measured the thing. Authoring belongs with
whoever holds the fixture and the evidence; a later task rewriting it from
scratch re-derives what the measurement already knew. A dedicated suite task
keeps the separate obligation of auditing that every registered check is still
true of the current artifact, which no single measuring task can do.

Before a check is registered it must:

- **reject something.** Failure sensitivity against at least one injection, with
  the injections named where the check is documented. A check shown only to
  accept is not evidence -- and both checks PLN-0002-11 added passed their
  baseline while fail-opening under injection;
- **be reachable through `mise run`** with its declared environment passed by
  `--allow-env=`, verified rather than assumed. `sandbox.deny_env` strips
  everything else, and `T4-CONFEXT-001` was registered and unreachable for a
  period because of it;
- **declare its capabilities**, so an absent fixture blocks and fails the
  profile rather than skipping;
- **state its timeout against the profile budget.** `complete` now carries
  roughly seven guest boots across `T4-SLICE-001`, `T4-SLICE-002` and
  `T4-CONFEXT-001`; each check that adds "just one boot" is spending a shared
  budget no single task can see. A deferred registration declares its budget
  and spends none of it until the deferral is lifted, which is part of what
  lifting one costs; and
- **be documented here**, with what it establishes and what it does not.

## Deferred checks

Ruled 2026-08-15 by Jason Tarasovic, under PLN-0002-11. The accepted
[validation contract](validation-contract.md) already defines `deferred` --
`complete` "never silently includes ... a deferred test", the manifest lists
every registered test with its reason, and `deferred` is "valid only when
already justified in the governing requirements-to-test trace". Nothing had
needed it, so nothing implemented it. These two do.

A registration declares deferral by carrying a justification: `Test.deferred`
is that text, and it must name the trace that carries the deferral. The runner
then guarantees, in four places rather than one, that a deferred check cannot
be mistaken for coverage:

- **selection** excludes it from `fast` and `complete`, so it produces no
  result at all -- not `passing`, not `blocked`;
- **`check:run <ID>`** on a deferred ID is a selection error. Reporting the ID
  unknown would be false and running it would defeat the deferral;
- **the runner-private `_execute` path** refuses it, closing the last route by
  which it could report success; and
- **the manifest** carries it under `omissions` with `"state": "deferred"` and
  the declared justification as its reason, and `counts.deferred` reports the
  deferred registrations belonging to the profile that ran. `check:list` shows
  a `STATE` column, because a deferred check that listed identically to a
  running one reads as coverage the profile does not have.

Deferral does not fail the profile. What fails is **lifting one without writing
the assertion**: `tools/validation/slice_signature.py` holds bodies that report
"not implemented" and return nonzero, so removing a `deferred=` declaration
turns the profile red rather than green. A deferred registration whose body
returned zero would be this plan's ninth fail-open and the worst of them,
sitting in the registry looking like coverage of the one requirement the
artifact does not meet.

`T4-SLICE-003` and `T4-SLICE-004` are the two, both tracing `SYS-049` to
PLN-0002-10. That task measured a `/usr` verity signature by the **enrolled**
authority over a root hash the image does not carry (`sig-foreign`), and one by
an **unenrolled** authority (`sig-wrong-key`), each booting to `running` with
zero failed units under firmware whose `db` carries the verity signer. They are
registered separately because they are distinct substitutions with distinct
diagnostics, and one check would hide whichever half was fixed first. Neither
asserts the observed behaviour: a check that encodes a fail-open passes because
the mechanism is broken and goes red when it is fixed. They assert what SYS-049
requires, which is why they are deferred rather than failing -- until `S-005`
decides the mechanism, there is no refusal to assert, because the kernel
refuses a signature it has no key for and `systemd-veritysetup` retries without
it. The measurement itself stays in `src/slice/measure-substitution.py` and the
[substitution records](artifact-substitution-records.md); what these
registrations carry is the obligation, so it survives PLN-0002 closing.

## Current implementation boundary

The Python 3.14 runner implements named registration and selection, exact
runner and child environment allowlists, per-test process groups and timeouts,
live bounded output capture, interruption and descendant cleanup,
machine-readable results, synthetic-canary and conservative credential-marker
scanning, out-of-result quarantine, and before/after identities covering Git,
untracked, and ignored checkout state. Mise blocks inherited environment and
network syscalls around the complete task and prevents acquisition before task
launch. `T5-VAL-001` exercises these failure boundaries with synthetic
processes. `T5-VAL-002` retains the empty-mise-cache acquisition-boundary
result.

PRE-015 is satisfied. The empty-cache and bootstrap-boundary increments are
accepted. Clean-checkout profile evidence is obtained: a fresh clone at
`42f23b9`, bootstrapped exactly as documented above, passed `check:fast` and
`check:complete` at `passing=4 failing=0` and left the checkout clean. The
pinned least-privilege CI workflow is deferred to PRE-017. When written it must
set the bootstrap configuration variables above for canonical invocation too:
config-discovery isolation cannot be declared in `mise.toml`, so canonical
local runs still admit ancestor and global configuration. That boundary is
proposed in
[PR-0025](reviews/0025-config-discovery-boundary.md) and awaits review.
