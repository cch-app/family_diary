"""Public export/backup endpoints -- published content only.

Same public-safety gate as the web pages: drafts and unreviewed media are
never included, since these endpoints are publicly reachable.
"""

from __future__ import annotations

import io
import json
import zipfile
from datetime import UTC, datetime

import frontmatter
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse

from diary.content.repository import ContentRepository, get_repository

router = APIRouter()


def _entry_to_dict(entry) -> dict:
    return {
        "slug": entry.slug,
        "title": entry.frontmatter.title,
        "date": entry.frontmatter.date.isoformat(),
        "author_label": entry.frontmatter.author_label,
        "family_members": entry.frontmatter.family_members,
        "tags": entry.frontmatter.tags,
        "milestone": entry.frontmatter.milestone,
        "excerpt": entry.frontmatter.excerpt,
        "body_markdown": entry.body_markdown,
        "media": [
            {"path": m.path, "alt": m.alt, "caption": m.caption, "media_type": m.media_type}
            for m in entry.frontmatter.media
            if m.reviewed_safe
        ],
    }


def _entry_to_markdown_bytes(entry) -> bytes:
    """Serialize an entry using only its publicly-safe fields.

    Reuses _entry_to_dict's media filtering rather than writing entry.file_path
    directly, since the on-disk file also carries unreviewed media metadata and
    review-internal fields that must never reach a public export.
    """
    data = _entry_to_dict(entry)
    body = data.pop("body_markdown")
    post = frontmatter.Post(body, **data)
    return frontmatter.dumps(post).encode("utf-8")


@router.get("/export.json")
def export_json(repo: ContentRepository = Depends(get_repository)):
    data = {
        "exported_at": datetime.now(UTC).isoformat(),
        "entries": [_entry_to_dict(e) for e in repo.published_entries],
    }
    return JSONResponse(content=data)


@router.get("/export.zip")
def export_zip(repo: ContentRepository = Depends(get_repository)):
    buffer = io.BytesIO()
    manifest_entries = []

    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for entry in repo.published_entries:
            zf.writestr(
                f"entries/{entry.file_path.name}", _entry_to_markdown_bytes(entry)
            )
            manifest_entries.append({"slug": entry.slug, "title": entry.frontmatter.title})
            for media in entry.frontmatter.media:
                if not media.reviewed_safe:
                    continue
                media_path = repo.content_dir / "media" / media.path
                if media_path.is_file():
                    zf.writestr(f"media/{media.path}", media_path.read_bytes())

        manifest = {
            "exported_at": datetime.now(UTC).isoformat(),
            "entries": manifest_entries,
        }
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=family-diary-export.zip"},
    )
