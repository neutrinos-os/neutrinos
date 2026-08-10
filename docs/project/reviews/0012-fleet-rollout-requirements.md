---
id: PR-0012
subject: Fleet release rollout requirements
reviewer: Codex adversarial pass
date: 2026-08-10
status: accepted
---

# Fleet release rollout requirements review

## Decision scope

This review asks whether SYS-075 through SYS-085 should become normative before
NeutrinOS chooses a fleet rollout protocol, controller, client, database,
dashboard, maintenance-window implementation, or reboot coordinator.

It reviews the policy boundaries in DES-0009 and proposed exercise EX-0011. It
does not accept Omaha, Nebraska, Cincinnati, Zincati, FleetLock, a custom
service, or a static-record format merely because one is a leading candidate.

## Summary judgment

The requirements should be accepted. They keep rollout blast-radius control
from weakening the already accepted identity, authorization, eligibility, and
offline lifecycle model. They also make small-fleet reality explicit: exact
members and role evidence matter more than percentages.

The strongest objection is operating cost. The requirements could produce a
miniature distributed control plane for three machines. Acceptance therefore
depends on semantic rather than component requirements: an attended procedure
over simple immutable records must be allowed to satisfy them.

## Accepted requirement disposition

### SYS-075: Rollout decisions bind exact subjects and authorities

Every plan and decision identifies the exact release authorization, deployment
variants, promotion evidence set, inventory snapshot, policy, authority,
ordering, validity, target scope, gates, and actions it governs. Rollout may
restrict authorized use; it cannot authorize a different deployment or rewrite
promotion history.

### SYS-076: Targeting comes from authoritative inventory

Cohort membership derives from enrolled identity and an immutable authoritative
inventory snapshot. Selectors are deterministic and reconstructible. Runtime
self-labels and mutable backend state cannot elevate a machine, assign its role,
or silently change an active cohort.

This permits exact materialized membership for the initial fleet and a pinned
selector algorithm for a future larger fleet.

### SYS-077: Rollout actions remain separate from local eligibility

Discovery, acquisition, staging, activation permission, local selection,
reboot coordination, trial boot, assessment, and blessing retain their distinct
consequences. Every target independently verifies exact authorization,
integrity, compatibility, freshness, and local policy. A channel, server
response, rollout grant, or reboot slot cannot replace those checks.

### SYS-078: Every transition is qualified from exact source to target

A rollout action binds the current and target deployment identities and a
permitted transition. Ordering labels do not justify skipped releases,
downgrades, input-baseline changes, or state transitions that lack applicable
compatibility evidence.

### SYS-079: Advancement uses explicit evidence and denominators

Each cohort states exact membership, representativeness, gates, deadlines,
missing-data policy, and stop conditions. Observations bind machine, target
deployment, boot, policy, producer, and time. Missing, stale, mismatched,
excluded, deferred, failed, and successful members remain distinct; local
blessing cannot become fleet qualification.

### SYS-080: Pause, resume, supersession, and withdrawal are ordered

Control decisions are authenticated, append-only, idempotent, replay-resistant,
and comparable under a named epoch and ordering policy. Acquisition pause,
activation pause, resume, supersession, and withdrawal state their scope and
in-flight boundary. Withdrawal outranks ordinary grants and exceptions without
erasing bytes or historical evidence.

### SYS-081: Fleet-service failure stops new unsafe progress only

Unavailable discovery, rollout, publication, telemetry, or coordination cannot
grant new progress. Cached decisions are bound to exact machine, action,
source, target, epoch, and freshness. Retained local boot, assessment recording,
blessing, eligible fallback, deliberate rollback, and recovery continue under
SYS-041, and reconnect safely reconciles replayed or delayed records.

### SYS-082: Availability coordination is separate and bounded

Activation and reboot obey declared role/failure-domain windows, inhibitors,
drain behavior, concurrency, external observation, and alternate-access
requirements. Any lease has owner, scope, expiry, crash recovery, and
reconciliation semantics. It confers no software eligibility or authority.

Singleton high-consequence roles require an honest attended or otherwise
explicit policy; they do not gain redundancy from cohort terminology.

### SYS-083: Pins and deferrals expose their consequence

Each pin or deferral records owner, reason, exact scope, creation, expiry or
review trigger, support/security consequence, and remediation. It cannot
override withdrawal. Healthy, pinned, stale, current, and supported remain
independent status properties.

### SYS-084: Rollout status and audit are exact and privacy-bounded

Status reconstructs plans, decisions, grants, observations, in-flight actions,
exceptions, and per-machine lifecycle state from retained attributable records,
while preserving native diagnostics. Machine identifiers, topology, timing,
failures, and exposure are collected, disclosed, retained, redacted, and
deleted under a named private-fleet policy.

### SYS-085: Emergency rollout compresses time, not identity

Emergency rollout binds the maintenance-policy incident class, exact affected
scope, reduced gates and claims, skipped checks, blast radius, minimum SYS-012
evidence, fallback or maintenance recovery, stop overrides, approver, and
follow-up obligation. An automatic stop can be overridden only by a new
attributable risk decision.

## Guardrails from adversarial review

### Do not equate percentages with evidence

A one-of-one cohort is not statistically safer than a singleton. Plans state
literal members and what their observations cover.

### Do not let fleet services own boot correctness

Fleet services may offer and schedule. Local retained policy verifies and owns
the accepted lifecycle. A service outage is a loss of new progress, not a loss
of already retained boot or fallback.

### Do not claim an instantaneous pause

An already consumed grant or committed boot selection may be in flight. The
design must bound and show that set rather than promise impossible synchronous
revocation.

### Do not count silence as health

An unreachable target can be excluded, deferred, or accepted as risk through an
explicit decision. It cannot silently improve a success rate.

### Do not make a reboot lock an update permission

Availability coordination answers whether disruption is acceptable now. It
does not answer whether the bytes are authentic, eligible, or safe.

## Strongest rejected alternatives

### Let every machine follow `stable`

Rejected. A mutable channel cannot express exact targets, source-to-target
compatibility, phase evidence, bounded pause, or historical reasoning.

### Let the rollout server be authoritative fleet state

Rejected. Database loss or compromise would change desired intent and history,
and offline machines could not independently verify decisions.

### Treat target-reported group and health as authoritative

Rejected. A compromised or misconfigured target could select an easier cohort
or advance later members.

### Require an always-on coordinator

Rejected for the initial phase. It adds an availability and maintenance
dependency before the fleet demonstrates a need for one.

### Ban emergency cohort compression

Rejected. Inaction can be riskier during active exploitation. The reduced path
must be explicit and bounded rather than impossible or informal.

## Required implementation evidence

Acceptance establishes policy only. DES-0009 still requires:

1. one complete static-record or attended rollout;
2. exact cohort derivation over the reference inventory;
3. local action and eligibility separation;
4. a blocked direct transition and valid intermediate path;
5. failure, missing, forged, stale, and mismatched observations;
6. pause races and bounded in-flight accounting;
7. replay, conflict, resume, supersession, and withdrawal;
8. offline service, publication, DNS, WAN, and clock failure;
9. reboot-lease crash/partition and singleton router handling;
10. pin, deferral, stale, and unsupported behavior;
11. normal and emergency operator procedures; and
12. measured comparison with Nebraska and Cincinnati-derived semantics.

## Decision

Accepted by Jason Tarasovic on 2026-08-10. SYS-075 through SYS-085 are
normative policy boundaries. DES-0009 remains in review until its required
implementation evidence resolves the record model, mechanism, and operating
cost.
