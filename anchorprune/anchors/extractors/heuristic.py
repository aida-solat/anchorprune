"""Heuristic anchor extractor.

A thin adapter over the deterministic :class:`AnchorCandidateExtractor` so the
v0.3 pipeline can treat extraction uniformly. Its output is byte-for-byte
identical to the v0.1/v0.2 extractor, keeping the deterministic benchmark
unchanged.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, List, Optional

from anchorprune.anchors.extractor import AnchorCandidateExtractor
from anchorprune.anchors.extractors.base import AnchorExtractor, _evidence_index
from anchorprune.anchors.models import CandidateAnchor
from anchorprune.blocks.models import PayloadBlock
from anchorprune.evidence.linker import EvidenceLinker

if TYPE_CHECKING:  # pragma: no cover - typing only
    from anchorprune.core.state_graph import GovernedStateGraph
    from anchorprune.domains.models import DomainProfile


class HeuristicAnchorExtractor(AnchorExtractor):
    def __init__(
        self,
        linker: Optional[EvidenceLinker] = None,
        *,
        extra_directive_patterns: Optional[List["re.Pattern"]] = None,
    ) -> None:
        self._inner = AnchorCandidateExtractor(
            linker=linker, extra_directive_patterns=extra_directive_patterns
        )

    def extract_candidates(
        self,
        blocks: List[PayloadBlock],
        state_graph: Optional["GovernedStateGraph"] = None,
        domain_profile: Optional["DomainProfile"] = None,
    ) -> List[CandidateAnchor]:
        return self._inner.extract(blocks, _evidence_index(state_graph))
