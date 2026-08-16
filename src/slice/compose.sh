#!/bin/sh
# Compose the PLN-0001 reference-VM slice deployment set.
#
# Acquisition is bounded by the declared inputs below: nothing resolves a
# floating reference. Mutates no host state, needs no root and no host package
# installation -- a step that starts needing either is a boundary crossing and
# a stop condition.
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build_root=${NEUTRINOS_SLICE_BUILD_ROOT:-${XDG_CACHE_HOME:-$HOME/.cache}/neutrinos/slice}

# Selection: which artifact of the many this can build. All three come from the
# environment rather than a file, because an edited working tree makes the
# selection untraceable, and all three are passed to compose.py as arguments --
# what each one *means* is composition's to know, so the lists of arms and
# variants live there and not in two places.
#
# The arm is Format= on /usr, the one variable PLN-0002 measures; everything
# else is held identical by construction, so any C-007 difference is the
# filesystem's. The variant is PLN-0002 amendment 5. The role names the
# capability declaration that selects the session variant's packages -- one role
# today, named rather than assumed so a second one is a value here.
arm=${NEUTRINOS_SLICE_ARM:-erofs}
variant=${NEUTRINOS_SLICE_VARIANT:-primary}
role=${NEUTRINOS_SLICE_ROLE:-workstation}

# The harness machine-id, declared here and nowhere else.
#
# It is delivered to the guest as the `system.machine_id` SMBIOS type 11
# credential by tools/validation/slice_boot.py, so the artifact carries no
# machine identity -- PLN-0001's standing finding is that the harness supplies
# what the harness needs, and a machine-id baked into a release artifact would
# be one machine's identity inside something meant to boot on many.
#
# It is also what composition/state-partitions/20-var.conf's UUID= is derived
# from, because the Discoverable Partitions Specification requires a /var
# partition's UUID to be HMAC-SHA256(machine-id, var-type-uuid) or
# systemd-gpt-auto-generator will not mount it. repart takes no substitution, so
# that file holds a literal and T2-STATE-001 recomputes it from this value. The
# two move together or the check fails; neither can drift silently.
harness_machine_id=6a5f2c8e4b3d47a19e7c0d5f8b62a134

# Six peer directories, no arm holding a privileged name (PLN-0002-06). `out`
# survives as a symlink because the PLN-0001 records name it and an operator's
# NEUTRINOS_SLICE_ARTIFACT_DIR may point at it.
out_dir="$build_root/out-$arm"
if [ "$variant" != primary ]; then
    out_dir="$out_dir-$variant"
fi

# No value here is restated from input-set.toml. The mkosi commit, the
# tools-tree base image and its package list, the overlay digests, the overlay's
# own name and the repository URL were all copied into this script, because sh
# cannot parse TOML without a dependency this slice has not declared. Each moved
# to the helper that uses it -- buildroot.py, acquire-overlay.py, compose.py,
# retain-repository.py -- and each reads the declaration. Where a helper can
# read the declaration, it reads it; what remains here is selection and layout,
# which the declaration does not name.
#
# The overlay's *root* is layout and stays. Its name was a restated value hiding
# inside a path, which is how it outlived the sweep that removed the others.
overlay_dir="$build_root/inputs/overlay"

# The selection is valid and this will not be a silent no-op -- checked before
# anything below does work, so a build that will be refused costs a second
# rather than a build root and two extension rebuilds. compose.py runs the same
# two checks again when it composes.
#
# Before the mkdir, not after: an unknown arm used to be rejected before any
# directory was created, and creating the output first left `out-xfs` behind
# for a selection the script had just refused.
python3 "$root/compose.py" --precheck --build-root="$build_root" \
    --output="$out_dir" --overlay="$overlay_dir" \
    --arm="$arm" --variant="$variant" --role="$role" -- "$@"

mkdir -p "$build_root" "$out_dir"

if [ ! -e "$build_root/out" ]; then
    ln -s out-erofs "$build_root/out"
fi

# The build root: synthetic signing material, mkosi at its declared commit, and
# a tools tree matching its declared recipe. The last two read input-set.toml
# directly, so the copies this script used to carry are gone; see buildroot.py
# for why the tools tree is keyed by digest rather than by existence, and why
# the verity subject fails rather than regenerating.
python3 "$root/buildroot.py" --build-root="$build_root"

