---
id: PR-0007
subject: Deployment lifecycle requirements
reviewer: Codex adversarial pass
date: 2026-08-09
status: accepted
---

# Deployment lifecycle requirements review

## Decision scope

This review asks which substrate-independent lifecycle behavior must become
normative before NeutrinOS selects a deployment substrate. It covers artifact
traceability, literal qualification, promotion, discovery, staging,
eligibility, selection, trial boot, assessment, blessing, fallback, rollback,
retention, garbage collection, status, withdrawal, offline operation, and
compromise recovery.

It does not select a package ecosystem, artifact format, updater, bootloader,
partition layout, publication service, signature envelope, status API, boot-
attempt count, health timeout, retention count, release cadence, rollout
algorithm, or freshness window. Those choices must satisfy these requirements
rather than define them retroactively.

## Summary judgment

The lifecycle model is strong enough to constrain a substrate decision. Its
most important property is that the deployment set remains the unit across
qualification, authorization, staging, selection, blessing, fallback,
rollback, and withdrawal even when an implementation stores its artifacts
separately.

The strongest reason to reject the model is implementation cost. Complete-set
joins, local eligibility gates, status correlation, and closure-aware garbage
collection could turn into a second updater or fleet manager. Acceptance is
therefore conditional on a narrow ownership boundary: NeutrinOS owns policy,
evidence joins, and conformance tests; the selected substrate must own transfer,
storage, boot selection, attempt accounting, and rollback mechanics wherever
it can satisfy the requirements.

## Accepted requirement disposition

### Ratify existing candidates

The following candidate requirements express durable policy and are now
`Accepted`:

| Requirements | Reason to make normative now |
| --- | --- |
| SYS-001, SYS-002 | Source traceability and literal deployment-set qualification define what promotion is allowed to claim. |
| SYS-003 | Interrupted-update recovery is a substrate acceptance boundary, not an implementation preference. |
| SYS-005 | Roles share lifecycle semantics without being forced into identical artifact shapes. |
| SYS-008 | On-machine deployment identity is required to join boot and runtime observations to release evidence. |
| SYS-010 | Role-health criteria are required before trial boot and blessing can have precise meanings. |
| SYS-012 | Emergency releases may shorten policy but may not discard minimum identity, provenance, literal-artifact, changed-behavior, and applicable fallback, rollback, or maintenance-recovery evidence. |
| SYS-013 | Vulnerability and update ownership must be assigned before choosing the contents of a deployment variant. |
| SYS-028, SYS-029 | Authorization is content- and scope-bound, independent of discovery location, and cannot affect selection before complete verification. |
| SYS-031 | Status properties remain independent rather than collapsing into `signed`, `healthy`, `current`, or `green`. |
| SYS-035 | Compromise recovery is distinct from ordinary rollback and treats mutable state as potentially hostile. |
| SYS-036 | Authorization cannot launder an unqualified rebuild, even when its source and inputs are attributable. |
| SYS-037 | Normal, recovery-only, and withdrawn status must coexist with bounded offline operation and recovery. |

### Retire overlapping candidates

The following early requirements are now `Superseded` rather than remaining as
second weaker statements of accepted policy:

| Requirement | Superseded by | Reason |
| --- | --- | --- |
| SYS-004 | SYS-019 | The state-contract requirement defines the owner and lifecycle inventory more precisely. |
| SYS-006 | SYS-014 through SYS-018 | The accepted configuration boundary covers versioned intent, deterministic composition, attributable native output, and qualified-artifact deployment. |
| SYS-007 | SYS-027 | The accepted security-claim schema names the exact threat-model fields. |
| SYS-009 | SYS-021 through SYS-023 | The accepted compatibility, migration, fallback, and commit-barrier requirements are testable refinements. |
| SYS-011 | SYS-031 | The status requirement includes the same distinctions without overloading one release-state label. |

Supersession preserves history; it does not weaken the accepted replacement.

### Add missing lifecycle requirements

SYS-038 through SYS-041 are normative:

- SYS-038 makes trial attempts bounded and durable, makes assessment precede
  blessing, and separates automatic fallback from deliberate recovery.
- SYS-039 scopes blessing to one exact deployment on one machine. A successful
  local boot cannot mint global qualification or authorization.
- SYS-040 makes complete-closure reachability the retention and garbage-
  collection invariant, including recovery environments and shared content.
