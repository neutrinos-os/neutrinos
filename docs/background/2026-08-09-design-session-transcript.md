# Linux Distribution Design Session Transcript

**Date:** August 9, 2026  
**Topic:** Building a modern systemd-native Linux distribution

> Note: This transcript covers the current Linux-distribution design session. Web citations from the chat have been converted to explicit links where possible so the Markdown remains self-contained.

---

## User

I’m going to be developing my own Linux distribution. I’ve been using Linux for 20 years so I have a good sense of the landscape but I’m looking for high quality YouTube videos (no AI slop) specifically on unique features, custom distro creation, etc. there’s a relatively new group, maybe UAPI?, that has some interesting ideas

## Assistant

Yes — **UAPI Group** is almost certainly what you were thinking of. For a new distro, I’d spend time there before I spent much time on traditional “build a distro from scratch” material. The UAPI specs are essentially an attempt to standardize a more modern Linux OS composition model: Boot Loader Specification, Discoverable Partitions, Discoverable Disk Images, extension images, UKIs, TPM PCR conventions, filesystem hierarchy, etc.

UAPI specifications:  
https://uapi-group.org/specifications/specs/

For YouTube, I’d start with these. I’m deliberately favoring talks by the people building the machinery or conference presentations over influencer/tutorial content.

| Priority | Video | Why it's worth watching |
|---|---|---|
| ⭐⭐⭐ | **mkosi: Building Bespoke Operating System Images** | Probably the closest match to what you're doing. `mkosi` builds complete OS images from distro packages and is heavily used in systemd development. https://www.youtube.com/watch?v=6EelcbjbUa8 |
| ⭐⭐⭐ | **Unified Kernel Images (UKIs) — Lennart Poettering** | UKI as the atomic kernel/initrd/cmdline/metadata/signature unit. https://www.youtube.com/watch?v=7UhwK3g99_0 |
| ⭐⭐⭐ | **Immutable and Stateless Systems with systemd — Lennart Poettering** | Older, but conceptually excellent. https://www.youtube.com/watch?v=pL0AMLiwPj8 |
| ⭐⭐⭐ | **System and Configuration Extensions for Image-based Linux** | `systemd-sysext` + `systemd-confext`. https://www.youtube.com/watch?v=XTy3scX6rF4 |
| ⭐⭐⭐ | **systemd-confext Two Years On: Versioned Overlays for /etc** | Useful for thinking about vendor defaults versus admin-owned `/etc`. https://www.youtube.com/watch?v=ZQanQTkL8bw |
| ⭐⭐ | **One Boot Config to Rule Them All: Bringing UAPI Boot Loader Specification…** | Directly about UAPI boot conventions. https://www.youtube.com/watch?v=x5vKCc8fVJI |
| ⭐⭐ | **The road to a trusted and measured boot chain in Bootable Containers** | Fedora bootable-container trust chain. https://www.youtube.com/watch?v=xQT5IqL0kzc |
| ⭐⭐ | **Bootc: Hands on Demo** | Concrete bootable-container model. https://www.youtube.com/watch?v=fccox6sGCWA |
| ⭐⭐ | **systemd-sysext in Prod: What We Learned Extending /usr** | Production experience. https://www.youtube.com/watch?v=fof2hXjgZ1g |
| ⭐⭐ | **mkosi-initrd: initrds built from system packages** | Modern initrd model. https://www.youtube.com/watch?v=gpGBgZA-E_c |

### The UAPI/systemd rabbit hole

The architecture particularly worth evaluating:

```text
UEFI → systemd-boot → signed UKI → Discoverable Disk Image
→ dm-verity protected /usr → writable state separately
→ sysext/confext for composition → sysupdate for atomic updates
```

That is quite different from the classic:

```text
GRUB → kernel + arbitrary initramfs → root filesystem
→ dpkg/rpm/pacman mutates root forever
```

UAPI's Discoverable Partitions Specification:  
https://uapi-group.org/specifications/specs/discoverable_partitions_specification/

Discoverable Disk Images:  
https://uapi-group.org/specifications/specs/discoverable_disk_image/

Lennart Poettering, **Fitting Everything Together**:  
https://0pointer.net/blog/fitting-everything-together.html

Outside the systemd/UAPI worldview, I’d deliberately study:

- NixOS / Nix: https://www.youtube.com/watch?v=9l-U2NwbKOc
- Fedora CoreOS / Atomic / bootc: https://www.youtube.com/watch?v=xQT5IqL0kzc
- Flatcar: https://www.youtube.com/watch?v=reR0UCJ7Ezo
- Buildroot vs Yocto: https://www.youtube.com/watch?v=wCVYQWFIvBs

All Systems Go! 2024 playlist:  
https://www.youtube.com/playlist?list=PLWYdJViL9EipIImmvuoGFAeS-lKeHH2DD

---

## User

