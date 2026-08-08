"""Publication status and safety-scan result models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PublicationStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    PUBLISHED = "published"


class SafetyFindingSeverity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SafetyScanResult(BaseModel):
    passed: bool = False
    last_scanned_at: datetime | None = None
    findings: list[str] = Field(default_factory=list)
    overrides: list[str] = Field(default_factory=list)
