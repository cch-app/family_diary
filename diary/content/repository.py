"""In-memory content repository: the single query surface over loaded entries."""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path

from diary.content.loader import load_all_entries, load_family_members
from diary.models.entry import DiaryEntry
from diary.models.family_member import FamilyMember


class ContentRepository:
    def __init__(self, content_dir: Path):
        self.content_dir = content_dir
        self._all_entries: list[DiaryEntry] = load_all_entries(content_dir)
        self.family_members: dict[str, FamilyMember] = load_family_members(
            content_dir / "family_members.yaml"
        )

    @property
    def published_entries(self) -> list[DiaryEntry]:
        return sorted(
            (e for e in self._all_entries if e.is_public),
            key=lambda e: e.frontmatter.date,
            reverse=True,
        )

    def get_by_slug(self, slug: str) -> DiaryEntry | None:
        for entry in self._all_entries:
            if entry.slug == slug and entry.is_public:
                return entry
        return None

    def milestones(self) -> list[DiaryEntry]:
        return [e for e in self.published_entries if e.frontmatter.milestone]

    def by_year_month_day(
        self, year: int, month: int | None = None, day: int | None = None
    ) -> list[DiaryEntry]:
        result = []
        for e in self.published_entries:
            d = e.frontmatter.date
            if d.year != year:
                continue
            if month is not None and d.month != month:
                continue
            if day is not None and d.day != day:
                continue
            result.append(e)
        return result

    def all_tags(self) -> list[str]:
        tags: set[str] = set()
        for e in self.published_entries:
            tags.update(e.frontmatter.tags)
        return sorted(tags)

    def filter(
        self,
        *,
        family_member: str | None = None,
        tag: str | None = None,
        milestone: bool | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        query: str | None = None,
    ) -> list[DiaryEntry]:
        results = self.published_entries
        if family_member is not None:
            results = [e for e in results if family_member in e.frontmatter.family_members]
        if tag is not None:
            results = [e for e in results if tag in e.frontmatter.tags]
        if milestone is not None:
            results = [e for e in results if e.frontmatter.milestone is milestone]
        if date_from is not None:
            results = [e for e in results if e.frontmatter.date >= date_from]
        if date_to is not None:
            results = [e for e in results if e.frontmatter.date <= date_to]
        if query:
            results = self._match_query(results, query)
        return results

    def search(self, query: str) -> list[DiaryEntry]:
        return self._match_query(self.published_entries, query)

    @staticmethod
    def _match_query(entries: list[DiaryEntry], query: str) -> list[DiaryEntry]:
        needle = query.strip().lower()
        if not needle:
            return entries
        matched = []
        for e in entries:
            haystack = " ".join(
                [
                    e.frontmatter.title,
                    e.body_markdown,
                    " ".join(e.frontmatter.tags),
                ]
            ).lower()
            if needle in haystack:
                matched.append(e)
        return matched

    def is_media_reviewed_and_public(self, relative_path: str) -> bool:
        for entry in self._all_entries:
            if not entry.is_public:
                continue
            for media in entry.frontmatter.media:
                if media.path == relative_path and media.reviewed_safe:
                    return True
        return False


@lru_cache
def get_repository() -> ContentRepository:
    """FastAPI dependency: per-process singleton, rebuilt on cold start.

    Tests override this via app.dependency_overrides pointed at fixture
    content -- never the real content/ directory.
    """
    from diary.config import get_settings

    return ContentRepository(get_settings().content_dir)
