---
id: DES-0009
title: Fleet release promotion and rollout control
status: in-review
owners: [Jason Tarasovic]
reviewers: [Codex adversarial pass]
created: 2026-08-10
last_updated: 2026-08-10
depends_on: [DES-0001, DES-0003, DES-0005, DES-0008]
decision_backlog: [L-006, L-007]
related_adrs: []
---

# Fleet release promotion and rollout control

## Problem

NeutrinOS has defined what a deployment is, what makes it eligible on a
machine, and what evidence may support promotion. It has not yet defined how an
authorized release moves across the personal fleet without turning a mutable
channel, percentage, server response, or successful boot into authority it does
not possess.

The initial fleet is small and heterogeneous. A percentage rollout over one
workstation, one router, and one separate server would create false precision.
The design must instead make every consequential transition attributable while
remaining small enough for one maintainer to operate during both normal and
urgent releases.

The original design session suggested Omaha/Nebraska for deciding who should
update and when, while systemd-sysupdate or another accepted substrate owns
artifact transfer and installation. That separation remains useful. Adoption
of Omaha, Nebraska, Cincinnati, Zincati, FleetLock, or a custom service does not
follow from it.

## Goals

- Separate release authorization, rollout policy, artifact transfer, local
  eligibility, and reboot coordination.
- Bind every rollout action to exact release, deployment, policy, inventory,
  and evidence identities.
- Limit blast radius with role-aware ordered cohorts and explicit gates.
- Make pause, resume, withdrawal, pinning, and emergency behavior precise.
- Preserve local boot, health recording, fallback, and deliberate rollback when
  fleet services or the WAN are unavailable.
- Support a static or operator-driven personal-fleet implementation before a
  continuously available rollout service is justified.
- Produce status that explains both what happened and why a machine did or did
  not advance.

## Non-goals

- Selecting the update transport, discovery protocol, database, message bus,
  dashboard, or hosted service.
- Replacing the accepted deployment lifecycle with a fleet controller.
- Defining a public distribution, multiple maintained release lines, or an SLA.
- Treating one machine's successful blessing as fleet qualification.
- Guaranteeing continuous availability for singleton roles such as the initial
  router.
- Automatically remediating arbitrary workload or mutable-state failures.
- Selecting fixed cohort sizes, timers, maintenance windows, or failure
  thresholds before the representative exercise.

## Accepted requirements and constraints

The design inherits these accepted boundaries:

- SYS-028 and SYS-029 make authorization content- and scope-bound and require
  complete local verification before selection.
- SYS-031 keeps authorization, qualification, freshness, currentness, health,
  blessing, support, and local modification distinct.
- SYS-036 prevents authorization from laundering an unqualified rebuild.
- SYS-037 through SYS-041 define withdrawal, bounded trials, machine-local
  blessing, closure retention, and offline lifecycle behavior.
- SYS-042 through SYS-047 make fleet inventory authoritative over role and
  machine intent; runtime observation cannot assign a role.
- SYS-064 requires an upstream-universe transition to establish a new baseline
  and repeat applicable qualification.
- SYS-065 through SYS-074 define immutable historical evidence, promotion
  evidence sets, current vulnerability assessment, and compromise traversal.
- The maintenance policy promises one current release line and best-effort
  security response, not permanent support for every retained deployment.
- A systemd ecosystem component is preferred when it satisfies a requirement;
  another component needs a concrete advantage or fills a real systemd gap.

## Decision drivers

1. The router has the highest availability consequence and no same-role
   redundant peer in the initial fleet.
2. `desktop-jason`, `router`, and `misc` are different role realizations; one is
   not automatically a valid canary for another.
3. Release identity and authorization must remain verifiable without trusting
   the current response of a rollout server.
4. A single maintainer needs an inspectable procedure with bounded ceremony.
5. Acquiring bytes early is often safe and useful; selecting them for boot and
   rebooting are separate operational risks.
6. Missing or stale telemetry must not be counted as success.
7. An outage of the control plane must stop unsafe new progress without
   breaking an already usable machine.
8. Emergency response must be faster than normal rollout but still more
   attributable than an improvised manual update.

## Options considered

