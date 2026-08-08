from pathlib import Path

import pytest

from diary.content.loader import (
    EntryLoadError,
    load_all_entries,
    load_family_members,
    parse_entry_file,
)
from diary.models.review import PublicationStatus

FIXTURES = Path(__file__).parent.parent / "fixtures" / "sample_content"


class TestParseEntryFile:
    def test_parses_valid_published_entry(self):
        entry = parse_entry_file(FIXTURES / "entries" / "2026-05-01-first-steps.md")
        assert entry.frontmatter.title == "First Steps"
        assert entry.frontmatter.status == PublicationStatus.PUBLISHED
        assert entry.frontmatter.milestone is True
        assert "first steps" in entry.body_markdown.lower()
        assert entry.body_html is not None
        assert "<p>" in entry.body_html

    def test_parses_draft_entry(self):
        entry = parse_entry_file(FIXTURES / "entries" / "2026-06-01-draft-thoughts.md")
        assert entry.frontmatter.status == PublicationStatus.DRAFT
        assert entry.is_public is False

    def test_slug_derived_from_filename(self):
        entry = parse_entry_file(FIXTURES / "entries" / "2026-05-10-picnic-day.md")
        assert entry.slug == "picnic-day"

    def test_malformed_frontmatter_raises_entry_load_error(self, tmp_path):
        bad_file = tmp_path / "bad.md"
        bad_file.write_text(
            "---\ntitle: Missing Date\n---\nBody without a date field.\n",
            encoding="utf-8",
        )
        with pytest.raises(EntryLoadError):
            parse_entry_file(bad_file)


class TestLoadAllEntries:
    def test_loads_every_markdown_file(self):
        entries = load_all_entries(FIXTURES)
        assert len(entries) == 3

    def test_missing_entries_dir_returns_empty_list(self, tmp_path):
        assert load_all_entries(tmp_path) == []

    def test_skip_invalid_true_ignores_bad_files(self, tmp_path):
        entries_dir = tmp_path / "entries"
        entries_dir.mkdir()
        (entries_dir / "bad.md").write_text(
            "---\ntitle: no date\n---\nbody\n", encoding="utf-8"
        )
        (entries_dir / "good.md").write_text(
            "---\ntitle: Good\ndate: 2026-01-01\n---\nbody\n", encoding="utf-8"
        )
        entries = load_all_entries(tmp_path, skip_invalid=True)
        assert len(entries) == 1
        assert entries[0].frontmatter.title == "Good"

    def test_skip_invalid_false_raises_on_bad_file(self, tmp_path):
        entries_dir = tmp_path / "entries"
        entries_dir.mkdir()
        (entries_dir / "bad.md").write_text(
            "---\ntitle: no date\n---\nbody\n", encoding="utf-8"
        )
        with pytest.raises(EntryLoadError):
            load_all_entries(tmp_path, skip_invalid=False)


class TestLoadFamilyMembers:
    def test_loads_members_keyed_by_label(self):
        members = load_family_members(FIXTURES / "family_members.yaml")
        assert set(members) == {"Mom", "Dad", "Kid A"}
        assert members["Kid A"].role == "child"

    def test_missing_file_returns_empty_dict(self, tmp_path):
        assert load_family_members(tmp_path / "nope.yaml") == {}
