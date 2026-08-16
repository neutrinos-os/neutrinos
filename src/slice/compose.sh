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
    primary|content|seed|state) ;;
    *)
        echo "compose: no variant '$variant'; expected primary, content, seed or state" >&2
        exit 1
        ;;
esac

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

# Duplicates input-set.toml deliberately: sh cannot validate TOML without a
# dependency this slice has not declared. PLN-0001-05 registers the check that
# the two agree; until then a drift is unguarded.
mkosi_repository=https://github.com/systemd/mkosi
# Paired with the systemd-261 OBS overlay in input-set.toml -- the same
# 2026-08-11 snapshot, twenty minutes apart. They move together or not at all.
mkosi_commit=d5ff0d0d9884cc4e06900057e2ad44adee29cb8e
tools_image=registry.fedoraproject.org/fedora@sha256:93f227979b6ef8395cde2a38dee260ef4cbecaab7668ee45d97960aba910e918
repository_url=https://dl.fedoraproject.org/pub/fedora/linux/releases/44/Everything/x86_64/os

# The tools tree supplies the package manager that resolves the image, so it is
# a composition input and is built from the same frozen repository. The host's
# rolling packages here would be an undeclared, moving input in the position
# that decides what the image contains.
tools_packages="distribution-gpg-keys cpio systemd systemd-ukify systemd-boot
                dosfstools mtools e2fsprogs erofs-utils btrfs-progs
                squashfs-tools tar zstd xz python3 createrepo_c"

# Acquisition reads input-set.toml itself, through acquire-overlay.py, so these
# digests are the declared ones rather than a copy. Where a helper can read the
# declaration, it reads it.
overlay_dir="$build_root/inputs/overlay"

# Synthetic verity signing material for the confext. Never enrolled outside a
# disposable VM, destroyed with the build root; PLN-0002 forbids production
# material and needs none, since what is under test is whether the mechanism
# binds, not whose key signs.
#
# Every generation below is guarded on the certificate, not the key: openssl
# writes the key first, and an interrupted run otherwise leaves a key with no
# certificate that a key-guarded check skips forever. Observed in the
# PLN-0002-01 spike.
keys_dir="$build_root/keys"

mkdir -p "$build_root" "$keys_dir" "$out_dir"

if [ ! -e "$build_root/out" ]; then
    ln -s out-erofs "$build_root/out"
fi

# One verity subject across every build root: PLN-0002 amendment 4, declared in
# docs/project/artifact-parameter-declaration.md. The subject is what `db` and
# /usr/lib/verity.d carry, so two subjects means a fixture and an artifact
# disagreeing about who the trusted signer is.
verity_cn="NeutrinOS verity, synthetic"

# Checked against the subject rather than the file: with the guards below,
# changing the string alone would be a silent no-op on an existing build root,
# reading as satisfied while every artifact kept the old signer. Fails rather
# than regenerating, which would change the signature of artifacts already
# measured.
if [ -f "$keys_dir/verity.crt" ] &&
   [ "$(openssl x509 -noout -subject -in "$keys_dir/verity.crt")" != "subject=CN=$verity_cn" ]; then
    echo "compose: $keys_dir/verity.crt has subject" \
         "$(openssl x509 -noout -subject -in "$keys_dir/verity.crt")," \
         "and PLN-0002 amendment 4 declares 'subject=CN=$verity_cn'." \
         "Artifacts signed by the old key keep it until they are rebuilt." \
         "To adopt the declared subject:" \
         "rm -f $keys_dir/verity.key $keys_dir/verity.crt $keys_dir/verity.der" >&2
    exit 1
fi

if [ ! -f "$keys_dir/verity.crt" ]; then
    openssl req -x509 -newkey rsa:2048 -nodes -days 30 \
        -subj "/CN=$verity_cn/" \
        -keyout "$keys_dir/verity.key" -out "$keys_dir/verity.crt"
fi

