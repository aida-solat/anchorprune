"""Hybrid conflict detector.

Combines the authoritative heuristic hard gate with optional model-assisted
semantic signals. The contract is strict:

- Every heuristic edge is preserved, unchanged. Critical (system-anchor) edges
  are hard gates and are never removed or downgraded.
- Model edges are added only as NON-critical signals, and only for anchors the
  heuristic did not already flag as critical.

So a model can enrich detection but can never override or clear a hard gate.
"""

from __future__ import annotations

from typing import List, Optional

from anchorprune.anchors.models import CandidateAnchor
from anchorprune.anchors.registry import HybridAnchorRegistry
from anchorprune.conflicts.detector import ContradictionFn
from anchorprune.conflicts.detectors.base import ConflictDetector
from anchorprune.conflicts.detectors.heuristic import HeuristicConflictDetector
from anchorprune.conflicts.detectors.model_based import ModelAssistedConflictDetector
from anchorprune.conflicts.models import ConflictEdge
from anchorprune.llm.base import LLMClient


class HybridConflictDetector(ConflictDetector):
    def __init__(
        self,
        llm: LLMClient,
        *,
        contradiction_fn: Optional[ContradictionFn] = None,
        temperature: float = 0.0,
    ) -> None:
        self.heuristic = HeuristicConflictDetector(contradiction_fn=contradiction_fn)
        self.model = ModelAssistedConflictDetector(llm, temperature=temperature)

    def detect(
        self, candidate: CandidateAnchor, registry: HybridAnchorRegistry
    ) -> List[ConflictEdge]:
        heuristic_edges = self.heuristic.detect(candidate, registry)
        # Hard gates and any heuristic-flagged targets are authoritative.
        critical_targets = {e.target_ref for e in heuristic_edges if e.critical}

        merged: List[ConflictEdge] = list(heuristic_edges)
        for edge in self.model.detect(candidate, registry):
            # A model signal can never apply to a target already hard-gated, and
            # is always forced non-critical regardless of model claims.
            if edge.target_ref in critical_targets:
                continue
            if edge.critical:
                edge = edge.model_copy(update={"critical": False})
            merged.append(edge)
        return merged
