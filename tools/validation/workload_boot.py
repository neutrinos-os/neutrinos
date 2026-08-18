"""T4 check: the workload artifact serves the two capabilities C-009 named.

Guards `capability.containers` and `capability.microvm` on the artifact that
ships. It is **not** the C-009 comparison: that ran on 2026-08-18 and its
workload axis is an accepted draw (A-007), so do not add a second filesystem
arm here -- it would re-run a finished measurement on every run.

Two asserts are shaped by a way their subject succeeds while being wrong:

  containers  the bind-mounted file's owner is checked from outside the
              container. A write under a broken uid mapping still succeeds; it
              just lands as the wrong uid, which is the single-UID fallback the
              subid fix removed.
  microvm     `--kvm=yes` rather than negotiated, because `systemd-vmspawn`
              falls back to TCG silently and an emulated boot proves nothing
              about a machine whose role is running microVMs. The space clause
              is a ratio against a full copy taken in the same boot, never a
              constant, so a filesystem that stopped reflinking cannot pass.

What this does NOT assert, because a reader will otherwise assume it does:

  * A-007's other axes -- failure, repair, quota, encryption, operational. This
    runs on a 2 GB volume at 1% full, the most favourable case for Btrfs's
    known low-space behavior, and cannot see it.
  * that the nested guest reaches a *serviceable* system. Its boot image is an
    ESP and a UKI with no /usr verity partitions, so it reaches PID 1 and then
    emergency. Reaching PID 1 is the assert.
  * persistence across a power cycle: the artifact is attached `snapshot=on`
    and the harness never boots the same disk twice.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.validation import vm  # noqa: E402
from tools.validation.slice_boot import HARNESS_MACHINE_ID  # noqa: E402

# vmspawn defaults to 2 GB and the outer guest has exactly 2048 MB, so the
# default killed the inner qemu in feature probing -- an allocation failure
# that reads as a boot failure.
INNER_RAM = "512M"
INNER_BOOT_SECONDS = 120
SOURCE_BYTES = 117440512

PROBE_SCRIPT = r'''
echo "NEUTRINOS-WORKLOAD-BEGIN"
# Wait for the device rather than sampling it: sampling immediately races
# kvm_amd autoloading, and the race reads as a filesystem difference.
waited=0
while [ ! -e /dev/kvm ] && [ $waited -lt 60 ]; do sleep 1; waited=$((waited + 1)); done
# One key per line: the parser reads a value to end of line, so two keys on
# one line arrive as one unequal value and turn success into a failure.
echo "WORKLOAD kvm=$(test -e /dev/kvm && echo yes || echo no)"
echo "WORKLOAD kvm_waited=$waited"
# Reported unconditionally: "no /dev/kvm" has two causes and the failure text
# must say which. No `svm` means the outer qemu is emulating; `svm` with no
# module means kvm_amd had not autoloaded.
echo "WORKLOAD virt_flag=$(grep -oE ' svm | vmx ' /proc/cpuinfo | head -1 | tr -d ' ')"
echo "WORKLOAD kvm_modules=$(ls /sys/module 2>/dev/null | grep -c kvm)"
echo "WORKLOAD kvm_module_list=$(ls /sys/module 2>/dev/null | grep kvm | tr '\n' ',')"
echo "WORKLOAD kvm_dmesg=$(dmesg 2>/dev/null | grep -i 'kvm\|svm' | tail -4 | tr '\n' '|')"
echo "WORKLOAD nested_param=$(cat /sys/module/kvm_amd/parameters/nested 2>&1)"
echo "WORKLOAD var_fstype=$(findmnt -no FSTYPE --target /var)"

# containers
install -d -o neutrinos -g neutrinos /home/neutrinos/rootfs/usr/bin /home/neutrinos/rootfs/bin /home/neutrinos/rootfs/lib64 /home/neutrinos/src
cp /usr/bin/sh /home/neutrinos/rootfs/usr/bin/sh
for lib in $(ldd /usr/bin/sh 2>/dev/null | grep -oE '/[^ ]*\.so[^ ]*'); do cp -L $lib /home/neutrinos/rootfs/lib64/ 2>/dev/null; done
ln -sf ../usr/bin/sh /home/neutrinos/rootfs/bin/sh
chown -R neutrinos:neutrinos /home/neutrinos
install -d -o neutrinos -g neutrinos -m 0700 /run/user/1000
echo "WORKLOAD subid=$(getsubids neutrinos 2>&1 | tr '\n' ' ')"
runuser -u neutrinos -- env XDG_RUNTIME_DIR=/run/user/1000 HOME=/home/neutrinos podman run --rm -v /home/neutrinos/src:/src --rootfs /home/neutrinos/rootfs /usr/bin/sh -c 'echo written-from-container > /src/container-file' >/dev/null 2>&1
echo "WORKLOAD container_file_owner=$(stat --format=REPLACEME /home/neutrinos/src/container-file 2>/dev/null)"
echo "WORKLOAD container_file_content=$(cat /home/neutrinos/src/container-file 2>/dev/null)"

# microvm
mkdir -p /var/vm
cp /dev/vdb /var/vm/image.raw
sync
before=$(df -B1 --output=used /var | tail -1 | tr -d ' ')
cp --reflink=always /var/vm/image.raw /var/vm/clone.raw && ok=yes || ok=no
sync
after=$(df -B1 --output=used /var | tail -1 | tr -d ' ')
cp --reflink=never /var/vm/image.raw /var/vm/full.raw 2>/dev/null
sync
after2=$(df -B1 --output=used /var | tail -1 | tr -d ' ')
rm -f /var/vm/full.raw
echo "WORKLOAD reflink ok=$ok reflink_bytes=$((after - before)) fullcopy_bytes=$((after2 - after))"
# SYSTEMD_LOG_LEVEL=debug is load-bearing, not tracing: the `accel` line
# asserted below appears only in vmspawn's debug output.
SYSTEMD_LOG_LEVEL=debug timeout INNER_TIMEOUT systemd-vmspawn --image=/var/vm/clone.raw --tpm=no --secure-boot=no --ram=INNER_RAM_VALUE --kvm=yes --console=read-only > /tmp/nested.log 2>&1
echo "WORKLOAD nested_accel=$(grep -aoE 'accel = "[a-z]+"' /tmp/nested.log | head -1 | tr -d '\n')"
echo "WORKLOAD nested_pid1=$(grep -ac 'systemd\[1\]:' /tmp/nested.log)"
echo "NEUTRINOS-WORKLOAD-END"
'''

LINE = re.compile(r"WORKLOAD (?P<key>[a-z0-9_]+)=(?P<value>.*?)\s*$", re.MULTILINE)
REFLINK = re.compile(
    r"WORKLOAD reflink ok=(?P<ok>\S+) reflink_bytes=(?P<reflink>-?\d+) "
    r"fullcopy_bytes=(?P<full>-?\d+)",
    re.MULTILINE,
)


def _boot_image(artifact_directory: Path, work: Path) -> Path:
    """An ESP carrying the artifact's own UKI, as a GPT disk image.

    Built host-side with mtools and sfdisk: no loop device, no root, and the
    closure ships no mkfs.vfat (the owner ruled filesystem tooling to a sysext,
    C-011). When that sysext lands, this is what it replaces. The UKI comes
    from the artifact directory because extracting it from the guest's ESP
    would need a privileged mount of an artifact this check must not write.
    """
    uki = artifact_directory / "neutrinos-slice.efi"
    staging = work / "esp" / "EFI" / "BOOT"
    staging.mkdir(parents=True)
    shutil.copy(uki, staging / "BOOTX64.EFI")

    image = work / "microvm.raw"
    with image.open("wb") as handle:
        handle.truncate(SOURCE_BYTES)
    subprocess.run(
        ["sfdisk", str(image)],
        input=(
            "label: gpt\n"
            "start=2048, size=210944, "
            "type=C12A7328-F81F-11D2-BA4B-00A0C93EC93B, name=\"EFI System Partition\"\n"
        ),
        text=True,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["mformat", "-i", f"{image}@@1M", "-F", "-v", "ESP"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["mcopy", "-i", f"{image}@@1M", "-s", str(work / "esp" / "EFI"), "::"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return image


def check_workload_boot() -> int:
    from tools.validation.check import WORKLOAD_ARTIFACT_ENV

    directory = Path(os.environ[WORKLOAD_ARTIFACT_ENV]).resolve()
    artifact = directory / "neutrinos-slice.raw"
    _code, variables = vm.firmware_pair(secure_boot=False)

    script = (
        PROBE_SCRIPT.replace("INNER_TIMEOUT", str(INNER_BOOT_SECONDS))
        .replace("INNER_RAM_VALUE", INNER_RAM)
        # `%` is a systemd unit specifier and a stat format string is full of
        # them: `%U` expands to the unit's uid before the guest sees it.
        .replace("REPLACEME", "%%U:%%G")
    )
    unit = f"""[Unit]
