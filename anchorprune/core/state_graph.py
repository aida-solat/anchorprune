"""Governed State Graph.

The MVP uses plain object references rather than a real graph database. Anchors,
payload blocks, evidence references, milestones, and conflict edges are stored in
dictionaries keyed by id.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List

from pydantic import BaseModel, Field

from anchorprune.anchors.models import Anchor, AnchorClass
from anchorprune.blocks.models import PayloadBlock, PruningState
from anchorprune.conflicts.models import ConflictEdge
from anchorprune.evidence.models import EvidenceRef
from anchorprune.milestones.models import ReasoningMilestone


def _now() -> datetime:
    return datetime.now(timezone.utc)


class GovernedStateGraph(BaseModel):
    run_id: str = Field(default_factory=lambda: f"run_{uuid.uuid4().hex[:12]}")
    goal: str = ""
    domain: str = "default"

    anchors: Dict[str, Anchor] = Field(default_factory=dict)
    payload_blocks: Dict[str, PayloadBlock] = Field(default_factory=dict)
    evidence_refs: Dict[str, EvidenceRef] = Field(default_factory=dict)
    milestones: Dict[str, ReasoningMilestone] = Field(default_factory=dict)
    conflict_edges: List[ConflictEdge] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    step_index: int = 0

    # ---- mutation helpers -------------------------------------------------

    def add_anchor(self, anchor: Anchor) -> Anchor:
        self.anchors[anchor.id] = anchor
        self.updated_at = _now()
        return anchor

    def add_payload_block(self, block: PayloadBlock) -> PayloadBlock:
        self.payload_blocks[block.id] = block
        self.updated_at = _now()
        return block

    def add_evidence(self, evidence: EvidenceRef) -> EvidenceRef:
        self.evidence_refs[evidence.id] = evidence
        self.updated_at = _now()
        return evidence

    def add_milestone(self, milestone: ReasoningMilestone) -> ReasoningMilestone:
        self.milestones[milestone.id] = milestone
        self.updated_at = _now()
        return milestone

    def add_conflict(self, edge: ConflictEdge) -> ConflictEdge:
        self.conflict_edges.append(edge)
        self.updated_at = _now()
        return edge

    # ---- query helpers ----------------------------------------------------

    def anchors_by_class(self, anchor_class: AnchorClass) -> List[Anchor]:
        return [a for a in self.anchors.values() if a.anchor_class == anchor_class]

    def system_anchors(self) -> List[Anchor]:
        return self.anchors_by_class(AnchorClass.SYSTEM)

    def domain_anchors(self) -> List[Anchor]:
        return self.anchors_by_class(AnchorClass.DOMAIN)

    def runtime_anchors(self) -> List[Anchor]:
        return self.anchors_by_class(AnchorClass.RUNTIME)

    def live_blocks(self) -> List[PayloadBlock]:
        return [
            b
            for b in self.payload_blocks.values()
            if b.pruning_state != PruningState.EVICTED
        ]

    def summary(self) -> Dict[str, int]:
        blocks = list(self.payload_blocks.values())
        return {
            "anchors": len(self.anchors),
            "system_anchors": len(self.system_anchors()),
            "domain_anchors": len(self.domain_anchors()),
            "runtime_anchors": len(self.runtime_anchors()),
            "payload_blocks": len([b for b in blocks if b.pruning_state != PruningState.EVICTED]),
            "milestones": len(self.milestones),
            "evidence_refs": len(self.evidence_refs),
            "quarantined_blocks": len(
                [b for b in blocks if b.pruning_state == PruningState.QUARANTINED]
            ),
            "evicted_blocks": len(
                [b for b in blocks if b.pruning_state == PruningState.EVICTED]
            ),
            "conflict_edges": len(self.conflict_edges),
        }
