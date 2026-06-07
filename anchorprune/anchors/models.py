"""Core anchor data models.

Anchors are non-ordinary state objects representing constraints, policies,
schemas, facts, or decisions that should influence future reasoning steps.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AnchorClass(str, Enum):
    """The three layers of the hybrid anchor registry."""

    SYSTEM = "system"  # immutable, human-defined, highest priority
    DOMAIN = "domain"  # reviewable, extracted from trusted sources
    RUNTIME = "runtime"  # temporary facts/constraints discovered during a run


class AnchorType(str, Enum):
    """The semantic kind of an anchor (drives freshness sensitivity)."""

    POLICY = "policy"
    SCHEMA = "schema"
    CONSTRAINT = "constraint"
    FACT = "fact"
    DECISION = "decision"
    SECURITY = "security"
    COMPLIANCE_CERTIFICATE = "compliance_certificate"
    SUPPLIER_STOCK_STATUS = "supplier_stock_status"
    TEST_RESULT = "test_result"
    RUNTIME_ERROR = "runtime_error"


class AnchorPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AnchorStatus(str, Enum):
    APPROVED = "approved"
    QUARANTINED = "quarantined"
    EXPIRED = "expired"


class AnchorSource(str, Enum):
    """Where the candidate anchor originated, used for authority scoring."""

    HUMAN = "human"
    POLICY_DOCUMENT = "policy_document"
    TRUSTED_TOOL = "trusted_tool"
    MODEL_CROSS_VALIDATED = "model_cross_validated"
    MODEL_SINGLE = "model_single"
    MODEL_GUESS = "model_guess"


class Anchor(BaseModel):
    """An accepted anchor living in the governed state graph."""

    id: str = Field(default_factory=lambda: _new_id("anchor"))
    content: str
    anchor_class: AnchorClass
    anchor_type: AnchorType = AnchorType.CONSTRAINT
    priority: AnchorPriority = AnchorPriority.MEDIUM
    source: AnchorSource = AnchorSource.HUMAN

    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    status: AnchorStatus = AnchorStatus.APPROVED

    evidence_refs: List[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=_now)
    expires: Optional[str] = None  # e.g. "end_of_run" or an ISO timestamp
    reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_critical_system(self) -> bool:
        return (
            self.anchor_class == AnchorClass.SYSTEM
            and self.priority == AnchorPriority.CRITICAL
        )


class CandidateAnchor(BaseModel):
    """A proposed anchor that must pass through the Anchor Governor.

    A model may propose candidate anchors, but it should not directly create
    critical anchors.
    """

    content: str
    anchor_type: AnchorType = AnchorType.CONSTRAINT
    source: AnchorSource = AnchorSource.MODEL_SINGLE
    evidence_refs: List[str] = Field(default_factory=list)

    task_relevance: float = Field(default=0.5, ge=0.0, le=1.0)
    risk_impact: float = Field(default=0.5, ge=0.0, le=1.0)
    volatility: float = Field(default=0.5, ge=0.0, le=1.0)

    linked_block_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnchorDecisionAction(str, Enum):
    QUARANTINE = "quarantine"
    APPROVE_DOMAIN_ANCHOR = "approve_domain_anchor"
    APPROVE_RUNTIME_ANCHOR = "approve_runtime_anchor"
    RETAIN_AS_MILESTONE = "retain_as_milestone"
    REJECT = "reject"


class AnchorDecision(BaseModel):
    """The Anchor Governor's verdict on a candidate anchor."""

    action: AnchorDecisionAction
    weight: float = Field(ge=0.0, le=1.0)
    reason: Optional[str] = None
    expires: Optional[str] = None
    # Per-factor breakdown for auditability.
    score_breakdown: Dict[str, float] = Field(default_factory=dict)
