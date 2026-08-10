---
id: PR-0008
subject: Fleet intent and configuration requirements
reviewer: Codex adversarial pass
date: 2026-08-09
status: accepted
---

# Fleet intent and configuration requirements review

## Decision scope

This review asks whether SYS-042 through SYS-047 should become normative before
NeutrinOS selects configuration serialization, composition tooling,
provisioning transport, or an enrollment protocol. It reviews the authority and
identity boundaries proposed by DES-0005 and instantiated for the reference VM,
`desktop-jason`, and `router` by EX-0006.

It does not select repository paths, YAML or another syntax, a schema language,
a renderer, an inventory service, Ignition, cloud-init, a credential backend,
or a first-enrollment mechanism. It also does not accept DES-0005 as an
implemented or complete architecture.

## Summary judgment

SYS-042 through SYS-047 are normative. Together they prevent the
main failure modes that motivated the configuration design: desired intent
inferred from observation, hidden order, downstream records competing as
sources of truth, late-bound values carrying unqualified policy, and a
provisioning transport retaining permanent authority.

The strongest reason to reject the tranche is framework growth. Fleet records,
source declarations, composition evidence, late-bound contracts, policy gates,
and provisioning state could cost more to understand than the native
configuration they govern. Acceptance therefore requires a minimal-metadata
rule: a field exists only when it affects identity, attribution, validation,
authorization, compatibility, status, lifecycle, or recovery. Unambiguous
owner, scope, and consumer values may default at a configuration-source
boundary rather than being repeated for every native file.

## Accepted requirement disposition

SYS-042 through SYS-047 are accepted with the interpretations below.

### SYS-042: Fleet inventory and primary role

The fleet inventory is the source of desired machine intent. For the initial
fleet, each machine record has exactly one primary role. Role services may be
composed within that role, and user or workload functions remain independently
owned; neither requires arbitrary multi-role inheritance.

One primary role is an initial-model constraint, not a permanent prohibition.
It must be reviewed if a future machine genuinely needs several independently
maintained base roles. Adding multi-role behavior must define conflict,
identity, qualification, health, and state semantics rather than relying on
role ordering.

### SYS-043: Observation, bootstrap, and authority

A platform observation may satisfy a compatibility constraint. A bootstrap
hint may locate candidate provisioning intent. Neither assigns role or
authorizes deployment.

Normal machine selection joins four independently meaningful facts:

1. the enrolled machine identity is currently bound to one machine record;
2. that record supplies the current primary role assignment;
3. observed platform facts satisfy the bound platform constraints; and
4. the deployment identity is eligible and authorized for the applicable
   scope.

The requirement does not claim that version control alone authenticates first
enrollment. Provisioning intent needs a separate authenticated owner path under
L-003 before production enrollment.

### SYS-044: Fixed precedence and policy

The initial configuration scopes are exactly `common`, `role`, and `machine`,
with fixed precedence `common < role < machine`. Platform class is a
compatibility classification, not an implicit fourth configuration scope.
Reusable hardware-specific sources may be explicitly referenced by role or
machine intent without being applied merely because hardware was observed.

Precedence determines which value wins; it does not authorize that value.
Post-composition policy may reject the resolved result when it violates an
accepted project or role invariant. Exceptions to a normal invariant require a
separately visible policy, development, emergency, or recovery decision rather
than a generic machine override flag.

Same-scope conflicts fail unless an identified consumer-specific interpretation
policy defines their semantics. Native ordering such as distinct systemd
drop-ins remains native behavior when the exact file set and interpretation
policy are bound and qualified. Absence never means deletion; deletion is an
explicit attributable tombstone.

### SYS-045: Composition evidence

The composition record is immutable evidence, not another desired-state
database. It binds exact inputs, tool and policy identities, precedence
decisions, validations, resolved configuration, and rendered outputs. A
downstream deployment manifest may bind its identity; qualification and status
may attest to it. Those downstream objects cannot silently edit its source
intent.

Composition identity proves attribution and exact output for the named tools
and inputs. It does not by itself establish reproducible package, filesystem,
timestamp, signing, or complete deployment builds; those broader claims remain
under SYS-001 and L-002.

### SYS-046: Late-bound contracts

