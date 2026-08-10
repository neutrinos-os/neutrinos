---
id: DES-0007
title: Package inputs and snapshot policy
status: in-review
owners: [Jason Tarasovic]
reviewers: [Codex]
created: 2026-08-10
last_updated: 2026-08-10
depends_on: [DES-0001, DES-0003, DES-0005]
decision_backlog: [L-001, L-002, L-007]
related_adrs: []
---

# Package inputs and snapshot policy

## Problem

NeutrinOS must turn a changing upstream package repository into attributable,
repeatable inputs for exact deployment artifacts. Choosing Arch or Fedora is
not only a choice of package format. It selects an update model, security and
end-of-life process, build recipes, signing hierarchy, third-party ecosystem,
and amount of downstream maintenance inherited by one maintainer.

A mutable mirror URL is not an input identity. A frozen repository is not
necessarily secure or reproducible. A signed package is not proof that its
binary corresponds to reviewed source. An AUR recipe, COPR build, or RPM Fusion
package cannot silently inherit the trust assigned to an official repository.

This design defines the package-input boundary and proposes an initial upstream
without making the target machines package-managed mutable systems.

## Goals

- Select one supportable initial package universe for the reference roles.
- Resolve each build from an immutable, inspectable repository state.
- Preserve the exact package closure independently of upstream retention.
- Keep input identity, signature validity, provenance, vulnerability status,
  qualification, and release authorization distinct.
- Make third-party and project-built software explicit trust boundaries.
- Retain a fair, falsifiable Arch challenger before accepting the selection.
- Make upstream branch migration and end of life ordinary planned operations.

## Non-goals

- Use a package manager to mutate OS-owned files on deployed machines.
- Fork or repackage an entire upstream distribution.
- Promise bit-for-bit reproduction of upstream binary packages.
- Select the publication service, SBOM format, vulnerability scanner, mirror
  software, or build farm.
- Define user, project, container, VM, or GUI-application software placement.
- Admit AUR, RPM Fusion, COPR, or arbitrary upstream binaries by default.
- Maintain several downstream security branches or routinely backport fixes.

## Requirements and constraints

SYS-001, SYS-002, SYS-012, SYS-013, SYS-028, SYS-036, SYS-040, and SYS-041
already require attributable inputs, literal-artifact qualification, minimum
emergency gates, explicit maintenance ownership, independent authorization,
and offline operation after acquisition.

The accepted maintenance policy provides one current NeutrinOS release line
and best-effort response. Retained deployments may be useful rollback choices
without remaining security-current. DES-0005 requires source and composition
evidence to be bounded and inspectable. ADR-0001 prefers systemd ecosystem
mechanisms but does not make either upstream distribution authoritative.

The original design session explicitly left Arch and Fedora undecided. Jason's
Arch familiarity and preference for current system components are real inputs.
So are the cost of unrelated rolling changes during an urgent fix and the wish
not to grow a private packaging distribution.

## Decision drivers

1. A single maintainer must be able to identify, refresh, retain, and qualify
   all OS package inputs.
2. A security fix should not require either unbounded downstream backporting or
   an unnecessarily large unrelated change set.
3. Required systemd, kernel, storage, Wayland, container, and VM capabilities
   must be available without a growing private repository.
4. Repository state and exact package bytes must remain reconstructible after
   mirrors change or upstream retention expires.
5. Package scripts and third-party recipes are executable supply-chain inputs,
   not passive metadata.
6. The same package policy should initially serve VM, workstation, and router
   without requiring every role to install the same closure.
7. Upstream end of life and NeutrinOS currentness must be machine-observable.

## Options considered

### Fedora stable official repositories

Fedora stable supplies maintained release branches, staged updates, source RPM
and dist-git attribution, broad systemd/Wayland/container alignment, and a
bounded end-of-life event. It reduces urgent-response churn relative to a
rolling repository, but introduces periodic branch migrations and may lack a
new upstream feature until the next release.

Fedora's public repositories are not assumed to be a permanent timestamped
snapshot service. NeutrinOS must preserve the metadata and package bytes it
actually used.

### Arch official repositories at a dated archive state

Arch supplies current components, simple packaging, owner familiarity, and
daily official-repository snapshots in the Arch Linux Archive. Its supported
model is a coherent full rolling upgrade; holding or selectively updating part
of an old snapshot is not a security-maintenance strategy. Emergency updates
can therefore carry a larger unrelated change set.

