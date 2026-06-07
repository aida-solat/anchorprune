"""Compressors must preserve anchor/evidence linkage and source traceability."""

from anchorprune.blocks.models import PayloadBlock, PayloadBlockType
from anchorprune.core.state_graph import GovernedStateGraph
from anchorprune.llm.base import LLMClient, LLMRequest, LLMResponse
from anchorprune.pruning.compressors.heuristic import HeuristicCompressor
from anchorprune.pruning.compressors.model_based import ModelBasedCompressor


class _ShortLLM(LLMClient):
    def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(text="Compressed: approval required.", provider="stub")


class _EmptyLLM(LLMClient):
    def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(text="", provider="stub")


def _block() -> PayloadBlock:
    return PayloadBlock(
        block_type=PayloadBlockType.TOOL_OUTPUT,
        content=(
            "Purchases above 50000 require human approval. The vendor must hold "
            "valid ISO9001 certification. This is a long block worth compressing "
            "into a shorter governed summary while keeping the directives."
        ),
        linked_anchor_ids=["anchor_a", "anchor_b"],
        evidence_refs=["ev_1", "ev_2"],
    )


def _assert_links_preserved(source: PayloadBlock, result: PayloadBlock) -> None:
    assert result.linked_anchor_ids == source.linked_anchor_ids
    assert result.evidence_refs == source.evidence_refs
    assert result.metadata.get("source_block_id") == source.id
    assert result.compressed is True


def test_heuristic_compressor_preserves_links():
    graph = GovernedStateGraph(domain="default")
    src = _block()
    result = HeuristicCompressor().compress_block(src, graph, target_tokens=0)
    _assert_links_preserved(src, result)
    assert result.metadata.get("compressed_by") == "heuristic"
    assert len(result.content) < len(src.content)


def test_model_compressor_preserves_links_even_with_empty_model_output():
    graph = GovernedStateGraph(domain="default")
    src = _block()
    # Even when the model returns junk/empty, linkage is enforced structurally
    # and we fall back to a deterministic summary.
    for llm in (_ShortLLM(), _EmptyLLM()):
        result = ModelBasedCompressor(llm).compress_block(src, graph, target_tokens=40)
        _assert_links_preserved(src, result)
        assert result.metadata.get("compressed_by") == "model"
        assert result.content
