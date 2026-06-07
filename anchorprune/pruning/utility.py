"""Payload utility scoring (implementation spec section 7).

payload_utility =
    0.30 * max_linked_anchor_weight
  + 0.20 * evidence_value
  + 0.20 * decision_impact
  + 0.15 * recency
  + 0.10 * reuse_probability
  + 0.05 * uniqueness
  - 0.20 * redundancy
  - 0.25 * obsolete_status
  - 0.30 * conflict_severity
"""

from __future__ import annotations

from anchorprune.blocks.models import PayloadBlock
from anchorprune.core.state_graph import GovernedStateGraph
from anchorprune.evidence.scorer import score_evidence_strength


def _recency(block: PayloadBlock, current_step: int) -> float:
    """1.0 for the current step, decaying linearly over a 6-step window."""

    age = max(0, current_step - block.step_index)
    return max(0.0, 1.0 - age / 6.0)


def max_linked_anchor_weight(block: PayloadBlock, state_graph: GovernedStateGraph) -> float:
    weights = [
        state_graph.anchors[a_id].weight
        for a_id in block.linked_anchor_ids
        if a_id in state_graph.anchors
    ]
    return max(weights) if weights else 0.0


def score_payload_block(
    block: PayloadBlock,
    state_graph: GovernedStateGraph,
    current_step: int,
) -> float:
    anchor_weight = max_linked_anchor_weight(block, state_graph)
    evidence_value = score_evidence_strength(block.evidence_refs, state_graph.evidence_refs)
    recency = _recency(block, current_step)

    utility = (
        0.30 * anchor_weight
        + 0.20 * evidence_value
        + 0.20 * block.decision_impact
        + 0.15 * recency
        + 0.10 * block.reuse_probability
        + 0.05 * block.uniqueness
        - 0.20 * block.redundancy
        - 0.25 * (1.0 if block.obsolete else 0.0)
        - 0.30 * block.conflict_severity
    )
    return max(0.0, min(1.0, utility))
