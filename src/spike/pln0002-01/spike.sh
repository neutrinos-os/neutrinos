#!/bin/sh
# Drive the PLN-0002-01 early-boot spike.
#
# Same boundary as src/slice/compose.sh: no host mutation, no root, nothing
# written inside the checkout.
#
# It reuses the slice's tools tree. It did not always: the slice's is a declared
# input of PLN-0001, injecting a package overlay needs createrepo_c, and adding
# it to that declaration would have edited a completed plan's declared inputs to
# satisfy this one -- so the recipe was copied instead and the trees stayed
# separate. PLN-0002-02 then added createrepo_c to the declaration on its own
# merits, with its reason recorded in src/slice/input-set.toml, which spent the
# argument for a copy. See the tools-tree block below. The package cache was
# always shared: it is content-addressed by the frozen repository and holds no
# decision.
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

# Both the mkosi checkout and the tools tree come from the slice build root.
#
# This script used to build its own tools tree from a recipe it described as
# "the slice's recipe verbatim, plus createrepo_c". PLN-0002-02 added
# createrepo_c to the slice recipe, which removed the only stated difference,
# and the two were measured identical on 2026-08-12: the same 16293 entries,
# the same 234 package NEVRAs, and nine differing files that are all
# nondeterministic build metadata -- machine-id, the rpm and dnf databases,
# ldconfig's cache, the random seed, and a log. So two trees were duplication
# rather than independence. Owner ruling of 2026-08-12, question 9.
#
# Editing the apparatus of a completed spike is otherwise something this
# project does not do, and the guard that makes it admissible here is the one
# the ruling asked for: the artifact rebuilt through the slice tree is
# byte-identical to the retained one, so the recorded evidence is unchanged
# rather than assumed unchanged.
for required in mkosi tools; do
    if [ ! -d "$slice_root/$required" ]; then
        echo "spike: no $required at $slice_root/$required;" \
             "run src/slice/compose.sh first" >&2
        exit 1
    fi
done
tools_tree="$slice_root/tools"

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
# One subject for the verity signer across every build root: PLN-0002
# amendment 4, declared in docs/project/artifact-parameter-declaration.md, and
# the same string src/slice/compose.sh uses. Duplicated rather than shared
# because a shell script cannot read the declaration without a dependency
# neither script has; the guard below is what keeps the duplication honest.
#
# The keys already in this build root keep the spike's original subject, and
# nothing regenerates them here: the retained artifact is RES-0013's evidence
# and re-signing it would change the thing the evidence is about. So this guard
# fails a rebuild of the completed spike until the operator decides to adopt the
# declared subject, which is the correct order -- that decision changes an
# artifact's identity and is not one a build script should take on its own.
verity_cn="NeutrinOS verity, synthetic"

if [ -f "$keys_dir/verity.crt" ] &&
   [ "$(openssl x509 -noout -subject -in "$keys_dir/verity.crt")" != "subject=CN=$verity_cn" ]; then
    echo "spike: $keys_dir/verity.crt has subject" \
         "$(openssl x509 -noout -subject -in "$keys_dir/verity.crt")," \
         "and PLN-0002 amendment 4 declares 'subject=CN=$verity_cn'." \
         "The retained artifact was signed by the old key and keeps it." \
         "To rebuild this spike under the declared subject:" \
         "rm -f $keys_dir/verity.key $keys_dir/verity.crt $keys_dir/verity.der" >&2
    exit 1
fi

if [ ! -f "$keys_dir/verity.crt" ]; then
    openssl req -x509 -newkey rsa:2048 -nodes -days 30 \
        -subj "/CN=$verity_cn/" \
        -keyout "$keys_dir/verity.key" -out "$keys_dir/verity.crt"
fi

cd "$root"
PYTHONPATH="$slice_root/mkosi" python3 -m mkosi \
    --tools-tree="$tools_tree" \
    --package-cache-directory="$slice_root/pkgcache" \
    --package-directory="$overlay_dir" \
    --secure-boot-key="$keys_dir/secureboot.key" \
    --secure-boot-certificate="$keys_dir/secureboot.crt" \
    --verity-key="$keys_dir/verity.key" \
    --verity-certificate="$keys_dir/verity.crt" \
    --output-directory="$out_dir" \
    "$@"