Late-bound values are allowed only when their independent owner or observation
lifecycle makes embedding the value false or unsafe. The contract's semantic
effect remains identity-bound.

A value named `credential` or `metadata` may not carry undeclared units,
scripts, package selections, boot arguments, firewall rules, or other normal
privileged policy. A powerful input is identity-bound unless it is assigned to
an independently authorized administrator, user, or workload owner and receives
the corresponding machine-realization status consequence.

Contract metadata may inherit unambiguous defaults from a named contract class
or configuration source. The required fields are semantic obligations, not a
mandate to repeat identical syntax beside every value.

### SYS-047: Provisioning lifecycle

Provisioning is a deliberate transition that prepares storage, trust,
recovery, and enrollment before selecting a previously built deployment. Its
transport does not become the normal configuration authority.

The concrete mechanism may remain open, but it must eventually define
authenticated intent, completion state, replay protection, interruption,
retry, evidence retention, input retirement or inertness, and deliberate
reprovisioning. Reappearance of seed media, SMBIOS data, a metadata service,
kernel arguments, Ignition input, or cloud-init data after completion cannot
silently change role, identity, preserved state, or selected deployment.

## Field-authority guardrail

EX-0006 establishes the following authority flow:

```text
fleet inventory owns desired intent
        |
        v
composition record binds exact resolved and rendered results
        |
        v
deployment manifest binds exact release-owned artifacts
        |
        +-> qualification record attests tested claims
        |
        +-> release authorization permits an exact identity and scope
        |
        v
machine status reports the resulting realization
```

Binding and attesting are intentionally not authoring. A deployment manifest,
qualification record, release authorization, or status record that disagrees
with the source intent is invalid evidence or a different candidate; it does
not revise the machine record.

## Adversarial challenges and guardrails

### C-001: Version-controlled inventory is not authenticated enrollment

- Severity: critical
- Claim: a reviewed machine record does not prove that a blank machine is the
  intended physical or virtual machine, especially when SMBIOS and metadata
  are attacker-controlled.
- Disposition: accepted as an explicit boundary. SYS-043 prevents observation
  from granting authority, while SYS-047 requires a separate authenticated
  provisioning path. No production identity may be enrolled until L-003
  resolves that path.
- Residual risk: the first-enrollment ceremony and trust anchor remain open.

### C-002: One primary role creates composite-role proliferation

- Severity: high
- Claim: every combination of workstation, storage, VM-host, DNS, VPN, and
  monitoring behavior could become a new role and qualification variant.
- Disposition: EX-0006 shows that the initial functions divide into one primary
  role, release-owned role services, and independently owned workloads. A
  multi-role need is a review trigger rather than a forbidden future design.
- Residual risk: the boundary between a base role service and a privileged
  workload may be contested by real software.

### C-003: Rejecting platform scope duplicates hardware policy

- Severity: high
- Claim: several machines using one board may repeat module, firmware, device,
  and storage policy references.
- Disposition: one reusable exact configuration source can be explicitly
  referenced by several roles or machine records. This duplicates a short
  reviewed reference, not the policy bytes, and keeps observation from applying
  behavior.
- Residual risk: measured repetition or omission errors may later justify a
  platform scope, which would require a new precedence and authority decision.

### C-004: Machine precedence can defeat role security

- Severity: critical
- Claim: deterministic resolution can still cleanly disable boot integrity,
  fallback safety, health checks, firewall policy, or recovery separation.
- Disposition: SYS-044 requires post-composition validation against accepted
  invariants. EX-0006 enumerates the initial non-overridable set. Precedence is
  not exception authority.
- Residual risk: the exact enforcement representation remains open, and an
  overly broad exception mechanism could recreate the defect.

### C-005: Native configuration has its own merge semantics

- Severity: high
- Claim: treating every duplicate consumer or destination as replacement can
  corrupt the intended behavior of systemd drop-ins, networkd matching,
  tmpfiles, sysusers, and other upstream formats.
- Disposition: same-scope conflict is defined at the declared output key or
  complete destination, not merely the consuming component. Distinct native
  objects retain upstream ordering under a named interpretation policy. Exact
  inputs and final outputs remain in the composition record.
- Residual risk: weak upstream validators and surprising cross-file behavior
  still require role-level integration tests.

