---
status: open
last_updated: 2026-08-15
governing_plan: PLN-0002
---

# Three early-boot findings, drafted for decision

PLN-0002-01 handed back three findings and took none of them. This draft states
each one, what it blocks, and what the options are, so that a ruling is a
choice between stated alternatives rather than a decision made in passing by
whichever task hits it first.

**All three are now ruled, and none of the rulings closes its finding
entirely.** Finding 1's *plan* half was ruled on 2026-08-11 and its **design
half remains open**, which moved to PLN-0002-03b and, when that task left the
plan on 2026-08-15 by owner ruling, to an open sub-question under `S-004` owned
by DES-0005. Findings 2 and 3 were ruled on
2026-08-12, both **narrower than the options put up**: finding 2 adopts A and
leaves B and D open rather than selecting a design, and finding 3 rules the
direction only and leaves the mechanism to `L-003`. Each ruling is recorded
inline below at the finding it settles.

Options carry arguments, not outcomes, and where a recommendation was declined
that is recorded rather than edited away. Sole acceptance authority is the
owner.

Evidence for all three is the [early-boot record](spike-early-boot-record.md).
Finding 1 was blocking. Its plan half being ruled unblocked PLN-0002-03a; its
design half still blocks the confext partition PLN-0002-04 stopped short of
placing, and that is now the only blocking item left in this document.

---

## Finding 1: a separately delivered confext has nowhere to live

> **Owner ruling, 2026-08-11: option D for this plan.** The confext lives at
> `/usr/lib/confexts` as a declared measurement fixture, and PLN-0002 measures
> formats and not delivery. **This settles nothing about the design.** The
> design question -- A, B, or E -- is not ruled and moves to PLN-0002-03b
> (accepted 2026-08-11) with [RES-0015](../research/comparisons/stateless-etc-configuration-delivery.md)
> as its evidence.
>
> The fixture must be declared in the task text of the task that builds it, not
> in a record written afterwards, because a delivery path that works repeatedly
> is exactly how a fixture becomes a decision. If any later task's argument
> depends on where the confext lives, that task stops and returns here.

### What was observed

`systemd-confext-sysroot.service` merges into `/sysroot/etc` before
switch-root, exactly as C-013 assumed, and its search paths are
`/sysroot/var/lib/confexts`, `/sysroot/usr/local/lib/confexts`, and
`/sysroot/usr/lib/confexts`. On a tmpfs root the first two are empty at that
moment and nothing can put anything in them. Only the third survives, and it is
**inside the authenticated `/usr`**.

`systemd-confext-initrd.service` is the only unit that searches
`/.extra/confext` and `/.extra/global_confext`, and it merges into the
*initrd's* `/etc`, which switch-root discards. So a confext delivered beside
the UKI never reaches the real `/etc` by that route.

### Why it matters

DES-0005 separates the release artifact from configuration: several disjoint
confexts, authored and signed independently, with per-confext failure policy.
The only surviving delivery path fuses them. A confext inside `/usr` ships with
the release, is covered by the release's root hash, and cannot be replaced
without replacing the release -- which is the opposite of what the amendment is
for.

### What the answer is not

Not a `/usr` change and not a confext-format change. The mechanism works; the
question is where the bytes live at the moment the merge runs.

### Options

**A. Give the machine a small persistent volume for `/var/lib/confexts`.**
Restores DES-0005's separation with no new mechanism: the search path already
exists and systemd already looks there. Costs the property that made the tmpfs
root attractive -- nothing persists -- and reopens the persistence question
DES-0006 records as open, plus `C-009` on the state filesystem. It also
contradicts nothing: C-008 already puts `/var` on a machine-state volume, so
this is arguably implementing C-008 rather than deviating from it.

**B. A separate confext partition on the same disk, mounted before the merge.**
Keeps configuration out of the release artifact and out of a general-purpose
writable volume, and is authenticated independently by its own signature. Needs
an ordering guarantee in early boot that does not exist yet and needs the
partition discovered before `systemd-confext-sysroot.service` runs. This is the
option PLN-0002-04 would have taken if it were taking one.

**C. Deliver the confext into the initrd and re-merge after switch-root.**
Uses only what exists, but means the confext is carried by the UKI's initrd,
which makes it part of the signed boot artifact -- the same fusion as putting
it in `/usr`, with more steps.

**D. Accept `/usr/lib/confexts` for this plan only**, as a measurement fixture,
and record that PLN-0002 measures formats and not delivery. Cheapest, and
honest so long as it is never read as the answer. It leaves DES-0005's
separation undemonstrated.

