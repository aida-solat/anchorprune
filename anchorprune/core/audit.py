"""Audit Log.

Records every governance and pruning decision so a run can be explained after
the fact: which anchors were applied, what was quarantined, what was pruned.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AuditEventType(str, Enum):
    RUN_CREATED = "run_created"
    PAYLOAD_ADDED = "payload_added"
    ANCHOR_PROPOSED = "anchor_proposed"
    ANCHOR_DECISION = "anchor_decision"
    CONFLICT_DETECTED = "conflict_detected"
    PRUNING_ACTION = "pruning_action"
    CONTEXT_COMPOSED = "context_composed"
    STEP_COMPLETED = "step_completed"


class AuditEvent(BaseModel):
    id: str = Field(default_factory=lambda: f"audit_{uuid.uuid4().hex[:12]}")
    event_type: AuditEventType
    step_index: int = 0
    timestamp: datetime = Field(default_factory=_now)
    detail: Dict[str, Any] = Field(default_factory=dict)


class AuditLog:
    def __init__(self) -> None:
        self.events: List[AuditEvent] = []

    def record(
        self, event_type: AuditEventType, step_index: int = 0, **detail: Any
    ) -> AuditEvent:
        event = AuditEvent(event_type=event_type, step_index=step_index, detail=detail)
        self.events.append(event)
        return event

    def to_list(self) -> List[Dict[str, Any]]:
        return [e.model_dump(mode="json") for e in self.events]
