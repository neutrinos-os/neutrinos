---
id: PR-0011
subject: Supply-chain evidence and vulnerability requirements
reviewer: Codex adversarial pass
date: 2026-08-10
status: accepted
---

# Supply-chain evidence and vulnerability requirements review

## Decision scope

This review asks whether SYS-065 through SYS-074 should become normative before
NeutrinOS selects SBOM, attestation, VEX, scanner, evidence-storage,
transparency-log, or signing implementations.

It reviews the semantic boundaries in DES-0008 and proposed exercise EX-0010.
It does not accept SLSA, in-toto, DSSE, CycloneDX, SPDX, OSV, CSAF, PURL, or a
SLSA assurance level merely because those are leading representations.

## Summary judgment

The requirements should be accepted. They make evidence useful for decisions
instead of ornamental: every record has an exact subject and owner, promotion
freezes its historical basis, post-release assessment remains append-only,
reproducibility claims name their boundary, and VEX cannot erase findings.

The strongest objection is operational scale. A project can satisfy the words
with a sprawling evidence lake that one maintainer cannot inspect. Acceptance
therefore requires purpose-limited records, direct bidirectional queries, and a
measured personal-fleet cost before the mechanism design is accepted.

## Accepted requirement disposition

### SYS-065: Evidence records have exact semantics and identity

Every evidence record binds exact subjects and claim type, literal format and
schema version, producer/tool identity, generation time, dependencies,
completeness/omissions, sensitivity, verification policy, and its own content
identity. A digest identifies the record but does not establish truth.

### SYS-066: Evidence joins are acyclic and historical

Build, composition, SBOM, qualification, reproduction, vulnerability, and
authorization records reference existing subject identities through
content-identified evidence sets. Promotion records the exact evidence set it
used. Later records append or supersede claims under policy; they do not mutate
deployment identity or historical evidence.

This requirement permits a compact index or native publication relationship;
it does not require a graph database or custom general-purpose schema.

### SYS-067: Provenance exposes production and assurance boundaries

Build provenance identifies exact output subjects, declared material inputs,
builder/platform, build type and parameters, toolchain/environment, isolation,
network/secrets policy, times, completeness, and whether it was builder-
generated or reconstructed. Producer authentication and any SLSA or other
assurance level remain separately verified claims.

### SYS-068: SBOM coverage is exact and owner-aware

Each deployment SBOM binds the exact deployment/artifact subjects and inventories
release-owned package and non-package executable components, native and source
identities, digests, dependencies/containment, and maintainers. Vendored,
generated, opaque, unparsed, and separately owned content is represented or
declared as a coverage gap rather than silently omitted.

The requirement does not make NeutrinOS the update owner for user, workload,
guest, or externally installed firmware software.

### SYS-069: Reproducibility claims name their comparison

Build replay, same-builder byte equality, independent bit reproduction,
semantic comparison, failure, and unassessed status are distinct. Every result
names exact compared subjects, inputs/instructions/environment boundary,
builder trust relation, algorithm, differences or exclusions, and consequence.

This does not require every upstream or signed artifact to reproduce. It
prohibits a narrower comparison from being advertised as reproduction of a
different final artifact.

### SYS-070: Vulnerability intake preserves sources and uncertainty

Vulnerability processing retains exact source records, acquisition and
modification times, identifiers/aliases, source authority, component matching
method, native/source package and deployment mapping, configuration/role,
severity sources, backport/fork evidence, conflicts, and unknown coverage.

No finding means only that declared inputs produced no finding. It does not
mean the deployment has no vulnerabilities.

### SYS-071: Assessment and VEX are scoped, attributable claims

Each applicability, exploitability, reachability, mitigation, accepted-risk,
or negative VEX claim binds the exact deployment/component/vulnerability and
applicable role/configuration, issuer/authority, justification, evidence,
policy, time, expiry/review trigger, and action. It cannot delete the source
finding, imply a fix, or transfer to another subject without re-evaluation.

### SYS-072: New security knowledge changes status, not identity