Yeah. I currently run Arch. TPM PCRs (not really doing much but being calculated), UKI, initially (2020?) with systemd-homed but moved away from it, i3, {systemd-networkd,boot,resolved,oomd}. Super minimal. Used CoreOS professionally for ~5 years. I’ve tried a couple of times to start from coreos but the fork of a fork of gentoo was too painful. Have the roughest familiarity with mkosi (check the PRs and issues for user:JTarasovic).  I’m building my workstation but I think I’d like a common setup for router, workstation, laptop, other servers, etc. the router currently runs nixos but there’s something not quite right about it. I love having my network config in “code” and version control though. Want to do more microvm stuff and have been using containers for well over 10 years. I’d like to be able to test my config/setup so I can confidently make changes and roll back as needed. I also like new safer,faster alternatives to some of the crufty coreutils

## Assistant

Given that background, the interesting project is **not “make an Arch derivative.”** It’s closer to building a small image-based OS framework where Arch happens to be one possible source of packages.

The direction I’d investigate:

```text
Git repo
→ machine/profile definition
→ mkosi build
→ signed UKI + immutable-ish root image
→ boot in VM
→ integration tests
→ publish image/update
→ transactional deployment to physical machines
```

`systemd-repart` is central to this. Systemd image-building documentation:  
https://systemd.io/BUILDING_IMAGES/

A useful repo shape:

```text
os/
├── mkosi.conf
├── mkosi.images/
│   ├── base/
│   ├── workstation/
│   ├── router/
│   ├── server/
│   └── microvm/
├── profiles/
├── systemd/
├── repart.d/
├── sysupdate.d/
├── tests/
└── packages/
```

The declarative language can mostly be the native configuration of the components themselves instead of Nix expressions.

### mkosi as distro build system

Systemd development workflow with mkosi:  
https://systemd.io/HACKING/

For a router, boot a VM with representative WAN/LAN topology and test DHCP, DNS, nftables, routing, WireGuard, upgrade, rollback, etc.

### `systemd-sysupdate`

GNOME OS + systemd-sysupdate:  
https://www.youtube.com/watch?v=EaEsb1WYgoQ

The important separation is:

```text
BUILD SYSTEM            UPDATE SYSTEM

pacman/dnf/etc.
       ↓
    mkosi image
       ↓
systemd-sysupdate
```

### DDIs + `systemd-repart`

Discoverable Disk Image spec:  
https://uapi-group.org/specifications/specs/discoverable_disk_image/

Discoverable Partitions spec:  
https://uapi-group.org/specifications/specs/discoverable_partitions_specification/

A key design constraint:

> Make the artifact portable, rather than making the installation procedure portable.

### `/usr` vs `/etc` vs `/var`

I’d seriously consider:

```text
/usr     OS — generated, versioned, replaceable
/etc     machine configuration
/var     persistent machine state
/home    user state
```

Potentially with a read-only base image and `sysext`/`confext`.

Extension image spec:  
https://uapi-group.org/specifications/specs/extension_image/

### MicroVMs

Investigate `systemd-vmspawn` first. Systemd’s VM/container integration docs:  
https://systemd.io/WRITING_VM_AND_CONTAINER_MANAGERS/

The powerful goal is that:

```text
mkosi build
mkosi vm
```

boots the literal distro artifact, not a simulation.

### Rollback

Prefer image/boot rollback over filesystem snapshots as the primary OS rollback mechanism.

Boot Loader Specification:  
https://uapi-group.org/specifications/specs/boot_loader_specification/

### TPM

Linux TPM PCR registry:  
https://uapi-group.org/specifications/specs/linux_tpm_pcr_registry/

A useful target:

```text
Secure Boot validates UKI
→ UKI/root image identity measured
→ TPM releases disk key
→ only OS releases signed by your distro key satisfy policy
```

### Don’t fork a distro

Initially:

```text
Arch packages
    ↓
   mkosi
    ↓
your immutable OS image
```

Your distro is then image layout, package selection, kernel config, UKI construction, system defaults, profiles, updates, tests, and signing policy—not a divergent copy of Arch packaging.

---

## User

While we’re chatting, what’s about individual user program installs? I use mise for quite a bit currently but if I had a base on all machines, some of that would naturally fall there (ripgrep, jq, etc).

## Assistant

I’d separate **“belongs to the OS”** from **“belongs to me”** pretty aggressively.

| Layer | Examples | Mechanism |
|---|---|---|
| Base OS | `rg`, `jq`, `fd`, `bat`, `git`, `tmux`, `nft`, `ip`, `strace` | mkosi/package set → `/usr` |
| User baseline | `fzf`, `delta`, `yq`, `gh`, assorted CLI tools | mise global config |
| Project environment | Node, Python, Terraform, Rust toolchain | mise project config |

Mise docs:  
https://mise.jdx.dev/dev-tools/

A useful model:

```text
/usr/bin              OS
/usr/local/bin        site/admin
~/.local/bin          user
~/.local/share/mise   user-managed versions
```

I would **not** use sysext for random personal software.

Systemd sysext docs:  
https://www.freedesktop.org/software/systemd/man/systemd-sysext.html

For user environment reconstruction, dotfiles + mise is a good middle ground between plain dotfiles and Home Manager.

For GUI apps, per-user Flatpak is a reasonable boundary:  
https://docs.flatpak.org/en/latest/using-flatpak.html

Linuxbrew could fill gaps but adds another large packaging universe:  
https://docs.brew.sh/Manpage  
https://docs.brew.sh/Homebrew-on-Linux

A useful ownership model:

