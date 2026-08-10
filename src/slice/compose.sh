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
                squashfs-tools tar zstd xz python3"

mkdir -p "$build_root"

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

cd "$root/composition"
PYTHONPATH="$build_root/mkosi" exec python3 -m mkosi \
    --tools-tree="$build_root/tools" \
    --output-directory="$build_root/out" \
    "$@"