### Fedora Rawhide

Rejected as the normal source. It improves feature currency while discarding
the stable-branch update and end-of-life properties that distinguish Fedora in
this decision. It remains useful only as research or a source for an explicitly
owned future package.

### Multiple upstream distributions by role

Deferred. DES-0001 permits different artifact shapes, but two upstream package
universes multiply advisory interpretation, build behavior, source retention,
and qualification. A second universe requires a demonstrated role requirement
that outweighs that cost.

### Build every package from upstream source

Rejected. It would turn NeutrinOS into a general package distribution and make
the sole maintainer responsible for integration and security work already done
upstream.

## Proposed decision

Use one supported Fedora stable release branch as the initial primary package
universe for the reference VM, `desktop-jason`, and `router`. Use only the
official release and stable-update repositories by default. Rawhide,
updates-testing, COPR, RPM Fusion, and other repositories are not implicit
sources.

The selected Fedora branch is a versioned build input, not the identity of
NeutrinOS and not a runtime update channel. Select the newest stable branch
that satisfies the required capability floor and leaves a practical
qualification window. If fewer than six months of upstream support remain at
initial adoption, explicitly justify using it instead of qualifying its
successor.

For every build candidate, create a NeutrinOS **package input snapshot**:

1. declare the upstream distribution, release branch, architecture, enabled
   repository identities, trust keys, and repository policy;
2. acquire and hash the exact repository metadata used for resolution;
3. solve the complete role-specific package closure with no undeclared source;
4. verify package signatures and record exact NEVRA, content digest, source RPM,
   repository, reason, and dependency edges;
5. retain the metadata and literal package bytes in a project-controlled,
   content-addressed intake store;
6. run package installation and scriptlets in an isolated builder without
   release-signing keys, machine secrets, or undeclared network access; and
7. bind the input-snapshot identity and resolution evidence into the build and
   deployment provenance.

The preserved intake store is the reproducibility boundary. An upstream URL,
mirror timestamp, DNF cache, package name, or NEVRA alone is insufficient.
Upstream signatures authenticate accepted upstream packages; NeutrinOS release
authorization applies later to qualified deployment outputs and does not
replace that verification.

### Source classes

| Class | Initial policy | Required evidence |
| --- | --- | --- |
| Fedora official binary RPM | May enter after snapshot resolution and signature verification | Repository metadata, RPM identity and digest, signature result, source RPM and maintenance owner |
| Fedora source RPM/dist-git | Evidence and rebuild input; not automatically rebuilt | Source identity, recipe revision, sources, patches, build reference |
| NeutrinOS-built RPM | Exceptional owned overlay for a missing capability or accepted patch | Pinned sources, reviewed spec/patches, isolated build closure, tests, owner and removal/upstream condition |
| RPM Fusion or COPR binary | Not enabled as a transitive repository; explicit binary-import exception only | Repository and key identity, exact binary/source attribution, license, maintenance owner, isolation and qualification |
| AUR recipe | Research lead only under the Fedora decision | Reviewed pinned recipe and upstream sources; it does not enter the image or intake store directly |
| Upstream binary blob | Exceptional binary-only import | Publisher identity, digest/signature, license, update owner, sandbox boundary, vulnerability source and replacement/removal trigger |

Third-party intake is per package or reviewed finite set, never blanket trust in
a repository merely because its metadata is signed. Prefer an official Fedora
package, then an upstreamed Fedora package, then a small project-owned source
build. Reject an attractive component when carrying it would create an
unbounded downstream maintenance obligation.

### Branch lifecycle

NeutrinOS tracks one Fedora branch as current. Moving from Fedora N to N+1 is a
new package-input baseline and full release qualification event, not an in-place
machine distribution upgrade. During qualification, deployments from both
branches may be retained, but only one NeutrinOS release line is current.

The migration plan must begin early enough to qualify the successor before the
selected branch reaches end of life. Once upstream maintenance ends, affected
deployments become stale and then unsupported under explicit policy; local
retention does not extend upstream support.

### Arch challenger

Before accepting Fedora, EX-0009 must build equivalent VM, workstation, and
router closures from:

- one Fedora stable package input snapshot; and
- one dated, coherent Arch official-repository snapshot.

The comparison must measure required-feature availability, missing packages,
custom-package count, closure and image size, update churn, security-fix
workflow, metadata and byte retention, source attribution, build-script side
effects, mkosi behavior, and maintainer effort. Arch wins if Fedora requires a
material private overlay or branch work that costs more than qualifying whole
Arch snapshots.