```text
system       Git commit → image
profile      Git commit → image/sysext
user         dotfiles → mise
project      repo → mise
GUI app      user → Flatpak
container    workload → OCI image
microVM      workload → OS/DDI image
```

---

## User

What are the flat pack alternatives and are we just re-inventing fedora atomic sway?

## Assistant

There’s a real risk of reinventing **Fedora Sway Atomic**.

Fedora Atomic Desktops:  
https://docs.fedoraproject.org/en-US/atomic-desktops/

rpm-ostree administrator handbook:  
https://coreos.github.io/rpm-ostree/administrator-handbook/

If the design is simply:

> immutable host + Sway + Flatpak + containers + rollback

then Fedora Sway Atomic is already that.

Where your design becomes meaningfully different is if the primitive is **one testable machine-image system for router/server/laptop/workstation/microVM**, rather than a desktop-first Atomic Fedora edition.

### Flatpak alternatives

| Mechanism | Best use | Take |
|---|---|---|
| Flatpak | Sandboxed GUI apps | probably default |
| AppImage | portable self-contained apps | useful escape hatch |
| Snap | cross-distro app/service packages | capable, but probably not worth adopting here |
| Nix profiles | per-user packages | interesting |
| mise | CLI tools/runtimes | keep |
| Toolbx/Distrobox | mutable dev environments | different problem |
| OCI | services/dev workloads | yes |
| sysext | host-integrated functionality | machine profiles, not random apps |

AppImage concepts:  
https://docs.appimage.org/introduction/concepts.html

Snap:  
https://snapcraft.io/

Nix manual:  
https://nixos.org/manual/nix/stable

Fedora Toolbx:  
https://docs.fedoraproject.org/en-US/atomic-desktops/toolbox/

Litmus test:

> Can you name an invariant your distro gives you that Fedora Atomic does not?

Examples that could justify it:

- Every deployed OS/config pair has previously booted and passed role-specific integration tests unchanged.
- One artifact/config model spans bare metal, workstation, router, server, and microVM.
- Updating means replacing a cryptographically identified disk image, not constructing an OSTree deployment on the target.

---

## User

I’m all in on the systemd ecosystem and I’d like to migrate to Wayland (it wasn’t ready for remote work in 2020 but it probably is now). How do I identify the remaining components I’d need and make informed choices about them (greeter, notification manager, etc)

## Assistant

Treat the desktop as a **capability matrix**, not a pile of packages.

A reasonable initial stack:

| Capability | Candidate |
|---|---|
| compositor | Sway |
| session lifecycle | uwsm + systemd --user |
| login | greetd |
| graphical greeter | ReGreet or tuigreet |
| bar | Waybar or swaybar |
| launcher | fuzzel |
| notifications | mako |
| lock | swaylock |
| idle | swayidle |
| audio/video | PipeWire + WirePlumber |
| screen sharing | xdg-desktop-portal + xdg-desktop-portal-wlr |
| generic portal | xdg-desktop-portal-gtk |
| clipboard | wl-clipboard |
| screenshots | grim + slurp |
| polkit | one lightweight agent |
| secrets | one Secret Service provider |
| X compatibility | Xwayland |
| remote desktop | wayvnc if needed |

Sway:  
https://github.com/swaywm/sway

### uwsm

Universal Wayland Session Manager:  
https://github.com/Vladimir-csp/uwsm/blob/master/README.md

Systemd desktop integration:  
https://systemd.io/DESKTOP_ENVIRONMENTS/

Portal integration docs:  
https://flatpak.github.io/xdg-desktop-portal/docs/system-integration.html

A desirable process tree:

```text
logind
└─ user@1000.service
   └─ graphical-session.target
      ├─ sway
      ├─ mako
      ├─ waybar
      ├─ portals
      ├─ polkit-agent
      └─ ...
```

### greetd

greetd manual:  
https://man.archlinux.org/man/greetd.1.en

ReGreet:  
https://github.com/rharish101/regreet

### notifications

mako:  
https://github.com/emersion/mako

### portals

XDG Desktop Portal:  
https://flatpak.github.io/xdg-desktop-portal/

xdg-desktop-portal-wlr:  
https://github.com/emersion/xdg-desktop-portal-wlr

PipeWire design:  
https://docs.pipewire.org/page_design.html

xdg-desktop-portal-wlr releases:  
https://github.com/emersion/xdg-desktop-portal-wlr/releases

RemoteDesktop limitation / issue:  
https://github.com/emersion/xdg-desktop-portal-wlr/issues/2

wayvnc:  
https://github.com/any1/wayvnc

A first prototype could be:

```text
Sway
uwsm
greetd
tuigreet
PipeWire
WirePlumber
xdg-desktop-portal
xdg-desktop-portal-wlr
xdg-desktop-portal-gtk
mako
fuzzel
swaylock
swayidle
wl-clipboard
grim
slurp
Xwayland
<polkit agent>
<Secret Service provider>
Firefox
foot
```

---

## User

uwsm sounds awesome. I definitely spent too much time trying to get X to run as a user. How does that work with systemd-oomd? Already use greetd so that makes sense. Need help on polkit agent. Use xfce’s now. But it’s actually a broader issue. Do I just end up using a bunch of gnome tools? I don’t hate it but getting a consistent look and feel is tough without a full, fat DE.

