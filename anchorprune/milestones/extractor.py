"""Reasoning Milestone Extractor.

Produces compact milestones from payload blocks (typically when a block is
compressed) or directly from governor decisions that resolve to
``retain_as_milestone``.
"""

from __future__ import annotations

from anchorprune.anchors.models import CandidateAnchor
from anchorprune.blocks.models import PayloadBlock
from anchorprune.milestones.models import ReasoningMilestone
from anchorprune.pruning.compression import compress_block, compress_text


class MilestoneExtractor:
    def from_block(
        self,
        block: PayloadBlock,
        *,
        stage: str = "compression",
        confidence: float = 0.6,
        step_index: int = 0,
    ) -> ReasoningMilestone:
        return ReasoningMilestone(
            stage=stage,
            finding=compress_block(block),
            confidence=confidence,
            linked_anchor_ids=list(block.linked_anchor_ids),
            linked_block_ids=[block.id],
            evidence_refs=list(block.evidence_refs),
            step_index=step_index,
        )

    def from_candidate(
        self,
        candidate: CandidateAnchor,
        *,
        weight: float,
        step_index: int = 0,
        stage: str = "governor_retained",
    ) -> ReasoningMilestone:
        return ReasoningMilestone(
            stage=stage,
            finding=compress_text(candidate.content),
            confidence=weight,
            linked_block_ids=list(candidate.linked_block_ids),
            evidence_refs=list(candidate.evidence_refs),
            step_index=step_index,
        )
