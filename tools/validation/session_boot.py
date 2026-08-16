"""T4 check: the session artifact reaches a graphical session.

One capability per assertion, taken from src/roles/workstation/capabilities.toml
so the declaration and the check cannot drift into disagreement about what the
role means. What is asserted here is the `session` stage only.

Two capabilities are deliberately NOT asserted, and saying so is the point:

  graphics  -- its assert requires a hardware renderer rather than a software
               fallback. A disposable VM has no DRM device and sway runs on the
               headless backend, so this check cannot produce evidence for it.
               Passing it here would turn "no GPU at all" into a green result.
  login     -- its assert requires an account to authenticate *through* greetd.
               This check observes that greetd is running and that its PAM stack
               resolves; it does not drive a login. Asserting the weaker thing
               under the stronger name is how a check stops meaning anything.

The environment drop-ins are written into /run by the probe rather than shipped.
A physical workstation has a DRM device and a login; making the artifact
headless and self-starting to suit the harness would be accommodating the test
in the artifact under test.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.validation import vm  # noqa: E402
from tools.validation.slice_boot import HARNESS_MACHINE_ID  # noqa: E402

SESSION_UID = 1000

PROBE_UNIT = """[Unit]
Description=NeutrinOS session probe
After=multi-user.target
Wants=multi-user.target
Conflicts=shutdown.target

[Service]
Type=oneshot
StandardOutput=journal+console
StandardError=journal+console
ExecStart=/usr/bin/sh -c 'echo "NEUTRINOS-SESSION-BEGIN"; \
echo "PROBE greetd=$(systemctl is-active greetd.service)"; \
echo "PROBE account=$(id -u neutrinos 2>/dev/null)"; \
echo "PROBE homedir=$(stat -c %%U /home/neutrinos 2>/dev/null)"; \
echo "PROBE homesource=$(findmnt -no SOURCE --target /home)"; \
mkdir -p /run/systemd/user/sway.service.d /run/systemd/system/user@1000.service.d; \
printf "[Service]\\\\nEnvironment=WLR_BACKENDS=headless\\\\nEnvironment=WLR_LIBINPUT_NO_DEVICES=1\\\\n" \
  > /run/systemd/user/sway.service.d/10-headless.conf; \
printf "[Service]\\\\nEnvironment=XDG_RUNTIME_DIR=/run/user/1000\\\\n" \
  > /run/systemd/system/user@1000.service.d/10-runtime-dir.conf; \
systemctl daemon-reload; \
systemctl start user@1000.service >/dev/null 2>&1; \
echo "PROBE usermanager=$(systemctl is-active user@1000.service)"; \
runuser -u neutrinos -- env XDG_RUNTIME_DIR=/run/user/1000 systemctl --user start sway.service >/dev/null 2>&1; \
sleep 3; \
echo "PROBE sway=$(runuser -u neutrinos -- env XDG_RUNTIME_DIR=/run/user/1000 systemctl --user is-active sway.service)"; \
echo "PROBE graphicalsession=$(runuser -u neutrinos -- env XDG_RUNTIME_DIR=/run/user/1000 systemctl --user is-active graphical-session.target)"; \
echo "PROBE waylandsocket=$(ls /run/user/1000/wayland-1 2>/dev/null | wc -l)"; \
echo "PROBE swayenv=$(runuser -u neutrinos -- env XDG_RUNTIME_DIR=/run/user/1000 systemctl --user show-environment | grep -c WAYLAND_DISPLAY)"; \
echo "PROBE terminal=$(runuser -u neutrinos -- env XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-1 foot --version 2>&1 | grep -c foot)"; \
echo "PROBE journal=$(journalctl _SYSTEMD_USER_UNIT=sway.service _UID=1000 --no-pager -q | wc -l)"; \
echo "NEUTRINOS-SESSION-END"'
ExecStopPost=/usr/bin/systemctl poweroff --no-block

