"""Anchor-Aware Pruner (implementation spec section 8, RFC section 10).

Pruning decisions depend on the relationship between a payload block and the
anchors it links to, not only on a token budget:

    linked to critical system anchor   -> preserve intact
    linked to high-weight domain anchor -> preserve or compress carefully
    linked only to runtime anchors      -> compress into a milestone
    conflicts with a system anchor       -> quarantine
    low utility, no strong linkage       -> evict
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from anchorprune.anchors.models import AnchorClass
from anchorprune.blocks.models import PayloadBlock, PruningState
from anchorprune.core.state_graph import GovernedStateGraph
from anchorprune.domains.models import DomainProfile
from anchorprune.milestones.extractor import MilestoneExtractor
from anchorprune.pruning.compression import compress_block
from anchorprune.pruning.utility import score_payload_block

HIGH_WEIGHT_DOMAIN = 0.7


class PruningOp(str, Enum):
    PRESERVE = "preserve"
    COMPRESS = "compress"
    QUARANTINE = "quarantine"
    EVICT = "evict"


class PruningAction(BaseModel):
    block_id: str
    op: PruningOp
    utility_score: float
    reason: str


def _linked_anchor_classes(block: PayloadBlock, graph: GovernedStateGraph):
    return [
        graph.anchors[a_id]
        for a_id in block.linked_anchor_ids
        if a_id in graph.anchors
    ]


class AnchorAwarePruner:
    def __init__(self, milestone_extractor: Optional[MilestoneExtractor] = None) -> None:
        self.milestone_extractor = milestone_extractor or MilestoneExtractor()

    def prune(
        self, graph: GovernedStateGraph, domain_profile: DomainProfile
    ) -> List[PruningAction]:
        actions: List[PruningAction] = []

        for block in list(graph.payload_blocks.values()):
            if block.pruning_state == PruningState.EVICTED:
                continue

            # 1. Quarantine unsafe conflicts first.
            if block.quarantined or block.pruning_state == PruningState.QUARANTINED:
                block.pruning_state = PruningState.QUARANTINED
                block.quarantined = True
                actions.append(
                    PruningAction(
                        block_id=block.id,
                        op=PruningOp.QUARANTINE,
                        utility_score=block.utility_score,
                        reason="conflicts_with_system_anchor",
                    )
                )
                continue

            utility = score_payload_block(block, graph, graph.step_index)
            block.utility_score = utility

            linked = _linked_anchor_classes(block, graph)
            has_critical_system = any(a.is_critical_system for a in linked)
            has_high_domain = any(
                a.anchor_class == AnchorClass.DOMAIN and a.weight >= HIGH_WEIGHT_DOMAIN
                for a in linked
            )
            only_runtime = bool(linked) and all(
                a.anchor_class == AnchorClass.RUNTIME for a in linked
            )

            # 2. Preserve blocks tied to critical system anchors, intact.
            if has_critical_system:
                actions.append(
                    self._preserve(block, utility, "linked_to_critical_system_anchor")
                )
                continue

            # 3. High-weight domain anchor: preserve, or compress carefully.
            if has_high_domain:
                if utility < domain_profile.payload_compression_threshold:
                    actions.append(self._compress(block, graph, utility, "domain_anchor_compress"))
                else:
                    actions.append(self._preserve(block, utility, "linked_to_high_domain_anchor"))
                continue

            # 4. Only runtime anchors: compress into a milestone when low utility.
            if only_runtime and utility < domain_profile.payload_compression_threshold:
                actions.append(self._compress(block, graph, utility, "runtime_only_compress"))
                continue

            # 5. Low utility, no strong linkage: evict.
            if utility < domain_profile.payload_eviction_threshold and not linked:
                actions.append(self._evict(block, utility, "low_utility_no_anchor"))
                continue

            # 6. Default: preserve, but compress mid-utility blocks to save budget.
            if utility < domain_profile.payload_compression_threshold:
                actions.append(self._compress(block, graph, utility, "mid_utility_compress"))
            else:
                actions.append(self._preserve(block, utility, "sufficient_utility"))

        return actions

    # ---- operations -------------------------------------------------------

    def _preserve(self, block: PayloadBlock, utility: float, reason: str) -> PruningAction:
        block.pruning_state = PruningState.ACTIVE
        return PruningAction(
            block_id=block.id, op=PruningOp.PRESERVE, utility_score=utility, reason=reason
        )

    def _compress(
        self, block: PayloadBlock, graph: GovernedStateGraph, utility: float, reason: str
    ) -> PruningAction:
        if not block.compressed:
            milestone = self.milestone_extractor.from_block(
                block, stage=reason, confidence=max(0.4, utility), step_index=graph.step_index
            )
            graph.add_milestone(milestone)
            block.content = compress_block(block)
            block.token_estimate = max(1, len(block.content) // 4)
        block.compressed = True
        block.pruning_state = PruningState.COMPRESSED
        return PruningAction(
            block_id=block.id, op=PruningOp.COMPRESS, utility_score=utility, reason=reason
        )

    def _evict(self, block: PayloadBlock, utility: float, reason: str) -> PruningAction:
        block.evicted = True
        block.pruning_state = PruningState.EVICTED
        return PruningAction(
            block_id=block.id, op=PruningOp.EVICT, utility_score=utility, reason=reason
        )
