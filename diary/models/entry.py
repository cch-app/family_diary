"""Diary entry and its frontmatter model."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from diary.models.media import MediaAttachment
from diary.models.review import PublicationStatus, SafetyScanResult

_SLUG_FROM_FILENAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-(?P<slug>.+)$")


def slug_from_filename(stem: str) -> str:
    match = _SLUG_FROM_FILENAME_RE.match(stem)
    return match.group("slug") if match else stem


class EntryFrontmatter(BaseModel):
    title: str
    date: date
    author_label: str | None = None
    family_members: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    milestone: bool = False
    status: PublicationStatus = PublicationStatus.DRAFT
    reviewed: bool = False
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    safety_scan: SafetyScanResult = Field(default_factory=SafetyScanResult)
    media: list[MediaAttachment] = Field(default_factory=list)
    slug: str | None = None
    excerpt: str | None = None


class DiaryEntry(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    frontmatter: EntryFrontmatter
    body_markdown: str
    body_html: str | None = None
    file_path: Path
    created_at: datetime
    updated_at: datetime

    @property
    def slug(self) -> str:
        if self.frontmatter.slug:
            return self.frontmatter.slug
        return slug_from_filename(self.file_path.stem)

    @property
    def is_public(self) -> bool:
        """Single, defense-in-depth source of truth for public visibility.

        Independent of whether the CLI safety-gate was ever run, so a bad
        frontmatter combination can never be rendered publicly.
        """
        return (
            self.frontmatter.status == PublicationStatus.PUBLISHED
            and self.frontmatter.reviewed is True
            and self.frontmatter.safety_scan.passed is True
        )