- SYS-041 requires the locally retained lifecycle control path to survive loss
  of publication, discovery, signing, WAN, DNS, and the role's own production
  service path. Health assessment may observe that failure, but recording it
  and selecting a fallback cannot depend on the failed path.

## Lifecycle contract

The accepted requirements establish this common transition model:

```text
discovered -> acquired -> staged -> eligible -> selected
    -> trial boot -> assessed -> blessed
                         |
                         +-> failed -> eligible normal fallback or stop
```

The states have deliberately unequal strength:

- discovery identifies a candidate but confers no authorization;
- acquisition makes bytes present but inert;
- staging requires the complete integrity-verified deployment set;
- eligibility is a current policy decision over qualification,
  authorization, platform and state compatibility, freshness, and local
  policy;
- selection names one complete deployment set for a later boot;
- boot verifies the bytes actually used and reports their identity;
- assessment applies role-specific runtime health criteria;
- blessing changes only subsequent local selection policy; and
- failure may select only a retained deployment that is still eligible as a
  normal fallback candidate.

Deliberate rollback re-enters this normal eligibility and selection path.
Recovery remains a separately authorized operation and is never the automatic
successor of an exhausted trial.

## Adversarial challenges and guardrails

### C-001: Literal qualification can make urgent security response unusably slow

- Severity: critical
- Claim: requiring the final platform-signed deployment identity to pass the
  full normal suite could delay an urgent fix and encourage an undocumented
  bypass.
- Disposition: mitigated by SYS-012. Emergency policy may skip declared checks,
  but it retains minimum provenance, exact-artifact boot, changed-behavior,
  integrity, and applicable fallback, rollback, or maintenance-recovery
  evidence. The skipped checks and reduced claim remain visible.
- Residual risk: the minimum emergency suite and time budget remain open under
  L-002 and L-007 and must be exercised rather than first invented during an
  incident.

### C-002: Freshness can make an offline router unable to boot

- Severity: critical
- Claim: short expiry or mandatory online revocation checks can strand a
  healthy router precisely when its network path is unavailable.
- Disposition: SYS-037 and SYS-041 require a retained, anti-downgraded offline
  policy whose normal and exceptional outcomes are explicit. Failure to obtain
  new metadata cannot silently mean either `current` or `permanently
  unrecoverable`.
- Residual risk: the offline exposure window, clock assumptions, policy epoch,
  and refresh mechanism remain unresolved and may differ by role.

### C-003: Automatic fallback can loop or cross an unsafe state boundary

- Severity: critical
- Claim: repeated trial and fallback boots can oscillate indefinitely or boot
  an older deployment after incompatible state has been written.
- Disposition: SYS-021 through SYS-023 gate fallback on state compatibility;
  SYS-038 requires durable bounded attempts and a diagnosable stop when no
  eligible normal fallback remains.
- Residual risk: attempt counts, watchdog behavior, and exactly when state is
  considered changed require substrate and role exercises.

### C-004: A self-reported health check can bless a broken or malicious release

- Severity: critical
- Claim: a booted candidate controls many of its own health observations and
  could bless shallow success while its external function is broken.
- Disposition: SYS-010 requires externally observable role criteria where the
  role permits them; SYS-039 limits the consequence to one deployment on one
  machine and preserves global qualification and authorization as independent
  evidence.
- Residual risk: the workstation needs some post-login evidence, while the
  router needs an observer outside its potentially failed production data
  plane.

### C-005: Retention can preserve vulnerable artifacts forever

- Severity: high
- Claim: keeping deployments for fallback and offline recovery increases disk
  use and preserves known-vulnerable code.
- Disposition: retained, eligible, recovery-only, and withdrawn are separate
  properties. SYS-037 permits withdrawal without deleting historical evidence;
  SYS-040 preserves bytes only while a declared retention reference exists.
- Residual risk: retention classes, minimum counts, storage pressure behavior,
  and secure disposal remain open policy.

### C-006: Shared-content garbage collection can tear several deployments at once

- Severity: critical
- Claim: removing one apparently old object may break the selected deployment,
  every fallback, or the only retained recovery environment when artifacts are
  deduplicated.
- Disposition: SYS-040 makes reachability from each retained complete closure
  the invariant and requires interruption tests. An artifact is collectible
  only after every applicable retention reference is removed.
- Residual risk: upstream resource-retention models may not express the full
  cross-resource closure, forcing flattening or a small additional reachability
  join.

### C-007: Rich status becomes a second mutable control plane