## Assistant

`uwsm` and `systemd-oomd` are a natural pairing because uwsm gives the graphical session the cgroup structure that oomd can reason about.

Systemd desktop environment guidance:  
https://systemd.io/DESKTOP_ENVIRONMENTS/

systemd-oomd manual:  
https://www.freedesktop.org/software/systemd/man/systemd-oomd.service.html

Conceptually:

```text
user@1000.service
├── session.slice
│   └── session-graphical.slice
│       ├── sway
│       ├── portals
│       ├── polkit-agent
│       └── notifications
├── app.slice
│   └── app-graphical.slice
│       ├── firefox.scope
│       ├── foot.scope
│       └── slack.scope
└── background.slice
    └── background-graphical.slice
        └── ...
```

Current upstream systemd issue about oomd monitoring after daemon-reload:  
https://github.com/systemd/systemd/issues/43174

### GNOME tools vs GNOME desktop

Using GTK or individual GNOME applications does **not** mean adopting GNOME session infrastructure.

A useful distinction:

```text
GTK application
GNOME application
GNOME desktop infrastructure
```

For this stack, I’d intentionally choose GTK/Adwaita as the boring fallback UI substrate so the desktop feels coherent without pulling in GNOME Shell, Mutter, gnome-session, etc.

### Polkit

Polkit architecture:  
https://polkit.pages.freedesktop.org/polkit/polkit.8.html

You need exactly one graphical authentication agent. `polkit-gnome` is historically a boring standalone GTK agent despite the name.

The architectural line should be:

- individual GNOME/GTK apps: fine
- GNOME session/settings machinery: avoid unless deliberately chosen

A coherent lightweight stack:

```text
Sway
uwsm
greetd
mako
fuzzel
swaylock/swayidle
GTK
Adwaita
GTK portal backend
small GTK polkit agent
GTK apps where convenient
PipeWire/WirePlumber
systemd underneath
```

---

## User

Okay. Ready for those videos now.

## Assistant

Here is the advanced ordered syllabus.

### Phase 1 — Build the OS

1. **mkosi: Building Bespoke Operating System Images**  
https://www.youtube.com/watch?v=6EelcbjbUa8

2. **Creating Arch Linux images using mkosi**  
https://www.youtube.com/watch?v=SiyUpBwKL0A

3. **systemd-repart: Building Discoverable Disk Images**  
https://www.youtube.com/watch?v=af6fdSmZdvw

4. **Installing your OS with systemd-repart**  
https://www.youtube.com/watch?v=XaIPIHU3iGU

5. **mkosi-initrd: initrds built from system packages**  
https://www.youtube.com/watch?v=gpGBgZA-E_c

6. **New design for initrds — Zbigniew Jędrzejewski-Szmek**  
https://www.youtube.com/watch?v=6a_GZsdgSYA

### Phase 2 — Boot / integrity / identity

7. **Unified Kernel Images (UKIs) — Lennart Poettering**  
https://www.youtube.com/watch?v=7UhwK3g99_0

8. **Towards Secure Unified Kernel Images for Generic Linux Distributions and Everyone Else**  
https://www.youtube.com/watch?v=LvWqD274cKU

9. **Linux & TPMs**  
https://www.youtube.com/watch?v=0RSH3JXqShE

10. **systemd & TPM in 2024**  
https://www.youtube.com/watch?v=9gcBetR6gAU

11. **The road to a trusted and measured boot chain in Bootable Containers**  
https://www.youtube.com/watch?v=xQT5IqL0kzc

12. **UKIs and composefs support for Bootable Containers**  
https://www.youtube.com/watch?v=D7HqckeHlx8

### Phase 3 — Updates / rollback / composition

13. **GNOME OS + systemd-sysupdate**  
https://www.youtube.com/watch?v=EaEsb1WYgoQ

14. **GNOME OS' prêt-à-booter image**  
https://www.youtube.com/watch?v=KLZJ9NhBPDw

15. **Yocto's hidden gem: OTA and seamless updates with systemd-sysupdate**  
https://www.youtube.com/watch?v=ulNZJXrIxkw

16. **System and Configuration Extensions for Image-based Linux Distros and Beyond**  
https://www.youtube.com/watch?v=XTy3scX6rF4

17. **systemd-confext Two Years On: Versioned Overlays for /etc**  
https://www.youtube.com/watch?v=ZQanQTkL8bw

18. **Waiter, an OS please, with some sysext sprinkled on top**  
https://www.youtube.com/watch?v=xxNOHc4zY8c

19. **Shipping Container Runtimes as systemd-sysext Images**  
https://www.youtube.com/watch?v=nRHhI7uqb1E

20. **Integrating systemd soft-reboot into a distribution and surviving it**  
https://www.youtube.com/watch?v=tAOmW75gMzE

### Phase 4 — Testing

21. **Improving systemd's integration testing infrastructure**  
https://www.youtube.com/watch?v=_xmbJNB3yDI

22. **Testing the CentOS Hyperscale systemd backport with mkosi**  
https://www.youtube.com/watch?v=yK_7tKZLQ68

### Phase 5 — Competing architectures

23. **Reproducible and Immutable OS Images with NixOS**  
https://www.youtube.com/watch?v=YAl27ciB6c8

