"""What the enrollment must refuse, and what it must not silently reuse.

The signing tools are not run here. What is worth testing is the logic the
shell had no way to reach: the ESP offset parse, the guards, and the four
fail-open defects the conversion closed. Whether `sbvarsign` produces a
well-formed authenticated variable is T4-CONFEXT-001's question, and it answers
it by booting.
"""

from __future__ import annotations

import subprocess

import pytest

import enroll

ESP = "C12A7328-F81F-11D2-BA4B-00A0C93EC93B"
OTHER = "0FC63DAF-8483-4772-8E79-3D69D8477DE4"


def table(partitions, **top):
    return {"partitiontable": {"partitions": list(partitions), **top}}


def test_the_esp_offset_is_a_sector_count_scaled_by_the_declared_sector_size():
    parsed = table([{"type": ESP, "start": 2048}], sectorsize=4096)
    assert enroll.esp_offset(parsed) == 2048 * 4096


def test_a_table_without_a_sector_size_is_read_as_512():
    """sfdisk omits the field on some tables, and 512 is what it means by it."""
    assert enroll.esp_offset(table([{"type": ESP, "start": 2048}])) == 2048 * 512


def test_the_esp_is_found_by_type_rather_than_by_position():
    parsed = table([
        {"type": OTHER, "start": 2048},
        {"type": OTHER, "start": 4096},
        {"type": ESP, "start": 8192},
    ])
    assert enroll.esp_offset(parsed) == 8192 * 512


def test_the_type_guid_is_compared_case_insensitively():
    """sfdisk reports it uppercase; nothing should depend on that continuing."""
    assert enroll.esp_offset(table([{"type": ESP.lower(), "start": 34}])) == 34 * 512


@pytest.mark.parametrize("partitions", ([{"type": OTHER, "start": 2048}], []))
def test_no_esp_stops_rather_than_writing_at_offset_zero(partitions):
    """A wrong offset writes into a filesystem that is not the ESP."""
    with pytest.raises(SystemExit) as refused:
        enroll.esp_offset(table(partitions))
    assert "no ESP" in str(refused.value)


def test_require_names_every_missing_input_at_once(tmp_path):
    """One run per gap is what the shell's first-missing-only loop cost."""
    present = tmp_path / "present"
    present.write_text("", encoding="utf-8")
    with pytest.raises(SystemExit) as refused:
        enroll.require({
            present: "should not appear",
            tmp_path / "first": "the first reason",
            tmp_path / "second": "the second reason",
        })
    message = str(refused.value)
    assert "the first reason" in message and "the second reason" in message
    assert "should not appear" not in message


class Recorder:
    """Stand in for every tool the enrollment shells out to.

    Nothing here is signed: the point is which commands were issued, with what,
    and in what order. `sbsiglist`, `openssl` and `cp` are given a file to
    write so the steps that read their outputs have something to read.
    """

    def __init__(self):
        self.commands = []

    def __call__(self, command, **keywords):
        self.commands.append([str(part) for part in command])
        return self.respond([str(part) for part in command], keywords)

    def respond(self, command, keywords):
        tool = command[0]
        if tool == "openssl":
            self.write(command, "-out", b"DER")
        elif tool == "sbsiglist":
            self.write(command, "--output", b"ESL:" + command[-1].encode())
        elif tool == "sbvarsign":
            self.write(command, "--output", b"AUTH")
        elif tool == "cp":
            open(command[-1], "wb").write(b"ARTIFACT")
        elif tool == "sfdisk":
            return subprocess.CompletedProcess(
                command, 0,
                stdout='{"partitiontable": {"partitions": '
                       f'[{{"type": "{ESP}", "start": 2048}}]}}}}',
            )
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    @staticmethod
    def write(command, flag, content):
        open(command[command.index(flag) + 1], "wb").write(content)

    def issued(self, tool):
        return [command for command in self.commands if command[0] == tool]


@pytest.fixture
def build_root(tmp_path, monkeypatch):
    """A build root holding everything buildroot.py is responsible for."""
    keys = tmp_path / "keys"
    keys.mkdir()
    for name in ("platform.key", "platform.crt", "platform.der",
                 "secureboot.crt", "verity.crt"):
        (keys / name).write_text(name, encoding="utf-8")
    output = tmp_path / "out"
    output.mkdir()
    (output / "neutrinos-slice.raw").write_bytes(b"ARTIFACT")

    monkeypatch.setattr(enroll.shutil, "which", lambda tool: f"/usr/bin/{tool}")
    for variable in (
        "NEUTRINOS_ENROLL_ARTIFACT", "NEUTRINOS_ENROLL_FIXTURE_DIR",
        "NEUTRINOS_ENROLL_IMAGE_CERT", "NEUTRINOS_ENROLL_VERITY_CERT",
    ):
        monkeypatch.delenv(variable, raising=False)
    return tmp_path