### C-006: Composition evidence becomes larger than useful review

- Severity: high
- Claim: recording every default, source, override, validator, and output can
  create noisy evidence that technically exists but no person can inspect.
- Disposition: source-level defaults prevent repeated metadata, and inspection
  must provide targeted setting-to-output and output-to-source queries. The
  immutable full record remains available for reproduction and audit.
- Residual risk: actual scale and usability cannot be established until native
  configuration is instantiated.

### C-007: Late-bound data smuggles executable policy

- Severity: critical
- Claim: a constrained blob can still contain a systemd unit, routing policy,
  admission rules, or a script interpreted by a privileged consumer.
- Disposition: SYS-046 binds permitted semantic power, not only byte syntax.
  EX-0006 explicitly rejects late-bound normal policy and assigns independently
  managed powerful inputs a different owner and status.
- Residual risk: some services are policy interpreters by design; each such
  input needs an explicit ownership decision.

### C-008: Provisioning replay destroys state or identity

- Severity: critical
- Claim: a seed or metadata source can reappear after update or reboot and
  cause factory reset, re-enrollment, storage mutation, or role reassignment.
- Disposition: SYS-047 makes completion and replay behavior normative before a
  mechanism is selected. Ordinary boot treats completed provisioning input as
  inert; destructive reprovisioning requires deliberate authorization and its
  own state-preservation policy.
- Residual risk: continuously exposed instance metadata may be impossible to
  remove and therefore requires durable local replay state.

### C-009: Inventory availability becomes a boot dependency

- Severity: high
- Claim: a private repository or fleet service outage could stop a router from
  booting, falling back, or being diagnosed.
- Disposition: the inventory is a build and desired-intent source. Locally
  retained deployments, policy, evidence, and composition records satisfy the
  offline lifecycle under SYS-041; normal boot does not fetch or evaluate fleet
  intent.
- Residual risk: new builds and desired-state changes remain unavailable while
  the inventory source is unavailable, which is an operational backup concern.

### C-010: Observation drift silently rewrites intent

- Severity: high
- Claim: an inventory collector may update firmware, interface, storage, or
  device values in the same record used for desired configuration.
- Disposition: SYS-042 separates desired inventory from dated observation and
  status evidence. Drift changes compatibility or support status; it does not
  edit the machine record automatically.
- Residual risk: operator tooling must make reconciliation explicit without
  encouraging blind acceptance of observed values.

## Strongest rejected alternatives

### Infer machine intent from discovered hardware

Rejected. It confuses compatibility evidence with administrative purpose and
makes hardware or SMBIOS substitution an implicit role-change mechanism.

### Use a programmable module graph

Rejected for operator-facing intent under accepted SYS-014. Its flexibility
does not justify arbitrary evaluation, hidden imports, and difficult failure
attribution for this project.

### Store only final native files per machine

Rejected as the only authoring model. It is simple locally but duplicates
common and role intent and loses useful source-level review. The resolved and
rendered output already provides this flat diagnostic view.

### Make the provisioner the desired-state agent

Rejected. Repeated target mutation would let transport metadata and historical
state determine normal behavior outside deployment identity and qualification.

## Required implementation evidence

Acceptance establishes policy, not implementation conformance. DES-0005
still requires:

1. literal representative native systemd, networkd, tmpfiles, sysusers, mount,
   and kernel-policy inputs exercising source defaults and native ordering;
2. a small set of serialization and validation alternatives applied to the
   EX-0006 records;
3. an authenticated first-enrollment and replay state machine; and
4. an inspection example that traces one source to output and one output back
   to every contributing source without reading the full composition record.

## Decision

Accepted by Jason Tarasovic on 2026-08-09. SYS-042 through SYS-047 are
normative with the interpretations above. This ratifies the source-of-truth,
primary-role, observation, precedence, composition-evidence, late-bound, and
provisioning boundaries while leaving formats and mechanisms open.

Acceptance resolves the DES-0005 review's owner-policy and candidate-
requirement actions. DES-0005 remains in review until representative native
inputs and serialization alternatives demonstrate that the model stays smaller
and clearer than the configuration it governs. L-003 remains open for the
authenticated first-enrollment mechanism.
