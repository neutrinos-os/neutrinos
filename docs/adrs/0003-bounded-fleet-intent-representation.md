---
id: ADR-0003
title: Use bounded TOML records, native configuration, and generated JSON evidence
status: accepted
date: 2026-08-09
deciders: [Jason Tarasovic]
designs: [DES-0005]
supersedes: []
superseded_by: []
---

# Use bounded TOML records, native configuration, and generated JSON evidence

## Context

NeutrinOS needs checked-in common, role, and machine intent without recreating
a programmable module language or waiting for project schemas to expose every
upstream setting. The representation must fail on unknown intent, retain exact
source attribution, and produce deterministic evidence for the deployment
variant that was actually qualified.

[DES-0005](../designs/0005-fleet-intent-and-configuration/README.md)
defines the fleet inventory, fixed scope composition, native-input boundary,
and composition record. [RES-0005](../research/comparisons/fleet-intent-representation.md)
compares TOML, restricted YAML, authored JSON, CUE, and native-only authoring.
[EX-0007](../research/exercises/0007-native-configuration-and-inspection.md)
applies the proposed split to sanitized representative router intent.

## Decision

NeutrinOS uses TOML 1.0 for operator-authored fleet, role, platform, machine,
source, contract, and policy records. The accepted authoring profile is a
restricted JSON-compatible data model: strings, booleans, integers in the JCS
exact-safe range, typed arrays, and string-keyed tables. Floats, TOML date/time
values, mixed-type arrays, and implicit application conversions are prohibited.

Each record declares an immutable schema identifier and is validated
structurally using JSON Schema Draft 2020-12. Unknown fields and unsupported
schema versions fail. Schema annotations do not insert defaults; NeutrinOS-
owned composition materializes all accepted defaults in resolved output.
Schemas validate record structure, not enrollment authority, cross-record
policy, native configuration semantics, or release authorization.

Supported upstream configuration remains literal and upstream-native. A small
source manifest declares its scope, owner, consumer, interpretation policy,
target-relative root, and exact finite file list. Source-level defaults avoid
per-file repetition. Globs, recursive discovery, mutable imports, runtime
observation, and filesystem traversal order do not define the source closure.

Resolved configuration and composition evidence use a generated JSON data
model rather than hand-authored JSON. Semantic identity is calculated over a
canonical representation while exact source-byte identities remain in the
composition record. RFC 8785 JCS is the leading canonicalization candidate;
the concrete library and encoding dependency remain subject to the validation
gates in RES-0005 before signed or deployment identity relies on them.

Reference resolution, fixed `common < role < machine` composition,
consumer-specific native interpretation, post-composition policy, and
qualification are separately owned implementation boundaries. Inventory data
may name fixed policy identifiers, but it may not supply expressions, plugins,
scripts, validator code, or an alternate composition algorithm.

## Alternatives considered

### Restricted YAML plus JSON Schema

Rejected for the initial authoring surface. It offers convenient nesting but
requires NeutrinOS to prohibit and consistently test aliases, tags, merge
behavior, non-string keys, duplicate-key edge cases, and other syntax that the
accepted records do not need.

### Authored JSON plus JSON Schema

Rejected for normal authoring because it lacks comments and makes routine
human edits noisy. JSON remains the generated resolved-data and evidence
model.

### CUE data and constraints

Rejected for operator-authored intent. Its imports, expressions,
comprehensions, defaults, generation, and scripting capabilities would reopen
the language-evaluation boundary prohibited by SYS-014. A project-owned
validator implementation may be reconsidered only after measured evidence
shows the accepted structural and owned-code split is inadequate.

### Native files plus directory conventions only

Rejected as the entire model. Native files cannot themselves express machine
identity, role assignment, platform constraints, exact source order, state and
late-bound contracts, or the field-authority boundary.

### Project schema for every upstream setting

Rejected under SYS-015. It would reproduce schema lag, lose upstream
semantics, and turn NeutrinOS into a second configuration system for each
consumer.

## Consequences

### Benefits

- Authored intent remains bounded data with comments and ordinary diffs.
- New supported native settings do not require a NeutrinOS schema addition.
- Structural, referential, native, policy, and qualification failures remain
  attributable to distinct owners and validation stages.
- Source-level defaults keep manifests smaller while resolved output exposes
  every effective value.
- Generated JSON provides a stable machine-readable inspection and evidence
  model without becoming the normal authoring syntax.

### Costs and constraints

- NeutrinOS must define and test a strict TOML subset and the TOML-to-JSON data
  mapping.
- JSON Schema cannot prove cross-record or security properties; owned code and
  direct tests remain necessary.
- Each native consumer needs an explicit interpretation and validation policy
  because ordering and collision semantics differ.
- A canonicalization implementation and corpus must be qualified before its
  output becomes a signed identity.
- Deeply nested records may be awkward in TOML and are a signal to simplify
  the model rather than introduce templates.

### Accepted risks

- Project-owned reference and policy validation could accumulate hidden
  semantics if its behavior and composition records are not kept inspectable.
- JSON Schema can itself become difficult to review if complex conditional or
  dynamic features are admitted without restraint.
- A later real-world inventory may show that restricted YAML is materially
  clearer for specific records.
- Native validators may accept configurations whose cross-file or runtime
  behavior is still unsafe; integrated qualification remains mandatory.

## Validation and review triggers

Before production identity depends on the representation, run the positive and
negative corpora specified by RES-0005 across independent TOML parsers and JCS
implementations and the selected JSON Schema validator. Demonstrate exact
setting-to-output and output-to-setting inspection and add a native upstream
setting without changing a NeutrinOS schema.

Revisit this decision when:

- representative records routinely require deep nesting or duplicated
  metadata;
- parser disagreement cannot be eliminated by the restricted profile;
- cross-record validation grows into a data-driven programming language;
- canonicalization implementations cannot agree on the accepted corpus;
- a native consumer cannot be attributed and qualified without lossy
  translation; or
- measured authoring and review evidence makes the restricted-YAML challenger
  materially simpler without expanding semantic ambiguity.