# Package cache inside this build root, not the user's shared mkosi cache:
# PLN-0001-07 found 58 RPMs there that the declared repository does not
# contain, left by injected faults. A build resolving from a shared cache
# cannot say where its inputs came from.
#
# Before the build, not after -- an overlay that cannot be verified must stop
# the composition rather than be discovered in the artifact.
python3 "$root/acquire-overlay.py" --destination="$overlay_dir"

# The confext, built before the artifact that carries it. PLN-0002-03a. It
# resolves no repository, so it builds whether or not the declared repository
# is reachable.
#
# Staging the signed image into /usr/lib/confexts is a declared fixture, not a
# decision: owner ruling 2026-08-11 on finding 1 option D, and it fuses release
# and configuration, which DES-0005's amendment separates. PLN-0002-03b owns
# the design.
#
# The certificate travels in /usr/lib/verity.d because that is where systemd
# looks. It is not sufficient for enforcement: measured 2026-08-11, the kernel
# returns -ENOKEY for a key in no keyring and systemd merges unsigned anyway.
# docs/project/etc-path-carve.md.
#
# Both signings and the staging tree, in fixtures.py. NEUTRINOS_SKIP_CONFEXT
# keeps its name and its meaning: measure-build-time.py sets it,
# retain-artifact-digests.py reports on it, and the artifact-parameter and
# format-measurement records cite it as a condition of measurements already
# taken.
if [ -z "${NEUTRINOS_SKIP_CONFEXT:-}" ]; then
    python3 "$root/fixtures.py" --build-root="$build_root"
fi

# The artifact. compose.py owns what an arm and a variant mean, the mkosi
# invocation, and the refusal to report success without composing; the caller's
# arguments pass through after `--` so `--force` or `summary` still reach mkosi.
python3 "$root/compose.py" --build-root="$build_root" \
    --output="$out_dir" --overlay="$overlay_dir" \
    --arm="$arm" --variant="$variant" --role="$role" -- "$@"

# Retention is a build step, not something to remember afterwards; without it
# the declared repository is a URL whose bytes survive only as a side effect of
# the last build's cache, which is what made PLN-0001-07's first offline
# rebuild impossible. It fails closed on a package the declared repository does
# not contain, so it is also the check that nothing undeclared entered the
# cache.
#
# It reads the declared repository itself, URL and metadata digest together, so
# it retains the declared publication rather than whatever the URL serves.
#
# Only when a build produced an image: `clean`, `--help` and the other verbs
# have nothing to retain, and fetching metadata for them would put a network
# dependency on operations that have none.
if [ -f "$out_dir/neutrinos-slice.manifest" ]; then
    python3 "$root/retain-repository.py" \
        --cache="$build_root/pkgcache" \
        --overlay="$overlay_dir" \
        --destination="$build_root/inputs/repository"
fi

# The T4-CONFEXT-001 fixture. After retention, and that ordering is a fix: this
# step failed on its first real run, `set -eu` aborted the script, and
# retention silently did not happen. A step added for a new check must not take
# out an established one.
#
# Only the enrollment remains here, because only it needs the composed
# artifact: it copies the artifact and writes the signed variable updates into
# the copy's ESP. The two extension images are delivered to the fixture
# directory by fixtures.py, with the build that produced them.
#
# It needs an image-signing certificate to keep in `db` beside the verity
# signer, since enrolling without one produces a machine whose firmware refuses
# its own UKI. buildroot.py generates that certificate, so the else branch is
# the damaged-build-root case. It reports and continues rather than failing the
# composition: the fixture's absence blocks T4-CONFEXT-001, which is the same
# signal in the place that reads it.
if [ -f "$out_dir/neutrinos-slice.manifest" ] && [ -z "${NEUTRINOS_SKIP_CONFEXT:-}" ]; then
    if [ -f "$build_root/keys/secureboot.crt" ]; then
        sh "$root/enroll-fixture.sh"
    else
        echo "compose: no image-signing certificate at $build_root/keys/secureboot.crt," \
             "so the T4-CONFEXT-001 fixture was not built. buildroot.py generates" \
             "that certificate, so its absence means the build root is damaged" \
             "rather than incomplete." >&2
    fi
fi
