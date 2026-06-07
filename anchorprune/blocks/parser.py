"""Block Parser.

Turns raw inputs (user goals, documents, tool outputs, model outputs) into
PayloadBlock objects, estimating a rough token count for budgeting.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from anchorprune.blocks.models import PayloadBlock, PayloadBlockType


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars/token), good enough for budgeting."""

    if not text:
        return 0
    return max(1, len(text) // 4)


class BlockParser:
    def parse(
        self,
        content: str,
        block_type: PayloadBlockType,
        *,
        step_index: int = 0,
        evidence_refs: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PayloadBlock:
        return PayloadBlock(
            block_type=block_type,
            content=content,
            step_index=step_index,
            token_estimate=estimate_tokens(content),
            evidence_refs=list(evidence_refs or []),
            metadata=metadata or {},
        )

    def parse_many(
        self, items: List[Dict[str, Any]], *, step_index: int = 0
    ) -> List[PayloadBlock]:
        blocks: List[PayloadBlock] = []
        for item in items:
            block_type = PayloadBlockType(item.get("block_type", "tool_output"))
            blocks.append(
                self.parse(
                    item["content"],
                    block_type,
                    step_index=step_index,
                    evidence_refs=item.get("evidence_refs"),
                    metadata=item.get("metadata"),
                )
            )
        return blocks
