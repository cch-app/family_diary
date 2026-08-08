import io
import json
import zipfile


class TestExportJson:
    def test_returns_only_published_entries(self, client):
        response = client.get("/export.json")
        assert response.status_code == 200
        data = response.json()
        titles = [e["title"] for e in data["entries"]]
        assert "First Steps" in titles
        assert "Picnic Day" in titles
        assert "Draft Thoughts" not in titles

    def test_entries_include_body_markdown(self, client):
        response = client.get("/export.json")
        data = response.json()
        first = next(e for e in data["entries"] if e["slug"] == "first-steps")
        assert "first steps" in first["body_markdown"].lower()

    def test_unreviewed_media_excluded(self, client):
        response = client.get("/export.json")
        data = response.json()
        first = next(e for e in data["entries"] if e["slug"] == "first-steps")
        assert all(m for m in first["media"])  # only reviewed_safe media present


def _build_zip_content_dir(tmp_path):
    content_dir = tmp_path / "content"
    entries_dir = content_dir / "entries"
    media_dir = content_dir / "media"
    entries_dir.mkdir(parents=True)
    media_dir.mkdir(parents=True)

    (media_dir / "safe.jpg").write_bytes(b"safe-photo-bytes")
    (media_dir / "unreviewed.jpg").write_bytes(b"unreviewed-photo-bytes")

    (entries_dir / "2026-05-01-first-steps.md").write_text(
        "---\n"
        'title: "First Steps"\n'
        "date: 2026-05-01\n"
        'author_label: "Mom"\n'
        "status: published\n"
        "reviewed: true\n"
        "safety_scan:\n"
        "  passed: true\n"
        "  findings: []\n"
        "  overrides: []\n"
        "media:\n"
        "  - path: safe.jpg\n"
        "    alt: Reviewed safe photo\n"
        "    reviewed_safe: true\n"
        "  - path: unreviewed.jpg\n"
        "    alt: UNREVIEWED-SECRET-MARKER\n"
        "    reviewed_safe: false\n"
        "---\n"
        "Today Kid A took their first steps.\n",
        encoding="utf-8",
    )
    return content_dir


class TestExportZipFiltering:
    def test_unreviewed_media_metadata_excluded_from_entry_file(self, client_factory, tmp_path):
        content_dir = _build_zip_content_dir(tmp_path)
        client = client_factory(content_dir)
        response = client.get("/export.zip")
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            entry_bytes = zf.read("entries/2026-05-01-first-steps.md")
        assert b"UNREVIEWED-SECRET-MARKER" not in entry_bytes
        assert b"unreviewed.jpg" not in entry_bytes
        assert b"Reviewed safe photo" in entry_bytes

    def test_reviewed_media_bytes_read_from_repo_content_dir(self, client_factory, tmp_path):
        content_dir = _build_zip_content_dir(tmp_path)
        client = client_factory(content_dir)
        response = client.get("/export.zip")
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            names = zf.namelist()
            assert "media/safe.jpg" in names
            assert zf.read("media/safe.jpg") == b"safe-photo-bytes"
            assert "media/unreviewed.jpg" not in names


class TestExportZip:
    def test_returns_zip_with_manifest(self, client):
        response = client.get("/export.zip")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            names = zf.namelist()
            assert "manifest.json" in names
            manifest = json.loads(zf.read("manifest.json"))
            slugs = [e["slug"] for e in manifest["entries"]]
            assert "first-steps" in slugs
            assert "picnic-day" in slugs

    def test_zip_excludes_draft_entries(self, client):
        response = client.get("/export.zip")
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            names = zf.namelist()
        assert not any("draft-thoughts" in n for n in names)

    def test_zip_only_includes_published_markdown_files(self, client):
        response = client.get("/export.zip")
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            names = [n for n in zf.namelist() if n.startswith("entries/")]
        assert len(names) == 2