24. **bootc: Generating an ecosystem around bootable OCI containers**  
https://www.youtube.com/watch?v=rCokgSYiVHQ

25. **From Container to Bare Metal: Redefining OS Build with bootc**  
https://www.youtube.com/watch?v=acKbf3V3rJk

26. **systemd-ifying postmarketOS, our immutable future, and why**  
https://www.youtube.com/watch?v=S6EpCmYEovY

27. **Efficient RAUC Updates using composefs**  
https://www.youtube.com/watch?v=dMCGEZrWN8Y

### Phase 6 — Wayland

28. **Master your PipeWire streams with WirePlumber**  
https://www.youtube.com/watch?v=63Sdv0VDCQU

### Phase 7 — MicroVMs

29. **What Are MicroVMs? And Why Should I Care?**  
https://www.youtube.com/watch?v=4d0NIfuFLXc

30. **A Secure and Fast microVM for Serverless Computing — Firecracker**  
https://www.youtube.com/watch?v=PAEMGa-i2lU

All Systems Go! 2024:  
https://www.youtube.com/playlist?list=PLWYdJViL9EipIImmvuoGFAeS-lKeHH2DD

---

## User

It’d be valuable to have custom kernels for size, speed, maybe no initrd, etc. how would that work in the system we’ve been talking about?

## Assistant

Treat the **kernel configuration as another built/tested artifact with role-specific variants**.

A likely structure:

```text
kernel/
├── common.config
├── workstation.config
├── laptop.config
├── router.config
└── microvm.config
```

Build graph:

```text
kernel source
+ common config
+ role config
    ↓
build kernel
    ↓
kernel artifact/modules
    ↓
mkosi
    ↓
UKI + root/usr image
    ↓
boot/integration tests
    ↓
signed release artifact
```

Likely kernel families:

| Kernel | Target |
|---|---|
| generic | workstation/laptop fallback |
| router | known networking hardware |
| server | storage/network/server features |
| microvm | aggressively minimal |

### No-initrd

Linux EFI stub docs:  
https://docs.kernel.org/admin-guide/efi-stub.html

No-initrd is very plausible for microVMs and possibly a router if all root-path drivers/filesystems are built in.

mkosi news / kernel module controls:  
https://man.archlinux.org/man/extra/mkosi/mkosi.news.7.en

Systemd root filesystem discovery:  
https://systemd.io/ROOTFS_DISCOVERY/

The more sophisticated the root chain becomes—LUKS, TPM, dm-verity, partition discovery—the more useful a small systemd initrd becomes.

Suggested result:

```text
WORKSTATION
  custom kernel
  tiny initrd
  TPM + encryption + verity
  signed UKI

LAPTOP
  broader custom kernel
  tiny initrd
  TPM + encryption

ROUTER
  small networking kernel
  maybe CONFIG_MODULES=n
  potentially no initrd

MICROVM
  tiny virtio-only kernel
  CONFIG_MODULES=n
  no initrd
```

---

## User

What’s the advantage of using arch packages vs eg fedora packages in the proposed system? What about AUR vs rpm-fusion?

## Assistant

In this design, the package ecosystem matters **mostly at build time**, not at runtime.

Arch advantages:

- very current systemd/kernel/Mesa/wlroots/PipeWire
- simple PKGBUILDs
- easy patching/rebuilding
- AUR as an enormous recipe library
- familiar to you

Arch overview:  
https://wiki.archlinux.org/title/Arch_Linux

Official repositories:  
https://wiki.archlinux.org/title/Official_repositories

Arch comparison:  
https://wiki.archlinux.org/title/Arch_compared_to_other_distributions

Fedora advantages:

- coherent release branches
- security fixes without unrelated rolling churn
- stronger distro-level integration/policy
- institutional alignment with systemd/Wayland/PipeWire/SELinux/container work

Fedora:  
https://fedoraproject.org/

### AUR vs RPM Fusion

These are not really equivalent.

RPM Fusion is a normal community-maintained binary repository integrated into Fedora:  
https://docs.fedoraproject.org/en-US/quick-docs/rpmfusion-setup/

AUR is a user-maintained recipe repository; Arch explicitly treats AUR packages as unsupported and user-responsibility:  
https://wiki.archlinux.org/title/Arch_User_Repository

For this distro, a good rule would be:

```text
official Arch repo
    ↓
may enter build directly

AUR
    ↓
never enters image directly
    ↓
review/pin/vendor
    ↓
CI build
    ↓
our repository
```

The biggest argument against frozen Arch snapshots is security maintenance: Arch assumes continuous upgrades, while Fedora release branches are better suited to receiving targeted fixes.

---

## User

Can you create that YouTube playlist for me?

## Assistant

I can’t create the playlist inside your YouTube account from here because there isn’t a connected YouTube integration available in this chat.

I can, however, turn the syllabus into a clean ordered list of YouTube URLs or an HTML page.

---

## User

Yeah, full list as links that I can copy and paste into notes or something

## Assistant

### OS images / mkosi / repart

1. **mkosi: Building Bespoke Operating System Images**  
https://www.youtube.com/watch?v=6EelcbjbUa8

2. **Creating Arch Linux images using mkosi**  
https://www.youtube.com/watch?v=SiyUpBwKL0A

