"""Application settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FAMILY_DIARY_")

    content_dir: Path = PROJECT_ROOT / "content"

    @property
    def media_dir(self) -> Path:
        return self.content_dir / "media"


@lru_cache
def get_settings() -> Settings:
    return Settings()
