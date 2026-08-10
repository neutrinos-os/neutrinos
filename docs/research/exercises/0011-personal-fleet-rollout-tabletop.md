---
id: EX-0011
title: Representative personal-fleet rollout tabletop
status: proposed
date: 2026-08-10
exercise_type: tabletop
evidence_class: analysis-only
related_designs: [DES-0009]
---

# Representative personal-fleet rollout tabletop

## Purpose and evidence limit

This exercise tests whether DES-0009 can control a real small heterogeneous
fleet without percentage theater or a bespoke always-on controller.

It initially uses records and simulated observations. It does not prove the
selected updater, bootloader, health checks, network path, or signing mechanism.
Later executable spikes must replay the same cases against the literal local
substrate and any candidate rollout service.

## Fixture

Use the authoritative inventory records for:

- the reference qualification VM;
- `desktop-jason`, the first physical target;
- `router`, a singleton high-consequence network role; and
- `misc`, a separate server whose eventual role requirements remain less
  complete.

Do not infer equivalence from hardware discovery or from all machines being
owned by one person. Each scenario states which role and platform behavior its
observation covers.

## Release fixture

Construct release `N+1` with exact deployment variants:

| Variant | Intended scope | Representative evidence |
| --- | --- | --- |
| `D-vm` | reference VM | full virtual boot and lifecycle suite |
| `D-workstation` | `desktop-jason` | workstation configuration and health policy |
| `D-router` | `router` | routing, firewall, DHCP/DNS, WAN/LAN, fallback, alternate access |
| `D-server` | `misc` | only the accepted server capability subset; uncovered behavior remains explicit |

The release authorization and promotion evidence set are frozen before rollout.
Create a second release `N+2` for supersession and emergency cases.

## Proposed rollout record

The initial encoding should be plain enough to inspect in a diff. At minimum it
must bind:

- plan identity and schema;
- release authorization and evidence-set identities;
- fleet inventory snapshot;
- ordered cohort definitions and exact members;
- current and target deployment identity per member;
- permitted transition identity;
- staging, activation, observation, and expiry policy;
- pause and withdrawal precedence;
- decision authority and policy epoch; and
- privacy and retention class.

Whether grants are separately signed or derived from this record is an output
of the exercise, not an assumption.

## Cohort model

| Cohort | Members | What it can establish | What it cannot establish |
| --- | --- | --- | --- |
| `vm-role-gates` | disposable VM instances for changed variants | artifact boots, local lifecycle, simulated role contracts | physical firmware, peripherals, real network cutover |
| `workstation-physical` | `desktop-jason` | literal workstation platform and user-visible health | router or server role behavior |
| `server-physical` | `misc` when its role gates exist | literal server realization | router availability or workstation UX |
| `router-attended` | `router` | literal singleton role with alternate access and fallback | statistical redundancy or a second router |

If `misc` lacks accepted role requirements when the exercise runs, exclude it
before plan start with that exact reason. Do not count it as a successful member.

## Scenario matrix

### R-001: Normal ordered rollout

1. Publish and verify `N+1` without activating any target.
2. Allow all members to acquire and stage inert variants.
3. Activate and assess `vm-role-gates`.
4. Advance workstation, then the eligible server target.
5. Enter the attended router window only after its specific external checks,
   fallback, and alternate-access preconditions pass.
6. Reconstruct every decision and machine state from retained records.

Pass if no channel pointer or server response substitutes for exact identity and
each cohort advancement names its actual denominator and observations.

### R-002: Runtime self-label attempts cohort elevation

Have `desktop-jason` report itself as the eager router canary or change a group
label in client configuration.

Pass if targeting still follows enrolled identity and the frozen inventory
snapshot, the false report is diagnostic only, and no different variant or
earlier activation becomes available.

### R-003: Staged but activation-paused

Stage `N+1` on every member, then issue an activation pause before selection.

Pass if bytes remain inert, normal boot is unchanged, no reboot lease can
override the pause, and status distinguishes staged from selected.

### R-004: Pause race

Issue a bounded activation grant to one cohort, consume it at successive points
around local selection, and introduce a pause at each point.

Record the exact point after which the transition is in flight. Pass only if the
maximum possible blast radius is derivable and the UI never claims an
instantaneous stop it cannot enforce.

### R-005: Failed canary with eligible fallback

Boot a candidate that fails the applicable health assessment and returns to an
eligible retained deployment.

Pass if the exact failure survives fallback, local blessing is absent, the
cohort pauses, later cohorts receive no activation grant, and an operator must
append a reasoned decision to resume or supersede.

