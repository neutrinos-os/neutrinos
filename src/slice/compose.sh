#!/bin/sh
# Compose the PLN-0001 reference-VM slice deployment set.
#
# Acquisition is bounded by declared inputs: the pinned mkosi revision, the
# pinned tools-tree base image digest, and the single frozen Fedora repository
# named in input-set.toml. Nothing here resolves a floating reference.
#
# This script mutates no host state. It writes only under the build root, which
# is outside the checkout, and it requires no root and no package installation
# on the build host. If a step here starts needing either, that is a boundary
# crossing and a stop condition, not a prerequisite to satisfy.
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build_root=${NEUTRINOS_SLICE_BUILD_ROOT:-${XDG_CACHE_HOME:-$HOME/.cache}/neutrinos/slice}

# Declared inputs. These duplicate input-set.toml deliberately: a shell script
# cannot validate TOML without adding a dependency this slice has not declared,
# so the values are repeated and PLN-0001-05 registers the check that they
# agree. Until then a drift between the two is possible and unguarded.
mkosi_repository=https://github.com/systemd/mkosi
mkosi_commit=84af20892b61c8e177e391f997ded8b4cb5514f2
tools_image=registry.fedoraproject.org/fedora@sha256:93f227979b6ef8395cde2a38dee260ef4cbecaab7668ee45d97960aba910e918
repository_url=https://dl.fedoraproject.org/pub/fedora/linux/releases/44/Everything/x86_64/os

# The tools tree supplies the package manager that resolves the image. It is
# therefore a composition input, and it is built from the same frozen
# repository as the image rather than from the build host's own distribution.
# Using the host's rolling packages here would put an undeclared, moving input
# in the position that decides what the image contains.
tools_packages="distribution-gpg-keys cpio systemd systemd-ukify systemd-boot
                dosfstools mtools e2fsprogs erofs-utils btrfs-progs
                squashfs-tools tar zstd xz python3 createrepo_c"

# The declared package overlay. Note what is *not* duplicated here: acquisition
# reads input-set.toml itself, through acquire-overlay.py, so the digests it
# verifies against are the declared ones rather than a copy of them. The values
# above are repeated because a shell script cannot read TOML without a
# dependency this slice has not declared; a Python helper can, and where that is
# possible the declaration should be read rather than restated.
overlay_dir="$build_root/inputs/overlay"

# Synthetic verity signing material for the configuration extension. Never
# enrolled anywhere, never a trust anchor, and destroyed with the build root.
# PLN-0002's boundary forbids production signing material and this needs none:
# what is under test is whether the mechanism binds, not whose key signs.
#
# Guarded on the certificate rather than the key, because openssl writes the key
# first and an interrupted run otherwise leaves a key with no certificate that a
# key-guarded check skips forever. Observed in the PLN-0002-01 spike, not
# hypothesised.
keys_dir="$build_root/keys"

mkdir -p "$build_root" "$keys_dir"

if [ ! -f "$keys_dir/verity.crt" ]; then
    openssl req -x509 -newkey rsa:2048 -nodes -days 30 \
        -subj "/CN=NeutrinOS slice verity, synthetic/" \
        -keyout "$keys_dir/verity.key" -out "$keys_dir/verity.crt"
fi

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
    # mkosi refuses a tools tree without this path; the file's contents are
    # supplied by the sandbox at build time.
    touch "$build_root/tools/etc/resolv.conf"
fi

# The package cache lives inside this build root, not in the user's shared mkosi
# cache. PLN-0001-07 found 58 RPMs in the shared cache that the declared
# repository does not contain -- fc43 packages and `updates` builds left behind
# by PLN-0001-06's injected faults. Nothing consumed them, but a cache shared
# across fault injection is not a retention store, and a build that resolves
# from one cannot say where its inputs came from.
# Before the build, not after: an overlay that cannot be verified must stop the
# composition rather than be discovered in the artifact.
python3 "$root/acquire-overlay.py" --destination="$overlay_dir"

# The configuration extension, built before the artifact that carries it.
#
# PLN-0002-03a. It resolves no repository -- a confext carries configuration and
# has no package closure -- so it builds whether or not the declared repository
# is reachable, and it does not consume the overlay or the package cache.
#
# Delivery is a **declared fixture**, not a decision: the signed image is staged
# into /usr/lib/confexts inside the authenticated artifact, per the owner ruling
# of 2026-08-11 on finding 1 option D. That fuses release and configuration,
# which is what DES-0005's amendment separates. PLN-0002-03b owns the design.
#
# The certificate travels beside it in /usr/lib/verity.d. Note what that does
# and does not buy: it is where systemd looks, and it is **not** sufficient for
# the signature to be enforced. Measured on 2026-08-11 -- dm-verity signature
# validation resolves the key through the kernel keyring, a synthetic key is in
# no keyring, the kernel returns -ENOKEY, and systemd falls back to unsigned
# verity and merges anyway. See docs/project/etc-path-carve.md.
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
fi

cd "$root/composition"
PYTHONPATH="$build_root/mkosi" python3 -m mkosi \
    --tools-tree="$build_root/tools" \
    --package-cache-directory="$build_root/pkgcache" \
    --package-directory="$overlay_dir/systemd-261" \
    --extra-tree="$confext_staging" \
    --output-directory="$build_root/out" \
    "$@"

# Retention is a build step, not something to remember afterwards. Without it
# the declared repository is a URL and the bytes behind it survive only as a
# side effect of the last build's cache, which is what made PLN-0001-07's first
# offline rebuild impossible. Retention fails closed on a package the declared
# repository does not contain, so this step is also the check that nothing
# undeclared entered the cache.
#
# It runs only when a build produced an image: `mkosi clean`, `--help`, and the
# other verbs have nothing to retain, and fetching metadata for them would put
# a network dependency on operations that have none.
if [ -f "$build_root/out/neutrinos-slice.manifest" ]; then
    python3 "$root/retain-repository.py" \
        --repository="$repository_url" \
        --cache="$build_root/pkgcache" \
        --overlay="$overlay_dir" \
        --destination="$build_root/inputs/repository"
fi
