---
status: active
last_updated: 2026-08-10
governing_plan: PLN-0001
---

# Reference-VM slice composition record

PLN-0001-02. This records what the composition fixture produced, what its
identity is, and how to reconstruct it. The artifacts themselves are not in the
repository: the hygiene contract's binary and size bounds bind here, and a
1.3 GiB disk image is retained outside the checkout under the build root.

Composition ran unprivileged on `desktop-jason`. It installed nothing on the
host, required no root, and wrote only under the build root
(`${XDG_CACHE_HOME:-$HOME/.cache}/neutrinos/slice`). That was a constraint, not
a convenience: PLN-0001 permits no mutation of this host, so a composition path
that needed a host package would have been a stop condition.

## Fixture

| Part | Location |
| --- | --- |
| Declaration | `src/slice/input-set.toml`, schema `input-set-v2.schema.json` |
| Composition configuration | `src/slice/composition/mkosi.conf` |
| Entry point | `src/slice/compose.sh` |
| Build root | `${XDG_CACHE_HOME:-$HOME/.cache}/neutrinos/slice`, overridable with `NEUTRINOS_SLICE_BUILD_ROOT` |

Reconstruct with `./src/slice/compose.sh --force build`. The script clones mkosi
at the pinned commit, builds the tools tree from the pinned base image plus the
declared packages from the frozen repository, and runs the composition. It
resolves no floating reference.

## Output identity

Digests of the retained build, SHA-256:

| Artifact | Digest | Stable across builds |
| --- | --- | --- |
| `neutrinos-slice.efi` (UKI) | `575c847dd491a081ff364b0139fe3e81b4e00add7f08f12fb6b4c2582a8cd0fd` | yes |
| `neutrinos-slice.vmlinuz` | `4b37e4e542a62c580c751787848be6c99e6f908f6712c8c6da85516b8d541de2` | yes |
| `neutrinos-slice.initrd` | `e7061e2539c9bab9b2c3a94f7f4bf75d4da6103cba6d490730896d43382c8b71` | yes |
| `neutrinos-slice.raw` (disk) | `d3b5560d7394ce91f864ee1ee2ac1f42f1f936874fc72a686112c1edc42fb689` | **no** |

## Resolved package closure

104 RPMs, all from the single declared frozen repository. Anchor versions:

- `kernel-core` 6.19.10-300.fc44
- `systemd` 259.5-1.fc44
- `dbus-broker` 37-8.fc44
- `systemd-boot-unsigned` — the declaration requests `systemd-boot`, which
  Fedora satisfies through this package. The record names what was installed,
  not what was asked for.

The complete resolved set with exact versions is retained as
`neutrinos-slice.manifest` in the build root. `ManifestFormat=json` is set in
the composition configuration so the record is produced by every build rather
than by a flag someone remembers to pass.

## The disk image is not reproducible

Measured across four builds, two with a random repart seed and two with a fixed
one:

- the UKI, kernel, and initrd are bit-identical every time, with or without the
  fixed seed;
- the disk image differs every time, including with the seed fixed.

Fixing `Seed=` removes partition UUID randomness and was not sufficient.
Whatever else varies inside the image has not been identified. This is recorded
rather than resolved because SYS-016 asks for a comparison across two builds and
the honest answer today is that the comparison succeeds at the UKI layer and
fails at the disk layer. PLN-0001-07's offline reconstruction must compare the
UKI and the resolved package set, not the `.raw` digest, until this is
understood.

## What this does not establish

- **Nothing boots yet.** The artifact has not been executed. Booting is
  PLN-0001-03, and a disk image that builds is not a disk image that starts.
- **No mechanism is selected.** mkosi and Fedora 44 remain candidate fixtures.
  bootc and a literal Arch snapshot remain the required challengers, and this
  build working is not evidence for mkosi over bootc because bootc was not
  tried. See [PR-0029](reviews/0029-g1-gate-approval.md) C-005.
- **The declaration is enforced at one point only.** `LocalMirror=` makes the
  single frozen repository the only one that exists during the build, which is
  why `updates` cannot leak in. That is a property of this configuration, not a
  guarantee of the fixture: a future change to `Mirror=` would silently restore
  mkosi's default repository set, including `updates`.
- **`--nogpgcheck` is used when building the tools tree.** The tools packages
  are fetched from the frozen repository over TLS but their signatures are not
  verified, because the keys arrive in the same transaction that installs them.
  The image build itself does verify signatures. This is a real gap in the
  tools-tree path and is not closed by the digest pin on the base image.
- **No registered check guards any of this**, including agreement between
  `compose.sh` and `input-set.toml`, which repeat the same values. Slice tests
  register under PLN-0001-05.