@pytest.fixture
def recorder(monkeypatch):
    recorder = Recorder()
    monkeypatch.setattr(enroll.subprocess, "run", recorder)
    return recorder


def test_an_enrollment_writes_the_fixture_the_check_consumes(build_root, recorder):
    fixture = enroll.enroll(build_root)
    assert fixture == build_root / "fixture" / "enrolled-artifact.raw"
    assert fixture.is_file()


def test_db_carries_the_image_signer_and_the_verity_signer(build_root, recorder):
    """db with the verity certificate alone refuses the machine's own UKI."""
    enroll.enroll(build_root)
    fixture_dir = build_root / "fixture"
    db = (fixture_dir / "db.esl").read_bytes()
    assert (fixture_dir / "image.esl").read_bytes() in db
    assert (fixture_dir / "verity.esl").read_bytes() in db
    assert db == (fixture_dir / "image.esl").read_bytes() + (
        fixture_dir / "verity.esl"
    ).read_bytes()


def test_pk_and_kek_carry_the_platform_key_and_db_does_not(build_root, recorder):
    enroll.enroll(build_root)
    signed = {command[command.index("--output") + 1].rsplit("/", 1)[-1]: command[-1]
              for command in recorder.issued("sbvarsign")}
    assert signed["PK.auth"].endswith("pk.esl")
    assert signed["KEK.auth"].endswith("pk.esl")
    assert signed["db.auth"].endswith("db.esl")


def test_every_signature_list_claims_the_same_generated_owner(build_root, recorder):
    """And it is a real GUID: a missing uuidgen used to yield the nil one."""
    enroll.enroll(build_root)
    owners = {command[command.index("--owner") + 1]
              for command in recorder.issued("sbsiglist")}
    assert len(owners) == 1
    assert owners.pop() != "00000000-0000-0000-0000-000000000000"


def test_two_enrollments_do_not_share_an_owner(build_root, recorder):
    """The owner is generated, so it is generated each time rather than found."""
    enroll.enroll(build_root)
    first = recorder.issued("sbsiglist")[0]
    recorder.commands.clear()
    enroll.enroll(build_root)
    assert recorder.issued("sbsiglist")[0] != first


def test_the_image_der_is_derived_rather_than_reused(build_root, recorder, monkeypatch):
    """The measured fail-open: an existence guard on `keys/secureboot.der`.

    Pointing the enrollment at a second image certificate left the first one's
    DER in place, so `db` carried the previous signer and the run reported
    success. Nothing is guarded by existence now, and the DER is written beside
    the fixture rather than into the shared keys directory.
    """
    other = build_root / "other.crt"
    other.write_text("other", encoding="utf-8")
    enroll.enroll(build_root)
    first = [command for command in recorder.issued("openssl")]

    recorder.commands.clear()
    monkeypatch.setenv("NEUTRINOS_ENROLL_IMAGE_CERT", str(other))
    enroll.enroll(build_root)
    second = recorder.issued("openssl")

    assert len(second) == len(first)
    assert any(str(other) in command for command in second)
    assert not (build_root / "keys" / "secureboot.der").exists()


def test_the_verity_der_stays_out_of_the_shared_keys_directory(build_root, recorder, monkeypatch):
    """verity-wrong's DER landing on verity.der corrupts every later run."""
    wrong = build_root / "keys" / "verity-wrong.crt"
    wrong.write_text("wrong", encoding="utf-8")
    monkeypatch.setenv("NEUTRINOS_ENROLL_VERITY_CERT", str(wrong))
    enroll.enroll(build_root)
    assert (build_root / "fixture" / "verity.der").is_file()
    assert not (build_root / "keys" / "verity.der").exists()


