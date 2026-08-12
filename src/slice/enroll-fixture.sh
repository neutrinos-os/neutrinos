#!/bin/sh
# Build the signature-enforcement fixture for T4-CONFEXT-001.
#
# The check needs a machine whose firmware trusts the confext signer, and it
# needs the composed artifact to stay byte-identical, because T3-SLICE-001 and
# T4-SLICE-001 assert exactly that. So this never touches the artifact: it
# copies it and enrolls into the copy.
#
# Enrollment happens through the ESP rather than from inside the guest. A guest
# cannot do it -- efivarfs marks existing variables immutable, and the artifact
# carries neither chattr nor a Python to clear the flag with. What does work is
# systemd-boot's auto-enrollment: PK.auth, KEK.auth and db.auth under
# \loader\keys\auto are enrolled on a firmware in setup mode, which a fresh
# variable store always is.
#
# All three keys are synthetic, generated into the build root, enrolled nowhere
# but in a disposable VM's variable store, and destroyed with the build root.
# PLN-0002's boundary forbids production signing material and this needs none:
# what is measured is whether an unenrolled signer is refused, not whose key
# does the enrolling.
set -eu

build_root=${NEUTRINOS_SLICE_BUILD_ROOT:-${XDG_CACHE_HOME:-$HOME/.cache}/neutrinos/slice}
keys_dir="$build_root/keys"
# Both overridable, so the same enrollment can be exercised against the
# PLN-0002-01 spike artifact without a slice composition. The step is the same
# either way -- it is the artifact's own ESP that is written -- and being able
# to run it against whatever artifact exists is what let it be measured rather
# than reviewed.
artifact=${NEUTRINOS_ENROLL_ARTIFACT:-$build_root/out/neutrinos-slice.raw}
fixture_dir=${NEUTRINOS_ENROLL_FIXTURE_DIR:-$build_root/fixture}
# A fixed name, because T4-CONFEXT-001 consumes this directory as a declared
# capability and a name that varied with the artifact would make the check
# guess at what it was given.
fixture="$fixture_dir/enrolled-artifact.raw"

[ -f "$artifact" ] || { echo "enroll-fixture: no artifact at $artifact" >&2; exit 1; }
image_cert=${NEUTRINOS_ENROLL_IMAGE_CERT:-$keys_dir/secureboot.crt}
[ -f "$image_cert" ] || {
    echo "enroll-fixture: no image-signing certificate at $image_cert;" \
         "db without it produces an unbootable machine" >&2; exit 1; }
[ -f "$keys_dir/verity.crt" ] || {
    echo "enroll-fixture: no verity certificate at $keys_dir/verity.crt;" \
         "compose.sh generates it" >&2; exit 1; }

for tool in sbsiglist sbvarsign mcopy sfdisk; do
    command -v "$tool" >/dev/null 2>&1 || {
        echo "enroll-fixture: $tool unavailable on PATH" >&2; exit 1; }
done

mkdir -p "$fixture_dir" "$keys_dir"

owner=$(uuidgen 2>/dev/null || echo 00000000-0000-0000-0000-000000000000)

# The platform key. It signs the variable updates and is enrolled as PK, which
# takes the firmware out of setup mode -- so it must exist before anything else
# is signed. It is not the verity signer: keeping them separate is what makes
# "the signer is trusted" a statement about db rather than about who built the
# image.
if [ ! -f "$keys_dir/platform.crt" ]; then
    openssl req -x509 -newkey rsa:2048 -nodes -days 30 \
        -subj "/CN=NeutrinOS slice platform key, synthetic/" \
        -keyout "$keys_dir/platform.key" -out "$keys_dir/platform.crt"
fi
[ -f "$keys_dir/platform.der" ] || openssl x509 -outform DER \
    -in "$keys_dir/platform.crt" -out "$keys_dir/platform.der"

# db carries two certificates: the image signer and the verity signer.
#
# The image signer is not optional, and leaving it out is not a smaller
# fixture -- it is a machine that cannot boot. Replacing db with the verity
# certificate alone means Secure Boot no longer trusts the UKI the artifact
# boots, the firmware refuses it, and the run times out with no console. That
# was measured, not reasoned: the first fixture built here did exactly that.
#
# The second verity key is deliberately absent from db, and that absence is the
# whole measurement: a confext signed with it has a valid signature by an
# authority the machine does not trust, which is what a substitution produces.
# The verity signer's DER form. compose.sh emits it, but this derives it when
# absent rather than depending on the order the two scripts ran in: a fixture
# that silently skips enrollment because one file was missing would produce a
# machine that trusts nothing and a check that fails for the wrong reason.
[ -f "$keys_dir/verity.der" ] || openssl x509 -outform DER \
    -in "$keys_dir/verity.crt" -out "$keys_dir/verity.der"

[ -f "$keys_dir/secureboot.der" ] || openssl x509 -outform DER \
    -in "$image_cert" -out "$keys_dir/secureboot.der"

sbsiglist --owner "$owner" --type x509 \
    --output "$fixture_dir/verity.esl" "$keys_dir/verity.der"
sbsiglist --owner "$owner" --type x509 \
    --output "$fixture_dir/image.esl" "$keys_dir/secureboot.der"
# A signature list is a concatenation of lists, so db is built by appending
# rather than by re-signing one combined certificate.
cat "$fixture_dir/image.esl" "$fixture_dir/verity.esl" >"$fixture_dir/db.esl"
sbsiglist --owner "$owner" --type x509 \
    --output "$fixture_dir/pk.esl" "$keys_dir/platform.der"

# Each variable is signed with the platform key. In setup mode the firmware
# accepts the update without verifying the signature, but the structure is
# still required: an unsigned payload is rejected as malformed rather than
# accepted as trusted.
for var in PK KEK db; do
    case $var in
        db) esl="$fixture_dir/db.esl" ;;
        *) esl="$fixture_dir/pk.esl" ;;
    esac
    sbvarsign --key "$keys_dir/platform.key" --cert "$keys_dir/platform.crt" \
        --output "$fixture_dir/$var.auth" "$var" "$esl"
done

cp --reflink=auto "$artifact" "$fixture"

# The ESP offset is read from the artifact's own partition table rather than
# assumed. It has moved once already between spike and slice, and a wrong
# offset here writes into a filesystem that is not the ESP.
offset=$(sfdisk --json "$fixture" | python3 -c '
import json, sys
table = json.load(sys.stdin)["partitiontable"]
sector = table.get("sectorsize", 512)
for partition in table["partitions"]:
    if partition["type"].upper() == "C12A7328-F81F-11D2-BA4B-00A0C93EC93B":
        print(partition["start"] * sector)
        break
else:
    raise SystemExit("no ESP in partition table")
')

mmd -i "$fixture@@$offset" ::/loader ::/loader/keys ::/loader/keys/auto 2>/dev/null || true
for var in PK KEK db; do
    mcopy -o -i "$fixture@@$offset" "$fixture_dir/$var.auth" "::/loader/keys/auto/$var.auth"
done

# Proof the copy differs from the artifact only as intended, and that the
# artifact itself was not touched. The check re-verifies the artifact digest
# too; this is the build-side half.
mdir -i "$fixture@@$offset" ::/loader/keys/auto
sha256sum "$artifact" >"$fixture_dir/artifact.sha256"
echo "enroll-fixture: wrote $fixture"
