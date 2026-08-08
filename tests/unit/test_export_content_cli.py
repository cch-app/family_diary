import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from export_content import export_full_backup


class TestExportFullBackup:
    def test_includes_all_files_regardless_of_status(self, tmp_path):
        content_dir = tmp_path / "content"
        entries_dir = content_dir / "entries"
        entries_dir.mkdir(parents=True)
        (entries_dir / "draft.md").write_text(
            "---\ntitle: Draft\ndate: 2026-01-01\nstatus: draft\n---\nsecret draft body\n"
        )
        (entries_dir / "published.md").write_text(
            "---\ntitle: Published\ndate: 2026-01-02\nstatus: published\n---\nbody\n"
        )
        (content_dir / "family_members.yaml").write_text("members: []\n")

        out_dir = tmp_path / "backups"
        zip_path = export_full_backup(content_dir, out_dir)

        assert zip_path.exists()
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
        assert any("draft.md" in n for n in names)
        assert any("published.md" in n for n in names)
        assert any("family_members.yaml" in n for n in names)

    def test_creates_out_dir_if_missing(self, tmp_path):
        content_dir = tmp_path / "content"
        content_dir.mkdir()
        (content_dir / "file.txt").write_text("data")
        out_dir = tmp_path / "nested" / "backups"

        zip_path = export_full_backup(content_dir, out_dir)
        assert zip_path.exists()
        assert out_dir.exists()
