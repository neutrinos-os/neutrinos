---
id: RES-0005
status: complete
last_updated: 2026-08-09
evidence_cutoff: 2026-08-09
decision_gates: [S-003, C-001, C-002]
related_designs: [DES-0005]
---

# Fleet-intent representation and validation

## Question

Which authoring and validation representation keeps the DES-0005 fleet
inventory bounded and reviewable without making upstream-native configuration
wait for a NeutrinOS schema or creating another programmable module system?

This comparison concerns fleet records, source manifests, contracts, and
composition metadata. It does not propose translating systemd, networkd,
tmpfiles, sysusers, nftables, or other supported native formats into one
project schema.

## Summary judgment

Use **TOML 1.0 authoring documents validated structurally as a restricted JSON
data model by JSON Schema Draft 2020-12**, with exact upstream-native files
listed by small source manifests. Emit resolved configuration and composition
records as canonical JSON; do not use JSON as the normal hand-authored format.

This representation boundary is accepted by
[ADR-0003](../../adrs/0003-bounded-fleet-intent-representation.md). It does
not select a TOML parser, JSON Schema validator, canonicalization library,
implementation language, or repository split.

The crucial constraint is more important than the syntax choice:

```text
operator-authored TOML data + literal native files
        -> separately owned deterministic implementation
        -> resolved canonical data + exact rendered files + evidence
```

Schemas validate record shape. Owned composition code resolves references,
applies the fixed scopes, and evaluates cross-record invariants. Native tools
validate native files. Project policy evaluates security and role invariants.
None of those functions is supplied as executable content by a machine record.

## Decision drivers

1. Records must be pleasant to review and edit without language evaluation.
2. Unknown fields, ambiguous types, duplicate definitions, and unsupported
   schema versions must fail.
3. Comments and formatting must not alter resolved semantic identity.
4. Exact ordered references must remain obvious in diffs.
5. Native files must remain literal and attributable.
6. Structural schema, cross-record integrity, native semantics, and security
   policy must not blur into one universal language.
7. The initial implementation must be realistic for one maintainer.

## Upstream facts

