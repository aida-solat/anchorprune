"""Hybrid Anchor Registry.

Three layers: System (immutable), Domain (reviewable), Runtime (expirable).
The registry is a thin, query-friendly view over a GovernedStateGraph's anchors
plus a list of quarantined candidates.
"""

from __future__ import annotations

from typing import List

from anchorprune.anchors.models import (
    Anchor,
    AnchorClass,
    AnchorPriority,
    AnchorStatus,
    CandidateAnchor,
)


class HybridAnchorRegistry:
    def __init__(self) -> None:
        self.system: List[Anchor] = []
        self.domain: List[Anchor] = []
        self.runtime: List[Anchor] = []
        self.quarantined: List[CandidateAnchor] = []

    # ---- registration -----------------------------------------------------

    def add(self, anchor: Anchor) -> Anchor:
        if anchor.anchor_class == AnchorClass.SYSTEM:
            self.system.append(anchor)
        elif anchor.anchor_class == AnchorClass.DOMAIN:
            self.domain.append(anchor)
        else:
            self.runtime.append(anchor)
        return anchor

    def quarantine(self, candidate: CandidateAnchor) -> None:
        self.quarantined.append(candidate)

    # ---- queries ----------------------------------------------------------

    def all_anchors(self) -> List[Anchor]:
        return [*self.system, *self.domain, *self.runtime]

    def critical_system_anchors(self) -> List[Anchor]:
        return [
            a
            for a in self.system
            if a.priority == AnchorPriority.CRITICAL and a.status == AnchorStatus.APPROVED
        ]

    @classmethod
    def from_anchors(cls, anchors: List[Anchor]) -> "HybridAnchorRegistry":
        registry = cls()
        for anchor in anchors:
            registry.add(anchor)
        return registry