Description=NeutrinOS workload probe
DefaultDependencies=no
After=local-fs.target sysinit.target var.mount home.mount systemd-tmpfiles-setup.service
Wants=local-fs.target
Conflicts=shutdown.target

[Service]
Type=oneshot
StandardOutput=journal+console
StandardError=journal+console
TimeoutStartSec=600
ExecStart=/usr/bin/bash -c {script!r}
ExecStopPost=/usr/bin/systemctl poweroff --no-block

[Install]
WantedBy=multi-user.target
"""

    with tempfile.TemporaryDirectory(prefix="neutrinos-workload-t4-") as raw:
        work = Path(raw)
        store = work / "OVMF_VARS.fd"
        shutil.copy(variables, store)
        store.chmod(0o600)
        credential_dir = work / "credentials"
        credential_dir.mkdir()
        image = _boot_image(directory, work)
        console = vm.boot(
            artifact,
            work=work,
            store=store,
            secure_boot=False,
            credentials={
                "system.hostname": "workload-t4-fixture",
                "system.machine_id": HARNESS_MACHINE_ID,
                "passwd.hashed-password.root": "",
            },
            credential_files=[
                vm.credential_file(
                    credential_dir,
                    "systemd.extra-unit.neutrinos-workload-probe.service",
                    unit,
                )
            ],
            extra_disks=[image],
            cmdline_extra=["systemd.wants=neutrinos-workload-probe.service"],
            timeout_seconds=900,
        )

    failures: list[str] = []
    if (
        "NEUTRINOS-WORKLOAD-BEGIN" not in console
        or "NEUTRINOS-WORKLOAD-END" not in console
    ):
        print("workload probe did not run to completion in the guest", file=sys.stderr)
        return 1

    observed = {match["key"]: match["value"] for match in LINE.finditer(console)}

    if observed.get("kvm") != "yes":
        flag = observed.get("virt_flag") or "none"
        modules = observed.get("kvm_modules", "?")
        if flag == "none":
            failures.append(
                "no /dev/kvm in the guest, and the guest CPU exposes no "
                f"virtualization flag (modules={modules}): the outer VMM is "
                "emulating rather than using KVM, so this is the harness and "
                "not the artifact"
            )
        else:
            failures.append(
                f"no /dev/kvm in the guest after waiting "
                f"{observed.get('kvm_waited', '?')}s, though the CPU exposes "
                f"{flag} (modules={modules})"
            )
    if not observed.get("subid", "").startswith("0:"):
        failures.append(f"no subordinate range for neutrinos: {observed.get('subid')!r}")

    # The container assert, checked from outside: owner, not exit status.
    owner = observed.get("container_file_owner", "")
    if owner != "neutrinos:neutrinos":
        failures.append(
            "bind-mounted file not owned by the session user after a rootless "
            f"container wrote it: {owner!r}"
        )
    if observed.get("container_file_content") != "written-from-container":
        failures.append("bind-mounted source tree was not writable from inside")

    # The microVM assert.
    reflink = REFLINK.search(console)
    if reflink is None:
        failures.append("no reflink measurement line")
    else:
        if reflink["ok"] != "yes":
            failures.append("cp --reflink=always failed on the state volume")
        reflinked = int(reflink["reflink"])
        full = int(reflink["full"])
        if full < SOURCE_BYTES // 2:
            failures.append(
                f"full copy consumed {full} bytes, too few to be a real copy; "
                "the ratio below would be meaningless"
            )
        elif reflinked > full // 100:
            failures.append(
                f"reflink copy consumed {reflinked} bytes against {full} for a "
                "full copy, which is not materially less"
            )

    accel = observed.get("nested_accel", "")
    if 'accel = "kvm"' not in accel:
        failures.append(f"nested VM did not run under KVM: {accel!r}")
    if int(observed.get("nested_pid1") or 0) < 1:
        failures.append("nested VM never reached PID 1 from the reflink copy")

    if failures:
        # Every observation, not just the failing ones: a symptom without the
        # readings around it sends the next reader back into the guest.
        for key in sorted(observed):
            print(f"observed {key}={observed[key]!r}", file=sys.stderr)
    for failure in failures:
        print(failure, file=sys.stderr)
    return 1 if failures else 0
