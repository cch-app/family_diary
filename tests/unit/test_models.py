from datetime import date, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from diary.models.entry import DiaryEntry, EntryFrontmatter, slug_from_filename
from diary.models.media import MediaAttachment
from diary.models.review import PublicationStatus, SafetyScanResult


def make_entry(
    *,
    status: PublicationStatus = PublicationStatus.PUBLISHED,
    reviewed: bool = True,
    scan_passed: bool = True,
    file_stem: str = "2026-05-01-first-steps",
    slug: str | None = None,
) -> DiaryEntry:
    fm = EntryFrontmatter(
        title="First Steps",
        date=date(2026, 5, 1),
        status=status,
        reviewed=reviewed,
        safety_scan=SafetyScanResult(passed=scan_passed),
        slug=slug,
    )
    return DiaryEntry(
        frontmatter=fm,
        body_markdown="Hello",
        body_html="<p>Hello</p>",
        file_path=Path(f"content/entries/2026/{file_stem}.md"),
        created_at=datetime(2026, 5, 1),
        updated_at=datetime(2026, 5, 1),
    )


class TestSlugFromFilename:
    def test_strips_date_prefix(self):
        assert slug_from_filename("2026-05-01-first-steps") == "first-steps"

    def test_no_date_prefix_returns_stem(self):
        assert slug_from_filename("first-steps") == "first-steps"


class TestDiaryEntrySlug:
    def test_uses_frontmatter_slug_when_present(self):
        entry = make_entry(slug="custom-slug")
        assert entry.slug == "custom-slug"

    def test_derives_slug_from_filename_when_absent(self):
        entry = make_entry(file_stem="2026-05-01-first-steps")
        assert entry.slug == "first-steps"


class TestIsPublicTruthTable:
    def test_published_reviewed_scan_passed_is_public(self):
        entry = make_entry(
            status=PublicationStatus.PUBLISHED, reviewed=True, scan_passed=True
        )
        assert entry.is_public is True

    def test_draft_is_not_public(self):
        entry = make_entry(
            status=PublicationStatus.DRAFT, reviewed=True, scan_passed=True
        )
        assert entry.is_public is False

    def test_pending_review_is_not_public(self):
        entry = make_entry(
            status=PublicationStatus.PENDING_REVIEW, reviewed=True, scan_passed=True
        )
        assert entry.is_public is False

    def test_approved_but_not_published_is_not_public(self):
        entry = make_entry(
            status=PublicationStatus.APPROVED, reviewed=True, scan_passed=True
        )
        assert entry.is_public is False

    def test_published_but_not_reviewed_is_not_public(self):
        entry = make_entry(
            status=PublicationStatus.PUBLISHED, reviewed=False, scan_passed=True
        )
        assert entry.is_public is False

    def test_published_reviewed_but_scan_not_passed_is_not_public(self):
        entry = make_entry(
            status=PublicationStatus.PUBLISHED, reviewed=True, scan_passed=False
        )
        assert entry.is_public is False


class TestMediaAttachmentValidation:
    def test_valid_relative_path_accepted(self):
        media = MediaAttachment(path="2026/05/photo.jpg", alt="A photo")
        assert media.path == "2026/05/photo.jpg"

    def test_absolute_path_rejected(self):
        with pytest.raises(ValidationError):
            MediaAttachment(path="/etc/passwd", alt="bad")

    def test_parent_traversal_rejected(self):
        with pytest.raises(ValidationError):
            MediaAttachment(path="../../etc/passwd", alt="bad")

    def test_traversal_in_middle_rejected(self):
        with pytest.raises(ValidationError):
            MediaAttachment(path="2026/../../../etc/passwd", alt="bad")

    def test_windows_style_absolute_rejected(self):
        with pytest.raises(ValidationError):
            MediaAttachment(path="C:/secrets/photo.jpg", alt="bad")

    def test_empty_alt_rejected(self):
        with pytest.raises(ValidationError):
            MediaAttachment(path="photo.jpg", alt="")

    def test_whitespace_only_alt_rejected(self):
        with pytest.raises(ValidationError):
            MediaAttachment(path="photo.jpg", alt="   ")

    def test_missing_alt_rejected(self):
        with pytest.raises(ValidationError):
            MediaAttachment(path="photo.jpg")
