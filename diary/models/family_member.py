"""Anonymized family member model."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class FamilyMember(BaseModel):
    label: str
    role: Literal["parent", "child", "grandparent", "other"] = "other"
    color: str | None = None
