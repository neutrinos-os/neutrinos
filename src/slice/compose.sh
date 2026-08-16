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

# The arm: Format= on /usr, the one variable PLN-0002 measures. Everything else
# is held identical by construction, so any C-007 difference is the filesystem's.
#
# Environment, not a file: an edited working tree makes the arm untraceable.
#
# Only the arm directory is passed below. mkosi picks up the shared
# composition/mkosi.repart/ by path suffix and appends the CLI value to it --
# verified against `mkosi summary`. Passing both hands repart the same
# --definitions twice.
arm=${NEUTRINOS_SLICE_ARM:-erofs}

if [ ! -d "$root/composition/mkosi.repart.$arm" ]; then
    echo "compose: no arm '$arm'; expected a partition definition directory at" \
         "$root/composition/mkosi.repart.$arm" >&2
    exit 1
fi

# The variant. PLN-0002 amendment 5, accepted 2026-08-14. `primary` is what
# everything measures; the other two are PLN-0002-10 substitution sources, and
# they exist because the build is bit-reproducible, so substituting a rebuild
# is vacuous. Task 10 needs a substitute validly signed by the enrolled key
# carrying a root hash the UKI does not name:
#
#   content  one declared marker file under /usr, so the image differs
#   seed     identical tree, different Seed=, so the identities differ
#
# Two routes because they fail differently -- a content variant that boots
# means integrity did not bind the contents, a seed variant that boots means it
# did not bind the identity. Environment-selected, like the arm and for the
# same reason.
# `state` is a fourth variant and is NOT a substitution source. It adds the
# machine-state and home partitions from composition/state-partitions/, so it
# is the first artifact this project has built with anything writable on it. It
# rides the variant axis because that axis already guarantees the one thing
# that matters here: a non-primary variant writes to its own output directory
# and therefore cannot overwrite the six retained PLN-0002-06 members, whose
# rebuild would void PLN-0002's tally.
variant=${NEUTRINOS_SLICE_VARIANT:-primary}

case "$variant" in
    primary|content|seed|state|session) ;;
    *)
        echo "compose: no variant '$variant'; expected primary, content, seed," \
             "state or session" >&2
        exit 1
        ;;
esac

# The role whose capability declaration drives the session variant's package
# selection. One role today; named rather than assumed so a second one is a
# value here and not an edit to the logic below.
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

# One-time migration of the historic layout. Moves rather than copies, so no
# build root ends up with two EROFS primaries disagreeing about which is
# current. An already-migrated root has a symlink and takes neither branch.
if [ -d "$build_root/out" ] && [ ! -L "$build_root/out" ]; then
    if [ -e "$build_root/out-erofs" ]; then
        echo "compose: $build_root/out is a directory and $build_root/out-erofs" \
             "already exists, so the migration to symmetric output names cannot" \
             "tell which is current. Remove whichever is stale and re-run." >&2
        exit 1
    fi
    mv "$build_root/out" "$build_root/out-erofs"
fi

# The last value restated from input-set.toml. The mkosi commit, the tools-tree
# base image and its package list used to be restated here too, because sh
# cannot validate TOML without a dependency this slice has not declared; they
# moved to buildroot.py, which reads the declaration. This one remains because
# retain-repository.py takes the URL as an argument rather than reading it, and
# retention is a separate concern from provisioning the build root.
repository_url=https://dl.fedoraproject.org/pub/fedora/linux/releases/44/Everything/x86_64/os

# Acquisition reads input-set.toml itself, through acquire-overlay.py, so these
# digests are the declared ones rather than a copy. Where a helper can read the
# declaration, it reads it.
overlay_dir="$build_root/inputs/overlay"

# Synthetic signing material, generated by buildroot.py: all four subjects of
# the declaration's table in one owner rather than three here and the platform
# key in enroll-fixture.sh. Never enrolled outside a disposable VM, destroyed
# with the build root.
keys_dir="$build_root/keys"

mkdir -p "$build_root" "$keys_dir" "$out_dir"

if [ ! -e "$build_root/out" ]; then
    ln -s out-erofs "$build_root/out"
fi

