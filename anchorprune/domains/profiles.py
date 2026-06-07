"""Built-in domain profiles.

These coefficients are defaults, not universal constants. They are tuned per
domain following the RFC's example adjustments:

- Healthcare: higher risk impact and freshness weight.
- Compliance: higher authority and evidence weight.
- Coding agents: higher task relevance and volatility weight.
- Procurement: balanced risk, evidence, and authority weighting.
"""

from __future__ import annotations

from typing import Dict

from anchorprune.domains.models import AnchorWeightConfig, DomainProfile

BUILTIN_PROFILES: Dict[str, DomainProfile] = {
    "default": DomainProfile(name="default"),
    "procurement": DomainProfile(
        name="procurement",
        anchor_weight_config=AnchorWeightConfig(
            authority=0.28,
            risk=0.27,
            evidence=0.25,
            relevance=0.10,
            freshness=0.10,
            conflict=0.25,
            volatility=0.10,
        ),
        token_budget=24000,
        require_human_review_for_domain_anchors=True,
    ),
    "coding_agent": DomainProfile(
        name="coding_agent",
        anchor_weight_config=AnchorWeightConfig(
            authority=0.20,
            risk=0.15,
            evidence=0.15,
            relevance=0.30,
            freshness=0.10,
            conflict=0.20,
            volatility=0.20,
        ),
        token_budget=32000,
    ),
    "healthcare": DomainProfile(
        name="healthcare",
        anchor_weight_config=AnchorWeightConfig(
            authority=0.25,
            risk=0.30,
            evidence=0.20,
            relevance=0.10,
            freshness=0.15,
            conflict=0.25,
            volatility=0.10,
        ),
        token_budget=20000,
        require_human_review_for_domain_anchors=True,
    ),
    "compliance": DomainProfile(
        name="compliance",
        anchor_weight_config=AnchorWeightConfig(
            authority=0.32,
            risk=0.20,
            evidence=0.28,
            relevance=0.10,
            freshness=0.10,
            conflict=0.25,
            volatility=0.05,
        ),
        token_budget=24000,
        require_human_review_for_domain_anchors=True,
    ),
}


def get_domain_profile(name: str) -> DomainProfile:
    """Return a built-in profile by name, falling back to ``default``."""

    return BUILTIN_PROFILES.get(name, BUILTIN_PROFILES["default"]).model_copy(deep=True)
