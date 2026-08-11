---
id: RES-0015
status: in-review
last_updated: 2026-08-11
evidence_cutoff: 2026-08-11
decision_gates: [S-004, C-009, L-003]
---

# Configuration delivery on a stateless `/etc`

## Question

Where does independently-signed configuration live on an image-based system
whose release artifact is read-only, and when is it merged into `/etc`?

Scoped deliberately. This is not a survey of configuration management. It is
the evidence for one drafted decision: PLN-0002-01 finding 1, recorded in the
[early-boot findings](../../project/early-boot-findings-for-decision.md), which
observed that on a tmpfs root the only surviving confext search path is inside
the authenticated `/usr`.

The crux question, stated before the survey ran so that the answer is not
shaped by what was found: **does anyone mount a discovered partition into a
confext search path inside the initrd, before the merge runs -- and if not,
why not?**

Extended on 2026-08-11 at owner prompting with a second question: **who runs a
tmpfs or otherwise stateless `/etc` in the field, and does anyone run one
together with confexts?** The first half has answers and useful operating
evidence; the second half does not.

## Headline

**No.** And the reason is uniform across every system examined: none of them
has a stateless `/etc`. Every shipping image-based system surveyed gives `/etc`
a persistent writable backing, and then delivers configuration by writing into
it. The separately-delivered, independently-signed configuration artifact that
DES-0005's amendment describes is, on the evidence available on 2026-08-11, not
a shipping pattern anywhere -- including in systemd's own reference
distribution, which has the mechanism available and does not use it.

This does not make DES-0005 wrong. It does mean option B of finding 1 is
**novel work, not adoption of prior art**, and the argument previously drafted
for it was written without knowing that.

A stateless `/etc` on its own *is* operated in the field -- NixOS impermanence,
and systemd's own `systemd.volatile=yes` -- but in every case it is populated
from a generated source rather than from a delivered artifact. **The pairing
NeutrinOS is building, a stateless `/etc` fed by confexts, is unattested.**

## Prior art

### ParticleOS (closest by construction)

systemd's own reference distribution, built with mkosi, same authors as the
confext mechanism. Read from the repository on 2026-08-11.

Its partition set is A/B `/usr` with verity and verity-signature partitions
(`10`/`11`/`12` and `20`/`21`/`22`), swap, `40-root.conf`, and `50-home.conf`.
The root partition is:

```
[Partition]
Type=root
Format=btrfs
SizeMinBytes=1G
Subvolumes=/var
Encrypt=tpm2
FactoryReset=yes
```

Four things follow, and each bears on a drafted option:

1. **The root is persistent, encrypted, and TPM-bound, with `/var` as a
   subvolume.** Not tmpfs. So `/var/lib/confexts` -- the location the confext
   manual calls "the primary place for installing configuration extensions" --
   is reachable by construction. This is the shape of finding 1's **option A**.
2. **ParticleOS uses no confexts at all.** A repository-wide code search for
   `confext` returns zero hits. The system with the best access to the
   mechanism does not deliver configuration with it.
3. **`/etc` is writable, and enablement happens at runtime.**
   `preset-global.service` carries `ConditionFirstBoot=yes` and
   `ConditionPathIsReadWrite=/etc`, and runs `systemctl preset-all --global`.
   This is directly contrary to finding 2's option A: ParticleOS does not have
   composition own all enablement, it keeps `/etc` writable and presets on
   first boot.
4. **`FactoryReset=yes` on the root** is how it gets statelessness when it
   wants it -- discard and rebuild the persistent volume, rather than never
   having one.

Its command line is `root=dissect mount.usr=dissect rw`, with an explicit
`systemd.image_policy=` requiring `usr=signed` and permitting
`root=encrypted+absent`, and a `systemd.image_filter=` selecting partitions by
label. Two mechanisms NeutrinOS has not considered and probably should:
`image_policy` states the integrity requirement per partition type *on the
command line, inside the signed UKI*, which is a stronger and more legible
assertion than "we mounted it and it worked".

### openSUSE MicroOS