3. **systemd-repart: Building Discoverable Disk Images**  
https://www.youtube.com/watch?v=af6fdSmZdvw

4. **Installing your OS with systemd-repart**  
https://www.youtube.com/watch?v=XaIPIHU3iGU

5. **mkosi-initrd: initrds built from system packages**  
https://www.youtube.com/watch?v=gpGBgZA-E_c

6. **New design for initrds — Zbigniew Jędrzejewski-Szmek**  
https://www.youtube.com/watch?v=6a_GZsdgSYA

### UKIs / Secure Boot / TPM

7. **Unified Kernel Images (UKIs) — Lennart Poettering**  
https://www.youtube.com/watch?v=7UhwK3g99_0

8. **Towards Secure Unified Kernel Images for Generic Linux Distributions and Everyone Else**  
https://www.youtube.com/watch?v=LvWqD274cKU

9. **Linux & TPMs**  
https://www.youtube.com/watch?v=0RSH3JXqShE

10. **systemd & TPM in 2024**  
https://www.youtube.com/watch?v=9gcBetR6gAU

11. **The road to a trusted and measured boot chain in Bootable Containers**  
https://www.youtube.com/watch?v=xQT5IqL0kzc

12. **UKIs and composefs support for Bootable Containers**  
https://www.youtube.com/watch?v=D7HqckeHlx8

### Updates / rollback / sysext / confext

13. **GNOME OS + systemd-sysupdate**  
https://www.youtube.com/watch?v=EaEsb1WYgoQ

14. **GNOME OS' prêt-à-booter image**  
https://www.youtube.com/watch?v=KLZJ9NhBPDw

15. **Yocto's hidden gem: OTA and seamless updates with systemd-sysupdate**  
https://www.youtube.com/watch?v=ulNZJXrIxkw

16. **System and Configuration Extensions for Image-based Linux Distros and Beyond**  
https://www.youtube.com/watch?v=XTy3scX6rF4

17. **systemd-confext Two Years On: Versioned Overlays for /etc**  
https://www.youtube.com/watch?v=ZQanQTkL8bw

18. **Waiter, an OS please, with some sysext sprinkled on top**  
https://www.youtube.com/watch?v=xxNOHc4zY8c

19. **Shipping Container Runtimes as systemd-sysext Images**  
https://www.youtube.com/watch?v=nRHhI7uqb1E

20. **Integrating systemd soft-reboot into a distribution and surviving it**  
https://www.youtube.com/watch?v=tAOmW75gMzE

### Testing / CI / reproducibility

21. **Improving systemd's integration testing infrastructure**  
https://www.youtube.com/watch?v=_xmbJNB3yDI

22. **Testing the CentOS Hyperscale systemd backport with mkosi**  
https://www.youtube.com/watch?v=yK_7tKZLQ68

### Other OS architectures

23. **Reproducible and Immutable OS Images with NixOS**  
https://www.youtube.com/watch?v=YAl27ciB6c8

24. **bootc: Generating an ecosystem around bootable OCI containers**  
https://www.youtube.com/watch?v=rCokgSYiVHQ

25. **From Container to Bare Metal: Redefining OS Build with bootc**  
https://www.youtube.com/watch?v=acKbf3V3rJk

26. **systemd-ifying postmarketOS, our immutable future, and why**  
https://www.youtube.com/watch?v=S6EpCmYEovY

27. **Efficient RAUC Updates using composefs**  
https://www.youtube.com/watch?v=dMCGEZrWN8Y

### Wayland

28. **Master your PipeWire streams with WirePlumber**  
https://www.youtube.com/watch?v=63Sdv0VDCQU

### MicroVMs

29. **What Are MicroVMs? And Why Should I Care?**  
https://www.youtube.com/watch?v=4d0NIfuFLXc

30. **A Secure and Fast microVM for Serverless Computing — Firecracker**  
https://www.youtube.com/watch?v=PAEMGa-i2lU

### Conference archive

All Systems Go! 2024 playlist:  
https://www.youtube.com/playlist?list=PLWYdJViL9EipIImmvuoGFAeS-lKeHH2DD

---

## User

Sweet. CoreOS had the Omaha(?) protocol for auto updates. Would we be able to use the flatcar version of that?

What about file systems? I’m partial to btrfs or zfs. I’d really like to use fs features to make containers and vms workflows better/easier.

## Assistant

Yes on Omaha/Nebraska, but I’d use it for **fleet rollout policy**, not the actual update transport.

Flatcar update docs:  
https://www.flatcar.org/docs/latest/updates-releases/

Nebraska development docs:  
https://www.flatcar.org/docs/latest/nebraska/development/

A useful architecture:

```text
CI produces release 142
    ↓
publish artifacts
    ↓
Nebraska decides WHO should get 142 and WHEN
    ↓
small Omaha client on host
    ↓
systemd-sysupdate performs installation
    ↓
reboot → boot counting → bless
```

### Filesystems

For this system, I’d favor **Btrfs as the default mutable filesystem** and leave ZFS as a supported storage/hypervisor role.

Btrfs subvolumes:  
https://btrfs.readthedocs.io/en/latest/btrfs-subvolume.html

Btrfs reflinks:  
https://btrfs.readthedocs.io/en/stable/Reflink.html