@pytest.mark.parametrize("missing", (
    "keys/platform.key", "keys/platform.crt", "keys/platform.der",
    "keys/secureboot.crt", "keys/verity.crt", "out/neutrinos-slice.raw",
))
def test_a_missing_input_stops_before_anything_is_written(build_root, recorder, missing):
    """`platform.crt` is in this list because sbvarsign used it unguarded."""
    (build_root / missing).unlink()
    with pytest.raises(SystemExit):
        enroll.enroll(build_root)
    assert not (build_root / "fixture" / "enrolled-artifact.raw").exists()


def test_a_missing_tool_names_all_of_them(build_root, monkeypatch):
    absent = {"sbvarsign", "mcopy"}
    monkeypatch.setattr(
        enroll.shutil, "which",
        lambda tool: None if tool in absent else f"/usr/bin/{tool}",
    )
    with pytest.raises(SystemExit) as refused:
        enroll.enroll(build_root)
    assert "sbvarsign" in str(refused.value) and "mcopy" in str(refused.value)


def test_mmd_and_mdir_are_required_though_the_shell_checked_neither(build_root, monkeypatch):
    for tool in ("mmd", "mdir", "openssl"):
        monkeypatch.setattr(
            enroll.shutil, "which",
            lambda name, absent=tool: None if name == absent else f"/usr/bin/{name}",
        )
        with pytest.raises(SystemExit) as refused:
            enroll.enroll(build_root)
        assert tool in str(refused.value)


def test_the_artifact_itself_is_never_opened_for_writing(build_root, recorder):
    """T3-SLICE-001 and T4-SLICE-001 assert the artifact is byte-identical."""
    artifact = build_root / "out" / "neutrinos-slice.raw"
    before = artifact.read_bytes()
    enroll.enroll(build_root)
    assert artifact.read_bytes() == before
    written = {command[-1] for command in recorder.issued("mcopy")}
    assert all(str(artifact) not in target for target in written)
    assert all(str(artifact) not in command[-1] for command in recorder.issued("mmd"))


def test_the_keys_are_copied_to_the_offset_the_partition_table_reports(build_root, recorder):
    enroll.enroll(build_root)
    fixture = build_root / "fixture" / "enrolled-artifact.raw"
    location = f"{fixture}@@{2048 * 512}"
    for command in recorder.issued("mcopy"):
        assert location in command
    assert {command[-1] for command in recorder.issued("mcopy")} == {
        "::/loader/keys/auto/PK.auth",
        "::/loader/keys/auto/KEK.auth",
        "::/loader/keys/auto/db.auth",
    }


def test_a_directory_that_exists_is_not_created_again(tmp_path, monkeypatch):
    recorder = Recorder()
    monkeypatch.setattr(enroll.subprocess, "run", recorder)
    enroll.make_directory(tmp_path / "image.raw", 1024, "/loader")
    assert recorder.issued("mdir")
    assert not recorder.issued("mmd")


def test_a_directory_that_is_absent_is_created(tmp_path, monkeypatch):
    issued = []

    def run(command, **keywords):
        command = [str(part) for part in command]
        issued.append(command)
        return subprocess.CompletedProcess(command, 1 if command[0] == "mdir" else 0)

    monkeypatch.setattr(enroll.subprocess, "run", run)
    enroll.make_directory(tmp_path / "image.raw", 1024, "/loader/keys")
    assert issued[-1] == ["mmd", "-i", f"{tmp_path / 'image.raw'}@@1024", "::/loader/keys"]


def test_a_failing_mmd_is_not_swallowed(tmp_path, monkeypatch):
    """`2>/dev/null || true` stood here and hid a wrong offset entirely.

    The stub honours `check` rather than raising unconditionally, because what
    is under test is that the call asks for it. A stub that always raised would
    pass against the suppressed version too.
    """
    def run(command, **keywords):
        command = [str(part) for part in command]
        if keywords.get("check"):
            raise subprocess.CalledProcessError(1, command)
        return subprocess.CompletedProcess(command, 1)

    monkeypatch.setattr(enroll.subprocess, "run", run)
    with pytest.raises(subprocess.CalledProcessError):
        enroll.make_directory(tmp_path / "image.raw", 1024, "/loader")


def test_the_recorded_digest_is_the_artifact_s_and_sha256sum_can_read_it(
    build_root, recorder
):
    import common

    enroll.enroll(build_root)
    artifact = build_root / "out" / "neutrinos-slice.raw"
    recorded = (build_root / "fixture" / "artifact.sha256").read_text(encoding="utf-8")
    assert recorded == f"{common.digest(artifact)}  {artifact}\n"