# Composition either produces the artifact it was asked for, or it fails.
#
# mkosi declines to rebuild an existing output -- "Output path ... exists
# already. (Use --force to rebuild.)" -- and exits 0. Everything after it then
# runs against the previous artifact and the script reports success having
# rebuilt nothing. Measured 2026-08-16: a rebuild intended to prove a deleted
# file was gone was a no-op, and verifying against its output would have
# reported a pass from the artifact the change was meant to alter.
#
# The existing mitigation is downstream and indirect: the verity certificate is
# copied unconditionally so that T3-SLICE-003 fails later. That makes the state
# visible to validation but leaves this script's own exit code meaningless, and
# a build tool whose exit code does not mean "built" is one every caller has to
# work around. Refusing here is the direct statement.
# Only a build can be a silent no-op. `summary`, `clean` and the rest pass
# through this script to mkosi and produce no artifact, so refusing them for an
# artifact that already exists would break the read-only verbs -- measured
# 2026-08-16, the first form of this guard exited 1 on `compose.sh summary`.
# Lines below already carry the same distinction, testing for a manifest before
# retention and before the fixture.
for argument in "$@"; do
    case "$argument" in
    --force | -f | -ff) force=yes ;;
    summary | clean | shell | boot | vm | qemu | ssh | journalctl | \
    coredumpctl | serve | burn | sysupdate | sandbox | documentation | \
    genkey | dependencies | completion | cat-config | box) verb=other ;;
    esac
done
if [ -e "$out_dir/neutrinos-slice.raw" ] &&
   [ "${force:-no}" = no ] && [ "${verb:-build}" = build ]; then
    echo "compose: $out_dir/neutrinos-slice.raw exists and --force was not" \
         "passed; mkosi would decline to rebuild it and this script would" \
         "report success without composing anything. Pass --force to rebuild," \
         "or remove the output directory." >&2
    exit 1
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
confext_staging="$build_root/confext-staging"
confext_out="$build_root/confext"

# Both signings and the staging tree, in fixtures.py. NEUTRINOS_SKIP_CONFEXT
# keeps its name and its meaning: measure-build-time.py sets it,
# retain-artifact-digests.py reports on it, and the artifact-parameter and
# format-measurement records cite it as a condition of measurements already
# taken.
if [ -z "${NEUTRINOS_SKIP_CONFEXT:-}" ]; then
    python3 "$root/fixtures.py" --build-root="$build_root"
fi

# Prepended to the caller's arguments so `--force` or `summary` still reaches
# mkosi. Each variant moves exactly one thing; anything else would make a task
# 10 failure unattributable.
#
# The seed is a declared literal and deliberately not the composition's Seed=.
# Deriving it would make the relationship between two artifacts an algorithm
# nobody wrote down.
variant_seed=8c1e5b47-2d93-4f60-a1e8-7d4c2f0b93a5

case "$variant" in
    content)
        set -- --extra-tree="$root/composition/mkosi.extra.variant-content" "$@"
        ;;
    seed)
        set -- --seed="$variant_seed" "$@"
        ;;
    state)
        # A second definitions directory rather than partitions added to the
        # shared composition/mkosi.repart/. RepartDirectories= is a list and the
        # CLI appends to it, so repart receives the shared directory, the arm
        # directory and this one; nothing in the shared set is edited, so a
        # `primary` build is byte-identical to what it produced before this
        # variant existed.
        set -- --repart-directory="$root/composition/state-partitions" \
               --extra-tree="$root/composition/mkosi.extra.state" "$@"
        ;;
    session)
        # State plus a graphical session. It includes the state variant's
        # partitions and mount units rather than repeating them, because the
        # session needs a home volume to put a home directory on: a session
        # composed without one works exactly once, which is the failure shape
        # T4-STATE-001 exists to catch.
        #
        # The package list comes from the role's capability declaration, which
        # is what makes that file a mechanism rather than a description. A
        # package no capability declares does not enter the image, and a
        # capability whose packages change moves the artifact.
        #
        # Only the `session` stage. The `workflow` stage is daily-use capability
        # that follows once a session exists, and pulling it in now would make
        # the first graphical boot depend on twenty packages whose failures are
        # unrelated to whether a session comes up.
        for package in $(python3 "$root/role-packages.py" --role="$role" --stage=session); do
            set -- --package="$package" "$@"
        done
        set -- --repart-directory="$root/composition/state-partitions" \
               --extra-tree="$root/composition/mkosi.extra.state" \
               --extra-tree="$root/composition/mkosi.extra.session" "$@"
        ;;
