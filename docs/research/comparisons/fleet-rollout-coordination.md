---
id: RES-0009
title: Fleet rollout and reboot-coordination prior art
status: draft
date: 2026-08-10
source_checked: 2026-08-10
related_designs: [DES-0009]
---

# Fleet rollout and reboot-coordination prior art

## Question

Which existing systems can supply NeutrinOS rollout policy or coordination
without becoming the artifact identity, release authority, local updater, or
authoritative fleet inventory?

This is a source review, not a product selection. Upstream behavior is dated
because these projects evolve.

## Required NeutrinOS boundary

```text
release authorization says what may run
rollout policy says who may advance and when
local eligibility verifies whether this exact machine may select it
update substrate transfers, stages, selects, and falls back
availability policy says whether activation may disrupt service now
```

A candidate may cover more than one box, but its native concepts must not erase
these distinctions.

## systemd-sysupdate and timers

systemd-sysupdate is the leading local lifecycle substrate candidate elsewhere
in this repository. Its natural scope is discovering, transferring, verifying,
and updating versioned local resources. systemd timers and services can schedule
polling and activation. This is valuable host machinery but does not by itself
provide authoritative fleet cohorts, observation gates, transition policy, or
reboot concurrency across machines.

Implication: systemd-first does not require inventing fleet policy inside
systemd-sysupdate. A narrow NeutrinOS policy client may call upstream local
interfaces after independently verifying a rollout decision.

Sources:

- <https://www.freedesktop.org/software/systemd/man/latest/systemd-sysupdate.html>
- <https://www.freedesktop.org/software/systemd/man/latest/sysupdate.d.html>
- <https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html>

## Omaha and Nebraska

Nebraska remains an active Flatcar project and update manager. Flatcar describes
it as using Omaha to monitor and orchestrate fleet rollout. Its current docs
show applications, packages, channels, default and custom groups, instance
registration/events, rollout-policy logic, and optional payload hosting.

Useful properties:

- a client-pull update-check model;
- explicit applications, groups, channels, and package assignments;
- rollout policy separate from default payload storage;
- visibility into client update events; and
- demonstrated operation beyond only a public vendor service.

Important mismatches or questions:

- Nebraska's normal Flatcar path assumes `update-engine` concepts and versioned
  packages rather than a NeutrinOS deployment-set manifest and evidence set.
- A channel or package assignment is not NeutrinOS release authorization.
- Client-provided aliases and other reported properties cannot assign role,
  group, or machine intent.
- The current documentation examples require deployment-specific transport
  security decisions; sample plain HTTP must not define NeutrinOS trust.
- Database state and web-UI actions need export as immutable attributable
  records if they are to support historical reconstruction.
- An adapter must preserve acquisition, staging, activation, and reboot as
  separate actions rather than treating one update response as all of them.

Verdict: mandatory challenger for rollout discovery and policy. Adopt only if a
literal protocol mapping is smaller and safer than minimal signed rollout
records plus the selected systemd-native local substrate.

Sources:

- <https://www.flatcar.org/docs/latest/updates-releases/>
- <https://www.flatcar.org/docs/latest/updates-releases/nebraska/managing-updates/>
- <https://www.flatcar.org/docs/latest/nebraska/development/>
- <https://github.com/flatcar/nebraska>

## Cincinnati and Zincati

Cincinnati represents valid release transitions as a directed acyclic graph.
Its protocol returns release nodes, payload references, and allowed edges.
Zincati's Fedora CoreOS client queries that graph and supplies stream, machine,
group, platform, and rollout-wariness inputs. The backend can progressively
offer an edge, while the client may still decide whether to apply it.

Useful properties:

- transition edges make skipped or forbidden upgrades explicit;
- phased offers and canary wariness are established concepts;
- client pull preserves some local decision making;
- rollout ordering and downgrade behavior are visible; and
- update discovery is distinguished from finalization/reboot strategy.

Important mismatches or questions:

- Zincati's concrete execution path uses rpm-ostree and Fedora CoreOS metadata.
- Dynamically assigned rollout scores are difficult to reconstruct unless the
  algorithm, inputs, and fleet denominator are retained.
- Percentages convey little safety for three heterogeneous machines.
- Stream, group, and client-supplied platform fields cannot replace the
  authenticated NeutrinOS inventory snapshot.
- An update graph edge still needs exact deployment identity, authorization,
  qualification, state compatibility, and local eligibility verification.

