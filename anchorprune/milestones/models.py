"""Reasoning milestone models.

Reasoning milestones are compact, high-utility summaries of decisions,
discoveries, resolved errors, unresolved risks, or important intermediate
findings that should be retained across execution steps.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return f"ms_{uuid.uuid4().hex[:12]}"


class ReasoningMilestone(BaseModel):
    id: str = Field(default_factory=_new_id)
    stage: str
    finding: str

    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    linked_anchor_ids: List[str] = Field(default_factory=list)
    linked_block_ids: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=_now)
    step_index: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
