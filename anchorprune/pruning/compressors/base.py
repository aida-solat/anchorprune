"""Compressor interface (v0.3 adapter layer).

A compressor turns a payload block into a smaller block. The governance contract
is strict and enforced structurally (not left to the model's good behavior):

- ``linked_anchor_ids`` MUST be preserved.
- ``evidence_refs`` (linked evidence) MUST be preserved.
- The result MUST record ``source_block_id`` for traceability/audit.

The :func:`enforce_linkage` helper builds a compliant result block from the
source block plus new content, guaranteeing the contract regardless of backend.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from anchorprune.blocks.models import PayloadBlock
from anchorprune.core.state_graph import GovernedStateGraph


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def enforce_linkage(
    source: PayloadBlock, new_content: str, *, compressed_by: str
) -> PayloadBlock:
    """Return a compressed copy of ``source`` that provably preserves linkage."""

    metadata = dict(source.metadata)
    metadata["source_block_id"] = source.id
    metadata["compressed_by"] = compressed_by
    return source.model_copy(
        update={
            "content": new_content,
            "compressed": True,
            "token_estimate": estimate_tokens(new_content),
            # Explicitly carried forward; never dropped by a backend.
            "linked_anchor_ids": list(source.linked_anchor_ids),
            "evidence_refs": list(source.evidence_refs),
            "metadata": metadata,
        }
    )


class Compressor(ABC):
    @abstractmethod
    def compress_block(
        self,
        block: PayloadBlock,
        state_graph: GovernedStateGraph,
        target_tokens: int,
    ) -> PayloadBlock:
        raise NotImplementedError
