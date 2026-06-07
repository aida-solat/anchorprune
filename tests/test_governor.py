from anchorprune.anchors.governor import AnchorGovernor
from anchorprune.anchors.models import (
    Anchor,
    AnchorClass,
    AnchorDecisionAction,
    AnchorPriority,
    AnchorSource,
    AnchorType,
    CandidateAnchor,
)
from anchorprune.anchors.registry import HybridAnchorRegistry
from anchorprune.domains.profiles import get_domain_profile
from anchorprune.evidence.models import EvidenceRef, EvidenceSourceType


def _registry_with_system(content: str) -> HybridAnchorRegistry:
    reg = HybridAnchorRegistry()
    reg.add(
        Anchor(
            content=content,
            anchor_class=AnchorClass.SYSTEM,
            anchor_type=AnchorType.POLICY,
            priority=AnchorPriority.CRITICAL,
        )
    )
    return reg


def test_hard_gate_quarantines_system_conflict():
    gov = AnchorGovernor()
    reg = _registry_with_system("Purchases above 50000 require human approval.")
    candidate = CandidateAnchor(
        content="Purchases above 50000 do not require human approval.",
        source=AnchorSource.MODEL_SINGLE,
    )
    decision = gov.evaluate_candidate_anchor(candidate, reg, get_domain_profile("procurement"))
    assert decision.action == AnchorDecisionAction.QUARANTINE
    assert decision.weight == 0.0
    assert decision.reason == "CRITICAL_CONFLICT_WITH_SYSTEM_ANCHOR"


def test_human_high_evidence_becomes_domain_anchor():
    gov = AnchorGovernor()
    reg = HybridAnchorRegistry()
    ev = EvidenceRef(source_type=EvidenceSourceType.POLICY_FILE, locator="policy://x")
    candidate = CandidateAnchor(
        content="Vendors must hold valid ISO9001 certification.",
        source=AnchorSource.HUMAN,
        anchor_type=AnchorType.POLICY,
        evidence_refs=[ev.id],
        task_relevance=0.9,
        risk_impact=0.9,
        volatility=0.0,
    )
    decision = gov.evaluate_candidate_anchor(
        candidate, reg, get_domain_profile("procurement"), evidence_index={ev.id: ev}
    )
    assert decision.action == AnchorDecisionAction.APPROVE_DOMAIN_ANCHOR
    assert decision.weight >= 0.85


def test_weak_model_guess_is_rejected_or_milestone():
    gov = AnchorGovernor()
    reg = HybridAnchorRegistry()
    candidate = CandidateAnchor(
        content="Maybe supplier C is cheaper somewhere.",
        source=AnchorSource.MODEL_GUESS,
        task_relevance=0.1,
        risk_impact=0.1,
        volatility=0.9,
    )
    decision = gov.evaluate_candidate_anchor(candidate, reg, get_domain_profile("default"))
    assert decision.action in (
        AnchorDecisionAction.REJECT,
        AnchorDecisionAction.RETAIN_AS_MILESTONE,
    )


def test_decision_to_anchor_classes():
    gov = AnchorGovernor()
    candidate = CandidateAnchor(content="x", source=AnchorSource.TRUSTED_TOOL)
    from anchorprune.anchors.models import AnchorDecision

    domain = gov.decision_to_anchor(
        candidate,
        AnchorDecision(action=AnchorDecisionAction.APPROVE_DOMAIN_ANCHOR, weight=0.9),
    )
    runtime = gov.decision_to_anchor(
        candidate,
        AnchorDecision(action=AnchorDecisionAction.APPROVE_RUNTIME_ANCHOR, weight=0.7),
    )
    assert domain.anchor_class == AnchorClass.DOMAIN
    assert runtime.anchor_class == AnchorClass.RUNTIME
