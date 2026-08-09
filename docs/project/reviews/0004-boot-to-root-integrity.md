---
id: PR-0004
subject: Boot-to-root integrity target
reviewer: Codex adversarial pass
date: 2026-08-09
status: accepted
---

# Boot-to-root integrity target review

## Decision scope

This decision accepts powered-off substitution by an attacker with temporary
physical access as an initial production threat and ratifies SYS-030. It does
not ratify the rest of DES-0003, select a substrate, require one cryptographic
format, or claim protection against malicious firmware or a compromised
running kernel.

## Accepted claim

Normal production boot must authenticate, from the configured platform trust
anchor, all release-owned boot artifacts and the release-owned immutable root
before granting them trusted-production status. Authenticating only the first
EFI executable or kernel is insufficient if privileged userspace remains
substitutable.

The claim excludes mutable machine, administrator, user, and workload state.
Executable mutable state remains part of the effective trust surface and must
be separately governed and reported.

Development, owner-authorized repair, and recovery paths may boot different
artifacts. They must be independently authorized and visibly distinguished
from the qualified normal-production path.

## Adversarial disposition

The requirement may increase integration and key-management cost and may rule
out otherwise mature substrate configurations. That cost is accepted as a
consequence of the threat boundary, but it does not justify selecting an
experimental implementation merely to check a mechanism box.

A candidate must demonstrate SYS-030 on a production-supported path. If no
candidate can do so responsibly, NeutrinOS must phase or delay physical
production deployment rather than silently weaken the claim.

## Decision

Accepted by Jason Tarasovic on 2026-08-09. SYS-030 is normative project policy.
The remaining threat-model requirements, physical key layout, role-specific
confidentiality objectives, and recovery mechanisms remain in review.