**E. Stage into `/run/confexts` and merge after switch-root.** The confext's
bytes live wherever is convenient and authenticated; a symlink in
`/run/confexts` points at them, and `systemd-confext.service` merges after
switch-root. Upstream explicitly endorses `/run/confexts` for symlinks. The
cost is timing: this merges after `local-fs.target`, so nothing before
`sysinit.target` can be configured by it. Added 2026-08-11 from
[RES-0015](../research/comparisons/stateless-etc-configuration-delivery.md).

### Argument

**Revised 2026-08-11 against [RES-0015](../research/comparisons/stateless-etc-configuration-delivery.md).**
The prior-art survey weakened the first half of what was originally drafted
here ("B for the design, D for this plan"), and the original is preserved below
so the change is visible rather than silent.

The survey's finding is that **option B has no prior art**. No surveyed
image-based system delivers configuration as a separately signed artifact into
a stateless `/etc`; every one of them gives `/etc` a persistent writable
backing instead. That includes ParticleOS, systemd's own reference
distribution, which has the confext mechanism available, has a persistent
TPM-encrypted root with `/var` as a subvolume, and **uses no confexts at all**.
Upstream names `/var/lib/confexts` as the primary install location. And on
medium-confidence evidence, confexts are validated against the same key as the
EFI binaries -- so a confext partition buys independent *delivery* and not
independent *signing*, which is half of what DES-0005 asks for.

So the revised argument is **A or E for the design, D for this plan**, with B
kept as the thing to build only if independent signing is confirmed achievable.
B was originally recommended partly because it looked like the clean way to
satisfy DES-0005; it is in fact the option nobody has built, for a reason that
is not obviously bad.

**Original argument, 2026-08-11, superseded:** "B for the design, D for this
plan. PLN-0002 exists to answer C-007, and none of its eight criteria is
affected by where the confext lives; taking a delivery decision to unblock a
format comparison is how a fixture becomes a decision. But B is the option that
satisfies DES-0005 without reopening persistence, and drafting it now is
cheaper than drafting it after four more tasks have assumed D."

The second half is unchanged and unaffected: D for this plan, because C-007 is
a format comparison and a delivery decision taken to unblock it is a fixture
becoming a decision.

The risk in D is specific and worth naming: PLN-0002-03a builds the first
confext tooling and the first path carve, PR-0030 C-006 already flags both as
becoming the reference by being first, and a fixture delivery path would be the
third such artefact in the same task.

---

## Finding 2: runtime unit enablement is unavailable

### What was observed

With a confext merged, `/etc` is a read-only overlay. First-boot presets then
fail wholesale -- roughly twenty `Failed to preset all unit` messages -- and
four units failed as a consequence, including `dbus.socket` never being
enabled. The refused-confext run is the same boot with one difference and had
zero preset failures and one unrelated failed unit, so the cause is attributed,
not inferred.

### Why it matters

`systemctl enable` at runtime writes to `/etc/systemd/system/*.wants`. On this
artifact that write cannot succeed. Anything that assumed a machine can enable
a unit after boot -- an operator action, a role change, a recovery step -- has
no mechanism.

### What has already changed

PLN-0002-02 moved the release's own enablement into
`/usr/lib/systemd/system/*.wants`, which is the vendor path systemd already
searches and which the release itself already uses. **The presets that failed
in the spike are enabled by construction now.** That closes the symptom for
release-owned units and closes nothing for the general question.

### Options

**A. Composition owns all enablement.** Every unit's enabled state is decided
when the artifact is built. Simple, verifiable, and consistent with an
immutable release. Means no per-machine enablement without a new release.

**B. Confexts own per-machine enablement**, shipping their own `.wants` links.
Fits DES-0005 -- enablement is configuration -- and gives per-machine variation
without a new release. Depends entirely on Finding 1: a confext that cannot be
delivered cannot enable anything.

**C. A writable drop-in path outside `/etc`**, for example
`/run/systemd/system` populated from an authenticated source at boot. Keeps
`/etc` read-only while allowing enablement, at the cost of a second mechanism
that has to be authored, ordered, and authenticated.

**D. systemd generators.** A generator runs at boot and on every
daemon-reload and writes unit symlinks into `/run/systemd/generator*`, which
needs no writable `/etc` at all. Added 2026-08-11 from
[RES-0015](../research/comparisons/stateless-etc-configuration-delivery.md):
this is what the NixOS community recommends for exactly this problem, where
`systemctl enable` fails with "Read-only file system" and the answer is
"declaratively, or with a generator". Unlike option C it is an upstream
mechanism with a defined contract rather than a path invented for the purpose,
and its input can be an authenticated file that the generator reads. It puts
logic in early boot, which is a cost the bounded-declarative-config default
should be weighed against.

### Argument

