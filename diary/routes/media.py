"""Review-gated media file serving.

Deliberately not a blind StaticFiles mount on content/media: a file that
physically exists on disk but has not been marked reviewed_safe on a
published entry must never be servable.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from diary.content.repository import ContentRepository, get_repository

router = APIRouter()


def resolve_within(relative_path: str, base_dir: Path) -> Path:
    base = base_dir.resolve()
    candidate = (base / relative_path).resolve()
    if candidate != base and os.path.commonpath([candidate, base]) != str(base):
        raise HTTPException(status_code=404)
    return candidate


@router.get("/media/{path:path}")
def serve_media(path: str, repo: ContentRepository = Depends(get_repository)):
    # media_dir is derived from the (test-overridable) repo's own content_dir,
    # not the un-overridden global settings, so serving stays consistent with
    # whichever content directory the repository dependency was built from.
    safe_path = resolve_within(path, repo.content_dir / "media")

    if not repo.is_media_reviewed_and_public(path):
        raise HTTPException(status_code=404)

    if not safe_path.is_file():
        raise HTTPException(status_code=404)

    return FileResponse(
        safe_path, headers={"Cache-Control": "public, max-age=31536000, immutable"}
    )