### Manual per-machine updates with an operator checklist

This is viable for the first few machines and is the operational baseline. It
has low infrastructure cost and makes singleton updates deliberately attended.
It becomes weak when the checklist is mutable, the selected identities are not
machine-readable, or observed failures are not joined back to the decision.

Retain it as a supported execution mode, but require the same immutable rollout
plan, grants, observations, and stop rules as automation.

### Minimal pull-based rollout records

Publish immutable, authenticated rollout revisions and machine-scoped or
cohort-scoped grants through ordinary static distribution. A small client pulls
them, verifies them, and invokes the selected local lifecycle substrate.
Observations may initially be collected manually or through a narrow endpoint.

This is the leading initial architecture because it can prove the semantics
without requiring a database-backed always-on controller. It is not accepted
until EX-0011 demonstrates replay resistance, pause/withdrawal behavior, and an
operator cost lower than manual drift.

### Omaha protocol with Nebraska

Nebraska is active Flatcar prior art for applications, channels, groups,
rollout policy, machine observations, and optional payload hosting. It directly
matches the transcript's proposed division of responsibility.

It is a mandatory challenger, not the default. Its protocol and product model
must be mapped to NeutrinOS deployment identities, authorization, exact
inventory targeting, local eligibility, and non-Flatcar transport. A client-
reported alias or group cannot become authoritative fleet intent.

### Cincinnati-style transition graph and phased offers

Cincinnati represents releases and permitted transitions as a directed graph;
Zincati supplies client identity hints, phased rollout wariness, canaries,
maintenance windows, and external reboot coordination. The transition-graph
model is especially useful when state or input-baseline compatibility prevents
skipping directly to the newest release.

Borrow the explicit transition semantics. Treat Cincinnati/Zincati as a
challenger because Zincati's concrete path is coupled to Fedora CoreOS and
rpm-ostree, and a percentage-based backend may be unnecessary for this fleet.

### Central push-based desired-state controller

A service commands each machine to install and reboot, and stores the canonical
fleet state in its database. This can provide a polished dashboard and fast
coordination.

Reject it as the initial architecture. It concentrates authority, encourages
the server's mutable state to replace checked-in fleet intent and signed
records, complicates offline behavior, and creates a custom control plane
before the fleet needs one.

### Channel pointer alone

Each machine follows `stable` and installs whatever identity the pointer names.
This is simple but cannot express role-specific gates, exact transition paths,
pause versus withdrawal, or why two machines received different outcomes.

Reject it. A channel may help discovery, but it is neither identity nor a
complete rollout decision.

## Proposed model

### Independent objects

| Object | Purpose | Identity and authority |
| --- | --- | --- |
| Release | Groups exact deployment variants | Immutable release record; version is only a label |
| Release authorization | Permits exact deployment identities for a scope | Signed by the accepted release authority |
| Rollout plan | Declares target inventory snapshot, transition policy, cohorts, gates, windows, and stop rules | Immutable content identity; names its authorizing policy |
| Rollout revision | Appends a start, advance, pause, resume, supersession, or termination decision | Ordered and authenticated; never edits prior revisions |
| Rollout grant | Permits a named machine or exact cohort member to take one bounded rollout action | Bound to machine, source, target, plan revision, action, and validity |
| Rollout observation | Reports a machine transition or health fact | Bound to machine, deployment, boot, plan, producer, time, and evidence |
| Reboot lease | Coordinates temporary availability impact | Grants no release authorization or local eligibility |
| Channel | Provides a mutable discovery hint | Not an identity and not sufficient authority |

A single serialized format may carry several of these objects only if their
identities, authorities, and consequences remain independently verifiable.

### Control flow

```text
qualified deployment variants + frozen evidence set
                    |
                    v
          release authorization
                    |
                    v
     rollout plan over inventory snapshot
                    |
           start/advance revision
                    |
                    v
  machine discovers bounded rollout grant
                    |
       +------------+-------------+
       |                          |
       v                          v
local authorization,        availability policy,
compatibility, freshness,   window, inhibitor,
and identity verification   and reboot lease
       |                          |
       +------------+-------------+
                    v
       acquire -> stage -> select -> trial
                    |
                    v
        attributable observation
                    |
                    v
         gate: advance, pause, or end
```