New or corrected advisories, assessment, VEX, exploit, and compromise facts
reevaluate currentness, support, eligibility, rollout, withdrawal, and recovery
under a named ordering/freshness/conflict policy without changing historical
deployment identity, provenance, SBOM, qualification, or authorization records.

Offline cached decisions disclose their knowledge time and freshness limit.

### SYS-073: Evidence remains available and safely bounded

Evidence required for selected, staged, retained, recovery-referenced,
withdrawn-but-installed, incident-held, or otherwise policy-referenced subjects
survives garbage collection and remains queryable without mutable upstream
services. Each class defines owner, sensitivity, redaction, retention, archive,
loss, and deletion behavior.

This does not require all machine logs or every scanner output to be kept
forever.

### SYS-074: Evidence-producer compromise is traversable

Compromise, revocation, or discovered misbehavior of a source, builder,
attester, qualifier, normalizer, scanner, or assessment authority must identify
every dependent record, deployment, release, and machine and drive explicit
reverification, reassessment, withdrawal, rebuild, requalification, or accepted
risk. Historical records are distrusted or superseded, not erased.

## Guardrails from adversarial review

### Do not turn formats into guarantees

A valid SLSA, in-toto, SPDX, CycloneDX, or VEX document can still be incomplete,
false, issued by the wrong party, or scoped to another subject. Policy verifies
the claim and producer separately from schema validity.

### Do not demand universal SBOM completeness

Completeness is measured by declared component classes and evidence sources.
Opaque and unparsed content must remain visible; requiring invented identities
would be worse than an explicit gap.

### Do not make VEX a deletion operation

VEX adds a contextual assessment. The vulnerability-source record and candidate
match remain available, and expiration or contradiction can reopen the decision.

### Do not create a digest cycle

The deployment manifest establishes D before Q, V, E, or A exists. Later
evidence references D. Promotion binds an evidence set; the manifest does not
mutate to include promotion.

### Do not require the evidence service for local boot

After eligible material and a freshness-bounded local decision are retained,
SYS-041 governs normal offline boot, assessment recording, fallback, and
rollback. Full evidence is for verification and operations, not an online boot
dependency.

## Strongest rejected alternatives

### One signed release metadata file containing everything

Rejected. It creates identity cycles, makes evolving vulnerability status
rewrite historical build facts, and grants one signer authority over claims
produced by builders, tests, and advisory sources.

### Trust the scanner's current database and dashboard

Rejected. Results cannot be reconstructed when feeds, aliases, matching logic,
or product behavior changes. Raw source and processing identity are evidence.

### Require bit reproduction before every release

Rejected. It may be valuable for selected project-built artifacts but is not
currently honest for every upstream package and signed output. Exact claim
status is more useful than a universal checkbox.

### Suppress non-exploitable findings

Rejected. Context can change, assessments expire, and mistakes happen. Preserve
the finding and add a scoped assessment.

### Store evidence only in CI logs

Rejected. CI logs are mutable-service records, are poorly subject-bound, and
may expire independently of retained deployments and incident needs.

## Required implementation evidence

Acceptance establishes policy only. DES-0008 still requires:

1. one acyclic representative evidence graph;
2. hostile, incomplete, forged, and mismatched provenance;
3. CycloneDX/SPDX coverage and semantic-loss comparison;
4. non-package, vendored, generated, opaque, initrd, and UKI inventory;
5. replay, same-builder, independent, excluded-field, and failed reproduction;
6. distro backport, alias, conflict, unknown, and missing-advisory cases;
7. valid, copied, expired, contradicted, and malicious VEX;
8. post-release reassessment and offline freshness;
9. producer-compromise dependency traversal; and
10. schema migration, redaction, retention, loss, and garbage collection.

## Decision

Accepted by Jason Tarasovic on 2026-08-10. SYS-065 through SYS-074 are
normative policy boundaries. DES-0008 remains in review until its required
implementation evidence resolves the concrete formats, mechanisms, and costs.
