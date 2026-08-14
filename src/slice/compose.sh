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

# The arm under test: the value of Format= on the /usr partition, which is the
# one variable PLN-0002 exists to measure. Everything else about the two arms is
# held identical by construction -- same tools tree, same package closure, same
# initrd, same verity pairing, same signing material -- so that a difference in
# any C-007 criterion is attributable to the filesystem and not to the build.
#
# Selected here rather than by editing a file, because editing a file to switch
# arms means the arm is whatever the working tree happened to say at build time
# and no artifact can be traced back to a declared value.
#
# Only the arm directory is passed below. The shared composition/mkosi.repart/
# is picked up by mkosi's own path suffix and the CLI value **appends** to it --
# verified against `mkosi summary`, which reported both directories, and not
# assumed. Passing the shared one explicitly as well listed it twice and would
# have handed systemd-repart the same --definitions path twice.
arm=${NEUTRINOS_SLICE_ARM:-erofs}

if [ ! -d "$root/composition/mkosi.repart.$arm" ]; then
    echo "compose: no arm '$arm'; expected a partition definition directory at" \
         "$root/composition/mkosi.repart.$arm" >&2
    exit 1
fi

# The EROFS arm keeps the historic output path and the ext4 arm gets its own,
# and that asymmetry is deliberate and temporary. `out` is what every registered
# check reads through NEUTRINOS_SLICE_ARTIFACT and what the recorded artifact
# digests refer to; renaming it to `out-erofs` now would invalidate those
# records to buy a symmetry that nothing yet consumes. PLN-0002-06 builds all
# four artifacts as first-class peers and is where the naming should become
# symmetric.
out_dir="$build_root/out"
if [ "$arm" != erofs ]; then
    out_dir="$build_root/out-$arm"
fi

# Declared inputs. These duplicate input-set.toml deliberately: a shell script
# cannot validate TOML without adding a dependency this slice has not declared,
# so the values are repeated and PLN-0001-05 registers the check that they
# agree. Until then a drift between the two is possible and unguarded.
mkosi_repository=https://github.com/systemd/mkosi
# Paired with the systemd-261 OBS overlay in input-set.toml: both are the
# 2026-08-11 snapshot, twenty minutes apart. They move together or not at all.
mkosi_commit=d5ff0d0d9884cc4e06900057e2ad44adee29cb8e
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

# One subject for the verity signer across every build root: PLN-0002
# amendment 4, declared in docs/project/artifact-parameter-declaration.md. The
# subject is what is enrolled in `db` and what sits in /usr/lib/verity.d, so two
# build roots using two subjects means a fixture and an artifact that disagree
# about who the trusted signer is. It looked cosmetic while the build roots were
# independent and stopped being cosmetic when enforcement became real.
verity_cn="NeutrinOS verity, synthetic"

# Checked against the subject, not against the file. Every generation below is
# guarded on the certificate existing, so changing the subject string alone
# would be a silent no-op on any build root that already has keys -- the
# declared parameter would read as satisfied while every artifact kept the old
# signer. This fails instead, because regenerating on its own initiative would
# silently change the root hash signature of artifacts already measured.
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

# The second key: valid material, wrong signer. PLN-0002-10 must distinguish a
# substitution failure from a signature failure, and it cannot do that with only
# one key -- a rejection could mean "this is not the artifact" or "this signature
# does not verify" and the test would not say which. So this one is generated in
# the same shape as the first and enrolled in nothing.
#
# It exists from now rather than from task 10 because both keys have to predate
# the artifacts they sign, and because a key introduced later is a parameter
# introduced later. Owner ruling 2026-08-11.
if [ ! -f "$keys_dir/verity-wrong.crt" ]; then
    openssl req -x509 -newkey rsa:2048 -nodes -days 30 \
        -subj "/CN=NeutrinOS slice verity, synthetic, unenrolled/" \
        -keyout "$keys_dir/verity-wrong.key" -out "$keys_dir/verity-wrong.crt"
fi