[Install]
WantedBy=multi-user.target
"""

FIELD = re.compile(r"PROBE (?P<key>[a-z]+)=(?P<value>\S*)\s*$", re.MULTILINE)

# key -> (expected value, capability it evidences, what a mismatch means)
#
# "login-precondition" is not a capability in the declaration, and that is
# deliberate. greetd running and an account existing are things the `login`
# capability needs; they are not what it asserts, which is that an account
# authenticates *through* greetd. Labelling them `login` put that capability in
# both the asserted and the not-asserted list at once, which reads as evidence
# for something no boot here has shown.
EXPECTATIONS: tuple[tuple[str, str, str, str], ...] = (
    ("greetd", "active", "login-precondition", "greetd is not running, so nothing can authenticate"),
    ("account", str(SESSION_UID), "login-precondition", "systemd-sysusers did not create the session account"),
    ("homedir", "neutrinos", "login-precondition", "the home directory is missing or owned by the wrong user"),
    ("usermanager", "active", "session-lifecycle", "the user manager did not start; PAM is the usual cause"),
    ("sway", "active", "compositor", "the compositor did not reach active"),
    ("graphicalsession", "active", "session-lifecycle", "graphical-session.target was not pulled in by the compositor"),
    ("waylandsocket", "1", "compositor", "no Wayland display socket in the user runtime directory"),
    ("swayenv", "1", "session-lifecycle", "WAYLAND_DISPLAY was not published to the user manager, so later units must guess at it"),
    ("terminal", "1", "terminal", "the terminal emulator did not execute"),
)


def check_session_boot() -> int:
    from tools.validation.check import SESSION_ARTIFACT_ENV

    artifact = Path(os.environ[SESSION_ARTIFACT_ENV]).resolve() / "neutrinos-slice.raw"

    with tempfile.TemporaryDirectory(prefix="neutrinos-session-t4-") as raw:
        work = Path(raw)
        _, variables = vm.firmware_pair(secure_boot=False)
        store = work / "OVMF_VARS.fd"
        shutil.copy(variables, store)
        store.chmod(0o600)
        credential_dir = work / "credentials"
        credential_dir.mkdir()
        console = vm.boot(
            artifact,
            work=work,
            store=store,
            secure_boot=False,
            credentials={
                "system.hostname": "session-t4-fixture",
                "system.machine_id": HARNESS_MACHINE_ID,
                "passwd.hashed-password.root": "",
            },
            credential_files=[
                vm.credential_file(
                    credential_dir,
                    "systemd.extra-unit.neutrinos-session-probe.service",
                    PROBE_UNIT,
                )
            ],
            cmdline_extra=["systemd.wants=neutrinos-session-probe.service"],
            timeout_seconds=300,
        )

    if "NEUTRINOS-SESSION-BEGIN" not in console or "NEUTRINOS-SESSION-END" not in console:
        # A probe that did not finish is not a pass. Without this the parse finds
        # nothing, reports nothing, and the check succeeds having observed
        # nothing -- the failure shape this project already has eight of.
        print("session probe did not run to completion in the guest", file=sys.stderr)
        return 1

    observed = {m.group("key"): m.group("value") for m in FIELD.finditer(console)}
    failures: list[str] = []
    evidenced: dict[str, Any] = {}

    for key, expected, capability, meaning in EXPECTATIONS:
        seen = observed.get(key)
        evidenced[key] = seen
        if seen is None:
            failures.append(f"{capability}: probe reported no {key} value")
        elif seen != expected:
            failures.append(
                f"{capability}: {key} is {seen!r}, expected {expected!r} — {meaning}"
            )

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "capabilities_asserted": sorted({c for _, _, c, _ in EXPECTATIONS}),
                "capabilities_not_asserted": {
                    "graphics": "no DRM device in a disposable VM; sway runs headless",
                    "login": "greetd runs and its PAM stack resolves; no login is driven",
                    "session-diagnostics": "needs a deliberately failed session",
                },
                "observed": evidenced,
                "result": "passing",
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0
