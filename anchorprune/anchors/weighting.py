"""Anchor weighting engine.

Implements the scoring functions behind the anchor weighting equation
(RFC sections 6-8):

    anchor_weight = αA·authority + αR·risk + αE·evidence + αT·relevance
                    + αF·freshness - βC·conflict - βV·volatility
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from anchorprune.anchors.models import AnchorSource, AnchorType, CandidateAnchor
from anchorprune.domains.models import AnchorWeightConfig
from anchorprune.evidence.models import EvidenceRef

# RFC section 7: Authority Level Reference.
AUTHORITY_LEVELS: Dict[AnchorSource, float] = {
    AnchorSource.HUMAN: 1.00,
    AnchorSource.POLICY_DOCUMENT: 0.90,
    AnchorSource.TRUSTED_TOOL: 0.75,
    AnchorSource.MODEL_CROSS_VALIDATED: 0.55,
    AnchorSource.MODEL_SINGLE: 0.30,
    AnchorSource.MODEL_GUESS: 0.10,
}

# RFC section 8: per-type freshness sensitivity (1.0 = highly time-sensitive).
FRESHNESS_SENSITIVITY: Dict[AnchorType, float] = {
    AnchorType.SECURITY: 0.05,
    AnchorType.SCHEMA: 0.05,
    AnchorType.POLICY: 0.1,
    AnchorType.CONSTRAINT: 0.2,
    AnchorType.DECISION: 0.3,
    AnchorType.COMPLIANCE_CERTIFICATE: 0.5,
    AnchorType.FACT: 0.6,
    AnchorType.SUPPLIER_STOCK_STATUS: 0.9,
    AnchorType.TEST_RESULT: 0.9,
    AnchorType.RUNTIME_ERROR: 0.95,
}

# Sources that may be promoted directly to a domain anchor.
TRUSTED_SOURCES = {
    AnchorSource.HUMAN,
    AnchorSource.POLICY_DOCUMENT,
    AnchorSource.TRUSTED_TOOL,
}


def score_authority(source: AnchorSource) -> float:
    return AUTHORITY_LEVELS.get(source, 0.1)


def estimate_risk_impact(candidate: CandidateAnchor) -> float:
    return _clamp(candidate.risk_impact)


def score_evidence(
    evidence_ref_ids: Iterable[str],
    evidence_index: Optional[Dict[str, EvidenceRef]] = None,
) -> float:
    """Evidence strength = strongest available supporting reference.

    No evidence yields 0.0. With an index, we use the maximum effective
    reliability of the linked references; otherwise we approximate by count.
    """

    ids = list(evidence_ref_ids)
    if not ids:
        return 0.0
    if evidence_index:
        reliabilities = [
            evidence_index[i].effective_reliability for i in ids if i in evidence_index
        ]
        if reliabilities:
            return _clamp(max(reliabilities))
    # Fallback: diminishing returns on raw count.
    return _clamp(min(1.0, 0.4 + 0.2 * len(ids)))


def score_task_relevance(candidate: CandidateAnchor) -> float:
    return _clamp(candidate.task_relevance)


def score_dynamic_freshness(
    candidate: CandidateAnchor,
    anchor_type: AnchorType,
    age_days: Optional[float] = None,
) -> float:
    """Freshness score in [0, 1]; 1.0 means "as good as fresh".

    Low-sensitivity types (security, schema) stay near 1.0 regardless of age.
    High-sensitivity types decay quickly with age.
    """

    sensitivity = FRESHNESS_SENSITIVITY.get(anchor_type, 0.3)
    if age_days is None:
        # Unknown age: assume fresh, lightly discounted by sensitivity.
        return _clamp(1.0 - 0.1 * sensitivity)
    decay = sensitivity * min(1.0, age_days / 30.0)
    return _clamp(1.0 - decay)


def estimate_volatility(candidate: CandidateAnchor) -> float:
    return _clamp(candidate.volatility)


def compute_anchor_weight(
    config: AnchorWeightConfig,
    *,
    authority: float,
    risk: float,
    evidence: float,
    relevance: float,
    freshness: float,
    conflict: float,
    volatility: float,
) -> float:
    weight = (
        config.authority * authority
        + config.risk * risk
        + config.evidence * evidence
        + config.relevance * relevance
        + config.freshness * freshness
        - config.conflict * conflict
        - config.volatility * volatility
    )
    return _clamp(weight)


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))
