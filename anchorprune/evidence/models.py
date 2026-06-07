"""Evidence reference models.

Evidence references link anchors, milestones, and payload blocks to source
documents, tool outputs, database records, or other trusted evidence.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return f"ev_{uuid.uuid4().hex[:12]}"


class EvidenceSourceType(str, Enum):
    DOCUMENT = "document"
    DATABASE = "database"
    TOOL_OUTPUT = "tool_output"
    HUMAN_INPUT = "human_input"
    POLICY_FILE = "policy_file"
    CODE_REPOSITORY = "code_repository"
    MODEL_INFERENCE = "model_inference"


# Default per-source reliability used by the evidence scorer.
SOURCE_RELIABILITY: Dict[EvidenceSourceType, float] = {
    EvidenceSourceType.POLICY_FILE: 0.95,
    EvidenceSourceType.HUMAN_INPUT: 0.9,
    EvidenceSourceType.DOCUMENT: 0.8,
    EvidenceSourceType.DATABASE: 0.8,
    EvidenceSourceType.CODE_REPOSITORY: 0.75,
    EvidenceSourceType.TOOL_OUTPUT: 0.7,
    EvidenceSourceType.MODEL_INFERENCE: 0.3,
}


class EvidenceRef(BaseModel):
    id: str = Field(default_factory=_new_id)
    source_type: EvidenceSourceType
    locator: str  # e.g. file path, URL, table:row, tool name
    snippet: Optional[str] = None

    # Optional explicit reliability override (0..1). Falls back to source default.
    reliability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    freshness_days: Optional[float] = Field(default=None, ge=0.0)

    created_at: datetime = Field(default_factory=_now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def effective_reliability(self) -> float:
        if self.reliability is not None:
            return self.reliability
        return SOURCE_RELIABILITY.get(self.source_type, 0.5)
