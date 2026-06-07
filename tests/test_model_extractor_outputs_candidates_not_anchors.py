"""The model-based extractor must emit candidates only, never approved anchors."""

import json

from anchorprune.anchors.extractors.model_based import ModelBasedAnchorExtractor
from anchorprune.anchors.models import Anchor, AnchorSource, CandidateAnchor
from anchorprune.blocks.models import PayloadBlock, PayloadBlockType
from anchorprune.llm.base import LLMClient, LLMRequest, LLMResponse


class _JSONStubLLM(LLMClient):
    def __init__(self, payload: dict) -> None:
        self._text = json.dumps(payload)

    def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(text=self._text, provider="stub", model="stub")


def _blocks():
    return [
        PayloadBlock(
            block_type=PayloadBlockType.TOOL_OUTPUT,
            content="Purchases above 50000 require human approval.",
        )
    ]


def test_model_extractor_returns_only_candidate_anchors():
    stub = _JSONStubLLM(
        {
            "candidate_anchors": [
                {
                    "content": "Purchases above 50000 require human approval.",
                    "anchor_type": "policy",
                    "task_relevance": 0.8,
                    "rationale": "explicit threshold",
                },
                # Even if the model claims a trusted/human source, it is coerced
                # back to a model source: a model can never self-promote.
                {
                    "content": "All vendors must be ISO9001 certified.",
                    "anchor_type": "compliance_certificate",
                    "source": "human",
                    "task_relevance": 0.9,
                },
            ]
        }
    )
    extractor = ModelBasedAnchorExtractor(stub)
    out = extractor.extract_candidates(_blocks())

    assert len(out) == 2
    for cand in out:
        assert isinstance(cand, CandidateAnchor)
        assert not isinstance(cand, Anchor)
        # Never a trusted/human source, regardless of what the model asserts.
        assert cand.source in {
            AnchorSource.MODEL_SINGLE,
            AnchorSource.MODEL_CROSS_VALIDATED,
            AnchorSource.MODEL_GUESS,
        }


def test_model_extractor_tolerates_malformed_output():
    class _Bad(LLMClient):
        def generate(self, request: LLMRequest) -> LLMResponse:
            return LLMResponse(text="not json at all", provider="stub")

    assert ModelBasedAnchorExtractor(_Bad()).extract_candidates(_blocks()) == []
