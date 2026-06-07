"""Anchor Governor.

The control layer that decides whether a candidate anchor is approved as a
domain anchor, approved as a runtime anchor, retained as a milestone,
quarantined, or rejected.

A model may *propose* candidate anchors, but it must not directly create
critical anchors. Every candidate passes through the governor.
"""

from __future__ import annotations

from typing import Dict, Optional

from anchorprune.anchors.models import (
    Anchor,
    AnchorClass,
    AnchorDecision,
    AnchorDecisionAction,
    AnchorPriority,
    AnchorStatus,
    CandidateAnchor,
)
from anchorprune.anchors.registry import HybridAnchorRegistry
from anchorprune.anchors.weighting import (
    TRUSTED_SOURCES,
    compute_anchor_weight,
    estimate_risk_impact,
    estimate_volatility,
    score_authority,
    score_dynamic_freshness,
    score_task_relevance,
)
from anchorprune.conflicts.detector import ConflictDetector, ContradictionFn
from anchorprune.domains.models import DomainProfile
from anchorprune.evidence.models import EvidenceRef
from anchorprune.evidence.scorer import score_evidence_strength


class AnchorGovernor:
    def __init__(self, contradiction_fn: Optional[ContradictionFn] = None) -> None:
        self.detector = ConflictDetector(contradiction_fn=contradiction_fn)

    def evaluate_candidate_anchor(
        self,
        candidate: CandidateAnchor,
        registry: HybridAnchorRegistry,
        domain_profile: DomainProfile,
        evidence_index: Optional[Dict[str, EvidenceRef]] = None,
        age_days: Optional[float] = None,
    ) -> AnchorDecision:
        evidence_index = evidence_index or {}

        # 1. Pre-scoring hard gate (RFC section 9): system-anchor conflict.
        critical_conflict = self.detector.check_system_conflict(
            candidate, registry.critical_system_anchors()
        )
        if critical_conflict is not None:
            return AnchorDecision(
                action=AnchorDecisionAction.QUARANTINE,
                weight=0.0,
                reason="CRITICAL_CONFLICT_WITH_SYSTEM_ANCHOR",
                score_breakdown={"conflict": critical_conflict.severity},
            )

        w = domain_profile.anchor_weight_config

        authority = score_authority(candidate.source)
        risk = estimate_risk_impact(candidate)
        evidence = score_evidence_strength(candidate.evidence_refs, evidence_index)
        relevance = score_task_relevance(candidate)
        freshness = score_dynamic_freshness(candidate, candidate.anchor_type, age_days)
        conflict = self.detector.non_critical_conflict_severity(
            candidate, registry.all_anchors()
        )
        volatility = estimate_volatility(candidate)

        anchor_weight = compute_anchor_weight(
            w,
            authority=authority,
            risk=risk,
            evidence=evidence,
            relevance=relevance,
            freshness=freshness,
            conflict=conflict,
            volatility=volatility,
        )

        breakdown = {
            "authority": authority,
            "risk": risk,
            "evidence": evidence,
            "relevance": relevance,
            "freshness": freshness,
            "conflict": conflict,
            "volatility": volatility,
            "anchor_weight": anchor_weight,
        }

        # 2. Threshold ladder (RFC section 11).
        if (
            anchor_weight >= domain_profile.domain_anchor_threshold
            and candidate.source in TRUSTED_SOURCES
        ):
            return AnchorDecision(
                action=AnchorDecisionAction.APPROVE_DOMAIN_ANCHOR,
                weight=anchor_weight,
                score_breakdown=breakdown,
            )

        if anchor_weight >= domain_profile.runtime_anchor_threshold:
            return AnchorDecision(
                action=AnchorDecisionAction.APPROVE_RUNTIME_ANCHOR,
                weight=anchor_weight,
                expires="end_of_run",
                score_breakdown=breakdown,
            )

        if anchor_weight >= domain_profile.milestone_threshold:
            return AnchorDecision(
                action=AnchorDecisionAction.RETAIN_AS_MILESTONE,
                weight=anchor_weight,
                score_breakdown=breakdown,
            )

        return AnchorDecision(
            action=AnchorDecisionAction.REJECT,
            weight=anchor_weight,
            reason="LOW_ANCHOR_VALUE",
            score_breakdown=breakdown,
        )

    def decision_to_anchor(
        self, candidate: CandidateAnchor, decision: AnchorDecision
    ) -> Optional[Anchor]:
        """Materialize an approved decision into an Anchor (or None)."""

        if decision.action == AnchorDecisionAction.APPROVE_DOMAIN_ANCHOR:
            anchor_class = AnchorClass.DOMAIN
            priority = AnchorPriority.HIGH
        elif decision.action == AnchorDecisionAction.APPROVE_RUNTIME_ANCHOR:
            anchor_class = AnchorClass.RUNTIME
            priority = AnchorPriority.MEDIUM
        else:
            return None

        return Anchor(
            content=candidate.content,
            anchor_class=anchor_class,
            anchor_type=candidate.anchor_type,
            priority=priority,
            source=candidate.source,
            weight=decision.weight,
            status=AnchorStatus.APPROVED,
            evidence_refs=list(candidate.evidence_refs),
            expires=decision.expires,
            reason=decision.reason,
        )