The rollout layer can make progress more restrictive. It cannot make a locally
ineligible deployment eligible, bless a deployment, rewrite fleet intent, or
authorize a different identity.

### Targeting and cohorts

The rollout plan names an immutable inventory snapshot. Membership derives
from enrolled machine identity, authoritative role assignment, platform class,
and explicit rollout attributes in that snapshot. Host-supplied labels are
observations only.

Cohorts are ordered, named sets, not percentages without a denominator. Each
cohort records:

- exact members or a deterministic selector plus snapshot identity;
- the deployment variant each member is expected to receive;
- why the cohort is representative and what it cannot establish;
- entry and exit gates;
- observation deadline and missing-data treatment;
- concurrency and reboot constraints; and
- automatic and operator-controlled stop conditions.

The initial shape is expected to be:

1. disposable representative VMs for each changed role or platform contract;
2. any explicitly identified low-consequence physical canary for that same
   applicable behavior;
3. ordinary workstation or server targets; and
4. singleton high-consequence targets through an attended window with a tested
   fallback and appropriate out-of-band access.

This is a policy shape, not a claim that `desktop-jason` validates `router`.
When no representative physical canary exists, that gap remains explicit and
the singleton gate becomes stricter rather than pretending the fleet is large.

### Transition paths

Every grant binds both current and target deployment identities. It references
a permitted transition edge whose evidence covers state-schema compatibility,
required intermediate releases, input-baseline changes, and applicable role
behavior.

The human ordering label may help choose a preferred target, but it cannot
prove that an arbitrary old machine may skip directly to it. If no eligible
edge exists, the machine remains held with an attributable reason.

### Staging and activation

Rollout actions are distinct:

1. discover metadata;
2. acquire inert bytes;
3. stage and integrity-verify a complete deployment set;
4. authorize selection of an exact staged deployment;
5. obtain any required availability window or reboot lease;
6. select one bounded trial boot; and
7. report assessment and blessing state.

Policy may allow acquisition or staging fleet-wide before any cohort may
activate. A stage grant never implies permission to select or reboot. Reboot
coordination never implies that the staged deployment is eligible.

### Advancement gates

A gate evaluates a declared observation set rather than a dashboard color. It
names the exact cohort denominator and distinguishes:

- succeeded and blessed;
- booted but not yet assessed;
- locally failed with fallback;
- failed without usable fallback;
- unreachable or missing telemetry;
- deliberately deferred or pinned; and
- excluded before the cohort began.

Only observations bound to the exact target deployment and applicable health
policy count. Qualification remains global evidence; blessing remains local.
An operator may accept risk and advance despite a gap, but the exception must
be a new attributable decision rather than silently changing the gate result.

For the personal fleet, an applicable hard failure in the first physical
member should default to an automatic pause. Automatic advance is allowed only
after EX-0011 establishes useful gates and failure detection. Resume always
requires a new revision and cannot be inferred from elapsed time alone.

### Pause, resume, supersession, and withdrawal

A rollout revision is append-only and has an order within a named policy epoch.
Clients reject replay, ambiguity, and incomparable conflicting decisions.

- **Pause acquisition** prevents new acquisition for the affected scope.
- **Pause activation** prevents new selections and reboots but may permit inert
  staging.
- **Resume** names the pause it supersedes and the evidence or accepted risk
  supporting renewed progress.
- **Supersede** redirects future grants to a new exact release or plan; it does
  not mutate already issued history.
- **Withdrawal** removes normal authorization or eligibility according to its
  scope and outranks an ordinary rollout grant, pin, or channel result.

Already running machines reevaluate currentness and support when a withdrawal
or new vulnerability fact arrives. Forced immediate reboot is not assumed:
role policy chooses containment, fallback, maintenance recovery, shutdown, or a
replacement release. Historical bytes and evidence remain subject to retention
policy.

### Offline and failed-controller behavior

An unavailable rollout service cannot grant new progress. A machine may use a
cached grant only for the exact action, source, target, machine, policy epoch,
and validity bound it carries. Clock uncertainty and stale revocation knowledge
must be visible.

