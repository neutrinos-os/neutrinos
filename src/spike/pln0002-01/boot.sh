#!/bin/sh
# Boot the PLN-0002-01 spike artifact, report on the early-boot state, and stop.
#
# Deliberately not the slice's boot harness. tools/validation/slice_boot.py is
# guest-driven: it waits for a vsock notification and reports readiness. That is
# the right shape for a registered check and the wrong shape here, because the
# question is what happens *before* the guest is in a position to notify
# anything, and a run that never reaches userspace is a result rather than a
# timeout.
#
# Nothing the guest needs comes from the artifact. Console, firstboot answers,
# hostname, and the report unit itself all arrive as SMBIOS Type 11 credentials,
# which keeps PLN-0001's finding intact: the image carries no configuration, and
# the reason this boots is not that configuration was baked in.
#
# snapshot=on, so the artifact is never written. Verified afterwards by digest.
set -eu

build_root=${NEUTRINOS_SPIKE_BUILD_ROOT:-${XDG_CACHE_HOME:-$HOME/.cache}/neutrinos/pln0002}
# Both overridable, so faults.sh can boot a variant artifact into its own run
# directory without disturbing the reference boot's evidence.
artifact=${1:-$build_root/out/pln0002-01.raw}
run_dir=${NEUTRINOS_SPIKE_RUN:-$build_root/boot}
timeout_seconds=${NEUTRINOS_SPIKE_BOOT_TIMEOUT:-180}

code=/usr/share/edk2/x64/OVMF_CODE.4m.fd
vars=/usr/share/edk2/x64/OVMF_VARS.4m.fd

[ -f "$artifact" ] || { echo "boot: no artifact at $artifact; run spike.sh build" >&2; exit 1; }

rm -rf "$run_dir"
mkdir -p "$run_dir"
cp "$vars" "$run_dir/OVMF_VARS.fd"

before=$(sha256sum "$artifact" | cut -d' ' -f1)

# The read probe reads every file in /usr. dm-verity verifies lazily, per block,
# on read: a block nothing touches is never checked, so a boot that succeeds
# proves only that the blocks the boot happened to read are intact. Reading the
# whole tree is what turns "it booted" into a statement about the artifact.
#
# The report is a unit injected as a credential rather than a script in the
# image, for the same reason as everything else here: the artifact stays the
# thing under test instead of becoming a thing built to pass its own test.
#
# It is passed through a file rather than an inline -smbios string because the
# unit is multi-line and the shell quoting required to inline it is its own
# source of error.
{
    printf 'io.systemd.credential:systemd.extra-unit.spike-report.service='
    cat <<'UNIT'
[Unit]
Description=PLN-0002-01 early-boot report
After=multi-user.target
Requires=multi-user.target
[Service]
Type=oneshot
StandardOutput=journal+console
ExecStart=/usr/bin/sh -c 'echo "SPIKE-REPORT-BEGIN"; \
echo "## usr mount"; findmnt -no SOURCE,FSTYPE,OPTIONS /usr; \
echo "## root mount"; findmnt -no SOURCE,FSTYPE,OPTIONS /; \
echo "## etc mount"; findmnt -no SOURCE,FSTYPE,OPTIONS /etc || echo "(not a mount point)"; \
echo "## verity"; ls -l /dev/mapper/; \
echo "## confext status"; systemd-confext status || true; \
echo "## confext units"; systemctl list-units --all --no-legend "systemd-confext*" "systemd-sysext*"; \
echo "## confext unit files present"; ls /usr/lib/systemd/system/ | grep confext; \
echo "## merged marker"; cat /etc/spike-in-usr.conf 2>&1; \
echo "## extension search dirs"; for d in /run/confexts /var/lib/confexts /usr/local/lib/confexts /usr/lib/confexts /.extra; do printf "%s: " "$d"; ls "$d" 2>&1 | tr "\\n" " "; echo; done; \
echo "## etc writability"; touch /etc/spike-write-probe 2>&1 && echo "WRITE SUCCEEDED" || echo "write refused"; \
echo "## verity read probe"; find /usr -type f -exec cat {} + >/dev/null 2>/tmp/readerr; echo "read exit $?, stderr:"; head -5 /tmp/readerr; \
echo "## dm-verity kernel messages"; dmesg | grep -i verity | tail -5 || echo "(none)"; \
echo "## failed units"; systemctl list-units --state=failed --no-legend || true; \
echo "SPIKE-REPORT-END"'
ExecStopPost=/usr/bin/systemctl poweroff
[Install]
WantedBy=multi-user.target
UNIT
} >"$run_dir/report.cred"

# The unit has to be pulled in by something. [Install] is not processed for a
# unit that arrives as a credential, so the dependency is added as a drop-in --
# also through a file, because an inline -smbios string cannot carry a newline.
{
    printf 'io.systemd.credential:systemd.unit-dropin.multi-user.target='
    cat <<'DROPIN'
[Unit]
Wants=spike-report.service
DROPIN
} >"$run_dir/dropin.cred"

set +e
timeout "$timeout_seconds" qemu-system-x86_64 \
    -machine q35,smm=on,accel=kvm:tcg \
    -cpu host \
    -m 2048 \
    -nographic \
    -no-reboot \
    -drive "if=pflash,unit=0,format=raw,readonly=on,file=$code" \
    -drive "if=pflash,unit=1,format=raw,file=$run_dir/OVMF_VARS.fd" \
    -drive "if=virtio,format=raw,file=$artifact,snapshot=on" \
    -smbios "type=11,value=io.systemd.credential:firstboot.locale=C.UTF-8" \
    -smbios "type=11,value=io.systemd.credential:firstboot.timezone=UTC" \
    -smbios "type=11,value=io.systemd.credential:firstboot.keymap=us" \
    -smbios "type=11,value=io.systemd.credential:system.hostname=pln0002-01" \
    -smbios "type=11,value=io.systemd.credential:passwd.hashed-password.root=!*" \
    -smbios "type=11,path=$run_dir/report.cred" \
    -smbios "type=11,path=$run_dir/dropin.cred" \
    -serial mon:stdio \
    >"$run_dir/console.log" 2>"$run_dir/qemu.log" </dev/null
status=$?
set -e

after=$(sha256sum "$artifact" | cut -d' ' -f1)
[ "$before" = "$after" ] || { echo "boot: artifact changed during boot" >&2; exit 1; }

echo "boot: qemu exit $status, console at $run_dir/console.log"
