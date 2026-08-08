"""Media attachment model."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Literal

from pydantic import BaseModel, field_validator


class MediaAttachment(BaseModel):
    path: str
    alt: str
    caption: str | None = None
    media_type: Literal["image", "video", "audio"] = "image"
    reviewed_safe: bool = False

    @field_validator("path")
    @classmethod
    def no_traversal(cls, v: str) -> str:
        if not v:
            raise ValueError("media path must not be empty")
        normalized = v.replace("\\", "/")
        if normalized.startswith("/") or ":" in normalized:
            raise ValueError(f"media path must be relative, got {v!r}")
        parts = PurePosixPath(normalized).parts
        if ".." in parts:
            raise ValueError(f"media path must not contain '..', got {v!r}")
        return normalized

    @field_validator("alt")
    @classmethod
    def alt_required(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("media alt text is required and must not be empty")
        return v