Btrfs send/receive:  
https://btrfs.readthedocs.io/en/latest/btrfs-send.html

Btrfs qgroups:  
https://btrfs.readthedocs.io/en/latest/btrfs-qgroup.html

Use filesystem features for mutable state, not OS version identity.

Example:

```text
ESP / UKIs
immutable OS image(s)
/var → Btrfs
/home → Btrfs
```

For VMs, reflinks make disposable copies of raw/DDI images extremely cheap.

### ZFS

OpenZFS snapshots/clones:  
https://openzfs.github.io/openzfs-docs/Basic%20Concepts/Datasets/Snapshots%20and%20Clones.html

OpenZFS zvols:  
https://openzfs.github.io/openzfs-docs/Basic%20Concepts/Datasets/ZVOLs.html

ZFS is arguably nicer for dedicated VM/storage hosts because of datasets, clones, zvols, and replication, but it complicates the custom-kernel story because it’s an out-of-tree module.

Likely hybrid:

```text
general machines:
  Btrfs for /var and /home

storage/hypervisor profile:
  ZFS pool for VM/storage datasets
```

A particularly attractive idea:

```text
/var/lib/myos/images/
├── router.raw
├── build-agent.raw
├── microvm.raw
└── ...
```

Store DDIs on Btrfs, reflink them for disposable `systemd-vmspawn`/`systemd-nspawn` instances.

---

## User

What can we learn from gnomeos? What ideas are worth using? What work could we use?

## Assistant

GNOME OS is probably the **closest living reference implementation** for the architecture we’ve been discussing.

### 1. Immutable host functionality as an OS problem

Adrian Vovk on GNOME OS design:  
https://blogs.gnome.org/adrianvovk/2024/10/25/a-desktop-for-all/

The useful invariant is that equivalent installations are actually equivalent, rather than every host accumulating local package layering.

### 2. OSTree → systemd-sysupdate validates the direction

GNOME OS moved away from OSTree toward `systemd-sysupdate`:  
https://blogs.gnome.org/tbernard/2025/04/

This aligns with Secure Boot, encryption, sysext, and the broader systemd image ecosystem.

### 3. Optional features

GNOME OS helped drive optional-feature support in sysupdate, suitable for things like development tooling and proprietary drivers:  
https://blogs.gnome.org/tbernard/2025/04/

This maps well to `devel`, `nvidia`, `virtualization-host`, etc.

### 4. Developer sysext workflow

GNOME OS work around development sysexts:  
https://blogs.gnome.org/sophieh/2026/04/30/testing-library-code-in-gnome-os/

A good workflow is:

```text
build component
→ dev.sysext.raw
→ attach to test OS/VM
→ activate
→ test
```

### 5. `/etc` and confext

GNOME OS hackfest writeup:  
https://blogs.gnome.org/adrianvovk/2026/02/18/gnome-os-hackfest-fosdem-2026/

They learned that copying/symlinking vendor defaults into `/etc` causes drift and are moving toward `systemd-confext` + overlayfs.

### 6. Image builder lessons

The same 2026 hackfest writeup describes GNOME OS prototyping BuildStream → mkosi → UAPI DDI, arguing strongly against writing bespoke image-generation machinery.

### 7. Security/installer work

GNOME STF writeup:  
https://blogs.gnome.org/tbernard/2025/04/11/gnome-stf-2024/

Useful prior art for Secure Boot, encryption, installer integration, homed, and systemd/UAPI gaps.

### 8. CI boots the actual OS

GNOME OS site:  
https://os.gnome.org/

OpenQA and CI integration are useful models for testing the literal OS artifact.

### 9. Debug symbols

GNOME OS moved debug material toward debuginfod-style workflows rather than shipping huge debug images everywhere:  
https://planet-gnome-org-c59c6f.pages.gitlab.gnome.org/

### 10. CVE scanning

GNOME’s STF work also includes vulnerability reporting tied back to source packages/components:  
https://blogs.gnome.org/tbernard/2025/04/11/gnome-stf-2024/

### What not to copy initially

- BuildStream as the primary package universe
- “Flatpak everywhere” as an absolute
- systemd-homed without reevaluation

GNOME 51 alpha / BuildStream release context:  
https://discourse.gnome.org/t/gnome-51-alpha-released/36027/1

GNOME OS still treating homed as important:  
https://blogs.gnome.org/adrianvovk/2026/02/18/gnome-os-hackfest-fosdem-2026/

GNOME OS update limitations and delta discussion:  
https://blogs.gnome.org/tbernard/2025/06/01/summer-of-gnome-os/

---

## User

What’s happened with homed in the last 5 years or so? I was having docker and podman issues mainly that were blockers.

## Assistant

A lot has improved, but the specific blocker you likely hit—**rootless container storage and subordinate-ID assumptions inside a homed-managed home**—is not fully gone.

Homed/homectl docs:  
https://www.freedesktop.org/software/systemd/man/250/homectl.html

Podman rootless tutorial:  
https://github.com/containers/podman/blob/main/docs/tutorials/rootless_tutorial.md

Docker rootless docs:  
https://docs.docker.com/engine/security/rootless/

A key tension remains:

