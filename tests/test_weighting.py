from anchorprune.anchors.models import AnchorSource, AnchorType, CandidateAnchor
from anchorprune.anchors.weighting import (
    AUTHORITY_LEVELS,
    compute_anchor_weight,
    score_authority,
    score_dynamic_freshness,
)
from anchorprune.domains.models import AnchorWeightConfig


def test_authority_ordering():
    assert score_authority(AnchorSource.HUMAN) == 1.0
    assert score_authority(AnchorSource.MODEL_GUESS) < score_authority(
        AnchorSource.MODEL_SINGLE
    )
    assert AUTHORITY_LEVELS[AnchorSource.POLICY_DOCUMENT] == 0.90


def test_freshness_sensitivity_by_type():
    cand = CandidateAnchor(content="x")
    fresh_security = score_dynamic_freshness(cand, AnchorType.SECURITY, age_days=60)
    fresh_stock = score_dynamic_freshness(cand, AnchorType.SUPPLIER_STOCK_STATUS, age_days=60)
    # Security barely decays; stock status decays a lot.
    assert fresh_security > 0.9
    assert fresh_stock < fresh_security


def test_anchor_weight_is_clamped():
    cfg = AnchorWeightConfig()
    w = compute_anchor_weight(
        cfg,
        authority=1.0,
        risk=1.0,
        evidence=1.0,
        relevance=1.0,
        freshness=1.0,
        conflict=0.0,
        volatility=0.0,
    )
    assert 0.0 <= w <= 1.0

    w_low = compute_anchor_weight(
        cfg,
        authority=0.0,
        risk=0.0,
        evidence=0.0,
        relevance=0.0,
        freshness=0.0,
        conflict=1.0,
        volatility=1.0,
    )
    assert w_low == 0.0
