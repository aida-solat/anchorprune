"""Conflict edge models.

Conflict edges represent detected contradictions or incompatibilities between
candidate anchors, existing anchors, payload blocks, or policy constraints.
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def _new_id() -> str:
    return f"conflict_{uuid.uuid4().hex[:12]}"


class ConflictKind(str, Enum):
    SYSTEM_ANCHOR = "system_anchor"  # critical: triggers a hard gate
    DOMAIN_ANCHOR = "domain_anchor"  # non-critical penalty
    PAYLOAD = "payload"  # contradicts existing payload state


class ConflictEdge(BaseModel):
    id: str = Field(default_factory=_new_id)
    source_ref: str  # candidate/block identifier
    target_ref: str  # anchor/block identifier it conflicts with
    kind: ConflictKind
    severity: float = Field(default=0.5, ge=0.0, le=1.0)
    critical: bool = False
    reason: Optional[str] = None