## State and compatibility

Package input snapshots and build evidence are release-owned records. They are
not deployed mutable state. The installed RPM database may remain in the
read-only root as inventory evidence, but DNF is not a supported mutation path
on a target.

Changing a repository, branch, package set, weak-dependency policy, solver,
macro set, install script behavior, or project overlay changes the composition
record and may change deployment identity. State compatibility continues to be
governed by DES-0002; a package branch migration cannot silently migrate
machine, user, or workload state.

## Security and trust

The design protects against mirror mutation, dependency confusion across
undeclared repositories, loss of old package bytes, accidental partial input
mixing, and unreviewed third-party build recipes. It does not prove that an
upstream maintainer, signing key, build system, or source is uncompromised.

Repository and package signatures, source attribution, reproducibility,
vulnerability status, qualification, and NeutrinOS authorization remain
separate evidence. Repository keys have an explicit trust and rotation policy;
key expiry or revocation cannot be “fixed” by disabling signature checking.

Package scriptlets, triggers, macros, dependency generators, and project build
recipes execute inside the trusted build path. The builder exposes no release
private key or fleet secret, uses declared network inputs only during
acquisition, and records filesystem output and relevant script diagnostics.

## Failure and recovery

- Missing or changed metadata/package bytes fail acquisition; a mirror fallback
  may supply only the identical expected content.
- An unavailable upstream does not affect already-built deployments or their
  local boot and rollback behavior.
- A lost intake object blocks reproduction and must be visible; it does not
  authorize silent re-resolution from a current mirror.
- A signature, dependency, license, or source-attribution failure blocks the
  candidate before artifact qualification.
- A branch reaching end of life marks currentness/support status and triggers
  migration; it does not mutate a running deployment.
- A compromised upstream or repository key triggers affected-input analysis,
  release withdrawal as applicable, rebuild from a trusted baseline, and the
  accepted authority/recovery process.

## Operations and diagnostics

For any file in a deployment, the operator should be able to trace the owning
package, literal package digest, source package/recipe, repository snapshot,
input owner, build, qualification, and release. For any input package, the
operator should be able to enumerate every deployment that contains it.

Input refresh produces a reviewable delta: added, removed, upgraded,
downgraded, source-changed, signature/key-changed, dependency-reason-changed,
and license-changed packages. A release gate distinguishes routine refresh,
branch migration, project-overlay change, and emergency security response.

## Verification

The design cannot be accepted until EX-0009 demonstrates:

1. equivalent Fedora and Arch closures for all three reference variants;
2. offline rebuild of the image tree from only the preserved input snapshot;
3. failure on mirror mutation, missing objects, mixed repository states,
   changed keys, unsigned packages, and undeclared repositories;
4. bidirectional file-to-source and package-to-deployment attribution;
5. a representative routine refresh and critical security update on each
   candidate, including unrelated churn and skipped-test evidence;
6. one Fedora branch-migration tabletop and one Arch rolling-snapshot
   regression tabletop;
7. an isolated package-script test proving signing and fleet secrets are absent;
8. a third-party source and binary-only intake exercise; and
9. measured owner time, storage, closure size, build time, and qualification
   expansion.

## Risks and unresolved questions

- Does Fedora stable contain sufficiently current systemd and kernel features
  for DES-0006 without a private overlay?
- Can exact Fedora repository metadata and package bytes be captured and
  retained simply enough for one maintainer?
- Which weak-dependency and package-exclusion policies produce the smallest
  honest role closures without diverging from Fedora assumptions?
- How are Fedora advisories joined to exact source/binary package identities?
- Which required workstation capabilities would force RPM Fusion, COPR, or an
  upstream binary exception?
- Should selected source RPMs be independently rebuilt for verification, and
  at what risk threshold?
- How much overlap is required while qualifying a Fedora branch migration?
- Does one universe remain justified for future storage or microVM roles?

## Accepted requirements

PR-0010 accepts SYS-057 through SYS-064. They define immutable resolution,
closure retention, coherent repository state, freshness, third-party intake,
build-code isolation, and upstream lifecycle behavior without accepting Fedora.

## Review disposition

The design is in adversarial review. RES-0007 supports Fedora as the leading
candidate, while EX-0009 is required before the ecosystem selection can become
an ADR. The policy requirements were accepted on 2026-08-10 independently of
that selection.
