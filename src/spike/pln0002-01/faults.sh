#!/bin/sh
# Induce the three failures PLN-0002-01 owes the rest of PLN-0002.
#
# PR-0030 C-009 made failure capture task 01's job so that later tasks are not
# inventing diagnostics while something is already broken. The requirement is
# specific: the diagnostics must *distinguish* a missing filesystem driver from
# a root-hash mismatch from a refused confext. Three failures that all print
# "failed to mount" would satisfy the letter and none of the intent.
#
# Each fault is one deviation from the reference artifact and nothing else.
#
#   hash-mismatch  a single byte flipped inside the authenticated /usr, with the
#                  UKI, root hash, and signature all left correct
#   no-modules     the modules initrd withheld, so dm-verity cannot be set up,
#                  with the artifact itself byte-for-byte valid
#   bad-confext    the confext's extension-release naming a base it does not
#                  match, with everything else intact
#
# Results are written per fault and read afterwards. A fault that fails to fail
# is the interesting outcome, as PLN-0001-06 found when its seventh injection
# built a complete artifact from an undeclared repository.
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build_root=${NEUTRINOS_SPIKE_BUILD_ROOT:-${XDG_CACHE_HOME:-$HOME/.cache}/neutrinos/pln0002}
fault=${1:?usage: faults.sh hash-mismatch|no-modules|bad-confext}

faults_dir="$build_root/faults/$fault"
rm -rf "$faults_dir"
mkdir -p "$faults_dir"

case "$fault" in
hash-mismatch)
    # The /usr partition starts at sector 1050624 of a 512-byte-sector image.
    # One byte is flipped well inside it, so the corruption is in data verity
    # covers rather than in a header something else would reject first. That
    # distinction is the whole point: a header failure would be indistinguishable
    # from a format problem, and this must be attributable to the hash.
    cp --reflink=auto "$build_root/out/pln0002-01.raw" "$faults_dir/artifact.raw"
    python3 - "$faults_dir/artifact.raw" <<'PY'
import sys
offset = 1050624 * 512 + 4096 * 1000
with open(sys.argv[1], "r+b") as f:
    f.seek(offset)
    before = f.read(1)
    f.seek(offset)
    f.write(bytes([before[0] ^ 0xFF]))
print(f"flipped byte at {offset}: {before.hex()} -> {bytes([before[0] ^ 0xFF]).hex()}")
PY
    NEUTRINOS_SPIKE_RUN="$faults_dir/run" "$root/boot.sh" "$faults_dir/artifact.raw" || true
    ;;
no-modules)
    # The artifact is valid and correctly signed; only the initrd changes. This
    # separates "the machine cannot materialise the device" from "the machine
    # will not trust the content", which are the two failures most easily
    # confused when comparing two filesystem formats.
    #
    # This withholds the whole modules initrd rather than one driver. Excluding
    # EROFS specifically could not be expressed through mkosi v26's module
    # patterns: `-*erofs*` matched nothing, because the glob does not cross the
    # path separators in kernel/fs/erofs/erofs, and the bare basename `-erofs`
    # after `default` did not exclude it either -- in both cases the machine
    # booted clean, which is the failure mode where an injection looks like it
    # worked because nothing broke. The filesystem-driver-specific case is
    # therefore carried to PLN-0002-09, where per-format behaviour is measured.
    NEUTRINOS_SPIKE_OUT="$faults_dir/out" "$root/spike.sh" build --force \
        --kernel-modules-initrd=no
    NEUTRINOS_SPIKE_RUN="$faults_dir/run" "$root/boot.sh" "$faults_dir/out/pln0002-01.raw" || true
    ;;
bad-confext)
    # ID=debian against a Fedora base. The confext is otherwise well-formed and
    # sits in the same authenticated /usr as the reference, so a refusal here is
    # the base-compatibility guard SYS-123 requires and DES-0005's amendment
    # relies on, not a delivery or signature failure.
    tree="$faults_dir/extra/usr/lib/confexts/spike-in-usr/etc"
    mkdir -p "$tree/extension-release.d"
    printf 'ID=debian\nVERSION_ID=13\n' \
        >"$tree/extension-release.d/extension-release.spike-in-usr"
    printf 'origin=usr-lib-confexts-wrong-base\n' >"$tree/spike-in-usr.conf"
    NEUTRINOS_SPIKE_OUT="$faults_dir/out" "$root/spike.sh" build --force \
        --extra-tree="$faults_dir/extra"
    NEUTRINOS_SPIKE_RUN="$faults_dir/run" "$root/boot.sh" "$faults_dir/out/pln0002-01.raw" || true
    ;;
*)
    echo "faults: unknown fault $fault" >&2
    exit 1
    ;;
esac

echo "faults: $fault console at $faults_dir/run/console.log"