```text
homed:
  portable user identity
  UID may differ per host

rootless containers:
  user UID
  + stable subordinate UID/GID ranges
  + on-disk files owned by mapped IDs
```

Current systemd TODO still explicitly mentions a companion directory for container images owned by arbitrary UIDs:  
https://github.com/systemd/systemd/blob/main/TODO.md

Other improvements include:

- LUKS/fscrypt/Btrfs/directory/CIFS home backends
- richer authentication including FIDO2/PKCS#11/recovery keys
- user record integration
- resource controls
- session locking improvements

homed.conf:  
https://www.freedesktop.org/software/systemd/man/latest/homed.conf.html

systemd-homed service:  
https://www.freedesktop.org/software/systemd/man/devel/systemd-homed.service.html

Session-freezing issue example:  
https://github.com/systemd/systemd/issues/33626

Podman system service:  
https://docs.podman.io/en/latest/markdown/podman-system-service.1.html

A possible mitigation is keeping heavy container/VM storage outside `$HOME`, but that doesn’t solve bind-mounted source trees inside the home.

---

## User

That wouldn’t help when you’re trying to mount in a local/file directory into a container though, would it?

## Assistant

Right. Moving Podman/Docker’s internal storage out of `$HOME` only fixes the container-store side.

Podman user namespace docs:  
https://docs.podman.io/en/v4.3/markdown/options/userns.container.html

Docker rootless docs:  
https://docs.docker.com/engine/security/rootless/

The more promising primitive is **idmapped mounts**, which allow the same underlying filesystem tree to appear under a different UID/GID mapping without recursive chown.

Kernel idmapped-mount documentation:  
https://dri.freedesktop.org/docs/drm/filesystems/idmappings.html

Conceptually:

```text
actual home filesystem
    ↓
idmapped view
    ↓
container user namespace
```

But current homed + Podman integration is not yet something I’d assume is transparent and boring.

For a container-heavy workflow, a simpler invariant may still be:

```text
same UID everywhere
same subuid/subgid ranges everywhere
normal Btrfs home
Podman --userns=keep-id
```

---

## User

Is it possible to get rid of Perl from the base system?

## Assistant

Yes. There’s no fundamental reason Perl has to exist in the runtime image.

The important distinction is **build dependency vs runtime dependency**.

Systemd Fedora package reference:  
https://packages.fedoraproject.org/pkgs/systemd/systemd/

Arch Perl policy:  
https://wiki.archlinux.org/title/Perl_Policy

A good design:

```text
BUILD ENVIRONMENT
  perl/python/gcc/etc. as needed

RUNTIME IMAGE
  only operational dependencies
```

If a parent-distro package drags Perl in solely for helper scripts you don’t need, repackage/split it.

I’d make runtime absence an automated invariant, and potentially aim for no runtime scripting language at all in router/microVM profiles.

---

## User

What can we learn/steal from Amutable?

## Assistant

Amutable is still early enough that there isn’t much public implementation to copy directly yet, but its framing is highly relevant: **deterministic, cryptographically verifiable integrity across build, boot, and runtime**.

Amutable:  
https://amutable.com/

Introduction:  
https://amutable.com/blog/introducing-amutable

Team:  
https://amutable.com/about

The biggest ideas to steal:

### 1. End-to-end integrity

```text
Git commit
+ pinned package inputs
+ kernel source/config
+ build-tool identity
    ↓
reproducible manifest
    ↓
root/usr image hash
    ↓
dm-verity root hash
    ↓
UKI tied to that identity
    ↓
Secure Boot + TPM measurements
    ↓
running system can attest what release it is
```

### 2. Verifiably correct `/usr`, not merely read-only `/usr`

Use dm-verity and signed image identity.

Systemd environment/image-policy documentation:  
https://github.com/systemd/systemd/blob/main/docs/ENVIRONMENT.md

### 3. Aggressive deterministic-vs-mutable state separation

```text
VERIFIABLE:
  /usr
  kernel
  initrd
  signed config/extensions

MUTABLE:
  /var
  /home
  logs
  container/VM writable state
```

Systemd TODO for future measurement/integration ideas:  
https://github.com/systemd/systemd/blob/main/TODO.md

### ParticleOS

ParticleOS under the systemd GitHub organization is probably the more concrete codebase to study today:  
https://github.com/systemd

Amutable explicitly mentions ParticleOS experience:  
https://amutable.com/blog/introducing-amutable

Useful ParticleOS areas to inspect:

- mkosi structure
- repart definitions
- sysupdate
- UKI
- Secure Boot
- dm-verity
- TPM
- distro abstraction
- CI
- multi-distro package inputs

### Runtime integrity

Amutable’s public material doesn’t yet specify the exact mechanism, so don’t assume a specific implementation. Technologies worth evaluating include IMA, fs-verity, Landlock, BPF-LSM, SELinux/AppArmor, kernel lockdown, image policies, and TPM-backed attestation.

### Provenance

A strong release could publish a signed manifest tying together:

```text
release
source commit
kernel source/config
package snapshot/manifest
root hash
UKI hash
```

Nebraska/Omaha could then decide **who may upgrade**, while sysupdate/verity/UKI enforce **what the release actually is**.

---

## User

Create a downloadable markdown file with the transcript of this session. Include all links.