Loss of discovery, rollout, telemetry, or reboot coordination must not prevent:

- booting an already selected eligible deployment;
- recording trial and health results locally;
- completing local blessing or eligible fallback under retained policy;
- deliberate rollback through the accepted local path; or
- entering separately authorized recovery.

After reconnection, reports and decisions are idempotent. A stale response must
not undo a later pause or withdrawal. A controller database restore must be
reconstructible from immutable plans, revisions, grants, and observations or
must explicitly disclose lost state.

### Availability and reboot coordination

Availability scheduling applies after software eligibility. Each role declares
whether activation requires:

- an attended or recurring maintenance window;
- a local inhibitor or drain contract;
- an external observer or out-of-band access;
- a bounded reboot lease;
- a maximum number of unavailable members per failure domain; and
- confirmation that the prior lease holder returned healthy or released its
  slot.

Leases require bounded expiry and ownership rules that survive client or
coordinator crashes. They are unsuitable as sole correctness evidence because
clock and partition behavior can create both leaked and duplicate slots.

For the initial router, the honest model is a singleton attended rollout with
representative VM qualification, local fallback, and tested alternate access.
Calling it a 100-percent final cohort adds no safety.

### Pins and deferrals

A pin fixes a machine to an exact deployment or blocks automatic activation. A
deferral delays an otherwise eligible action until a condition or deadline.
Both record owner, reason, scope, creation time, review or expiry, security and
support consequence, and remediation.

A pin cannot make a withdrawn deployment normally eligible. A pinned machine
may be healthy and intentionally operated while also stale or unsupported.
Those properties remain separate in fleet and local status.

### Emergency rollout

Emergency policy may compress cohorts, shorten observation periods, or require
attended simultaneous action when inaction is riskier. It still binds exact
subjects, records the incident trigger and affected scope, satisfies SYS-012's
minimum gate, names skipped checks and reduced claims, preserves an applicable
fallback or maintenance-recovery path, and creates a follow-up obligation.

An automatic safety stop remains valid during an emergency. Bypassing it
requires an explicit owner decision with the new blast radius and residual risk.

### Initial implementation posture

Start with data and procedure, not a service:

1. generate an immutable rollout plan from checked-in fleet intent and exact
   release authorization;
2. issue append-only per-machine or per-cohort action grants;
3. execute the plan manually or through a narrow pull client;
4. retain local and collected observations; and
5. reconstruct fleet status from the records.

Only introduce Nebraska, Cincinnati, a FleetLock service, or a NeutrinOS
controller when the exercise shows a concrete need. The selected host updater
continues to own transfer, staging, selection, boot attempt accounting, and
fallback wherever it satisfies the accepted lifecycle.

## State and compatibility

Plans, revisions, grants, observations, exceptions, and withdrawal facts are
immutable evidence records under DES-0008. Mutable indexes and dashboards may
cache their current interpretation but are rebuildable.

The fleet inventory snapshot is an input to a plan. Later inventory changes do
not silently add or remove members from an in-progress cohort. A new plan
revision must name the new snapshot and explain membership changes.

Rollout does not migrate mutable state by itself. Each permitted transition
references the applicable state compatibility and commit-barrier evidence from
DES-0002. Fallback after a failed trial remains conditional on that evidence.

## Security and trust

The rollout authority may decide timing and reduce scope. Unless explicitly
combined by an accepted future ADR, it cannot:

- authorize new artifact identities;
- sign platform boot artifacts;
- change role or machine intent;
- fabricate qualification or blessing;
- override withdrawal or recovery policy; or
- read unrelated machine, user, workload, or secret data.

Targets authenticate decisions and bind them to enrolled machine identity. The
service authenticates observations before using them for gates but treats a
compromised target's self-report as limited evidence. External role checks are
preferred where practical.

Machine identifiers, topology, versions, failures, update timing, and exposure
status are sensitive fleet data. Collection is purpose-limited, access-
controlled, retained by policy, and separable from public release evidence.

## Failure and recovery

