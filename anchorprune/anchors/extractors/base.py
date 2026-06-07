"""Anchor extractor interface.

An extractor proposes :class:`CandidateAnchor` objects from payload blocks.
Crucially, extractors *never* create approved anchors directly. Every candidate
they emit must still pass through the Anchor Governor. This is the project's
constitutional rule:

    LLM proposes. Anchor Governor disposes.

Three modes are provided: ``heuristic`` (deterministic, CI-safe, the default),
``model_based`` (LLM-assisted), and ``hybrid`` (both, merged).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, List, Optional

from anchorprune.anchors.models import CandidateAnchor
from anchorprune.blocks.models import PayloadBlock

if TYPE_CHECKING:  # pragma: no cover - typing only
    from anchorprune.core.state_graph import GovernedStateGraph
    from anchorprune.domains.models import DomainProfile


def _evidence_index(state_graph: Optional["GovernedStateGraph"]) -> Dict:
    return dict(getattr(state_graph, "evidence_refs", {}) or {})


class AnchorExtractor(ABC):
    """Proposes candidate anchors. Output must always be candidates, not anchors."""

    @abstractmethod
    def extract_candidates(
        self,
        blocks: List[PayloadBlock],
        state_graph: Optional["GovernedStateGraph"] = None,
        domain_profile: Optional["DomainProfile"] = None,
    ) -> List[CandidateAnchor]:
        raise NotImplementedError
