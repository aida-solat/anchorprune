"""Conflict detector interface (v0.3 adapter layer).

A conflict detector scans a candidate anchor against the anchor registry and
returns :class:`ConflictEdge` objects. The deterministic heuristic engine lives
in :mod:`anchorprune.conflicts.detector`; this package wraps it and adds optional
model-assisted detection.

Constitutional rule for this layer:

    Heuristic system-anchor conflicts are authoritative hard gates. A
    model-assisted detector may ADD non-critical semantic signals, but it can
    NEVER remove or override a heuristic hard-gate conflict.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from anchorprune.anchors.models import CandidateAnchor
from anchorprune.anchors.registry import HybridAnchorRegistry
from anchorprune.conflicts.models import ConflictEdge


class ConflictDetector(ABC):
    @abstractmethod
    def detect(
        self, candidate: CandidateAnchor, registry: HybridAnchorRegistry
    ) -> List[ConflictEdge]:
        raise NotImplementedError