### R-006: Missing and dishonest observations

Make one target unreachable; separately have a compromised simulated target
claim success for the wrong deployment identity.

Pass if neither counts as success, deadlines produce explicit missing status,
and any advancement requires exclusion, deferral, independent evidence, or an
accepted-risk revision.

### R-007: Invalid direct transition

Place one machine on `N-2` where state compatibility permits only
`N-2 -> N -> N+1`.

Pass if a human `latest` label, channel, or valid `N+1` authorization cannot
create a direct edge. The machine must take the qualified intermediate path or
remain held.

### R-008: Replay and conflicting revisions

After revision 4 pauses activation, replay revision 2 and present a separately
valid but incomparable revision claiming resume.

Pass if no new activation occurs, both conflicts remain visible, and recovery
requires an authenticated decision ordered under the accepted epoch policy.

### R-009: Withdrawal during offline operation

Let the router cache a grant, disconnect it, then withdraw `N+1`. Exercise the
grant before and after its declared validity boundary.

Pass if the documented offline exposure window is accurate, expired or
clock-uncertain new activation fails safely, existing eligible boot and local
fallback remain possible, and reconnect causes immediate reassessment without
rewriting history.

### R-010: Controller and publication outage

Remove rollout service, artifact publication, WAN, and DNS at these points:

- before discovery;
- after acquisition;
- after staging;
- after selection;
- during trial assessment; and
- after fallback.

Pass if new ungranted progress stops while every locally retained lifecycle
operation required by SYS-041 continues.

### R-011: Reboot coordination failure

Simulate a client that crashes while holding a reboot slot, then a network
partition that outlives the lease. Also perform the router update with no lock
service, using an attended window.

Pass if the design states what happens for leaked and potentially duplicate
slots, and if the lock cannot authorize software or replace local eligibility.

### R-012: Pin, deferral, and stale status

Pin one machine to `N`, defer another until a maintenance window, let both
review deadlines pass, and then withdraw `N` for normal use.

Pass if owner, reason, expiry, and remediation remain visible; the first machine
becomes stale or unsupported as applicable; and neither pin nor deferral
overrides withdrawal.

### R-013: Emergency supersession

After a material vulnerability is found in `N+1`, create `N+2` through the
minimum emergency gate. Skip one normal cohort with an explicit reason and
attempt simultaneous attended rollout.

Pass if the exact reduced evidence and blast radius are visible, staging and
activation remain separate, automatic safety stops still work, and overriding
a stop creates a new attributable decision and follow-up obligation.

### R-014: Authority compromise

Exercise independently:

- publication service offers attacker bytes;
- rollout authority offers an unauthorized deployment;
- release authority is compromised after promotion;
- target forges observations; and
- controller database is restored to an older snapshot.

Pass if each event's maximum authority is explicit, affected subjects are
queryable through DES-0008 evidence, historical facts remain intact, and no one
component silently gains all five powers.

## Candidate mapping

Repeat the record mapping for:

1. plain immutable rollout records plus attended execution;
2. Omaha/Nebraska groups, packages, channels, policies, and events; and
3. Cincinnati-style release nodes/edges plus a separate activation strategy.

For each, list:

- native fields used unchanged;
- adapters and NeutrinOS-specific fields;
- authority and authentication boundaries;
- data that exists only in a mutable database;
- exact behavior while services are unavailable;
- upgrade and backup burden; and
- components or custom code required on every target.

Do not award a feature simply because a UI displays a similar word.

## Measurements

| Measure | Minimal records | Nebraska | Cincinnati-derived |
| --- | --- | --- | --- |
| Components and persistent services | TBD | TBD | TBD |
| Credentials and authority roles | TBD | TBD | TBD |
| Immutable records per normal release | TBD | TBD | TBD |
| Private telemetry bytes retained | TBD | TBD | TBD |
| Normal rollout owner time | TBD | TBD | TBD |
| Pause-to-bounded-stop time | TBD | TBD | TBD |
| Emergency rollout owner time | TBD | TBD | TBD |
| Restore and reconstruction time | TBD | TBD | TBD |
| NeutrinOS-specific adapter/code size | TBD | TBD | TBD |

## Acceptance output

The completed exercise must produce:

- a concrete rollout-plan and decision schema;
- a machine-readable scenario result set;
- a decision on signed versus derived grants;
- exact pause/withdrawal and in-flight semantics;
- role-specific cohort and observation policy;
- normal and emergency runbooks;
- a candidate recommendation with measured operating cost; and
- proposed ADR text only if the evidence supports a mechanism decision.
