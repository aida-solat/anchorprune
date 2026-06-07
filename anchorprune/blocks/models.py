"""Payload block models.

Payload blocks are dynamic, potentially evictable pieces of state such as
conversation turns, intermediate drafts, tool outputs, logs, code attempts,
retrieved chunks, or model-generated reasoning artifacts.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return f"block_{uuid.uuid4().hex[:12]}"


class PayloadBlockType(str, Enum):
    USER_INPUT = "user_input"
    TOOL_OUTPUT = "tool_output"
    RETRIEVED_CHUNK = "retrieved_chunk"
    MODEL_OUTPUT = "model_output"
    INTERMEDIATE_DRAFT = "intermediate_draft"
    ERROR_LOG = "error_log"
    CODE_ATTEMPT = "code_attempt"


class PruningState(str, Enum):
    ACTIVE = "active"
    COMPRESSED = "compressed"
    QUARANTINED = "quarantined"
    EVICTED = "evicted"


class PayloadBlock(BaseModel):
    """A unit of evictable runtime state."""

    id: str = Field(default_factory=_new_id)
    block_type: PayloadBlockType
    content: str

    linked_anchor_ids: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)

    utility_score: float = Field(default=0.0)
    pruning_state: PruningState = PruningState.ACTIVE

    # Lifecycle flags (kept explicit for ergonomic checks and the spec's pruner).
    quarantined: bool = False
    compressed: bool = False
    evicted: bool = False

    # Signals consumed by the utility scorer.
    decision_impact: float = Field(default=0.0, ge=0.0, le=1.0)
    reuse_probability: float = Field(default=0.0, ge=0.0, le=1.0)
    uniqueness: float = Field(default=0.5, ge=0.0, le=1.0)
    redundancy: float = Field(default=0.0, ge=0.0, le=1.0)
    obsolete: bool = False
    conflict_severity: float = Field(default=0.0, ge=0.0, le=1.0)

    created_at: datetime = Field(default_factory=_now)
    step_index: int = 0
    token_estimate: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_alive(self) -> bool:
        return self.pruning_state not in (PruningState.EVICTED,)