Read-only btrfs root with snapshots; `/etc` is an **overlayfs**, whose upper
and work directories live at `/var/lib/overlay/<snapshot>/etc`, one overlay per
snapshot. First-boot configuration arrives out of band via Ignition or
Combustion, which run early and write into the persistent `/etc` overlay.

Same conclusion by a different mechanism: configuration is persisted state, not
a signed artifact. The per-snapshot overlay is a genuinely interesting property
NeutrinOS lacks a story for -- configuration is versioned *with* the release it
was applied to, so a rollback of `/usr` rolls back `/etc` with it.

### NixOS impermanence, and a read-only `/etc`

Added 2026-08-11 at owner prompting. This is the one place where a tmpfs `/etc`
is actually operated in the field, and it is worth separating two things NixOS
does that are usually discussed together.

**Impermanence / "erase your darlings"** (Graham Christensen, and the
`nix-community/impermanence` module) mounts `/` -- and therefore `/etc` -- as
tmpfs, keeping only `/boot`, `/nix`, and an explicit `/persist` on disk.
Everything not on an allowlist is gone at reboot. This works on NixOS for a
reason NeutrinOS does not share: NixOS's `/etc` is *already* generated, a tree
of symlinks into `/nix/store` produced by the activation script, so a tmpfs
`/etc` costs nothing to repopulate. The tmpfs is a consequence of `/etc` being
derived, not a mechanism for making it derived.

The community's own retrospectives are worth reading as operating evidence
rather than as design: the reported costs are memory pressure, loss on crash
before state is moved to persistent storage, and a long tail of discovering
what silently needed to persist.

**`system.etc.overlay.enable` / `system.etc.overlay.mutable`** is the newer and
closer analogue. `/etc` is an overlayfs over an immutable store-generated
lowerdir; with `mutable = true` the upper and work directories are
`/.rw-etc/upper` and `/.rw-etc/work`, and with `mutable = false` **only the
read-only lowerdir is mounted**. That is a genuinely read-only `/etc` in a
shipping distribution, and NixOS marks it experimental.

What breaks there is the most directly comparable evidence NeutrinOS has for
its own finding 2, because it is the same failure in a different system:
`systemd-sysusers` must match `/etc`'s mutability and the module asserts it;
`users.mutableUsers` conflicts; the impermanence module itself does not work
against an immutable overlay; and `systemctl enable` fails outright --
"Failed to enable unit: ... Read-only file system".

The answer the NixOS community gives to that last one is the useful part:

> "You're not meant to use `systemctl` to enable units on NixOS, it has to be
> done declaratively."

and, for cases that genuinely need runtime decisions, **systemd generators** --
which write unit symlinks into `/run/systemd/generator*` at boot and on
daemon-reload, requiring no writable `/etc` at all. This is a mechanism finding
2's drafted options did not list, and it is upstream-sanctioned rather than
invented.

**`systemd.volatile=`** should be recorded alongside it as systemd's own
expression of the same idea. `systemd.volatile=yes` has
`systemd-volatile-root.service` replace the root with a tmpfs and mount only
`/usr` into it read-only -- "fully stateless mode, with all configuration and
state reset at boot", `/etc` and `/var` served from an initially unpopulated
tmpfs. `state` makes only `/var` volatile; `overlay` makes the root an
overlayfs over a writable tmpfs.

That is, almost exactly, what PLN-0002-04's `root=tmpfs` produces. NeutrinOS
arrived at the arrangement through mkosi's spelling; systemd has a first-class
spelling for it, with a documented per-mode contract and the useful property
that none of the modes physically removes anything, so a machine can be booted
volatile temporarily without data loss. Whether NeutrinOS should express the
fixture as `systemd.volatile=` instead is a small question and not this
survey's to answer, but the two spellings should not be assumed identical
without checking.

### ostree / bootc

A three-way merge of `/etc` at deployment: base, current, and new. `/etc` is
persistent and writable; local modifications are preserved across updates by
diffing against the shipped defaults. Configuration is not signed and not
separable from the machine.

