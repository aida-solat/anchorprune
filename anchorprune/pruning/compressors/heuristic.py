"""Heuristic compressor.

Deterministic extractive summary (lead + salient directive sentences). Produces
content identical to the v0.1/v0.2 :func:`compress_text`, so the deterministic
benchmark is unchanged, while guaranteeing anchor/evidence linkage preservation.
"""

from __future__ import annotations

from anchorprune.blocks.models import PayloadBlock
from anchorprune.core.state_graph import GovernedStateGraph
from anchorprune.pruning.compression import compress_text
from anchorprune.pruning.compressors.base import Compressor, enforce_linkage


class HeuristicCompressor(Compressor):
    def __init__(self, max_sentences: int = 2) -> None:
        self.max_sentences = max_sentences

    def compress_block(
        self,
        block: PayloadBlock,
        state_graph: GovernedStateGraph,
        target_tokens: int = 0,
    ) -> PayloadBlock:
        new_content = compress_text(block.content, max_sentences=self.max_sentences)
        return enforce_linkage(block, new_content, compressed_by="heuristic")
