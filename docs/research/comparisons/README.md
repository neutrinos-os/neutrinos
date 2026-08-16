# Comparison index

Each entry carries the **durable conclusion** of one comparison — what it
decided, or refused to decide, and the one constraint most likely to matter
later. Read an entry here instead of the document; open the document only to
challenge its conclusion or to use its evidence.

A comparison is evidence, never authority. None of these selects an
architecture; where one led to an accepted decision, the ADR is named and the
ADR wins.

Entries are independent. Adding one does not invalidate another, and nothing
here is derived from anything else, so this index does not go stale the way a
join would.

## Substrate and system model

**[RES-0001 existing systems](existing-systems.md)** — `in-review`.
There is **no justification for building a new image, update, boot or rollback
substrate**. The project boundary is a thin role, configuration, qualification,
release and fleet-policy surface over existing components. NixOS was a credible
adopt-instead candidate on capability and was ruled out on the owner's operating
retrospective, not on features. ParticleOS is the closest executable reference
and should be studied and reused selectively — **not silently forked, and not
treated as a stable dependency**. CH-001 stays open: this does not yet show the
systemd-native surface beats bootc.

**[RES-0003 bootc vs systemd-sysupdate](bootc-vs-systemd-sysupdate.md)** —
`in-review`. Direct systemd/UAPI + mkosi composition is the **default substrate
candidate, not an accepted architecture**, because accepted SYS-030 requires
authenticating the complete release-owned boot and immutable-root chain and
bootc's production path does not currently demonstrate that — its systemd-boot
and sealed UKI/composefs path remains experimental. **bootc stays the strongest
challenger**, and NeutrinOS will not adopt its experimental backend merely to
satisfy the requirement. The selection cannot be finalised from documentation;
symmetric lifecycle spikes against both candidates gate the substrate ADR.

**[RES-0004 deployment-set substrate mapping](deployment-set-substrate-mapping.md)**
— `in-review`. **No custom updater or object store is justified**: static HTTP
plus signed checksum manifests and sysupdate targets suffice. Two NeutrinOS-owned
joins *are* justified — a detached release-evidence envelope (no native signature
object carries qualification, scope, compatibility, freshness and authorization
together) and a read-only status/gate join. Flattened normal configuration is the
initial safe mapping on both paths; note this predates ADR-0004, which moved
configuration to signed confexts.

## Storage, integrity and update

**[RES-0006 storage integrity and encryption](storage-integrity-and-encryption.md)**
— `complete`. Paper baseline: GPT with DPS types under `systemd-repart`; an
ESP-backed boot artifact store, two `/usr` slots, two matching dm-verity hash
slots, and an independently retained recovery artifact; LUKS2 state volumes split
by custody and unlock policy, Btrfs leading with ext4 as bounded challenger.
Its 2026-08-11 evidence update carries the parts that aged best: the verity path
is **implemented, not merely specified**; EROFS determinism is **real and
version-scoped**; and **the reference implementation authenticates `/usr`, not
the root** — the observation that became DES-0006 C-013 and
[ADR-0004](../../adrs/0004-usr-scoped-release-artifact.md). Recorded gap: the
embedded A/B updater projects had never been reviewed, which RES-0014 then did.

**[RES-0014 embedded A/B update field evidence](embedded-ab-update-field-evidence.md)**
— `complete`. The highest-yield transfer in the set, and the source of DES-0006
C-014/C-015. What the field knows: **mark the target ineligible before writing
the first byte**; boot-selection state must not live inside the thing it selects;
updating the bootloader is the irreducible single point of failure; **verify by
reading back, not by trusting the write**; small storage forces an honest choice
between fallback and retry; **rollback needs a loop breaker**; and there must be
a designed answer for when every deployment fails. Five failure-matrix additions
were proposed that DES-0006's verification list did not cover.

**[RES-0015 stateless `/etc` configuration delivery](stateless-etc-configuration-delivery.md)**
— `in-review`. **The single most important negative result in the corpus.** No
shipping image-based system surveyed has a stateless `/etc`; every one gives
`/etc` persistent writable backing and delivers configuration by writing into it
— including systemd's own reference distribution, which has the mechanism
available and does not use it. A stateless `/etc` *is* operated in the field
(NixOS impermanence, `systemd.volatile=yes`) but always populated from a
*generated* source, never a delivered artifact. **The pairing NeutrinOS is
building — stateless `/etc` fed by confexts — is unattested.** That does not make
ADR-0004 wrong; it makes it novel work rather than adoption of prior art, and the
argument originally drafted for it was written without knowing that.

## Configuration, identity and secrets

**[RES-0005 fleet intent representation](fleet-intent-representation.md)** —
`complete`, **accepted as [ADR-0003](../../adrs/0003-bounded-fleet-intent-representation.md)**.
TOML 1.0 authoring validated as a restricted JSON data model by JSON Schema
2020-12, exact native files by small source manifests, canonical JSON for
resolved output and evidence. The constraint that outlives the syntax choice:
authored data and native files flow through a *separately owned* deterministic
implementation to resolved data plus evidence. Schemas validate shape; owned code
resolves references; native tools validate native files; project policy evaluates
invariants. Parser, validator and JCS library remain spike results.

**[RES-0011 secret custody and delivery](secret-custody-and-delivery.md)** —
`draft`. **The mechanisms compose rather than compete.** Least-complex path to
exercise: administrative custody or issuer → machine/operation-scoped
authenticated transfer → local protected representation where needed → systemd
credential for one named service activation. systemd credentials lead the last
mile but select no custody backend; `systemd-creds` leads local representation;
age/SOPS is a custody/transport challenger; Vault-like services and SPIFFE are
scale- and workload-driven challengers only. Selects nothing.