Recorded here because bootc is the standing deployment-substrate challenger
(RES-0003). Its answer to this question is "persistent `/etc`, merged at
deployment time", which is neither A nor B.

### Tmpfs `/etc` **with** confext: no instance found

Searched explicitly on 2026-08-11, because the pairing is the actual NeutrinOS
arrangement and neither half alone is decisive.

**No deployment was found that runs a tmpfs or otherwise stateless `/etc` and
delivers configuration into it with confexts.** The two populations are
disjoint on the evidence available:

- The systems with a stateless `/etc` (NixOS impermanence,
  `systemd.volatile=yes`) populate it from a *generated* source -- the Nix
  store, or nothing at all -- not from a signed configuration artifact.
- The systems with the confext mechanism available and a stated interest in it
  (ParticleOS above) keep `/etc` persistent and do not use confexts.

This is negative evidence, and it is weaker than the positive kind: absence in
a bounded survey is not proof of absence. It is recorded because a search
engine asked about the combination will readily *describe* it -- the mechanisms
compose on paper, and summaries say so -- and a description of how two
mechanisms could combine is not a report that anyone has combined them. That
distinction is the whole value of this subsection.

The practical consequence for finding 1 is that NeutrinOS's arrangement is not
merely un-adopted in its delivery half; the **pairing** is unattested. That
raises the value of PLN-0002-01's measured evidence, which is currently the
only direct observation of how these two behave together, and it means the
early-boot record should be treated as the primary source rather than as
confirmation of an established pattern.

## Upstream statements bearing on the options

From the sysext/confext manual pages, read 2026-08-11:

- Search paths are `/run/confexts/`, `/var/lib/confexts/`,
  `/usr/lib/confexts/`, `/usr/local/lib/confexts/`, and **"the primary place
  for installing configuration extensions is `/var/lib/confexts/`"**. Upstream
  names the persistent location as the intended one.
- **"The first listed directory (`/run/confexts/`) is not suitable for carrying
  large binary images, however is still useful for carrying symlinks to
  them."** This is an explicit endorsement of the staging pattern raised
  against finding 1: mount the confext's real home somewhere, symlink it into
  `/run/confexts`. It applies to `systemd-confext.service` after switch-root,
  **not** to `systemd-confext-sysroot.service`, whose search paths were
  measured in PLN-0002-01 and do not include `/run`.
- Confext images support signed dm-verity, "both with split artifacts (`.raw`,
  `.verity`, `.roothash`, `.roothash.p7s`) and in GPT volumes", and per the
  upstream design discussion are expected to be **"signed with the same
  key/cert as the ones used to sign the EFI files."**

That last point is the survey's second substantive finding and needs stating
plainly: if confexts are validated against the same key as the UKI, then a
confext is *independently deliverable* but not *independently signed*. DES-0005
asks for both. Confidence is **medium** -- it is sourced from the upstream
design issue rather than from the manual page's normative text, and it has not
been measured. It should be verified before it is relied on, and PLN-0002-10's
wrong-but-valid-key injection is the natural place.

From systemd 261's NEWS, confirming what PLN-0002-01 measured:

- "New initrd services `systemd-sysext-sysroot.service` and
  `systemd-confext-sysroot.service` are provided. These services are used to
  merge system and configuration extensions for the main system from the
  initrd."
- Both are controlled by `systemd.sysext=` / `systemd.confext=` on the kernel
  command line, and a kill switch disabling merging entirely is honoured.

The command-line control matters: whether a confext is merged is an assertion
carried by the signed UKI, not by the machine.

## What this does to the drafted options

Restated against the evidence, not re-decided. Acceptance is the owner's.

- **Option A** (persistent `/var/lib/confexts`) is what upstream names as
  primary, what ParticleOS's layout would support, and what every surveyed
  system does in substance. Its cost is unchanged: it reopens persistence,
  `C-009`, and `L-003`.
- **Option B** (dedicated confext partition mounted in the initrd) has **no
  prior art**. The ordering guarantee it needs is still unverified, and the
  survey found nobody who has needed it. It is also weakened by the
  same-key finding: a separate partition buys independent *delivery* and, on
  current evidence, not independent *signing*.
