---
id: RES-0008
title: Supply-chain evidence standards comparison
status: in-review
date: 2026-08-10
evidence_cutoff: 2026-08-10
decision_gates: [L-002, L-006, L-007]
---

# Supply-chain evidence standards comparison

## Question

Which existing standards can represent NeutrinOS provenance, SBOM,
reproducibility, vulnerability, and VEX evidence without collapsing their trust
claims or requiring a custom general-purpose evidence model?

The comparison selects leading candidates for an exercise. It does not assert
that generating a conforming document provides the assurance described by that
standard's higher security levels.

## Standards and current versions

### SLSA and in-toto

The [SLSA v1.2 specification](https://slsa.dev/spec/v1.2/) defines separate
Build and Source tracks and recommends provenance and verification-summary
attestation formats. Its
[Build Track](https://slsa.dev/spec/v1.2/build-track-basics) distinguishes
provenance existence at Build L1 from hosted signed provenance at Build L2 and
a hardened build platform at Build L3.

The [SLSA provenance model](https://slsa.dev/spec/v1.2/provenance) describes
where, when, and how artifacts were produced. Its verification guidance
requires checking builder identity, envelope authenticity, build type, and
external parameters against expectations; storing a provenance document
without that verification is not a control.

The
[in-toto Attestation Framework v1 envelope](https://github.com/in-toto/attestation/blob/main/spec/v1/envelope.md)
separates a typed Statement/predicate from its authentication envelope and
recommends DSSE. This is a good fit for NeutrinOS's exact subject identity and
authority separation. It is not itself a storage or promotion system.

**Finding:** Use SLSA v1.2 build provenance in an in-toto Statement as the
leading build record. Treat SLSA level as a separate assessed claim. Use DSSE as
the leading envelope candidate, not an accepted cryptographic decision.

### SPDX 3.0.1

[SPDX 3.0.1](https://spdx.github.io/spdx-spec/v3.0.1/) is the current SPDX
standard and provides profiles for software, build, security, licensing, and
relationships. It is suitable for detailed source/package/artifact graphs and
license evidence. Its broad model may express more of NeutrinOS's graph in one
standard, but that breadth and newer tooling surface can increase complexity.

**Finding:** Mandatory SBOM challenger and likely best export when licensing or
source/build relationships dominate. Do not assume an SPDX document is a
complete deployment inventory without an explicit coverage statement.

### CycloneDX 1.7

The [CycloneDX specification overview](https://cyclonedx.org/specification/overview/)
identifies 1.7 as current and describes components, services, dependencies,
vulnerabilities, cryptographic assets, and several BOM types. CycloneDX also
defines an official in-toto predicate type for BOMs.

Its [VEX capability](https://cyclonedx.org/capabilities/vex/) represents
exploitability in the context of a product and integrates directly with
component/dependency identity. The integrated operational model may minimize
translation for a small project.

**Finding:** Leading canonical SBOM/VEX candidate. Exercise its handling of
distro package epochs/releases, source RPMs or PKGBUILDs, exact artifact
digests, vendored components, and deployment-scoped assessment.

### CSAF 2.0 VEX

The [OASIS CSAF 2.0 standard](https://docs.oasis-open.org/csaf/csaf/v2.0/os/csaf-v2.0-os.html)
defines structured security advisories and a VEX profile with product trees and
product status. It is strong for producer-to-consumer advisory exchange but may
be heavy for internal per-deployment assessment.

**Finding:** VEX interoperability challenger and useful intake for vendor
advisories; not the leading internal assessment representation.

### OSV schema and Package URL

The [OSV schema](https://ossf.github.io/osv-schema/) represents affected
ecosystem packages, explicit versions or version ranges, aliases, references,
and ecosystem-specific data. It is useful for normalizing source records while
retaining their identity. The OSV.dev service aggregates many sources but is
not universally authoritative and does not remove distro backport analysis.

The [Package URL specification](https://github.com/package-url/purl-spec/blob/main/PURL-SPECIFICATION.rst)
provides standard package coordinates across ecosystems. A PURL does not encode
literal bytes and can omit distro qualifiers relevant to a patched binary.

**Finding:** Use OSV as the leading normalized vulnerability-input shape and
PURL as one correlation key. Preserve native distro/source identities, exact
digests, source records, and match method.

### Reproducible Builds definition

The [Reproducible Builds definition](https://reproducible-builds.org/docs/definition/)
requires that any party given the same source, build environment, and
instructions can recreate bit-for-bit identical specified artifacts. Its
[build-environment guidance](https://reproducible-builds.org/docs/perimeter/)
emphasizes explicitly defining the tools, versions, OS assumptions, locale,
timezone, paths, user, and other relevant environment.

**Finding:** Use this strict meaning for `bit-reproducible`. Record build replay
and same-builder repeat results separately. Never call an unsigned-payload
comparison reproduction of a different signed artifact.

## Comparison by responsibility

| Responsibility | Leading candidate | Challenger or complement | NeutrinOS-specific policy still required |
| --- | --- | --- | --- |
| Build provenance | SLSA v1.2 provenance | SPDX Build profile | Material completeness, builder expectations, actual SLSA-level assessment |
| Typed attestation | in-toto Statement v1 | Native SPDX/CycloneDX document authentication | Subject policy, producer authority, storage, conflict handling |
| Envelope | DSSE | Other in-toto-compliant or project authority envelope | Key custody, rotation, offline verification, release-authority separation |
| Deployment SBOM | CycloneDX 1.7 JSON | SPDX 3.0.1 | Coverage, native distro identity, opaque/vendored content, owner boundary |
| License/source exchange | SPDX 3.0.1 | CycloneDX | License policy and source availability decisions |
| Vulnerability normalization | OSV schema | Native distro/vendor formats | Source authority, acquisition identity, conflict and backport analysis |
| Package correlation | Native identity + digest + PURL | CPE or source revision where applicable | Exact mapping to deployment, architecture, configuration and package snapshot |
| VEX/assessment | CycloneDX 1.7 | CSAF 2.0 VEX | Authority, evidence, expiry, copying rules, rollout/withdrawal consequence |
| Reproduction result | Reproducible Builds semantics plus a small typed result | SLSA verification summary/in-toto custom predicate | Compared artifact boundary, independent builder identity, failure policy |
| Evidence-set index | Small generated NeutrinOS record manifest | OCI referrer/index or another publication mapping later | Acyclic joins, retention references, purpose and policy identity |

## Why one universal document is rejected

SPDX and CycloneDX can represent several evidence classes, but using one schema
for everything would still not solve:

- which producer is authorized for a claim;
- whether the producer was compromised;
- which policy verified a record;
- which exact qualification authorized promotion;
- which post-release assessment is current;
- whether offline cached knowledge is acceptably fresh; or
- which missing fields mean unknown rather than absent.

Native records should remain native. The evidence-set manifest only joins their
identities and declared roles.

## Required semantic tests

### Subject identity

Every format must bind the exact artifact or deployment digest rather than only
a name/version. Conversion must preserve native package identity and the source
relationship in addition to PURL.

### Completeness and unknowns

The tool must distinguish an empty set from incomplete coverage. Opaque binary,
vendored code, unparsed initrd, missing source attribution, and unavailable
advisory data remain explicit.

### Time and mutation

Immutable build/SBOM evidence and mutable-world assessments must remain
separate. A later VEX or advisory cannot rewrite the promoted evidence set.

### Assurance

A schema-valid, signed record can still be false. Verification must evaluate
the producer, subject, expected process, format version, completeness, and
applicable trust/assurance policy.

## Recommendation

Start EX-0010 with:

- SLSA v1.2 provenance predicates in in-toto Statements;
- DSSE as the leading evidence envelope;
- CycloneDX 1.7 JSON as the leading deployment SBOM and VEX format;
- SPDX 3.0.1 as the mandatory SBOM/source/license challenger;
- native vendor/distro advisories retained literally and normalized into an
  OSV-shaped record for matching;
- native package identity plus content digest and PURL for correlation; and
- the strict Reproducible Builds definition for byte-level claims.

Accept none of these by name until the exercise demonstrates round-trip
identity, coverage, semantic loss, version pinning, offline validation, and
operator effort. A format choice should become an ADR only when changing it
would affect external interoperability or stored evidence policy.
