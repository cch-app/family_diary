from pathlib import Path


def _build_content_dir(tmp_path: Path, *, reviewed_safe: bool) -> Path:
    content_dir = tmp_path / "content"
    entries_dir = content_dir / "entries"
    media_dir = content_dir / "media"
    entries_dir.mkdir(parents=True)
    media_dir.mkdir(parents=True)

    (media_dir / "photo.jpg").write_bytes(b"fake-jpeg-bytes")
    (media_dir / "unreferenced.jpg").write_bytes(b"fake-jpeg-bytes-2")

    reviewed_yaml = "true" if reviewed_safe else "false"
    (entries_dir / "2026-01-01-entry.md").write_text(
        "---\n"
        "title: Entry\n"
        "date: 2026-01-01\n"
        "status: published\n"
        "reviewed: true\n"
        "safety_scan:\n"
        "  passed: true\n"
        "  findings: []\n"
        "  overrides: []\n"
        "media:\n"
        "  - path: photo.jpg\n"
        "    alt: A photo\n"
        f"    reviewed_safe: {reviewed_yaml}\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )
    return content_dir


class TestMediaRoute:
    def test_reviewed_safe_media_serves(self, client_factory, tmp_path):
        content_dir = _build_content_dir(tmp_path, reviewed_safe=True)
        client = client_factory(content_dir)
        response = client.get("/media/photo.jpg")
        assert response.status_code == 200
        assert response.content == b"fake-jpeg-bytes"

    def test_unreviewed_media_referenced_on_entry_404s(self, client_factory, tmp_path):
        content_dir = _build_content_dir(tmp_path, reviewed_safe=False)
        client = client_factory(content_dir)
        response = client.get("/media/photo.jpg")
        assert response.status_code == 404

    def test_file_present_on_disk_but_unreferenced_404s(self, client_factory, tmp_path):
        content_dir = _build_content_dir(tmp_path, reviewed_safe=True)
        client = client_factory(content_dir)
        response = client.get("/media/unreferenced.jpg")
        assert response.status_code == 404

    def test_path_traversal_blocked(self, client_factory, tmp_path):
        content_dir = _build_content_dir(tmp_path, reviewed_safe=True)
        client = client_factory(content_dir)
        response = client.get("/media/../family_members.yaml")
        assert response.status_code == 404

    def test_reviewed_safe_media_has_immutable_cache_header(self, client_factory, tmp_path):
        content_dir = _build_content_dir(tmp_path, reviewed_safe=True)
        client = client_factory(content_dir)
        response = client.get("/media/photo.jpg")
        assert "immutable" in response.headers.get("cache-control", "")