# Valid material, wrong signer. PLN-0002-10 must tell a substitution failure
# from a signature failure, which one key cannot do. Enrolled in nothing.
# Generated from here rather than from task 10 because both keys must predate
# the artifacts they sign. Owner ruling 2026-08-11.
if [ ! -f "$keys_dir/verity-wrong.crt" ]; then
    openssl req -x509 -newkey rsa:2048 -nodes -days 30 \
        -subj "/CN=NeutrinOS slice verity, synthetic, unenrolled/" \
        -keyout "$keys_dir/verity-wrong.key" -out "$keys_dir/verity-wrong.crt"
fi

# The image signer: third of the three distinct subjects in the declaration's
# signing-material table. Distinctness is load-bearing -- T4-CONFEXT-001's whole
# content is which signer `db` holds, and a shared subject would make enrolling
# one enroll the other. What `SecureBoot=` signs the UKI with.
if [ ! -f "$keys_dir/secureboot.crt" ]; then
    openssl req -x509 -newkey rsa:2048 -nodes -days 30 \
        -subj "/CN=NeutrinOS image, synthetic/" \
        -keyout "$keys_dir/secureboot.key" -out "$keys_dir/secureboot.crt"
fi

# UEFI db takes DER and openssl emits PEM. All three, so the negative cases are
# enrollable too.
for k in verity verity-wrong secureboot; do
    if [ ! -f "$keys_dir/$k.der" ]; then
        openssl x509 -outform DER -in "$keys_dir/$k.crt" -out "$keys_dir/$k.der"
    fi
done

if [ ! -d "$build_root/mkosi" ]; then
    git clone --quiet --filter=blob:none "$mkosi_repository" "$build_root/mkosi"
fi
git -C "$build_root/mkosi" checkout --quiet "$mkosi_commit"

if [ ! -d "$build_root/tools" ]; then
    # shellcheck disable=SC2086 -- word splitting of the package list is intended
    container=$(podman create --net=host "$tools_image" \
        dnf5 -y --repofrompath="pin,$repository_url" --repo=pin --nogpgcheck \
        install $tools_packages)
    podman start --attach "$container" >"$build_root/tools-build.log" 2>&1
    podman export "$container" >"$build_root/tools.tar"
    podman rm --force "$container" >/dev/null
    mkdir -p "$build_root/tools"
    tar -C "$build_root/tools" -xf "$build_root/tools.tar"
    # mkosi refuses a tools tree without this path; the sandbox supplies the
    # contents at build time.
    touch "$build_root/tools/etc/resolv.conf"
fi

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

if [ -z "${NEUTRINOS_SKIP_CONFEXT:-}" ]; then
    mkdir -p "$confext_out"
    (
        cd "$root/confext/neutrinos-network"
        PYTHONPATH="$build_root/mkosi" python3 -m mkosi \
            --tools-tree="$build_root/tools" \
            --verity-key="$keys_dir/verity.key" \
            --verity-certificate="$keys_dir/verity.crt" \
            --output-directory="$confext_out" \
            --force build
    )

    rm -rf "$confext_staging"
    mkdir -p "$confext_staging/usr/lib/confexts" "$confext_staging/usr/lib/verity.d"
    cp "$confext_out/neutrinos-network.raw" "$confext_staging/usr/lib/confexts/"
    cp "$keys_dir/verity.crt" "$confext_staging/usr/lib/verity.d/neutrinos-synthetic.crt"

    # The same tree, signed by the unenrolled key. T4-CONFEXT-001's comparison
    # means something only if the signer is the only difference; a second image
    # from a second source could be refused for being the wrong image. Not
    # staged into the artifact -- it is delivered from outside, as a
    # substitution would be.
    (
        cd "$root/confext/neutrinos-network"
        PYTHONPATH="$build_root/mkosi" python3 -m mkosi \
            --tools-tree="$build_root/tools" \
            --verity-key="$keys_dir/verity-wrong.key" \
            --verity-certificate="$keys_dir/verity-wrong.crt" \
            --output-directory="$confext_out-unenrolled" \
            --force build
    )
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