esac

cd "$root/composition"
# --initrd is passed here rather than declared because mkosi has no specifier
# for the output directory: %C, %P, %D, %F, %I is the whole set. Setting it
# makes want_default_initrd() return False, so the composition owns an initrd
# instead of adding to a synthesized one -- PLN-0002-05's ruling of 2026-08-12,
# and why mkosi.finalize.d/10-initrd-etc-factory no longer exists.
PYTHONPATH="$build_root/mkosi" python3 -m mkosi \
    --tools-tree="$build_root/tools" \
    --package-cache-directory="$build_root/pkgcache" \
    --package-directory="$overlay_dir/systemd-261" \
    --extra-tree="$confext_staging" \
    --repart-directory="$root/composition/mkosi.repart.$arm" \
    --output-directory="$out_dir" \
    --initrd="$out_dir/initrd" \
    --secure-boot-key="$keys_dir/secureboot.key" \
    --secure-boot-certificate="$keys_dir/secureboot.crt" \
    --verity-key="$keys_dir/verity.key" \
    --verity-certificate="$keys_dir/verity.crt" \
    "$@"

# Every run, whether or not mkosi rebuilt anything. mkosi declines to rebuild
# when the output exists, so regenerating signing material and re-running
# otherwise leaves a new key beside an artifact carrying the old signature --
# measured 2026-08-12, and it read as success. Copying unconditionally makes
# that state visible: T3-SLICE-003 fails because the bytes it searches for are
# no longer inside the image.
if [ -f "$keys_dir/verity.crt" ]; then
    cp "$keys_dir/verity.crt" "$out_dir/neutrinos-slice.verity.crt"
fi

# Retention is a build step, not something to remember afterwards; without it
# the declared repository is a URL whose bytes survive only as a side effect of
# the last build's cache, which is what made PLN-0001-07's first offline
# rebuild impossible. It fails closed on a package the declared repository does
# not contain, so it is also the check that nothing undeclared entered the
# cache.
#
# Only when a build produced an image: `clean`, `--help` and the other verbs
# have nothing to retain, and fetching metadata for them would put a network
# dependency on operations that have none.
if [ -f "$out_dir/neutrinos-slice.manifest" ]; then
    python3 "$root/retain-repository.py" \
        --repository="$repository_url" \
        --cache="$build_root/pkgcache" \
        --overlay="$overlay_dir" \
        --destination="$build_root/inputs/repository"
fi

# The T4-CONFEXT-001 fixture. After retention, and that ordering is a fix: this
# step failed on its first real run, `set -eu` aborted the script, and
# retention silently did not happen. A step added for a new check must not take
# out an established one.
#
# It needs an image-signing certificate to keep in `db` beside the verity
# signer, since enrolling without one produces a machine whose firmware refuses
# its own UKI. This script generates that certificate, so the else branch is
# the damaged-build-root case. It reports and continues rather than failing the
# composition: the fixture's absence blocks T4-CONFEXT-001, which is the same
# signal in the place that reads it.
if [ -f "$out_dir/neutrinos-slice.manifest" ] && [ -z "${NEUTRINOS_SKIP_CONFEXT:-}" ]; then
    if [ -f "$keys_dir/secureboot.crt" ]; then
        sh "$root/enroll-fixture.sh"
        cp "$confext_out/neutrinos-network.raw" "$build_root/fixture/confext-enrolled.raw"
        cp "$confext_out-unenrolled/neutrinos-network.raw" \
            "$build_root/fixture/confext-unenrolled.raw"
    else
        echo "compose: no image-signing certificate at $keys_dir/secureboot.crt," \
             "so the T4-CONFEXT-001 fixture was not built. This script generates" \
             "that certificate, so its absence means the build root is damaged" \
             "rather than incomplete." >&2
    fi
fi