- Severity: high
- Claim: correlating substrate state with authorization, evidence, freshness,
  compatibility, and local modification can grow into a custom desired-state
  service whose own database controls boot.
- Disposition: SYS-031 requires observable properties, not a new ownership
  surface. The preferred implementation is a read-only join over substrate-
  native state and immutable evidence, preserving raw upstream output for
  diagnosis.
- Residual risk: an eligibility gate necessarily makes a policy decision; the
  substrate spikes must prove that this remains a thin join rather than a
  replacement updater.

### C-008: Emergency policy becomes the routine path

- Severity: critical
- Claim: once a reduced emergency gate exists, schedule pressure can normalize
  its use.
- Disposition: an emergency release records its reason, skipped checks,
  reduced claims, approver, and follow-up qualification obligation. It cannot
  become indistinguishable from a normally qualified release in status or
  evidence.
- Residual risk: expiry or mandatory replacement of emergency authorization is
  deferred to release and freshness policy.

### C-009: A common lifecycle forces unlike roles into one artifact design

- Severity: high
- Claim: workstation, router, and VM requirements may be distorted to make one
  updater or disk shape appear universal.
- Disposition: SYS-005 standardizes identity and transition semantics, not
  artifact shape. Every deployment variant retains independent identity,
  qualification, role-health policy, and compatibility claims.
- Residual risk: supporting two substrate mechanisms would multiply lifecycle
  qualification cost and needs a stronger justification than role-specific
  artifact differences alone.

### C-010: Compromise recovery is mislabeled rollback

- Severity: critical
- Claim: booting an older exact deployment does not remove persistence from
  mutable executable state, identities, administrator overrides, user data, or
  workloads.
- Disposition: SYS-035 requires owner-aware quarantine, selective restore,
  re-enrollment, or destruction. Ordinary rollback makes no compromise-
  recovery claim.
- Residual risk: real state contracts and recovery tooling must demonstrate
  that selective treatment is operable rather than merely documented.

## Strongest rejected alternatives

### Let the substrate define the lifecycle

Rejected as project policy. Substrate-native states and commands are valuable
mechanisms, but neither candidate currently establishes the whole NeutrinOS
claim boundary across exact multi-artifact identity, qualification,
authorization scope, state compatibility, role health, freshness, and
recovery. Allowing the first implementation to define those semantics would
make the architecture impossible to compare adversarially.

### Treat a valid signature as eligibility

Rejected. A valid signature does not prove qualification, applicable role or
machine scope, state compatibility, freshness, absence of withdrawal, or local
support status.

### Always boot the newest discovered release

Rejected. A mutable discovery name or version ordering is neither identity nor
authorization. Discovery must not outrank the selected deployment before the
complete candidate passes eligibility gates.

### Automatically enter recovery after all normal boots fail

Rejected. Recovery has greater and differently scoped capabilities. Exhausted
normal fallback may stop and request deliberate recovery, but it must not cross
that authorization boundary automatically.

## Required evidence after acceptance

Acceptance establishes policy, not implementation conformance. Before a
substrate ADR can be accepted, both candidates must be exercised symmetrically
against at least these cases:

1. substitute metadata, a manifest, and every independently stored deployment
   artifact;
2. interrupt acquisition, verification, eligibility, selection, boot-attempt
   accounting, blessing, fallback, and garbage collection;
3. boot the exact staged identity, fail health assessment, and prove bounded
   fallback to one eligible retained normal deployment;
4. cross a state-compatibility commit barrier and prove the incompatible
   retained deployment is no longer an automatic fallback candidate;
5. withdraw and expire a retained deployment while preserving the declared
   offline recovery path;
6. remove registry, publication, signing, WAN, DNS, and production-role service
   availability and repeat boot, assessment, blessing, fallback, and rollback;
7. retain deployment sets with shared content, garbage-collect unrelated
   content, and prove every retained closure and recovery environment remains
   complete;
8. show raw substrate status and the correlated NeutrinOS status without a
   second mutable desired-state database; and
9. exercise an emergency release whose skipped checks and reduced support claim
   remain visible.

## Decision

Accepted by Jason Tarasovic on 2026-08-09. The requirement dispositions above
make the lifecycle semantics normative before selecting a substrate while
leaving mechanism and numeric policy open.

Acceptance closes the lifecycle-requirement item in the DES-0001 review, but it
does not by itself accept DES-0001. Owner review of the deployment-set boundary
and symmetric production-supported substrate evidence remain open.
