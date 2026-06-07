"""Payload Block Store.

A thin in-memory store with helpers for redundancy estimation. Backs the
GovernedStateGraph's payload dictionary in the MVP.
"""

from __future__ import annotations

import re
from typing import Dict, List

from anchorprune.blocks.models import PayloadBlock, PruningState


def _terms(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


class PayloadBlockStore:
    def __init__(self) -> None:
        self._blocks: Dict[str, PayloadBlock] = {}

    def add(self, block: PayloadBlock) -> PayloadBlock:
        self._blocks[block.id] = block
        return block

    def get(self, block_id: str) -> PayloadBlock:
        return self._blocks[block_id]

    def all(self) -> List[PayloadBlock]:
        return list(self._blocks.values())

    def active(self) -> List[PayloadBlock]:
        return [b for b in self._blocks.values() if b.pruning_state == PruningState.ACTIVE]

    def estimate_redundancy(self, block: PayloadBlock) -> float:
        """Max Jaccard similarity against other active blocks (0..1)."""

        base = _terms(block.content)
        if not base:
            return 0.0
        best = 0.0
        for other in self._blocks.values():
            if other.id == block.id or other.pruning_state == PruningState.EVICTED:
                continue
            other_terms = _terms(other.content)
            if not other_terms:
                continue
            jaccard = len(base & other_terms) / len(base | other_terms)
            best = max(best, jaccard)
        return best