**[RES-0012 Unix identity and rootless containers](unix-identity-and-rootless-containers.md)**
— `draft`. Smallest credible combination: fleet allocation record → classic fixed
human UID/GID → explicit matching subordinate range → per-workload rootless
namespace contract → idmapped bind/volume where qualified → sysusers or
DynamicUser per service-state need. **systemd-homed must be tested against that
baseline**, not dismissed from historical experience nor accepted from feature
lists. Never allocate sub-IDs opportunistically on the target.

**[software placement mechanisms](software-placement-mechanisms.md)** —
`research-note`, **no RES ID**. **No mechanism spans all placement classes
honestly.** Accept the owner/lifecycle taxonomy first, then select a deliberately
small mechanism set. Its most reusable content is the table of *false inferences
to reject* — that a container implies reproducibility or isolation, that a
Flatpak label implies safe confinement, that a digest defines a safe runtime and
state lifecycle, that broader package coverage is lifecycle-free.

## Inputs, evidence and rollout

**[RES-0007 package ecosystem and snapshot policy](package-ecosystem-and-snapshot-policy.md)**
— `in-review`. **Fedora stable leads** because its maintained branch and staged
updates better bound security-response churn for a single maintainer. **Arch
remains a mandatory challenger** and should replace Fedora if literal reference
closures show Fedora's older components, release migrations or third-party
overlay count outweigh the cost of qualifying rolling snapshots. Preserve exact
metadata and packages in a NeutrinOS intake snapshot — **Fedora branch policy is
not a historical byte-retention service**, which the 403 during Fedora 45 mass
branching later demonstrated in practice (see `L-002`).

**[RES-0008 supply-chain evidence standards](supply-chain-evidence-standards.md)**
— `in-review`. Leading set for EX-0010: SLSA v1.2 provenance in in-toto
Statements, DSSE envelopes, CycloneDX 1.7 JSON for SBOM/VEX, SPDX 3.0.1 as
mandatory challenger, native advisories retained literally and normalised
OSV-shaped, PURL plus content digest for correlation, strict Reproducible Builds
for byte-level claims. **One universal document is rejected.** Accept no format
by name until round-trip identity, coverage, semantic loss, offline validation
and operator effort are demonstrated.

**[RES-0009 fleet rollout coordination](fleet-rollout-coordination.md)** —
`draft`. Accept only substrate-independent rollout requirements; model one
rollout as immutable records plus an attended procedure; borrow transition-edge,
phased-offer, maintenance-window and reboot-slot semantics from Omaha/Nebraska,
Cincinnati/Zincati and FleetLock where they reduce custom logic. **Adopt a
service only when it is simpler in measured operation and does not become an
unreviewed authority.**

**[RES-0010 installation and provisioning](installation-and-provisioning.md)** —
`draft`. `systemd-sysinstall` leads under ADR-0001, gated on a released version
and the literal EX-0012 lifecycle, with a direct lower-level systemd mapping kept
as the conformance reference so its limits stay visible. Ignition is a mandatory
*generated-adapter* challenger for VM/cloud handoff and **must not become an
authoring surface**; bootc install is the integrated-lifecycle challenger;
cloud-init is compatibility-only and deferred. Accept no mechanism before
interruption, replay, clone, preservation, authority and secret-retirement tests.

## Tooling and process

**[RES-0013 VM test harness](vm-test-harness.md)** — `in-review`, owns `P-009`.
**Not a single-winner question**: boot-integrity and throughput roles have
opposite requirements, and the original recommendation was two harnesses for two
jobs. QEMU alone provides a writable firmware varstore and a TCG fallback;
Cloud Hypervisor and test.thing provide neither. **test.thing is GPL-3.0-or-later
and cannot be copied into this Apache-2.0 repository** — its techniques were
adopted without its code (notify-vsock readiness, SMBIOS credentials,
`snapshot=on`, all from systemd's documented interfaces and mkosi). Depends on
`W-002`: if NeutrinOS ships a VMM, the harness becomes a declared input.

**[RES-0016 record corpus maintenance](record-corpus-maintenance.md)** —
`in-review`, owns `P-010`. Separates three problems that get conflated:
referential integrity, derived state, and event history. Holds one line —
**authored prose stays in files while duplication is generated**, with frontmatter
as the generated projection. Retrieval and embeddings are deliberately out of
scope because this project's read discipline suppresses discovery on purpose;
binary storage is ruled out for any system of record because **the reviewable git
diff is the authority mechanism**. Selects nothing, and recommends exactly one
first step: **a validator**, because it addresses the whole observed failure class
at no dependency cost and fits the existing `check:fast` contract.

## Adversarial reviews of comparisons

**[RR-0001 on RES-0001](reviews/0001-existing-systems.md)** — `open`. Seven
challenges, of which the sharpest are that **the preferred conclusion may be
encoded in the premise**, that NixOS may already satisfy the claimed
distinction, and that **upstream security maintenance remains unowned**.
Resemblance to ParticleOS is not proof of a sustainable base.

**[RR-0002 on RES-0003](reviews/0002-bootc-vs-systemd-sysupdate.md)** — `open`.
Six challenges. The two most durable: **systemd-first is being relaxed exactly
when it becomes costly**, and **documentation maturity is not operational
reliability**. Also warns that sysupdate's composability may be a feature rather
than a missing product.
