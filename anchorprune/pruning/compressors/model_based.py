"""Model-based compressor.

Uses an LLM to produce a compact summary of a payload block. Link preservation
is NOT delegated to the model: the result is rebuilt from the source block via
:func:`enforce_linkage`, so ``linked_anchor_ids``, ``evidence_refs``, and
``source_block_id`` are always preserved regardless of what the model returns.
If the model fails or returns empty text, we fall back to the deterministic
heuristic summary.
"""

from __future__ import annotations

from anchorprune.blocks.models import PayloadBlock
from anchorprune.core.state_graph import GovernedStateGraph
from anchorprune.llm.base import LLMClient, LLMRequest
from anchorprune.pruning.compression import compress_text
from anchorprune.pruning.compressors.base import Compressor, enforce_linkage

_SYSTEM = (
    "You compress agent state. Preserve every constraint, policy, requirement, "
    "and decision verbatim in meaning. Return ONLY the compressed text, no "
    "preamble."
)


class ModelBasedCompressor(Compressor):
    def __init__(self, llm: LLMClient, *, temperature: float = 0.0) -> None:
        self.llm = llm
        self.temperature = temperature

    def compress_block(
        self,
        block: PayloadBlock,
        state_graph: GovernedStateGraph,
        target_tokens: int = 0,
    ) -> PayloadBlock:
        budget = f" Aim for about {target_tokens} tokens." if target_tokens else ""
        try:
            response = self.llm.generate(
                LLMRequest(
                    prompt=f"Compress this block.{budget}\n\n{block.content}",
                    system=_SYSTEM,
                    temperature=self.temperature,
                    max_tokens=max(32, target_tokens) if target_tokens else None,
                    metadata={"task": "compression", "source_block_id": block.id},
                )
            )
            new_content = (response.text or "").strip()
        except Exception:
            new_content = ""

        if not new_content:
            new_content = compress_text(block.content)
        return enforce_linkage(block, new_content, compressed_by="model")
