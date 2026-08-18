---
status: active
last_updated: 2026-08-15
---

# Decision backlog

This is the intake queue for project and architectural questions. `Stated
direction` means the design session expressed a strong preference; it does not
mean an ADR has been accepted. Accepted project-scope decisions may be recorded
in the charter or scope document; accepted architectural decisions require an
ADR.

This backlog owns question and decision state. Plans and issues must not turn it
into a duplicate task tracker, and the work register that once provided the
aggregate view is frozen.

**A state cell is one line: the position, and a pointer.** Where an open question
carries evidence that lives nowhere else, it goes in [Open question
notes](#open-question-notes) below, not in the cell. A cell that has grown into
an argument is a defect — the argument belongs in the design, review, research
exercise or record that owns it.

## Wave 0: project identity

| ID | Question | State | Depends on |
| --- | --- | --- | --- |
| P-001 | What problem and invariant justify NeutrinOS rather than adopting an existing system? | [In review: direct systemd/UAPI composition is the default candidate under SYS-030; bootc remains the lifecycle challenger](../research/comparisons/existing-systems.md) | — |
| P-002 | Is the initial product a personal fleet, reusable framework, or public distribution? | [Accepted: personal fleet and reusable framework](scope.md#initial-operating-scope) | P-001 |
| P-003 | What are the accepted principles and non-goals? | [Accepted after adversarial review](reviews/0001-charter-principles-and-scope.md) | P-001 |
| P-004 | Which role and hardware are the first reference target? | [Accepted: VM qualification, `desktop-jason` first, `router` second](scope.md#initial-target-strategy) | P-001, P-002 |
| P-005 | Is systemd-native composition a project constraint? | [Accepted: systemd-first](../adrs/0001-systemd-first.md) | P-001 |
| P-006 | What is the canonical project name and technical identifier? | [Accepted: NeutrinOS and `neutrinos`](naming.md#decision) | P-002 |
| P-007 | Under what license, and at what visibility, is this repository published? | [Accepted: Apache-2.0 and a public repository](scope.md#licensing-and-visibility) | P-002 |
| P-008 | How do changes land on `main`, and what must a required signature prove? | Open. Owner bypass deliberately enabled 2026-08-11: `main` is fully enforced against everyone but the owner and never against the owner. A temporary state, not the answer. [PR-0028](reviews/0028-continuous-integration-evidence.md#post-acceptance-evidence), [notes](#p-008-landing-changes-on-main) | P-007 |
| P-009 | Which VM runner fills which qualification role beyond the first slice, and what may be taken from GPL-3.0 tooling? | Open. QEMU is a fixture chosen without comparison, and this is **not a single-winner question** — the boot-integrity and throughput roles have opposite requirements. Blocked behind `W-002`. [RES-0013](../research/comparisons/vm-test-harness.md), [notes](#p-009-vm-runner-selection) | P-004, P-007, W-002 |
| P-010 | How are approvals, artifact lifecycle, and cross-document state kept correct as the record corpus grows? | Open, **deliberately deferred past G2** by Jason Tarasovic 2026-08-12. Accepted cost: a continuing rate of referential and duplicated-state failures, including acceptances that no mechanism guards. [RES-0016](../research/comparisons/record-corpus-maintenance.md), [notes](#p-010-record-corpus-maintenance) | P-003, P-008 |


## Wave 1: system and trust model

| ID | Question | State | Depends on |
| --- | --- | --- | --- |
| S-001 | What is the independently replaceable unit of deployment? | [In review: complete content-identified deployment set](../designs/0001-system-model/README.md) | P-003 |
| S-002 | What belongs to the OS, machine configuration, administrator, user, and workload? | [Ownership boundary accepted; implementation design remains in review](reviews/0003-state-ownership-requirements.md) | S-001 |
| S-003 | How are common and role-specific artifacts composed? | [Accepted: versioned fleet intent resolves common, role, and machine configuration into an identity-bound deployment variant](../designs/0005-fleet-intent-and-configuration/README.md) | P-004, S-001 |
| S-004 | What are the disk, partition, filesystem, and encryption models? | [Requirements accepted; concrete layout and mechanism design remains in review](reviews/0009-storage-layout-and-encryption-requirements.md). Scope resolved 2026-08-11 by DES-0006 C-013: the authenticated artifact is **`/usr`**, and `/etc` holds nothing durable. Still open: the `/usr` format (DES-0006 C-007), SYS-123 confext obligations, early-boot integrity, and **where a separately delivered confext lives and when it is merged**. [notes](#s-004-storage-layout-and-confext-delivery) | S-001, S-002 |
| S-005 | What threats and trust assertions govern boot and runtime? | [Boot-to-root and role objectives accepted; remaining threat model in review](reviews/0005-role-security-and-availability-objectives.md). **Open sub-question: an untrusted `/usr` verity signer does not stop the boot, by upstream design** — the enforcement point is the TPM unseal, not the mount. [notes](#s-005-verity-signer-enforcement) | S-001 |
| S-006 | How are signing keys generated, used, rotated, revoked, and recovered? | [Accepted policy: separate routine, exceptional, machine, and data authorities; mechanism exercises remain](../adrs/0002-separate-authority-and-recovery.md) | S-005 |

## Wave 2: build and lifecycle

| ID | Question | State | Depends on |
| --- | --- | --- | --- |
| L-001 | Which package ecosystem and snapshot policy supply OS inputs? | [Input and snapshot requirements accepted; Fedora stable leads and a literal Arch comparison is required before ecosystem selection](reviews/0010-package-input-requirements.md) | P-002, S-001 |
| L-002 | What reproducibility, provenance, SBOM, and vulnerability guarantees are required? | [Policy boundaries accepted; concrete evidence formats, mechanisms, and costs remain in review](reviews/0011-supply-chain-evidence-requirements.md). **Open sub-question: retention covers the image closure and not the tools closure**, so composition keeps a reachability dependency the image no longer has. [composition record](usr-artifact-composition.md), [notes](#l-002-tools-closure-retention) | L-001, S-005 |
| L-003 | How is a machine installed and enrolled? | [Policy boundaries accepted; installer, enrollment protocol, record formats, and operating cost remain in review](reviews/0013-installation-and-enrollment-requirements.md) | S-001, S-004, S-006 |
| L-004 | How are releases discovered, staged, booted, blessed, and rolled back? | [Requirements accepted; substrate conformance remains in research, with direct systemd/UAPI leading under SYS-030](reviews/0007-deployment-lifecycle-requirements.md) | S-001, S-004 |
| L-005 | How does mutable state remain safe across upgrade and rollback? | [Requirements accepted; migration and recovery mechanisms remain in review](../designs/0002-state-ownership/README.md#update-and-migration-protocol) | S-002, L-004 |
| L-006 | How are releases promoted, phased, paused, and withdrawn across a fleet? | [Policy boundaries accepted; rollout records, protocol, coordination mechanisms, and operating cost remain in review](reviews/0012-fleet-rollout-requirements.md) | L-002, L-004 |
| L-007 | What are the release cadence and security-response commitments? | [Accepted: single current line and best-effort response](maintenance-policy.md) | P-002, L-001, L-002 |


## Wave 3: configuration and workloads

| ID | Question | State | Depends on |
| --- | --- | --- | --- |
| C-001 | What is the source of truth and representation for machine and role configuration? | [Accepted: TOML records, JSON Schema structural validation, literal native sources, and generated canonical JSON evidence](../adrs/0003-bounded-fleet-intent-representation.md) | S-002, S-003 |
| C-002 | How are `/etc`, local overrides, secrets, and credentials owned and delivered? | [Policy accepted; custody, envelope, issuer, recovery, and exception mechanisms remain in review](reviews/0014-secret-and-credential-delivery-requirements.md). [DES-0005's amendment](../designs/0005-fleet-intent-and-configuration/README.md) settles the nine SYS-123 obligations. **Still open**: local overrides, secrets and credentials, which confexts do not resolve; the unqualified-configuration test path; the concrete path carve. [notes](#c-002-configuration-and-credential-delivery) | C-001, S-005 |
| W-001 | What are the supported identity, UID, sub-ID, and rootless-container semantics? | [Policy accepted: stable inventory-owned durable identity and explicit per-workload maps; exact allocations, classic accounts versus systemd-homed, runtime mappings, and migration remain in review](../designs/0012-unix-identity-and-rootless-containers/README.md) | S-002, C-001 |
| W-002 | What is the microVM artifact, networking, storage, and lifecycle model? | Open. Now blocks `P-009`: if workloads are microVMs, testing NeutrinOS in a VM is inherently nested, which constrains the long-term harness | S-003, S-004, C-001 |
| W-003 | Which software belongs in the OS, user environment, project, GUI sandbox, container, or VM? | [Policy accepted: owner/lifecycle placement classes, release-owned role dependencies, effective-access boundaries, and independent update domains; exact mechanisms remain in review](../designs/0013-software-placement/README.md) | S-002, W-001 |
| W-004 | When are role-specific kernels or no-initrd variants justified? | Open | P-004, S-004, L-002 |
| C-010 | Which `C` entries carry policy that ought to sit inside the verity boundary — `shadow` above all — and is Fedora's `pam_unix.so nullok` default NeutrinOS's? | Open, and **narrowed by measurement after two wrong diagnoses, both recorded here rather than edited away.** (1) "ADR-0004 empties `/etc`" — false: ADR-0004 regenerates `/etc`, and `mkosi.finalize` already relocates `/etc/pam.d` to `/usr/lib/pam.d`. (2) "`authselect select` never runs, so the links dangle" — false: Fedora's scriptlet applies the `local` profile at build, and the factory carries the generated files. Booted against the session artifact 2026-08-16: `/etc` reaches userspace with **77 entries**, `/etc/authselect` with **10**, `/usr/lib/pam.d/system-auth` is a symlink to `/etc/authselect/system-auth` and **resolves**; `systemd-tmpfiles-setup` reports success. The PAM chain was never broken. **The fixture-grade stack written on 2026-08-16 never shipped**: the greetd package supplies `/etc/pam.d/greetd` and `greetd-greeter` too, and `relocate` overwrites unconditionally (`mv` for files, `ln -sfn` for links), so all four fixture files were discarded at build. It is deleted; rebuilt and reverified 2026-08-16, `grep -rl NeutrinOS /usr/lib/pam.d` returns nothing and `T4-SESSION-001` passes with all nine observations unchanged. Recorded while measuring it: the shipped `local` profile carries **`pam_unix.so nullok`** in its auth and password stacks, so the artifact permits empty passwords as a Fedora default rather than as anything NeutrinOS chose — a separate disposition from the one below, and not yet anyone's. **A third diagnosis, in this row, was also wrong and is corrected here rather than edited away.** It asserted `C /etc/authselect`, putting auth policy in a writable `/etc` outside verity, and asked whether ParticleOS's `L?` should replace it. Both halves are false. Traced 2026-08-18: `authselect` has never appeared in `mkosi.finalize` — `git log --all -S authselect` over that file returns nothing — so it has always taken the `L` default, and `etc-path-carve.md`'s measured tally (PLN-0002-03a, 2026-08-11) already placed it among the 59 `L` entries, the `C` list being exactly `machine-id passwd shadow group gshadow subuid subgid adjtime ld.so.cache`. The `C` was inferred, never measured: the 2026-08-16 boot observed `/etc/authselect` holding 10 entries and `system-auth` resolving, both of which are equally true of `L` and of `C`, so that boot could not distinguish them. Measured on the booted `workload` artifact 2026-08-18: the generated fragment reads `L /etc/authselect`; `/etc/authselect` is a symlink to `/usr/share/factory/neutrinos-etc/authselect`; `/etc/nsswitch.conf` resolves into that same factory; and a write into it fails. Not `C`, not writable, not outside verity. `L?` is not an alternative placement either: read from systemd's `tmpfiles.c`, `?` sets `ignore_if_target_missing`, is accepted only on `L`, and silently skips the line when the source is absent — ParticleOS carries it because one `etc.conf` serves arch, debian, fedora and opensuse and authselect exists only on Fedora/CentOS. NeutrinOS emits a line only for an entry that exists at build time, so `?` would be a no-op. **The placement question is closed by measurement; NeutrinOS already does what ParticleOS does.** What genuinely remains is the general form, and it bites hardest where the row never looked: `shadow` carries the password hashes and is `C`, so it is writable and outside verity by construction — as `passwd`, `group` and `gshadow` must be for `systemd-sysusers` to write them at boot. Whether that coupling is acceptable, and whether the `nullok` default above is NeutrinOS's, are the open parts. | C-002, ADR-0004 |
| C-011 | Which package selections does a role need that the declared Fedora 44 closure cannot supply? | Open, narrowed 2026-08-18. Measured 2026-08-16 against the retained repository index: `uwsm` is absent, so the compositor's systemd user units are written into `/usr` instead; `polkit-gnome` is absent and only Qt/KDE agents exist; no `oo7` daemon exists, only `oo7-cli`, so the owner's Secret Service selection does not resolve. Each is a package-overlay, closure or substitution question, and none was re-decided by an agent. **`uwsm` resolved 2026-08-18**: pulled as a pinned COPR overlay (`pabrahamsson/hyprland`, fedora-44-x86_64, digest-verified) rather than a closure change; the hand-written units it replaces are removed, and `T4-SESSION-001` reverified passing through uwsm's own generated units. `capability.authorization-agent` substituted `xfce-polkit` for `polkit-kde` (also in-closure, no overlay needed) and `capability.secret-storage` substituted `gnome-keyring` for `oo7` (`oo7` commented, not deleted, pending Fedora 45/Rawhide). `polkit-gnome` and an `oo7` daemon remain unsupplied by the closure; C-011 stays open on those two. | C-001, W-003 |

## Wave 4: role designs

| ID | Question | State | Depends on |
| --- | --- | --- | --- |
| R-001 | What capabilities and tests define the workstation role? | Open | P-004, C-001, W-003 |
| R-002 | What capabilities and tests define the laptop role? | Open | P-004, C-001 |
| R-003 | What capabilities and tests define the router role? | Open | P-004, C-001 |
| R-004 | What capabilities and tests define server and storage roles? | Open | P-004, C-001, W-002 |
| R-005 | What capabilities and tests define a microVM guest? | Open | P-004, W-002 |

## Open question notes

Evidence for open questions that lives nowhere else. Anything a design, review,
research exercise or record already owns stays there and is cited, not repeated.
A note that grows past a short section is a sign its content has found a home and
should move.

### P-008: landing changes on `main`

Owner bypass was enabled 2026-08-11, after observation corrected the original
premise: a direct push is not rejected for a bypass-capable actor — it lands, the
remote records `Bypassed rule violations`, and the required check never runs.
Observed twice on real commits.

The ruleset stays `active` with all five rules (`deletion`, `non_fast_forward`,
`required_linear_history`, `required_signatures`, `required_status_checks`) and
two `always` bypass actors. So `main` is fully enforced against anyone who is not
the owner and never enforced against the owner, which also means
`required_signatures` and `required_linear_history` stop constraining owner
commits with nothing reporting when they would have fired.

**The 2026-08-15 remote measurement contradicts the premise this question was
punted on.** The 2026-08-12 punt was taken on a record stating that nothing had
been pushed and nothing was red; pushes had been landing since 2026-08-11 and the
required check had been red since. The constraint attached to the punt — answer
this before the `complete` job runs anywhere — was therefore unsatisfiable when it
was set, and the three-way choice is being made by default in favour of accepting
a red `complete`. Nothing is failing: the artifact and VM checks are `blocked` for
want of a composed artifact, and `mise` treats a blocked profile as a task
failure. This is expected and is not re-measured or reported.

### P-009: VM runner selection

QEMU alone provides a writable firmware varstore and a TCG fallback;
cloud-hypervisor and test.thing provide neither, and **test.thing's
GPL-3.0-or-later licence is incompatible with copying into this Apache-2.0
repository**. The techniques were adopted without the code — notify-vsock
readiness, SMBIOS credentials and `snapshot=on` are implemented from systemd's
documented interfaces and from mkosi (LGPL-2.1-or-later, already a declared build
input), with provenance in RES-0013.

Depends on `W-002`: if NeutrinOS ships a VMM, it stops being a harness and becomes
a declared input. KVM becoming available 2026-08-10 lifts only the "cannot run
here at all" objection; the varstore and TPM findings are independent of the
accelerator.

### P-010: record corpus maintenance

Measured 2026-08-11: 140 documents, ~258,000 words, 87 records, ~476 internal
links, all maintained by hand. One day's work produced four failures of a single
species — a rename leaving stale references across six files, a status surviving
in four places, the same status duplicated across three documents, and an
acceptance existing only as a sentence an agent typed. None was a reasoning
error; all were referential integrity or duplicated state.

**The acceptance case is the serious one.** `AGENTS.md` forbids agents from
accepting decisions, and that rule is enforced by agent good behaviour alone, with
no structural difference between a real approval and a fabricated one.

**A second species, 2026-08-15, in artifact lifecycle rather than documents**:
`check.py` creates a run directory per invocation and never removes it. 313 had
accumulated since 2026-08-10 — 285 `passing`, 28 `failing`, 718 MB — on a `/tmp`
mounted `usrquota`, where they contributed to a per-user quota that aborted a
PLN-0002-10 boot matrix mid-run with `EDQUOT` while `df` still showed 19 GB free.
The [validation contract](validation-contract.md) already rules on this:
successful local runs *may* remove bulky diagnostics, failed ones *must* preserve
them; the runner implements only the preserve half, for every outcome. The passing
directories were pruned by hand and the failing ones kept, which is exactly the
kind of fix this question exists over. The runner change is not taken, being
`tools/validation/` work under a deferred question.

### S-004: storage layout and confext delivery

Until the `/usr` format is answered, SYS-049 cannot be demonstrated without
selecting a mechanism by accident, which is why the owner deferred it to G2 rather
than growing it in PLN-0001.

**Where a separately delivered confext lives, and when it is merged**, moved here
from PLN-0002-03b by owner ruling 2026-08-15. PLN-0002 built a signed confext and
shipped it at `/usr/lib/confexts` as a **declared fixture** — inside the
authenticated artifact, so not separate delivery at all, and the fixture decided
nothing. PLN-0002-01 measured the constraint: on a tmpfs root the only confext
search path surviving to userspace is inside `/usr` itself, and a confext
delivered beside the UKI reaches only the initrd's `/etc`, which is discarded at
switch-root. This is what left PLN-0002-04's confext partition unplaced. Evidence:
[RES-0015](../research/comparisons/stateless-etc-configuration-delivery.md);
DES-0005 owns the design. Touches `C-009` and `C-002`; per-machine identity
sourcing passes to `L-003`.

### S-005: verity signer enforcement

Raised by PLN-0002-06, 2026-08-14, measured across both enrollment arms. The
kernel does refuse the signature — `device-mapper: reload ioctl failed: Required
key not available` — but `systemd-veritysetup` then retries without it, succeeds,
and reports the unit `Finished` (`veritysetup.c:437-443`, unconditional).
`systemd.image_policy=usr=signed` does not reach this: it is a structural
predicate satisfied by both arms, evaluated after `/usr` is mounted, and
non-fatal.

The outcome is not discarded, it is measured — `signed_activation` feeds
`pcrextend_verity_now()`, so a signed activation and an unsigned fallback extend
different PCR values. **Upstream's enforcement point is the unseal, not the
mount**, so a NeutrinOS that wants a bad signer to fail closed at boot must add
that itself or accept sealing as the mechanism. PLN-0002 lists TPM policy as out
of scope, so this is recorded rather than answered. See the [artifact parameter
declaration](artifact-parameter-declaration.md).

### L-002: tools closure retention

Raised by PLN-0002-02, 2026-08-11. The slice retains the declared repository
subset the image resolved against, so an image rebuild is offline. The tools tree
is declared by recipe rather than by digest — deliberately, because its export
timestamps make its own digest unstable — and its packages are not retained. That
stopped being theoretical the day `dl.fedoraproject.org` returned 403 for the
declared repository during Fedora 45 mass branching. The candidate answer is to
retain the tools closure the same way, which would also remove the standing
temptation to repoint a declared URL at a mirror under time pressure.

### C-002: configuration and credential delivery

Raised by PLN-0001-04: first-boot answers can be baked into the image's credstore
or supplied per-boot as SMBIOS Type 11 credentials. The composition amendment
chose the image without the question being asked; a physical host has no harness
to inject them, so the answer likely belongs to `L-003`. See
[RES-0013](../research/comparisons/vm-test-harness.md). Enlarged 2026-08-11 by
DES-0006 C-013: configuration is delivered only by signed confexts, so SYS-123's
full lifecycle applies. The unqualified-configuration test path conflicts with
`image_policy_confext_strict`.
