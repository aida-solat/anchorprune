"""AnchorPrune: Governed Anchored State Pruning for Long-Running AI Agents.

AnchorPrune does not summarize agent history. It governs agent state.

It restructures an agent's working memory into a governed state graph of
immutable anchors, reviewable domain constraints, expirable runtime facts,
payload blocks, reasoning milestones, evidence references, and conflict edges,
and decides for each state object whether it is preserved, compressed,
quarantined, evicted, or promoted into an anchor candidate.
"""

from anchorprune.anchors.models import (
    Anchor,
    AnchorClass,
    AnchorDecision,
    AnchorDecisionAction,
    AnchorPriority,
    AnchorType,
    CandidateAnchor,
)
from anchorprune.blocks.models import PayloadBlock, PayloadBlockType
from anchorprune.conflicts.models import ConflictEdge, ConflictKind
from anchorprune.core.runtime import AnchorPruneRuntime, StepResult
from anchorprune.core.state_graph import GovernedStateGraph
from anchorprune.domains.models import AnchorWeightConfig, DomainProfile
from anchorprune.evidence.models import EvidenceRef, EvidenceSourceType
from anchorprune.llm.mock import MockLLM
from anchorprune.milestones.models import ReasoningMilestone

__version__ = "0.5.0"

__all__ = [
    "Anchor",
    "AnchorClass",
    "AnchorType",
    "AnchorPriority",
    "AnchorDecision",
    "AnchorDecisionAction",
    "CandidateAnchor",
    "PayloadBlock",
    "PayloadBlockType",
    "EvidenceRef",
    "EvidenceSourceType",
    "ReasoningMilestone",
    "ConflictEdge",
    "ConflictKind",
    "GovernedStateGraph",
    "DomainProfile",
    "AnchorWeightConfig",
    "AnchorPruneRuntime",
    "StepResult",
    "MockLLM",
    "__version__",
]