The [TOML 1.0 specification](https://toml.io/en/v1.0.0) defines an unambiguous
mapping to a hash table, supports comments, and rejects repeated definitions of
a key or table. It also admits types outside JSON, including date/time values,
and does not define a null value. A NeutrinOS profile therefore has to be a
documented subset rather than “anything a TOML parser accepts.”

[JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12) provides a
versioned structural-validation vocabulary and can reject unevaluated object
properties. Its `default` keyword is an annotation and
[does not fill absent values](https://json-schema.org/understanding-json-schema/reference/annotations).
NeutrinOS must consequently own and materialize every semantic default rather
than depending on validator-specific mutation.

The [YAML 1.2.2 specification](https://yaml.org/spec/1.2.2/) includes tags,
anchors, aliases, arbitrary node graphs, and processor-sensitive duplicate-key
cases. A safe JSON-like YAML profile is possible, but NeutrinOS would have to
specify and enforce the rejected portions while gaining little for these
small, split records.

The [CUE specification](https://cuelang.org/docs/reference/spec/) describes a
strongly typed constraint language that also supports templating, generation,
imports, dynamic fields, comprehensions, and a general scripting layer. Those
features are useful, but putting CUE in the operator-facing authoring path
would reopen the programmability and evaluation boundary rejected by SYS-014.

[RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html) defines the JSON
Canonicalization Scheme (JCS) for repeatable hashing and signing. JCS requires
I-JSON-compatible data and represents numbers using the IEEE 754-compatible
JSON number model. NeutrinOS can avoid numeric ambiguity by prohibiting floats
and TOML date/time values and by constraining authored integers to the exact
safe range; identifiers requiring a wider domain are strings.

## Options compared

| Option | Strengths | Failure modes | Disposition |
| --- | --- | --- | --- |
| TOML plus JSON Schema | Comments, readable short records, unambiguous tables, broad parser model, schema independent of implementation language | Deep arrays of tables become awkward; TOML has non-JSON types; schema cannot prove cross-file policy | Preferred, with a strict profile and split records |
| Restricted YAML plus JSON Schema | Concise nested records; familiar inventory syntax; supports null directly | Must prohibit aliases, tags, merges, implicit surprises, duplicate keys, and non-string mapping keys consistently across parsers | Viable challenger, but added parser policy has no present benefit |
| Authored JSON plus JSON Schema | Exact JSON data model; simplest schema integration and canonicalization | No comments; noisy hand editing; encourages generated rather than explanatory source | Use for resolved output and evidence, not normal authoring |
| CUE data and constraints | Excellent cross-field constraints, unification, tooling, and generation | Becomes an operator-facing language; defaults, imports, expressions, and comprehensions can hide origins and evaluation | Reject for authored intent; reconsider only as project-owned validation implementation after measured JSON Schema limits |
| Native files plus directory convention only | Minimal metadata and maximal upstream fidelity | Cannot express role assignment, platform constraints, contracts, exact reference order, or field authority safely | Reject for inventory; retain native files inside declared sources |
| Project-specific schema for every setting | Uniform queries and potentially rich validation | Permanent schema lag, lossy translation, and a reimplementation of upstream semantics | Reject under SYS-015 |

## Accepted representation contract

### Authored documents

Fleet, role, platform-class, machine, configuration-source, late-bound, state,
health, and deployment-policy records use TOML 1.0. Each file declares an
exact NeutrinOS schema identifier. The authoring profile permits only:

- UTF-8 strings;
- booleans;
- integers in the JCS exact safe range;
- arrays whose item type is constrained by the applicable schema; and
- tables with string keys.

Floats, all TOML date/time types, mixed-type arrays, and application-defined
implicit type conversion are rejected. TOML has no null, so absence remains
absence. A deletion is a typed operation such as `operation = "remove"`, never
a magic empty string, false value, or null.

Every schema rejects unknown fields. A schema version is immutable after
publication; compatible additions use a new schema identifier. Schemas may
describe and validate structure but do not insert defaults or execute
transformations.

### Reference and source closure

One inventory revision pins all co-located records and native files. Authored
local references use stable logical names rather than manually repeated
digests. The composition record binds the inventory revision and hashes every
record and file actually read. An external source requires an immutable
locator and digest in a separately reviewed lock record.

References and files are exact lists. Globs, recursive directory discovery,
floating Git references, mutable URLs, environment-variable substitution, and
imports chosen by runtime observation do not define a source closure.

A native source mirrors target-relative paths beneath a declared `files/`
root. Its manifest supplies source-level defaults for scope, owner, consumer,
and interpretation policy, plus an exact file list. Per-file metadata appears
only for an exceptional target, mode, object type, merge rule, or validation
policy. Executable programs are package or build inputs, not executable bits
smuggled through configuration sources.

### Validation boundaries

| Boundary | Owned responsibility | Must not do |
| --- | --- | --- |
| TOML parser | Enforce TOML 1.0 syntax and reject duplicate definitions | Apply project defaults or resolve references |
| JSON Schema | Validate one parsed document's types, required fields, closed properties, and bounded local relationships | Mutate data, fetch mutable schemas, or become security authorization |
| Reference resolver | Resolve the exact finite closure and reject missing, cyclic, wrong-kind, or wrong-scope references | Evaluate operator code or infer references from directories |
| Composer | Apply only accepted `common < role < machine` semantics and explicit operations | Let document order or a plugin redefine precedence |
| Native validator | Interpret exact rendered files with the named upstream component/version | Claim cross-machine or release authorization |
| Policy validator | Enforce accepted project and role invariants over the complete result | Treat ordinary precedence as an exception mechanism |
| Qualification | Exercise integrated behavior of the literal deployment variant | Claim that syntax validation proves runtime behavior |

Cross-document constraints such as “the machine's role exists,” “the platform
class is allowed by the role,” and “a late-bound contract cannot carry a unit”
belong to owned validation code and tests. They are not expressed as snippets
or queries supplied by the inventory.

### Semantic identity and evidence

The implementation parses TOML into the restricted data model, validates it,
materializes accepted defaults, resolves exact references, and emits resolved
JSON. The semantic identity of the resolved record is the digest of its JCS
representation. Exact source-byte digests remain in the composition record, so
a comment-only change is attributable without pretending it changed machine
behavior.

JCS is the current canonical-output candidate, not yet a cryptographic-format
decision. A spike must confirm library agreement on the project corpus,
including Unicode and integer boundaries, before any signed identity depends
on it.

## Representative layout

The logical model can initially be co-located in one repository without
committing to a future fleet-repository split:

```text
fleet/
├── fleet.toml
├── machines/
│   ├── desktop-jason.toml
│   ├── reference-vm.toml
│   └── router.toml
├── platforms/
├── roles/
├── sources/
│   ├── common/
│   ├── machine/
│   └── role/
├── contracts/
│   ├── late-bound/
│   └── state/
├── policies/
│   ├── deployment/
│   └── health/
└── locks/
```

This is a content model, not an instruction to create production directories
now. Schema files and generated evidence are project implementation/build
assets, not desired fleet intent, and need not live under `fleet/`.

## Adversarial review

### “TOML becomes unreadable for real machine records”

This is credible for large nested arrays of tables. The response is to keep one
bounded record per concept, prefer ordered arrays of short references, and keep
subsystem configuration native. If the EX-0007-shaped records routinely need
deep nesting, the model should be simplified before replacing TOML with a more
powerful language.

### “JSON Schema is another DSL”

Schemas are project-owned interface definitions, not machine-owned programs.
The initial dialect should use a reviewable subset: types, required fields,
enums, patterns, numeric/string bounds, array uniqueness, references to fixed
schema resources, and closed properties. Complex dynamic references or deeply
nested conditionals require an explicit review. Cross-record and security
rules remain named implementation behavior with direct tests.

### “Custom validation code recreates hidden semantics”

Some custom semantics are unavoidable because no serialization schema can
prove enrollment authority, systemd cross-file behavior, or release policy.
The guardrail is ownership: one versioned implementation defines the accepted
algorithm; records select data and fixed policy identifiers, never expressions,
plugins, scripts, or validator source. The composition record names the exact
implementation and every decision it made.

### “Source-level defaults hide behavior”

Defaults may remove repetitive attribution metadata but are materialized in
resolved output. They cannot choose a role, source, file, condition, operation,
or policy. The inspection surface shows the inherited value and its defining
schema or source boundary.

### “Native filenames defeat NeutrinOS precedence”

Native formats have different semantics: systemd unit drop-ins generally apply
later names last, networkd selects the first matching `.network` file, while
tmpfiles and sysusers use earliest-entry behavior for conflicts. NeutrinOS
therefore does not pretend that one filename band implements all scopes.
Complete-path replacement and tombstones follow NeutrinOS scope rules;
distinct native objects follow an explicitly named consumer policy and must
pass consumer-specific conflict and integration checks. EX-0007 exercises this
boundary.

## Falsification and implementation gates

The architecture may accept this representation direction before production
code exists. Before selecting concrete libraries or making a deployment or
signature identity depend on it, a bounded spike must demonstrate:

1. all EX-0006 records can be expressed without templates or duplicated
   per-file metadata;
2. two independent TOML parsers produce the same restricted data for the test
   corpus and reject the negative corpus;
3. the selected JSON Schema validator rejects unknown fields and unsupported
   versions without modifying data;
4. two JCS implementations agree on the canonical corpus;
5. setting-to-output and output-to-setting inspection remain useful with real
   native files; and
6. adding an upstream-native setting requires no NeutrinOS schema change.

Choose the restricted-YAML challenger instead if real records are materially
clearer and the parser-profile negative corpus is cheap to enforce. Reconsider
CUE only if measured cross-record validation complexity exceeds owned code and
tests, and keep CUE out of the operator-authored data path unless SYS-014 is
deliberately revisited.

## Decision disposition

ADR-0003 accepts TOML 1.0 plus JSON Schema 2020-12, exact native sources, and
generated canonical JSON output as the DES-0005 representation direction. The
exact parser, validator, and JCS implementation remain spike results rather
than architectural commitments.