- **The `/run/confexts` symlink variant** is upstream-endorsed but merges after
  switch-root, so it cannot serve anything before `sysinit.target`. Whether
  that is sufficient depends on what the carve in PLN-0002-03a actually owns --
  which is a question that task can answer.
- **Option D** (fixture in `/usr/lib/confexts`) is unaffected. It remains
  correct for a plan that measures formats.

The argument previously drafted -- "B for the design, D for this plan" --
should be read as weakened on its first half. B was recommended partly because
it appeared to be the option that satisfied DES-0005 cleanly; the survey finds
it is the option nobody has built, for a reason that is not obviously bad. A
revised argument would be **A or the `/run` variant for the design, D for this
plan**, with B kept as the thing to build only if independent signing is
confirmed achievable.

## Incidental finding against PLN-0002-02

Not this survey's question, recorded because it was found and should not be
lost.

ParticleOS's `/usr/lib/tmpfiles.d/etc.conf` uses **`L` lines (symlinks) into
`/usr/share/factory/etc`, not `C` lines (copies)**, and says why in a comment:

> "This overrides the same file from systemd since we want to symlink
> everything into `/etc` instead of copying so updates to `/usr` propagate
> properly."

PLN-0002-02's generated factory fragment uses `C` lines. On this evidence a
copied `/etc` does not track `/usr` across an update, which is a property an
A/B `/usr` artifact needs and which PLN-0002 has not measured. Its
`mkosi.finalize` also resolves the factory-collision problem differently, by
copying with `--update=none` (never overwrite) rather than by failing the
build.

Neither is a defect proven in NeutrinOS's artifact. Both are candidate defects
in a mechanism this plan has already built, and belong in front of the owner
before PLN-0002-06 builds four artifacts on top of it.

## Sources

All read 2026-08-11.

- [systemd/particleos](https://github.com/systemd/particleos) -- `mkosi.conf`,
  `mkosi.finalize`, `mkosi.extra/usr/lib/repart.d/*`,
  `mkosi.extra/usr/lib/tmpfiles.d/etc.conf`,
  `mkosi.extra/usr/lib/systemd/system/preset-global.service`
- [systemd NEWS, CHANGES WITH 261](https://raw.githubusercontent.com/systemd/systemd/main/NEWS)
- [systemd-confext(8)](https://manpages.debian.org/testing/systemd/systemd-confext.8.en.html)
- [systemd-sysext(8)](https://man7.org/linux/man-pages/man8/systemd-sysext.8.html)
- [systemd issue #24864, signed verity-protected confext](https://github.com/systemd/systemd/issues/24864)
- [Portal:MicroOS/Design](https://en.opensuse.org/Portal:MicroOS/Design),
  [Portal:MicroOS/Combustion](https://en.opensuse.org/Portal:MicroOS/Combustion)
- [systemd-volatile-root(8)](https://man.archlinux.org/man/systemd-volatile-root.8.en),
  [systemd-fstab-generator(8)](https://www.man7.org/linux/man-pages/man8/systemd-fstab-generator.8.html)
  for `systemd.volatile=`
- [nix-community/impermanence](https://github.com/nix-community/impermanence)
  and [NixOS wiki: Impermanence](https://wiki.nixos.org/wiki/Impermanence)
- [`system.etc.overlay.mutable`](https://mynixos.com/nixpkgs/option/system.etc.overlay.mutable),
  [nixpkgs `nixos/modules/system/etc/etc.nix`](https://github.com/NixOS/nixpkgs/blob/master/nixos/modules/system/etc/etc.nix),
  and the breakage reports
  [nixpkgs#311665](https://github.com/NixOS/nixpkgs/issues/311665),
  [impermanence#210](https://github.com/nix-community/impermanence/issues/210)
- [NixOS Discourse: "`/etc/systemd/system/` is read-only... how do I enable template systemd units?"](https://discourse.nixos.org/t/so-etc-systemd-system-is-read-only-how-do-i-enable-template-systemd-units/78813)
