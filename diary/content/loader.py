"""Load diary entries and family members from the content directory."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import frontmatter
import yaml
from pydantic import ValidationError

from diary.content.markdown_renderer import render_markdown_safe
from diary.models.entry import DiaryEntry, EntryFrontmatter
from diary.models.family_member import FamilyMember

ENTRY_GLOB = "**/*.md"


class EntryLoadError(Exception):
    """Raised when a content file cannot be parsed into a valid DiaryEntry."""

    def __init__(self, path: Path, original: Exception) -> None:
        self.path = path
        self.original = original
        super().__init__(f"Failed to load entry {path}: {original}")


def parse_entry_file(path: Path) -> DiaryEntry:
    """Parse a single Markdown+frontmatter file into a DiaryEntry."""
    try:
        post = frontmatter.load(path)
        fm = EntryFrontmatter.model_validate(post.metadata)
        body_html = render_markdown_safe(post.content)
        stat = path.stat()
        return DiaryEntry(
            frontmatter=fm,
            body_markdown=post.content,
            body_html=body_html,
            file_path=path,
            created_at=fm.reviewed_at or datetime.fromtimestamp(stat.st_ctime),
            updated_at=datetime.fromtimestamp(stat.st_mtime),
        )
    except (ValidationError, yaml.YAMLError, OSError) as exc:
        raise EntryLoadError(path, exc) from exc


def load_all_entries(content_dir: Path, *, skip_invalid: bool = False) -> list[DiaryEntry]:
    """Load every Markdown entry under content_dir/entries.

    If skip_invalid is False (default), a malformed entry raises EntryLoadError
    immediately -- fail loudly rather than silently dropping content from the
    safety-scan gate. Set skip_invalid=True only for tooling that intentionally
    tolerates partial content (not used for the public-facing app).
    """
    entries_dir = content_dir / "entries"
    if not entries_dir.exists():
        return []
    entries: list[DiaryEntry] = []
    for path in sorted(entries_dir.glob(ENTRY_GLOB)):
        try:
            entries.append(parse_entry_file(path))
        except EntryLoadError:
            if not skip_invalid:
                raise
    return entries


def load_family_members(path: Path) -> dict[str, FamilyMember]:
    """Load anonymized family member labels from family_members.yaml."""
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    members = [FamilyMember.model_validate(m) for m in data.get("members", [])]
    return {m.label: m for m in members}
