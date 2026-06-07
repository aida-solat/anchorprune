"""Domain profile models.

AnchorPrune does not use a universal formula. Each domain provides its own
anchor-weight configuration, token budget, and governance thresholds.
"""

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field


class AnchorWeightConfig(BaseModel):
    """Coefficients for the anchor weighting equation.

    anchor_weight = authority*A + risk*R + evidence*E + relevance*T
                    + freshness*F - conflict*C - volatility*V
    """

    authority: float = 0.30
    risk: float = 0.25
    evidence: float = 0.20
    relevance: float = 0.15
    freshness: float = 0.10
    conflict: float = 0.20
    volatility: float = 0.10


class DomainProfile(BaseModel):
    name: str = "default"
    anchor_weight_config: AnchorWeightConfig = Field(default_factory=AnchorWeightConfig)

    token_budget: int = 16000

    # Governor thresholds (see RFC section 11).
    domain_anchor_threshold: float = 0.85
    runtime_anchor_threshold: float = 0.65
    milestone_threshold: float = 0.45

    # Eviction threshold for the anchor-aware pruner.
    payload_eviction_threshold: float = 0.25
    payload_compression_threshold: float = 0.55

    require_human_review_for_domain_anchors: bool = False

    metadata: Dict[str, Any] = Field(default_factory=dict)
