"""Domain policy pack models (v0.7).

A *policy pack* is a reusable, local, static description of how AnchorPrune
should govern a particular domain: which constraints are critical anchors, how
the anchor-weight equation is tuned, which payloads are dangerous, how
time-sensitive each kind of state is, and what a valid decision context must
contain.

    Policy packs configure governance. They do not perform governance.

A pack is pure configuration. It never approves anchors, quarantines payloads,
or composes context — the Anchor Governor, pruner, and context composer still
own every decision. A pack only supplies the coefficients, seed anchors,
conflict patterns, and expectations those components consume.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field

Priority = Literal["critical", "high", "medium", "low"]
Severity = Literal["low", "medium", "high", "critical"]
Sensitivity = Literal["low", "medium", "high"]


class PackWeightConfig(BaseModel):
    """Coefficients for the anchor-weight equation (mirrors AnchorWeightConfig)."""

    authority: float = 0.30
    risk: float = 0.25
    evidence: float = 0.20
    relevance: float = 0.15
    freshness: float = 0.10
    conflict: float = 0.20
    volatility: float = 0.10


class PackDomainProfile(BaseModel):
    """Domain profile knobs a pack sets: budget, weights, pruning thresholds.

    Thresholds are ordered preserve >= compress >= milestone >= eviction and map
    onto the runtime's DomainProfile thresholds in :mod:`anchorprune.policy_packs.apply`.
    """

    token_budget: int = 32000
    weights: PackWeightConfig = Field(default_factory=PackWeightConfig)
    preserve_threshold: float = 0.85
    compress_threshold: float = 0.65
    milestone_threshold: float = 0.45
    eviction_threshold: float = 0.30


class PackAnchor(BaseModel):
    """A seed anchor the pack contributes (pre-approved, like a system anchor)."""

    id: str
    type: str = "policy"
    priority: Priority = "critical"
    content: str
    tags: List[str] = Field(default_factory=list)


class FreshnessRule(BaseModel):
    """Advisory time-sensitivity for a kind of state (consumed where supported)."""

    anchor_type: str
    sensitivity: Sensitivity


class ConflictPattern(BaseModel):
    """A regex pattern whose match in payload signals a governance conflict."""

    id: str
    severity: Severity = "high"
    pattern: str
    conflicts_with: List[str] = Field(default_factory=list)


class DecisionContextRules(BaseModel):
    """What a valid composed decision context must (and must not) contain."""

    must_include: List[str] = Field(default_factory=list)
    must_not_include: List[str] = Field(default_factory=list)


class DomainPolicyPack(BaseModel):
    """A reusable domain governance policy pack."""

    name: str
    version: str = "0.1"
    description: str = ""

    domain_profile: PackDomainProfile = Field(default_factory=PackDomainProfile)
    system_anchors: List[PackAnchor] = Field(default_factory=list)
    domain_anchors: List[PackAnchor] = Field(default_factory=list)
    freshness_rules: List[FreshnessRule] = Field(default_factory=list)
    conflict_patterns: List[ConflictPattern] = Field(default_factory=list)
    expected_milestone_patterns: List[str] = Field(default_factory=list)
    decision_context_rules: DecisionContextRules = Field(
        default_factory=DecisionContextRules
    )

    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def all_anchors(self) -> List[PackAnchor]:
        return list(self.system_anchors) + list(self.domain_anchors)
