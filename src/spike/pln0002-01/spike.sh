#!/bin/sh
# Drive the PLN-0002-01 early-boot spike.
#
# Same boundary as src/slice/compose.sh: no host mutation, no root, nothing
# written inside the checkout.
#
# It builds its own tools tree rather than reusing the slice's. The slice's is a
# declared input of PLN-0001, pinned in src/slice/input-set.toml, and injecting
# a package overlay needs createrepo_c, which that recipe does not contain.
# Adding it there would edit a completed plan's declared inputs to satisfy this
# one. So the recipe is copied, createrepo_c is added, and the two trees stay
# separate. The package cache is still shared: it is content-addressed by the
# frozen repository and holds no decision.
#
# What this adds over the slice is the systemd overlay. Fedora 44 ships
# systemd 259.5 and stays on the 259.x series, so the declared closure has no
# systemd-confext-sysroot.service -- the unit DES-0006 C-013 names as the
# early-boot answer, new in systemd 261. The overlay is the OBS system:systemd
# build for Fedora 44, injected as a local package directory so LocalMirror=
# keeps enforcing the single frozen repository by construction.
#
# The overlay is a nightly, replaced upstream in place. That is why this script
# retains the RPMs and records their digests: the retained copy is the exact
# input, and the URL is only where it came from.
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
slice_root=${NEUTRINOS_SLICE_BUILD_ROOT:-${XDG_CACHE_HOME:-$HOME/.cache}/neutrinos/slice}
build_root=${NEUTRINOS_SPIKE_BUILD_ROOT:-${XDG_CACHE_HOME:-$HOME/.cache}/neutrinos/pln0002}

overlay_base=https://download.opensuse.org/repositories/system:/systemd/Fedora_44/x86_64
overlay_version=261.999+1208+g827144298-4747.1
overlay_packages="systemd systemd-boot systemd-libs systemd-shared systemd-sysusers systemd-udev"

overlay_dir="$build_root/inputs/systemd261"
keys_dir="$build_root/keys"
# Overridable so the fault variants in faults.sh build beside the good artifact
# rather than replacing it: a fault run that clobbers the reference is a fault
# run with nothing to compare against.
out_dir=${NEUTRINOS_SPIKE_OUT:-$build_root/out}

if [ ! -d "$slice_root/mkosi" ]; then
    echo "spike: no mkosi checkout at $slice_root/mkosi; run src/slice/compose.sh first" >&2
    exit 1
fi

# The slice's tools-tree recipe verbatim, plus createrepo_c. mkosi needs it to
# turn --package-directory into a local repository, and without it the build
# stops after syncing metadata with "createrepo_c not found."
tools_image=registry.fedoraproject.org/fedora@sha256:93f227979b6ef8395cde2a38dee260ef4cbecaab7668ee45d97960aba910e918
repository_url=https://dl.fedoraproject.org/pub/fedora/linux/releases/44/Everything/x86_64/os
tools_packages="distribution-gpg-keys cpio systemd systemd-ukify systemd-boot
                dosfstools mtools e2fsprogs erofs-utils btrfs-progs
                squashfs-tools tar zstd xz python3 createrepo_c"

if [ ! -d "$build_root/tools" ]; then
    mkdir -p "$build_root"
    # shellcheck disable=SC2086 -- word splitting of the package list is intended
    container=$(podman create --net=host "$tools_image" \
        dnf5 -y --repofrompath="pin,$repository_url" --repo=pin --nogpgcheck \
        install $tools_packages)
    podman start --attach "$container" >"$build_root/tools-build.log" 2>&1
    podman export "$container" >"$build_root/tools.tar"
    podman rm --force "$container" >/dev/null
    mkdir -p "$build_root/tools"
    tar -C "$build_root/tools" -xf "$build_root/tools.tar"
    touch "$build_root/tools/etc/resolv.conf"
fi

mkdir -p "$overlay_dir" "$keys_dir" "$out_dir"

# Retention before use. A missing package is a stop condition, not something to
# work around by reaching for a different build: the version string names an
# exact upstream commit and a different nightly is a different input.
for package in $overlay_packages; do
    file="$package-$overlay_version.x86_64.rpm"
    if [ ! -s "$overlay_dir/$file" ]; then
        curl -sSL --retry 3 --max-time 300 -o "$overlay_dir/$file" "$overlay_base/$file"
    fi
done

# The digest record is the declaration this spike has instead of a schema. It
# is written every run and compared by eye against the previous one; PLN-0002-02
# is where the overlay becomes a declared input with a check behind it.
(cd "$overlay_dir" && sha256sum ./*.rpm >"$build_root/inputs/systemd261.sha256")

# Synthetic signing material. A CommonName is capped at 64 characters, so the
# subject stays short and openssl's stderr is not discarded: the first version
# of this script hid a "string too long" failure behind 2>/dev/null and looked
# like it exited for no reason.
#
# Synthetic signing material. Regenerated only when absent, so a rebuild does
# not silently change the root hash signature and make two artifacts look
# different for a reason that has nothing to do with their content.
# Guarded on the certificate, not the key: openssl writes the key first, so an
# interrupted run leaves a key with no certificate and a key-guarded check
# skips regeneration forever. Observed, not hypothetical.
if [ ! -f "$keys_dir/secureboot.crt" ]; then
    openssl req -x509 -newkey rsa:2048 -nodes -days 30 \
        -subj "/CN=NeutrinOS PLN-0002-01 spike, synthetic/" \
        -keyout "$keys_dir/secureboot.key" -out "$keys_dir/secureboot.crt"
fi
if [ ! -f "$keys_dir/verity.crt" ]; then
    openssl req -x509 -newkey rsa:2048 -nodes -days 30 \
        -subj "/CN=NeutrinOS PLN-0002-01 spike verity, synthetic/" \
        -keyout "$keys_dir/verity.key" -out "$keys_dir/verity.crt"
fi

cd "$root"
PYTHONPATH="$slice_root/mkosi" python3 -m mkosi \
    --tools-tree="$build_root/tools" \
    --package-cache-directory="$slice_root/pkgcache" \
    --package-directory="$overlay_dir" \
    --secure-boot-key="$keys_dir/secureboot.key" \
    --secure-boot-certificate="$keys_dir/secureboot.crt" \
    --verity-key="$keys_dir/verity.key" \
    --verity-certificate="$keys_dir/verity.crt" \
    --output-directory="$out_dir" \
    "$@"
