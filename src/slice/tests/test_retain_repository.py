"""Retention keys reuse on the declared digest, and fetches from the declared URL."""

from __future__ import annotations

import gzip
import hashlib

import pytest

import retain_repository

URL = "https://example.invalid/repository"

REPOMD = """<?xml version="1.0" encoding="UTF-8"?>
<repomd xmlns="http://linux.duke.edu/metadata/repo">
 <data type="primary">
  <location href="repodata/primary.xml.gz"/>
 </data>
 <data type="filelists">
  <location href="repodata/filelists.xml.gz"/>
 </data>
</repomd>
""".encode("utf-8")

PRIMARY = b"""<?xml version="1.0" encoding="UTF-8"?>
<metadata xmlns="http://linux.duke.edu/metadata/common">
 <package>
  <location href="Packages/s/systemd-261-1.x86_64.rpm"/>
 </package>
</metadata>
"""


@pytest.fixture
def server(monkeypatch):
    """A recording stand-in for the network, holding what the URL would serve."""
    published = {
        f"{URL}/repodata/repomd.xml": REPOMD,
        f"{URL}/repodata/primary.xml.gz": gzip.compress(PRIMARY),
        f"{URL}/repodata/filelists.xml.gz": gzip.compress(b"<filelists/>"),
    }
    requested = []

    def fetch(url, destination):
        requested.append(url)
        if url not in published:
            raise AssertionError(f"fetched {url}, which this repository does not serve")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(published[url])
        return published[url]

    monkeypatch.setattr(retain_repository, "fetch", fetch)
    return requested


DIGEST = hashlib.sha256(REPOMD).hexdigest()


def test_every_file_the_index_names_is_fetched_from_the_declared_url(server, tmp_path):
    """A partial copy of a signed index is one whose completeness nobody can verify.

    This is also the regression test for the fetch that named the imported
    `repository` function instead of the URL: it produced a request to
    `<function repository at 0x...>/repodata/primary.xml.gz`. Nothing before
    this reached that line, because the reuse path above it skips the loop
    whenever a retention already exists.
    """
    primary = retain_repository.retain_metadata(URL, DIGEST, tmp_path)
    assert server == [
        f"{URL}/repodata/repomd.xml",
        f"{URL}/repodata/primary.xml.gz",
        f"{URL}/repodata/filelists.xml.gz",
    ]
    assert primary == tmp_path / "repodata" / "primary.xml.gz"


def test_a_url_serving_another_publication_is_refused_after_one_request(server, tmp_path):
    with pytest.raises(SystemExit) as raised:
        retain_repository.retain_metadata(URL, "0" * 64, tmp_path)
    assert "not the declared publication" in str(raised.value)
    # One request, not a full retention.
    assert server == [f"{URL}/repodata/repomd.xml"]


def test_the_mismatched_metadata_is_left_in_place_as_evidence(server, tmp_path):
    with pytest.raises(SystemExit):
        retain_repository.retain_metadata(URL, "0" * 64, tmp_path)
    assert (tmp_path / "repodata" / "repomd.xml").read_bytes() == REPOMD


def test_a_retained_declared_repository_is_reused_without_the_network(server, tmp_path):
    retain_repository.retain_metadata(URL, DIGEST, tmp_path)
    server.clear()
    primary = retain_repository.retain_metadata(URL, DIGEST, tmp_path)
    assert server == []
    assert primary == tmp_path / "repodata" / "primary.xml.gz"


def test_a_retention_of_another_repository_stops_rather_than_being_reused(server, tmp_path):
    """The existence guard this replaced went on attributing packages to it."""
    retain_repository.retain_metadata(URL, DIGEST, tmp_path)
    with pytest.raises(SystemExit) as raised:
        retain_repository.retain_metadata(URL, "0" * 64, tmp_path)
    assert "is not the declared repository" in str(raised.value)


def test_the_retention_is_not_discarded_on_a_declaration_edit(server, tmp_path):
    """A stop you can recover from, rather than a loss you cannot."""
    retain_repository.retain_metadata(URL, DIGEST, tmp_path)
    with pytest.raises(SystemExit):
        retain_repository.retain_metadata(URL, "0" * 64, tmp_path)
    assert (tmp_path / "repodata" / "repomd.xml").is_file()
    assert (tmp_path / "repodata" / "primary.xml.gz").is_file()


def test_decompress_reads_the_forms_the_repository_publishes(tmp_path):
    compressed = tmp_path / "primary.xml.gz"
    compressed.write_bytes(gzip.compress(PRIMARY))
    assert retain_repository.decompress(compressed) == PRIMARY

    plain = tmp_path / "primary.xml"
    plain.write_bytes(PRIMARY)
    assert retain_repository.decompress(plain) == PRIMARY


def test_retention_refuses_to_launder_an_undeclared_package(server, tmp_path, monkeypatch):
    """PLN-0001-06's injected faults left 58 such RPMs in a shared cache."""
    monkeypatch.setattr(
        retain_repository,
        "repository",
        lambda declaration: {"url": URL, "metadata_digest": DIGEST},
    )
    cache = tmp_path / "pkgcache"
    cache.mkdir()
    (cache / "from-somewhere-else-1.0.x86_64.rpm").write_bytes(b"")

    with pytest.raises(SystemExit) as raised:
        retain_repository.retain(cache=cache, destination=tmp_path / "repository")
    assert "launder an undeclared input" in str(raised.value)


def test_a_package_the_declared_overlay_contains_is_not_undeclared(server, tmp_path, monkeypatch):
    """acquire_overlay verified it by digest and retains it at its own path."""
    monkeypatch.setattr(
        retain_repository,
        "repository",
        lambda declaration: {"url": URL, "metadata_digest": DIGEST},
    )
    cache = tmp_path / "pkgcache"
    cache.mkdir()
    (cache / "systemd-261-1.x86_64.rpm").write_bytes(b"declared by the repository")
    (cache / "systemd-libs-261-1.x86_64.rpm").write_bytes(b"declared by the overlay")
    overlay = tmp_path / "overlay" / "systemd-261"
    overlay.mkdir(parents=True)
    (overlay / "systemd-libs-261-1.x86_64.rpm").write_bytes(b"declared by the overlay")

    destination = tmp_path / "repository"
    retain_repository.retain(cache=cache, destination=destination, overlay=tmp_path / "overlay")

    # Retained at the path the metadata names, and the overlay's package is not
    # copied in: the retained tree must not say the declared repository contains
    # packages it does not.
    assert (destination / "Packages/s/systemd-261-1.x86_64.rpm").is_file()
    assert not (destination / "Packages/s/systemd-libs-261-1.x86_64.rpm").exists()

    import json

    record = json.loads((destination / retain_repository.RETENTION_RECORD).read_text())
    assert record["package_count"] == 1
    assert record["overlay_package_count"] == 1
    assert record["source_url"] == URL
    assert record["repomd_sha256"] == DIGEST
