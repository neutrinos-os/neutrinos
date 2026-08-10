---
id: PR-0010
subject: Package input and snapshot requirements
reviewer: Codex adversarial pass
date: 2026-08-10
status: accepted
---

# Package input and snapshot requirements review

## Decision scope

This review asks whether SYS-057 through SYS-064 should become normative before
NeutrinOS selects Fedora or Arch, repository/mirror software, an SBOM format,
vulnerability tooling, a build service, or a publication protocol.

It reviews the package-input boundary in DES-0007. It does not accept Fedora as
the initial package ecosystem; that decision requires EX-0009 and an ADR.

## Summary judgment

The requirements should be accepted independently of the ecosystem selection.
They prevent a mutable mirror URL from becoming provenance, a valid signature
from becoming qualification, an immutable old snapshot from appearing current,
and a convenient third-party repository from becoming an unbounded trust root.

The strongest objection is project growth. Exact metadata retention, complete
closure evidence, source attribution, isolated package execution, and
third-party intake can become a private repository platform. The requirements
therefore define observable guarantees, not custom infrastructure; the
exercise must prefer small existing tools and literal object retention.

## Accepted requirement disposition

### SYS-057: Immutable repository resolution

Every package resolution names the distribution, branch or release,
architecture, repositories, priorities, trust policy, exact metadata identities,
solver, and dependency policy. A mutable URL, date, package name, or version
string alone is not input identity.

### SYS-058: Complete retained package closure

The build records and retains every exact binary package and repository metadata
object needed to reconstruct the resolved image input without re-resolving from
current upstream state. Source/recipe identity and available build evidence are
joined to each binary package. Literal byte retention may use existing
content-addressed repository software; the requirement does not select one.

### SYS-059: Coherent source universe

Resolution fails on undeclared repositories or accidental mixing of branches,
dates, architectures, and trust domains. An explicit third-party or project
source can participate only through its declared precedence and provenance and
causes a fresh whole-closure solve and qualification.

This generalizes Arch's no-partial-upgrade constraint without assuming Fedora
packages can safely be mixed arbitrarily.

### SYS-060: Freshness is not immutability

Snapshot identity, byte availability, signature validity, provenance,
vulnerability applicability, upstream support, NeutrinOS currentness, and
qualification are distinct. A newly published advisory can make an unchanged
snapshot stale or unsupported.

### SYS-061: Maintenance and end-of-life ownership

Every included package or project-built component identifies its upstream
branch, maintenance owner, advisory source, and end-of-life or replacement
trigger. Upstream end of life becomes visible before it silently invalidates
the current release line.

This does not promise that upstream advisories are complete; role exposure and
independent incident intake remain necessary.

### SYS-062: Finite third-party intake

A third-party recipe, repository, or binary does not enter merely because the
upstream package manager can consume it. The exact finite input must declare
source, license, recipe/build or binary publisher, maintenance owner,
vulnerability source, isolation, qualification, and removal behavior.

A binary-only input is permitted as an explicit limitation, not mislabeled as
source-reproducible.

### SYS-063: Executable build-input isolation

Package scriptlets, triggers, macros, dependency generators, and source recipes
are executable inputs. They run without release-signing private keys, fleet or
machine secrets, or undeclared network access, and their relevant filesystem
effects and diagnostics remain attributable.

This requirement does not claim the initial build system is hermetic against a
kernel or builder compromise. It prevents ordinary package code from sharing
the release-authority boundary by convenience.

### SYS-064: Upstream transition is a qualified release event

Changing the selected upstream branch or package universe creates a new input
baseline and requires full applicable deployment and state-compatibility
qualification. Retaining deployments from the previous branch does not extend
their upstream maintenance or make two NeutrinOS lines current.

## Guardrails from adversarial review

### Do not accept Fedora through these requirements

Both Fedora and Arch can satisfy the policy on paper. The literal closure,
update, third-party, and owner-effort comparison is the decision evidence.

### Do not require universal upstream reproducibility

The project must record what can and cannot be reproduced. Requiring every
upstream RPM or Arch package to reproduce bit-for-bit would reject both usable
inputs or quietly weaken the meaning of reproduction.

### Do not mirror more than the contract needs

The retained boundary is the exact closure, metadata, trust, source identity,
and evidence needed for reconstruction and audit. It need not clone every
package or build artifact in an upstream distribution.

### Do not make the package database a target updater

Keeping RPM or pacman metadata in a read-only root aids attribution. It does
not authorize mutation of OS-owned files or create a second deployment path.

## Strongest rejected alternatives

### Pin only package names and versions

Rejected. Repositories can replace metadata, rebuild versions, vary by
architecture, or change dependency resolution. Names and versions do not
identify the literal build inputs.

### Trust any repository whose metadata verifies

Rejected. Signature validity authenticates a configured repository authority;
it does not assign NeutrinOS maintenance ownership, source review,
qualification, or authorization.

### Download again when an old build must be reproduced

Rejected. Upstream mirrors and archives can remove or replace content, and a
new resolution may choose a different closure. Reproduction depends on retained
literal inputs.

### Freeze indefinitely for stability

Rejected. An immutable vulnerable snapshot is stale, not maintained. Stability
comes from qualifying new deployment artifacts and retaining deliberate
fallback/recovery, not ignoring input changes.

## Required implementation evidence

Acceptance establishes policy only. DES-0007 still requires:

1. populated Fedora and Arch reference closures;
2. offline reconstruction from retained exact inputs;
3. mixed-state, mirror-mutation, key, and dependency-confusion failures;
4. old-valid-snapshot vulnerability/currentness status;
5. hostile package-script isolation;
6. source and binary-only third-party intake;
7. routine, urgent, and major-transition measurements; and
8. bidirectional input-to-deployment and file-to-source attribution.

## Decision

Accepted by Jason Tarasovic on 2026-08-10. SYS-057 through SYS-064 are
normative with the interpretations above. This accepts immutable package-input
resolution, exact closure retention, coherent repository state, distinct
freshness and provenance claims, explicit maintenance ownership, finite
third-party intake, executable build-input isolation, and qualified upstream
transitions.

Acceptance does not select Fedora or Arch. Fedora stable remains the leading
candidate and Arch remains the mandatory challenger until EX-0009 supplies the
literal closure, refresh, transition, and owner-effort evidence required for an
ecosystem-selection ADR.