Verdict: borrow the explicit transition graph and the distinction between
phased offer and local action. Treat the full stack as a challenger only if the
fleet grows or transition complexity justifies it.

Sources:

- <https://coreos.github.io/zincati/development/cincinnati/protocol/>
- <https://coreos.github.io/zincati/usage/auto-updates/>
- <https://coreos.github.io/zincati/usage/agent-identity/>
- <https://github.com/openshift/cincinnati>

## FleetLock and maintenance windows

Zincati separates update discovery and staging from finalization. Its supported
strategies include immediate finalization, recurring maintenance windows, and
an external FleetLock service. FleetLock is a client-initiated HTTP protocol
modeling owned recursive semaphore slots for reboot coordination.

Useful properties:

- reboot availability is separate from payload discovery;
- a small protocol can sit over different lock backends;
- machine and group identity participate in slot allocation; and
- maintenance windows offer a service-free alternative.

Important mismatches or questions:

- a reboot slot proves neither software eligibility nor release authorization;
- recursive locks need careful crash and stale-owner semantics;
- simple success/error responses do not themselves provide a durable historical
  explanation;
- time zones, daylight-saving transitions, bad clocks, and missed windows need
  explicit treatment; and
- the initial fleet has no redundant router peer to protect with a counting
  semaphore.

Verdict: borrow the separation and test maintenance windows first. Do not deploy
a lock service until a real shared failure domain needs concurrent reboot
limits.

Sources:

- <https://coreos.github.io/zincati/usage/updates-strategy/>
- <https://coreos.github.io/zincati/development/fleetlock/protocol/>

## Minimal immutable rollout records

The smallest alternative is not a product. It is a set of authenticated,
content-identified rollout plans and append-only decisions distributed as
ordinary static objects. A pull client or an attended operator verifies a
machine-scoped action and invokes the local substrate.

Useful properties:

- directly uses NeutrinOS deployment, inventory, evidence, and authorization
  identities;
- works without an always-on database or service;
- history can live beside release evidence;
- manual and automated execution can consume the same records; and
- minimizes target data sent to an external service.

Risks:

- NeutrinOS must define the record and verifier;
- collecting observations and resolving concurrency may grow into a service;
- a home-grown protocol can repeat known replay and distributed-state mistakes;
  and
- operator ergonomics may be worse than Nebraska's existing interface.

Verdict: leading personal-fleet experiment, not an accepted implementation.
The result must be discarded if it grows beyond a thin policy/evidence layer.

## Comparison

| Criterion | Minimal records | Omaha/Nebraska | Cincinnati/Zincati | FleetLock/windows |
| --- | --- | --- | --- | --- |
| Exact NeutrinOS identities | Native by design | Adapter required | Adapter required | Out of scope |
| Transition graph | Must define | Package/channel oriented | Native strength | Out of scope |
| Phased offers | Must define | Native rollout policy | Native strength | Out of scope |
| Reboot coordination | Manual/window initially | Separate concern | Zincati strategy | Native focus |
| systemd local substrate | Directly composable | Custom client mapping | Custom client mapping | Composable after staging |
| Immutable decision history | Native goal | Must export/augment | Must retain graph/filter inputs | Must augment |
| Personal-fleet operating cost | Potentially lowest | Database/service/UI | Multiple specialized components | Low for windows, higher for lock service |
| Mature upstream behavior | No | Yes | Yes | Yes |
| Primary risk | Custom protocol growth | Semantic and payload coupling | Stack and scale mismatch | Confusing availability with eligibility |

## Candidate posture

1. Accept only substrate-independent rollout requirements.
2. Model one rollout as immutable records and an attended procedure.
3. Map the same scenario literally into Nebraska and Cincinnati concepts.
4. Borrow transition-edge, phased-offer, maintenance-window, and reboot-slot
   semantics where they reduce custom logic.
5. Prefer systemd-native host execution after the rollout policy decision.
6. Adopt a service only when it is simpler in measured operation and does not
   become an unreviewed authority.

## Evidence still required

- Nebraska API/Omaha message capture for a custom application and payload.
- Export and replay of Nebraska group rollout changes after database restore.
- Cincinnati graph with exact source/target deployment identities and a blocked
  state-incompatible edge.
- A static-record proof for pause, replay, withdrawal, and machine targeting.
- Measured component count, storage, credentials, upgrade burden, and operator
  time for every candidate.
