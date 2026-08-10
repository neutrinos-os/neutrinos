---
id: EX-0010
title: Representative supply-chain evidence graph
status: proposed
date: 2026-08-10
decision_gates: [L-002, L-006, L-007]
evidence_class: analysis-only
---

# Representative supply-chain evidence graph

## Purpose and evidence limit

Exercise DES-0008 against one representative VM deployment before selecting
formats or tools. This is analysis-only until literal generated artifacts and
verification results replace the placeholders.

The exercise must show which record answers a real decision, which authority
may issue it, and how a later security fact changes status without changing
deployment identity.

## Representative subjects

Use a sanitized deployment variant containing:

- a signed UKI with kernel and initrd;
- immutable root plus Verity artifact;
- exact resolved configuration;
- distribution packages including systemd, a cryptographic library, and one
  remotely reachable service;
- one small project-built package;
- one statically linked or vendored component;
- one non-package script;
- one opaque binary/firmware component; and
- qualification fixtures for a representative role.

Names and digests may be placeholders for the paper pass, but every relationship
must be shaped so literal identities can replace them without changing the
model.

## Evidence graph fixture

| Record | Exact subject | Required claim | Candidate representation |
| --- | --- | --- | --- |
| `P` | Package input snapshot | Repository state, closure, signatures, sources | DES-0007 native record |
| `C` | Resolved configuration | Sources, precedence, rendered outputs | DES-0005 composition record |
| `B-root` | Root/Verity artifact digests | Builder, materials P+C, parameters, environment | SLSA/in-toto provenance |
| `B-uki` | Signed UKI digest | Unsigned inputs, signing step/authority boundary, output | SLSA/in-toto provenance plus signing evidence |
| `D` | Deployment manifest digest | Complete release-owned closure | DES-0001 manifest |
| `M` | Deployment identity D | Component/dependency/source/license inventory and gaps | CycloneDX and SPDX candidates |
| `Q` | D + qualification policy/environment | Literal test result and limitations | Qualification record/in-toto candidate |
| `R1` | Named artifact subset | Replay and same-builder byte comparison | Reproduction-result candidate |
| `R2` | Same subset | Independent comparison and diff/result | Reproduction-result candidate |
| `VS1` | Vulnerability-source snapshot | Literal advisories and acquisition identity | Native plus OSV-normalized index |
| `V1` | D + component + advisory | Match/applicability/exploitability/action | CycloneDX VEX and CSAF challenger |
| `E1` | D + record identities | Promotion evidence set and verification policy | Small generated evidence-set manifest |
| `A` | D + Q + E1 + scope | Normal release authorization | DES-0004 authorization |

No record may include the digest of a record that must first include its own
digest. Draw and validate the dependency DAG before serializing it.

## Format comparison

Render the same inventory in CycloneDX 1.7 and SPDX 3.0.1, then compare:

- exact deployment/artifact subject binding;
- binary and source package identities including epoch/release/architecture;
- PURL plus native package coordinates and literal digest;
- containment, dependency, generated-from, built-from, and vendored relations;
- kernel, initrd, UKI, module, firmware, script, and opaque-component coverage;
- licensing and source-reference fidelity;
- declared unknown/incomplete coverage;
- VEX scoping and justification;
- deterministic serialization/canonical identity behavior;
- validator/tool availability and retained-version burden; and
- human inspection and conversion loss.

Populate this decision table:

| Gate | CycloneDX 1.7 | SPDX 3.0.1 | Decisive? |
| --- | --- | --- | --- |
| Exact subject and native identity | TBD | TBD | Must pass |
| Component/relationship coverage | TBD | TBD | Must pass minimum |
| Explicit unknowns and opaque content | TBD | TBD | Must pass |
| VEX integration | TBD | TBD | Important |
| License/source fidelity | TBD | TBD | Important |
| Deterministic generated output | TBD | TBD | Must pass |
| Offline validation/tool retention | TBD | TBD | Must pass |
| Conversion semantic loss | TBD | TBD | Contextual |
| Record size and owner effort | TBD | TBD | Decisive for personal phase |

## Provenance and hostile-producer cases

1. Produce a complete SLSA-shaped record from the builder.
2. Omit one material while remaining schema-valid.
3. Substitute another build's subject digest.
4. Sign a false statement with an otherwise trusted test key.
5. Supply correct provenance from an unapproved builder.
6. Change an external parameter not allowed by policy.
7. Reconstruct provenance after the build and label it accurately.
8. Claim a SLSA level without a matching build-platform assessment.

The verifier must separate format validity, authentication, expectation match,
completeness, and assurance level in every result.

## Reproduction cases

- Replay the build with retained inputs but produce differing bytes.
- Produce matching bytes twice on the same builder.
- Produce matching bytes on an independently identified environment.
- Match the unsigned root but not the signed UKI.
- Differ only in a declared ancillary field and prove that the compared subject
  excludes that field rather than relabeling the final artifact.
- Fail because a retained tool or source is unavailable.

Each result names the exact compared artifacts, environments, comparison
algorithm, diff identity, producer, and consequence for promotion.

## Vulnerability and VEX cases

| Scenario | Required result |
| --- | --- |
| Upstream version scanner flags code fixed by a distro backport | Preserve finding; join distro/source patch evidence; issue scoped assessment if justified |
| Distro advisory flags exact source package | Map to every affected deployment and machine through SBOM/package snapshot |
| Vendored library absent from package metadata | Coverage gap remains visible until binary/build evidence identifies it |
| Two sources disagree on severity or affected range | Preserve both; record conflict and named resolution policy |
| Advisory has several aliases | Join identities without merging merely related vulnerabilities |
| Component is present but vulnerable feature compiled out | Evidence-backed, expiring deployment-scoped VEX; not “fixed” |
| Service disabled only by identity-bound configuration | VEX binds exact deployment/configuration; config change triggers reassessment |
| `not affected` VEX copied to a rebuilt artifact | Reject subject mismatch |
| VEX expires or a newer source contradicts it | Reopen assessment and reevaluate promotion/rollout/withdrawal |
| Advisory appears after release | D remains unchanged; create VS2/V2/current-status decision |
| Primary aggregator lacks the advisory | Alternate source creates visible coverage/source finding |

## Failure, compromise, and retention cases

- Remove one evidence record required by E1.
- Corrupt an evidence-set manifest and one native record.
- Revoke or distrust the builder/evidence producer after promotion.
- Compromise the vulnerability normalizer without changing raw source records.
- Lose the current advisory service while the router is offline.
- Migrate an old schema record through a derived conversion with provenance.
- Sanitize evidence for publication and verify declared omissions.
- Fill the evidence store, then run garbage collection with selected, retained,
  withdrawn-installed, recovery, and incident-hold references.

## Pass criteria

The exercise passes on paper only when:

1. the graph is acyclic and every edge has one decision consumer;
2. immutable history and evolving assessment are visibly separate;
3. every negative or missing result remains attributable;
4. no format conformance is presented as an assurance level;
5. raw findings survive VEX and normalization;
6. offline status declares its knowledge time and freshness limit;
7. format conversion never becomes the only retained source; and
8. the owner can answer both deployment-to-source and advisory-to-machine
   queries without manually joining unrelated logs.