**Prior art contradicts A** ([RES-0015](../research/comparisons/stateless-etc-configuration-delivery.md),
2026-08-11). ParticleOS ships `preset-global.service` with
`ConditionFirstBoot=yes` and `ConditionPathIsReadWrite=/etc`, running
`systemctl preset-all --global` on first boot. It does not have composition own
enablement; it keeps `/etc` writable and presets at runtime. That is not an
argument that A is wrong for NeutrinOS -- NeutrinOS's `/etc` is read-only by
intent and ParticleOS's is not -- but A should be ruled knowing that the
closest comparable system chose the opposite, and that the cost of A is
per-machine enablement requiring a new release.

**A now, B as the design.** A is already true after PLN-0002-02 and needs no
decision. B is where DES-0005 points, and it is blocked behind Finding 1
rather than being an independent question. C should be rejected unless A and B
both prove insufficient: it adds a delivery path whose authentication story is
unwritten.

What must not happen is C arriving implicitly, as a task's convenience.

### Ruling

**Ruled 2026-08-12 by Jason Tarasovic: A now; B and D both stay open.** A is
adopted and needs no change, being already true after PLN-0002-02. The owner
declined the drafter's second half: **B is not selected as the design**, and
neither is D. The two remain live candidates to be decided later, which is a
narrower ruling than either option offered and is deliberate -- B is blocked
behind finding 1 and D arrived from RES-0015 only the day before, so choosing
between them now would rank a blocked option against a one-day-old one.

C is not ruled on. The drafter's argument against it stands as an argument:
it adds a delivery path whose authentication story is unwritten. The standing
guard is unchanged and applies to all three -- B, C, or D arriving implicitly
as a task's convenience is a stop condition, not a decision.

---

## Finding 3: `/etc/machine-id` has no home

### What was observed

`System cannot boot: Missing /etc/machine-id and /etc/ is read-only`. The
machine booted anyway, on a transient identity that changes every boot.

### Why it matters

The machine ID is the identity a great deal is keyed to: journal identity,
`systemd-networkd` DUIDs, TPM policy binding, and any fleet record that names a
machine. A transient one means a machine that cannot be recognised across
reboots. This is evidence for C-013's `L-003` deferral, not a resolution of it.

### Options

**A. Provisioned at install, on a persistent volume**, and bind-mounted or
copied into `/etc` at boot. The conventional answer, and the one `L-003`
already expects to make; it needs the same persistence Finding 1's option A
needs.

**B. Derived from hardware or firmware** -- an SMBIOS UUID or a TPM-sealed
value. No persistent volume, and stable across reinstalls. Ties machine
identity to hardware, which is wrong for a VM fleet and awkward for board
replacement, and derivation from an SMBIOS UUID is not a secret.

**C. Delivered as a credential**, which is how PLN-0001 and PLN-0002-01 already
supply `system.hostname`. Consistent with C-002's accepted policy that systemd
credentials are the default service interface. On a physical host there is no
harness to inject one, which is exactly the gap `L-003` records.

**D. Explicitly transient**, with everything that needs a stable identity
keyed to something else. Coherent, and a large claim: it forbids anything that
assumes machine continuity, and would need SYS-level review rather than a task.

### Argument

**A, and it belongs to `L-003`, not to PLN-0002.** Every option except D needs
either persistence or an installer, and both are `L-003`'s subject. PLN-0002
should record that its fixture boots on a transient identity and measure
nothing that depends on machine continuity. The value of ruling now is
negative: it stops a later task from choosing C because a credential was
convenient in a VM.

### Ruling

**Ruled 2026-08-12 by Jason Tarasovic: the direction only.** Machine identity
is **persistent and provisioned at install**. The mechanism is `L-003`'s and is
explicitly not decided here -- the ruling does not commit to a persistent
volume, so A's concrete shape stays open alongside anything else `L-003` finds.
B is excluded by the direction, since hardware or firmware derivation is not
installer provisioning; D is excluded, since it is the negation of persistence
and would need SYS-level review to adopt. C, credential delivery, is not
excluded as a *transport* -- what is excluded is C standing in for provisioning
because a VM harness made it easy, which is the specific accident this ruling
exists to prevent.

PLN-0002 is unchanged by it: the fixture boots on a transient identity, records
that it does, and measures nothing depending on machine continuity.

---

## What a ruling would unblock

| Finding | Blocks | Ruling needed before |
| --- | --- | --- |
| 1, confext delivery | ~~PLN-0002-03~~ and the confext partition PLN-0002-04 left out | **Plan half ruled D on 2026-08-11**, which unblocks the build-and-carve work. The design half is unruled and blocks only the confext partition and finding 2's option B |
| 2, runtime enablement | Nothing in PLN-0002 after PLN-0002-02 | **Ruled 2026-08-12: A now, B and D both left open.** PLN-0002-11 still registers what is asserted about `/etc`; the design half carries no deadline |
| 3, machine identity | Nothing in PLN-0002 | **Ruled 2026-08-12: direction only** -- persistent, provisioned at install. Mechanism is `L-003`'s and is not decided |
