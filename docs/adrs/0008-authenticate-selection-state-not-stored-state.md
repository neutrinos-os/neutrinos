---
id: ADR-0008
title: Do not authenticate general mutable state; authenticate the state that selects what boots
status: accepted
date: 2026-08-16
deciders: [Jason Tarasovic]
designs: [DES-0006]
supersedes: []
superseded_by: []
---

# Do not authenticate general mutable state; authenticate the state that selects what boots

## Context

[DES-0006 C-010](../designs/0006-storage-layout-and-encryption/review.md)
challenged the mutable-state posture: dm-crypt confidentiality and ordinary
filesystem checksums do not authenticate state against a malicious offline
writer, so an attacker could corrupt or plant executable state consumed after a
valid root boots.

The 2026-08-11 landscape check found the accepted-risk position **is the industry
position rather than a shortcut**. No comparable system authenticates general
mutable state: ChromeOS runs dm-verity on the rootfs only — the filesystem rather
than the whole partition — while parts of the stateful partition are dm-crypt
encrypted under a TPM-held system key with no integrity claim. Android has the
same shape: dm-verity for system, metadata encryption for userdata, no
authenticity.

**What those systems do authenticate is the small metadata that decides what
boots.** Android stores its AVB rollback index in eMMC/UFS **RPMB**, whose
accesses are authenticated by a key burned into eFUSE at manufacture. ChromeOS
keeps version and rollback state in **TPM NVRAM** and marks a failed kernel
partition `DMVERROR` so firmware stops selecting it.

The scope shifted under [ADR-0004](0004-usr-scoped-release-artifact.md) and
[ADR-0006](0006-ineligibility-before-overwrite-and-terminal-selection.md), which
is why this was revisited. Under full-root, `/etc` sat inside the authenticated
artifact; it does not now, so the unauthenticated writable root grew and early
boot reads from it before `/usr` is verified. Meanwhile the sharp target became
the **ESP**: unencrypted vfat holding the bootloader, the UKIs, boot-counter
state, and now the slot-ineligibility markers. Secure Boot with owner keys covers
executable substitution; **boot-selection state is not signed by anything.**

**Ruled and accepted 2026-08-11 as a narrowed claim.**

## Decision

**Offline authenticity stays out of scope for encrypted volumes**, matching every
comparable system. Encrypted state keeps the accepted risk, subject to the
hostile-state recovery exercise.

**Unencrypted boot-selection state is named as the real exposure and carries an
integrity obligation of its own.** That obligation is what ADR-0006's level 3
durable marking already reaches for. The consensus this follows is: **authenticate
the state that selects, not the state that stores.**

**The mechanism is deliberately not committed.** There is **no systemd-native
facility** for authenticated boot-selection state: `systemd-pcrlock` uses a TPM NV
index but is experimental and unrelated to boot counting, and systemd-boot's
counters are filenames on vfat. Building one would run against A-014 and
RES-0001's finding that NeutrinOS should not create mechanisms, so **the
obligation is recorded and the mechanism waits for the spike** rather than
incurring design debt now.

### Why the encrypted-volume case is narrower than it first appears

The [ADR-0007](0007-per-role-routine-unlock-policy.md) ruling does most of the
work. With PCR-bound sealing and a workstation PIN, an offline attacker who
modifies state **cannot subsequently unlock it**. Planting content into a volume
the attacker cannot decrypt is vandalism rather than a useful attack, so the
realistic hostile-state adversary is one who has already obtained unlock
capability, or is working on content outside the encrypted volumes.

## Alternatives considered

### dm-integrity or LUKS2 authenticated encryption for general state

Rejected for general state, partly answered from documentation as the challenge
required. LUKS2 authenticated encryption remains **experimental**; HMAC with
AES-XTS hashes the whole sector and is slow; few AEAD algorithms are usable and
several are discouraged; the dm-integrity journal is not encrypted; and
initializing authentication tags requires wiping the device first. Not a
production posture — though still worth a bounded measurement for a small
sensitive volume.

### Building an authenticated boot-selection store now

Rejected as design debt. It would mean NeutrinOS creating a mechanism, against
A-014 and RES-0001, before a spike has shown what the platform can actually
provide.

### Hardware anti-replay as a sufficient answer

Rejected as an absolute. The state-continuity literature is relevant to
ADR-0006's durable marker as much as here — **Memoir** (IEEE S&P 2011) uses hash
chains with NVRAM and monotonic counters against a malicious host; **Ariadne**
(USENIX Security 2016) reaches the theoretical minimum of one NV bit flip per
state update, NV wear being the binding constraint; **ROTE** (USENIX Security
2017) and **NARRATOR** (CCS 2022) are practical and distributed variants. A TPM
counter increment costs roughly 97 ms and a read roughly 35 ms — **acceptable per
boot, disqualifying per write**. And hardware anti-replay is not absolute:
[arXiv 2511.22340](https://arxiv.org/html/2511.22340v1) breaks eMMC RPMB
authentication with electromagnetic fault injection.

## Consequences

### Benefits

- The claim matches what the system actually provides, which is what C-010 asked
  for.
- Effort concentrates on the small, high-leverage metadata rather than on
  authenticating everything.
- No experimental cryptography enters the production path.
- The position is defensible by reference to how comparable systems are built.

### Costs and constraints

- Suspected hostile access routes to SYS-035 compromise recovery rather than
  normal mount, so recovery ceremony carries weight the mount path does not.
- The boot-selection integrity obligation has no owner mechanism and no date.
- A per-write authenticated counter is priced out by TPM latency, which
  constrains any future design to per-boot granularity.

### Accepted risks

- **Compromise may be undetectable**, so operators can mistakenly choose
  availability recovery over compromise recovery.
- **A named obligation with no mechanism can persist indefinitely as a documented
  gap**, and the ESP remains unauthenticated in the meantime.
- The narrowed claim depends on the ADR-0007 unlock policy holding; a role that
  cannot seal to PCRs loses the argument that offline modification is vandalism.

## Validation and review triggers

The hostile-state recovery exercise is what keeps the encrypted-volume accepted
risk honest, and it is not discharged by this decision. The substrate spike owes
an answer on whether an authenticated boot-selection store is reachable with
platform-native facilities.

Revisit this decision when:

- a systemd-native facility for authenticated boot-selection state appears, which
  would convert the recorded obligation into an implementable one;
- ADR-0006's level 3 marking proves infeasible, leaving the ESP exposure with no
  path to closure;
- LUKS2 authenticated encryption leaves experimental status and a bounded
  measurement on a small sensitive volume justifies it; or
- an attacker model appears in which content planted in an unreadable encrypted
  volume is useful rather than vandalism.
