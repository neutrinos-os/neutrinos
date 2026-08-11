---
status: active
last_updated: 2026-08-11
governing_plan: PLN-0001
---

# Reference-VM slice input declaration

This records what the slice's declared input set contains and, for each input,
what makes it exact. It is the PLN-0001-01 deliverable together with
`src/slice/input-set.toml` and `src/slice/schema/input-set-v3.schema.json`.
PLN-0002-02 carried it to version 3; the record stays PLN-0001's deliverable and
the addition is marked where it lands.

Exactness here means one thing: the input names a specific immutable byte
sequence, and a substitution is detectable. A version string, a branch name, a
mirror URL, or a repository that is republished on a schedule are all labels
that resolve differently at different times, and none of them is an identity.

## Representation

TOML 1.0 in the restricted JSON-compatible profile, validated structurally
against JSON Schema Draft 2020-12, per
[ADR-0003](../adrs/0003-bounded-fleet-intent-representation.md). The record
declares an immutable schema identifier and version; unknown fields and
unsupported versions fail rather than degrade.

The schema validates structure only. It does not check that a digest matches
the bytes at a URL, that a repository is reachable, or that a commit exists.
Those are composition-time obligations under SYS-057 through SYS-059, and
stating the boundary here is the point: a record that passes validation is
well-formed, not verified.

## What makes each input exact

| Input | Identity | Why that is exact |
| --- | --- | --- |
| Source | Full 40-character commit object name | Content-addressed over the whole tree and history. The schema rejects anything that is not 40 hex characters, so a branch or tag cannot be declared, because both move |
| Package snapshot | Frozen release repository plus recorded `repomd.xml` digest and the repository's own metadata revision | Fedora's release tree is immutable after GA, and its metadata filenames are content-addressed. The digest makes a silent republication detectable; the revision makes it attributable |
| Repository list | The complete, finite, ordered list | Precedence is declaration order. Any repository not named here is undeclared, and resolution from it must fail closed under SYS-059. A glob or a discovery step would make the closure unbounded |
| Tool identity | Git commit or SHA-256, with the kind declared alongside | A version string is a label the upstream can retag. The `identity_kind` field forces the record to say what the value actually is, and the schema constrains the format to match |
| Fleet intent | Named role and machine with explicit `common < role < machine` layer order | SYS-044 fixes the precedence. Declaring it rather than assuming it makes a violation observable in the record instead of implicit in composition code |

## Schema version 2

Version 1 modelled every tool as a single pinned executable. The package
manager that resolves the image is not that: it is a constructed set of
packages in a tools tree, and version 1 offered no way to declare it. Leaving
it undeclared would have put a moving input in the position that decides what
the image contains, which is the failure the whole declaration exists to
prevent. Version 2 adds `tools_tree` and is required, so a version 1 record no
longer validates.

The tools tree is declared by recipe -- a digest-pinned base image plus exact
packages from the frozen repository -- rather than by its own digest, because
exporting the tree produces unstable timestamps and its digest would change
without any input changing.

## Schema version 3

Added by PLN-0002-02. Version 3 adds `packages.overlays`, and it exists because
PLN-0002 needs a systemd newer than the frozen Fedora release carries:
DES-0006 C-013 names `systemd-confext-sysroot.service` as the mechanism that
merges a confext into the real `/etc` before switch-root, and that unit is new
in systemd 261 while Fedora 44 stays on the 259.x series.

Version 2 offered two ways to express that and both were worse. A second
repository would have retired the guarantee `LocalMirror=` enforces by
construction -- that exactly one repository exists -- which is the guarantee
F-RES-01 recorded as not holding by convention. An undeclared local directory
would have been the undeclared acquisition path itself.

An overlay is therefore declared, injected as a local package directory rather
than as a repository, and pinned **file by file with a SHA-256**. That is
stricter than a repository declaration, which pins metadata and takes package
identity from it, and it is stricter for a reason: the declared source is a
continuously republished nightly that upstream replaces in place, so the URL is
where the bytes came from and the digests are what they are. `reason` is a
required field. An overlay with no stated reason is a preference, and a
preference is not an input.

The overlay list is optional. An overlay is a deviation from the release
closure, and a declaration with none is the ordinary case.

## Deliberate omissions

Each of these is absent by decision, not oversight. Recording them here stops a
later task from adding one as though it were always intended.

- **The Fedora `updates` repository.** It is republished continuously and
  cannot be an exact input. Excluding it means the slice builds GA package
  versions and nothing newer, including no security updates. That is the cost
  of exactness for a disposable VM that makes no availability or vulnerability
  claim, and it would not be acceptable for a machine that did.
- **QEMU and the boot environment.** They execute the artifact but cannot change
  what composition produces. Pinning them in a composition-input record would
  put an identity where nothing checks it. The boot tool's identity belongs to
  PLN-0001-03's evidence.
- **The resolved package closure.** SYS-058 requires the complete resolved
  binary closure with exact package bytes, and that is generated evidence from
  PLN-0001-02, not an operator-authored input. Hand-authoring it would make the
  declaration a second, divergent definition of what composition resolved.
- **Any storage, encryption, or partition input.** Open under S-004 and
  deferred to G2.

## Candidate status

Fedora 44 and mkosi v26 appear here as concrete values because a declaration
with placeholder values would validate while proving nothing. They remain
candidate fixtures under PLN-0001, and bootc and a literal Arch snapshot remain
the required challengers. Repeated successful use of a value in this file is
not a decision and does not become one; see
[PR-0029](reviews/0029-g1-gate-approval.md) C-005.

## Verification performed

The instance validates against the schema, and the schema rejects eleven
constructed violations: a rolling repository, a branch name as source revision,
an unknown top-level field, an empty repository list, a `git-commit` identity
holding a SHA-256, an undeclared precedence layer, an unsupported schema
version, a tools tree pinned by tag instead of digest, an empty tools
package list, an overlay file with no digest, and an overlay with no stated
reason. A schema that has only ever been shown to accept is untested.

**Closed by PLN-0001-05.** `T2-SLICE-001` now performs this verification on
every `mise run check:fast`, against the schema the record's own `[schema]`
block declares. It reproduces all eleven rejections rather than only the
acceptance, because a schema shown only to accept is untested: an empty schema
would accept just as well.

The violations are expressed as mutations of the committed record, not as nine
fixture files. A fixture file is a copy and copies drift, so a record that
gained a field would leave stale files passing for reasons that no longer
held. The check itself was verified by adding a mutation the schema should
accept and confirming the check failed.