| Failure | Required behavior |
| --- | --- |
| Rollout service unavailable | Stop new uncached progress; preserve local lifecycle and diagnosis |
| Publication unavailable | Retained bytes continue to boot; acquisition waits without changing eligibility |
| Stale or replayed grant | Reject by subject, epoch, ordering, and freshness policy |
| Conflicting decisions | Fail closed for new affected transitions and surface both records |
| Target lies about role or cohort | Ignore self-assertion; use authenticated inventory snapshot |
| Target lies about health | Limit consequence to declared gate; require external evidence where needed |
| Missing telemetry | Count as missing, never success; pause or expire under declared gate |
| Controller loses state | Rebuild from records or disclose loss; never infer success |
| Client crashes mid-stage | Resume or discard through substrate-safe staging; no selection of a partial set |
| Client crashes holding reboot lease | Lease expiry and reconciliation prevent permanent fleet lock |
| Candidate fails trial | Record exact failure; use eligible fallback or diagnosable stop |
| Withdrawal arrives offline | Apply when authenticated knowledge arrives; disclose prior knowledge window |
| Maintainer error advances cohort | Append pause/withdrawal; preserve decision history and affected-machine set |
| Emergency replacement also fails | Stop expansion; use applicable fallback, containment, or maintenance recovery |

## Operations and diagnostics

A human-readable rollout view must answer:

- What exact release, deployment variant, and authorization applies?
- Which inventory snapshot and selector placed this machine here?
- What is the latest authenticated rollout decision it knows?
- Which action is allowed now, until when, and by whom?
- Which local eligibility or availability gate blocks progress?
- What exact deployment is staged, selected, booted, and blessed?
- What observations caused advance, pause, resume, or withdrawal?
- Which machines are missing, failed, pinned, stale, or unsupported?
- Can the machine boot, fall back, and report locally without the controller?

Raw substrate status remains visible. NeutrinOS status is a join over native
state and evidence, not a replacement for upstream diagnostics.

## Verification

EX-0011 must exercise at least:

1. a normal multi-variant release over representative VM, workstation, router,
   and separate-server records;
2. deterministic cohort membership from a frozen fleet inventory;
3. acquisition and staging before activation permission;
4. an invalid direct transition and a required intermediate transition;
5. success, failure, fallback, missing telemetry, and an explicit accepted-risk
   advance;
6. pause before discovery, after staging, and immediately before reboot;
7. resume, supersession, withdrawal, replay, and conflicting decisions;
8. controller, publication, DNS, WAN, and clock failure;
9. pin and deferral expiry plus stale/unsupported status;
10. a crashed reboot-lease holder and a singleton router window;
11. release-, rollout-, and target-authority compromise boundaries; and
12. normal and emergency operator time and record volume.

Mechanism comparison must map minimal static records, Omaha/Nebraska,
Cincinnati-style graphs, and reboot coordination to every accepted requirement
without assuming the server's current database is historical evidence.

## Risks and unresolved questions

- Is a rollout grant a separate signed object or a policy-derived view over a
  signed plan and authenticated inventory?
- Which decisions require the release-authorization authority, and which may be
  delegated to a narrower rollout authority?
- Can Nebraska faithfully carry NeutrinOS content identities and action
  separation without a large adapter or schema fork?
- Is a complete transition DAG useful at personal-fleet scale, or is an exact
  allowed-source set per release sufficient?
- Which observations can be trusted from the target, and which need an
  independent observer for workstation, router, and server roles?
- What freshness window is safe for cached staging and activation grants on an
  offline router?
- How should an attended update be represented so that it is automatable later
  without becoming an unrecorded exception?
- Does the initial fleet need distributed reboot locking at all?
- What is the smallest privacy-preserving machine identifier usable by an
  externally hosted rollout service?

## Accepted requirements

PR-0012 accepts SYS-075 through SYS-085 as policy boundaries. They define
rollout identity, targeting, action separation, transition compatibility,
evidence gates, pause/withdrawal ordering, offline behavior, availability
coordination, exceptions, audit/privacy, and emergency rollout without
selecting a protocol or service.

## Review disposition

The design is in adversarial review. RES-0009 compares current prior art and
EX-0011 is the representative personal-fleet gate. The accepted requirements
do not select minimal static records, Omaha/Nebraska, Cincinnati-derived
semantics, or any reboot coordinator.
