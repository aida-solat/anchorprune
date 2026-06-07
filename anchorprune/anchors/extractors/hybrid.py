"""Hybrid anchor extractor.

Runs the deterministic heuristic extractor and a model-based extractor, then
merges their candidates (heuristic first, model candidates that are not near
duplicates appended). Both streams still flow through the Anchor Governor.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from anchorprune.anchors.extractors.base import AnchorExtractor
from anchorprune.anchors.extractors.heuristic import HeuristicAnchorExtractor
from anchorprune.anchors.extractors.model_based import ModelBasedAnchorExtractor
from anchorprune.anchors.models import CandidateAnchor
from anchorprune.blocks.models import PayloadBlock
from anchorprune.evidence.linker import EvidenceLinker
from anchorprune.llm.base import LLMClient

if TYPE_CHECKING:  # pragma: no cover - typing only
    from anchorprune.core.state_graph import GovernedStateGraph
    from anchorprune.domains.models import DomainProfile


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


class HybridAnchorExtractor(AnchorExtractor):
    def __init__(
        self,
        llm: LLMClient,
        *,
        linker: Optional[EvidenceLinker] = None,
        temperature: float = 0.0,
    ) -> None:
        self.heuristic = HeuristicAnchorExtractor(linker=linker)
        self.model = ModelBasedAnchorExtractor(llm, temperature=temperature)

    def extract_candidates(
        self,
        blocks: List[PayloadBlock],
        state_graph: Optional["GovernedStateGraph"] = None,
        domain_profile: Optional["DomainProfile"] = None,
    ) -> List[CandidateAnchor]:
        heuristic = self.heuristic.extract_candidates(blocks, state_graph, domain_profile)
        model = self.model.extract_candidates(blocks, state_graph, domain_profile)

        seen = {_norm(c.content) for c in heuristic}
        merged = list(heuristic)
        for cand in model:
            if _norm(cand.content) not in seen:
                merged.append(cand)
                seen.add(_norm(cand.content))
        return merged
