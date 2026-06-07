"""Heuristic conflict detector.

Wraps the deterministic :func:`detect_conflict` engine over the full registry.
System-anchor conflicts are emitted as critical (hard-gate) edges.
"""

from __future__ import annotations

from typing import List, Optional

from anchorprune.anchors.models import CandidateAnchor
from anchorprune.anchors.registry import HybridAnchorRegistry
from anchorprune.conflicts.detector import ContradictionFn, detect_conflict
from anchorprune.conflicts.detectors.base import ConflictDetector
from anchorprune.conflicts.models import ConflictEdge


class HeuristicConflictDetector(ConflictDetector):
    def __init__(self, contradiction_fn: Optional[ContradictionFn] = None) -> None:
        self.contradiction_fn = contradiction_fn

    def detect(
        self, candidate: CandidateAnchor, registry: HybridAnchorRegistry
    ) -> List[ConflictEdge]:
        edges: List[ConflictEdge] = []
        for anchor in registry.all_anchors():
            edge = detect_conflict(candidate.content, anchor, self.contradiction_fn)
            if edge is not None:
                edges.append(edge)
        return edges
