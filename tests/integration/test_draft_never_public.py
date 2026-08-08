"""Exhaustively verify every non-public status/reviewed/scan-passed
combination is unreachable via every public surface: home, detail, search,
and export -- not just the one combination used in the happy-path fixtures.
"""

import pytest

CASES = [
    pytest.param("draft", False, False, id="draft"),
    pytest.param("pending_review", False, False, id="pending_review"),
    pytest.param("approved", True, True, id="approved_but_not_published"),
    pytest.param("published", False, True, id="published_not_reviewed"),
    pytest.param("published", True, False, id="published_scan_not_passed"),
]


def _write_entry(tmp_content_dir, status: str, reviewed: bool, scan_passed: bool):
    frontmatter = (
        "title: Secret Entry\n"
        "date: 2026-07-01\n"
        f"status: {status}\n"
        f"reviewed: {str(reviewed).lower()}\n"
        "safety_scan:\n"
        f"  passed: {str(scan_passed).lower()}\n"
        "  findings: []\n"
        "  overrides: []\n"
        "media: []\n"
    )
    tmp_content_dir("2026-07-01-secret-entry.md", frontmatter, "This must never be public.")
    return tmp_content_dir.content_dir


@pytest.mark.parametrize("status,reviewed,scan_passed", CASES)
def test_non_public_entry_absent_from_home(
    client_factory, tmp_content_dir, status, reviewed, scan_passed
):
    content_dir = _write_entry(tmp_content_dir, status, reviewed, scan_passed)
    client = client_factory(content_dir)
    response = client.get("/")
    assert "Secret Entry" not in response.text


@pytest.mark.parametrize("status,reviewed,scan_passed", CASES)
def test_non_public_entry_detail_404s(
    client_factory, tmp_content_dir, status, reviewed, scan_passed
):
    content_dir = _write_entry(tmp_content_dir, status, reviewed, scan_passed)
    client = client_factory(content_dir)
    response = client.get("/entries/secret-entry")
    assert response.status_code == 404


@pytest.mark.parametrize("status,reviewed,scan_passed", CASES)
def test_non_public_entry_never_in_search(
    client_factory, tmp_content_dir, status, reviewed, scan_passed
):
    content_dir = _write_entry(tmp_content_dir, status, reviewed, scan_passed)
    client = client_factory(content_dir)
    response = client.get("/search?q=Secret")
    assert "Secret Entry" not in response.text


@pytest.mark.parametrize("status,reviewed,scan_passed", CASES)
def test_non_public_entry_never_in_export_json(
    client_factory, tmp_content_dir, status, reviewed, scan_passed
):
    content_dir = _write_entry(tmp_content_dir, status, reviewed, scan_passed)
    client = client_factory(content_dir)
    response = client.get("/export.json")
    assert "Secret Entry" not in response.text


@pytest.mark.parametrize("status,reviewed,scan_passed", CASES)
def test_non_public_entry_never_in_export_zip(
    client_factory, tmp_content_dir, status, reviewed, scan_passed
):
    import io
    import zipfile

    content_dir = _write_entry(tmp_content_dir, status, reviewed, scan_passed)
    client = client_factory(content_dir)
    response = client.get("/export.zip")
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        names = zf.namelist()
    assert not any("secret-entry" in n for n in names)


@pytest.mark.parametrize("status,reviewed,scan_passed", CASES)
def test_non_public_entry_never_in_milestones_or_archive(
    client_factory, tmp_content_dir, status, reviewed, scan_passed
):
    content_dir = _write_entry(tmp_content_dir, status, reviewed, scan_passed)
    client = client_factory(content_dir)
    assert "Secret Entry" not in client.get("/milestones").text
    assert "Secret Entry" not in client.get("/archive/2026").text