# The image signer. PLN-0002-06, and the third of the three subjects the
# declaration's signing-material table keeps distinct.
#
# Distinct is load-bearing rather than tidy. T4-CONFEXT-001's entire content is
# which signer the disposable VM's `db` holds; if the image signer and the
# verity signer shared a subject, enrolling one would enroll the other and the
# measurement would stop discriminating. The same applies to the unenrolled
# verity key above.
#
# This is what `SecureBoot=` in the composition signs the UKI with, and it is
# also the certificate compose.sh has been reporting as absent every run since
# T4-CONFEXT-001 was registered: the slice-side fixture could not be built
# without it, so that check has been running against the PLN-0002-01 spike's
# artifact. From here it can be built against the slice's own.
#
# Synthetic, generated into the build root, never enrolled outside a disposable
# VM, destroyed with the build root. PLN-0002's boundary forbids production
# signing material and this needs none.
if [ ! -f "$keys_dir/secureboot.crt" ]; then
    openssl req -x509 -newkey rsa:2048 -nodes -days 30 \
        -subj "/CN=NeutrinOS image, synthetic/" \
        -keyout "$keys_dir/secureboot.key" -out "$keys_dir/secureboot.crt"
fi

# DER for firmware. UEFI db takes DER, openssl emitted PEM, and the enrollment
# path is the one place the distinction bites. All three are converted so that
# the negative cases are enrollable too if task 10 needs them to be.
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

    # The same tree, signed by the unenrolled key. T4-CONFEXT-001 compares the
    # two, and the comparison only means something if the signer is the only
    # difference: a second image built from a second source could be refused
    # for being the wrong image rather than for being signed by the wrong
    # authority, which is precisely the confusion the second key exists to
    # remove.
    #
    # It is not staged into the artifact. It exists to be delivered from
    # outside, as a substitution would be.
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

cd "$root/composition"
# --initrd points at the `initrd` subimage's output, and it is passed here
# rather than declared in mkosi.conf because mkosi has no specifier for the
# output directory: %C, %P, %D, %F and %I are the whole set, and none of them
# names it. The subimage writes to the same --output-directory, so this is that
# path plus the subimage's Output= name.
#
# Setting it is what makes want_default_initrd() return False, so the
# composition stops adding to mkosi's synthesized initrd and starts owning one.
# That is PLN-0002-05's ruling of 2026-08-12 and the reason
# mkosi.finalize.d/10-initrd-etc-factory no longer exists.
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

# Publish the verity signer beside the artifact, every run, whether or not mkosi
# rebuilt anything.
#
# "Every run" is the whole point. mkosi declines to rebuild when the output
# exists, so regenerating the signing material and re-running this script leaves
# a new key beside an artifact still carrying the old signature -- measured
# 2026-08-12 while implementing amendment 4, and it would have read as success
# because the build root's certificate was correct. Copying unconditionally
# makes that state visible instead: the published certificate moves, the
# artifact does not, and T3-SLICE-003 fails because the bytes it searches for
# are no longer inside the image.
if [ -f "$keys_dir/verity.crt" ]; then
    cp "$keys_dir/verity.crt" "$out_dir/neutrinos-slice.verity.crt"
fi

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
if [ -f "$out_dir/neutrinos-slice.manifest" ]; then
    python3 "$root/retain-repository.py" \
        --repository="$repository_url" \
        --cache="$build_root/pkgcache" \
        --overlay="$overlay_dir" \
        --destination="$build_root/inputs/repository"
fi

# The signature-enforcement fixture for T4-CONFEXT-001.
#
# After retention, not before, and that ordering is a fix rather than a
# preference: this step failed on its first real run, `set -eu` aborted the
# script, and retention -- the thing that makes the next offline rebuild
# possible at all -- silently did not happen. A step added for a new check must
# not be able to take out an established one.
#
# It needs an image-signing certificate, and the slice composition has none:
# there is no `SecureBoot=` in the composition fixture, so the UKI is unsigned
# and there is nothing to keep in `db` alongside the verity signer. Enrolling
# anyway produces a machine whose firmware refuses its own UKI. That is
# PLN-0002-06's synthetically signed UKI arriving as a prerequisite, so this
# says so and continues rather than failing the composition.
#
# Saying so loudly is the point. The fixture's absence is not swallowed: it
# **blocks** T4-CONFEXT-001, which is the same signal in the place that reads
# it.
if [ -f "$out_dir/neutrinos-slice.manifest" ] && [ -z "${NEUTRINOS_SKIP_CONFEXT:-}" ]; then
    if [ -f "$keys_dir/secureboot.crt" ]; then
        sh "$root/enroll-fixture.sh"
        cp "$confext_out/neutrinos-network.raw" "$build_root/fixture/confext-enrolled.raw"
        cp "$confext_out-unenrolled/neutrinos-network.raw" \
            "$build_root/fixture/confext-unenrolled.raw"
    else
        echo "compose: no image-signing certificate at $keys_dir/secureboot.crt," \
             "so the T4-CONFEXT-001 fixture was not built. The slice composition" \
             "declares no SecureBoot=; a signed UKI is PLN-0002-06's output." >&2
    fi
fi
