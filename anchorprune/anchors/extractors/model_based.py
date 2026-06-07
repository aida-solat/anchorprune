"""Model-based anchor extractor.

Asks an LLM to propose structured candidate anchors. The model's output is
*never* turned into an approved anchor here: it is parsed into
:class:`CandidateAnchor` objects (always from a ``model_*`` source) that must
still pass through the Anchor Governor. Malformed or partial model output is
tolerated and skipped rather than trusted.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from anchorprune.anchors.extractors.base import AnchorExtractor
from anchorprune.anchors.models import AnchorSource, AnchorType, CandidateAnchor
from anchorprune.blocks.models import PayloadBlock
from anchorprune.llm.base import LLMClient, LLMRequest

if TYPE_CHECKING:  # pragma: no cover - typing only
    from anchorprune.core.state_graph import GovernedStateGraph
    from anchorprune.domains.models import DomainProfile

_MODEL_SOURCES = {
    AnchorSource.MODEL_SINGLE,
    AnchorSource.MODEL_CROSS_VALIDATED,
    AnchorSource.MODEL_GUESS,
}

_SYSTEM = (
    "You extract candidate governance anchors (policies, constraints, security "
    "rules, schemas, key facts) from agent state. Respond with ONLY JSON of the "
    'form {"candidate_anchors": [{"content": str, "anchor_type": str, '
    '"task_relevance": number, "rationale": str}]}. Do not invent constraints '
    "that are not supported by the provided text."
)


def _build_prompt(blocks: List[PayloadBlock]) -> str:
    joined = "\n".join(f"- ({b.block_type.value}) {b.content}" for b in blocks)
    return (
        "Extract candidate anchors from the following agent state blocks.\n\n"
        f"{joined}\n\nReturn JSON only."
    )


def _parse_json_object(text: str) -> Optional[Dict[str, Any]]:
    """Best-effort extraction of the first JSON object from model text."""

    text = text.strip()
    # Strip code fences if present.
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def _coerce_anchor_type(value: Any) -> AnchorType:
    try:
        return AnchorType(str(value))
    except ValueError:
        return AnchorType.CONSTRAINT


def _coerce_source(value: Any) -> AnchorSource:
    try:
        source = AnchorSource(str(value))
    except ValueError:
        return AnchorSource.MODEL_SINGLE
    return source if source in _MODEL_SOURCES else AnchorSource.MODEL_SINGLE


def _clamp(value: Any, default: float = 0.5) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


class ModelBasedAnchorExtractor(AnchorExtractor):
    def __init__(self, llm: LLMClient, *, temperature: float = 0.0) -> None:
        self.llm = llm
        self.temperature = temperature

    def extract_candidates(
        self,
        blocks: List[PayloadBlock],
        state_graph: Optional["GovernedStateGraph"] = None,
        domain_profile: Optional["DomainProfile"] = None,
    ) -> List[CandidateAnchor]:
        if not blocks:
            return []

        response = self.llm.generate(
            LLMRequest(
                prompt=_build_prompt(blocks),
                system=_SYSTEM,
                temperature=self.temperature,
                metadata={"task": "anchor_extraction"},
            )
        )
        parsed = _parse_json_object(response.text)
        if not parsed:
            return []

        raw = parsed.get("candidate_anchors")
        if not isinstance(raw, list):
            return []

        candidates: List[CandidateAnchor] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            content = str(item.get("content", "")).strip()
            if not content:
                continue
            candidates.append(
                CandidateAnchor(
                    content=content,
                    anchor_type=_coerce_anchor_type(item.get("anchor_type")),
                    # A model-proposed candidate is always a model source; it can
                    # never claim a trusted/human source and so can never reach
                    # the domain-anchor tier on authority alone.
                    source=_coerce_source(item.get("source")),
                    evidence_refs=[
                        str(r) for r in (item.get("evidence_refs") or []) if r
                    ],
                    task_relevance=_clamp(item.get("task_relevance"), 0.5),
                    volatility=_clamp(item.get("volatility"), 0.5),
                    linked_block_ids=self._link_blocks(content, blocks),
                    metadata={"rationale": str(item.get("rationale", ""))[:280]},
                )
            )
        return candidates

    @staticmethod
    def _link_blocks(content: str, blocks: List[PayloadBlock]) -> List[str]:
        low = content.lower()
        linked = [
            b.id
            for b in blocks
            if low in b.content.lower() or b.content.lower() in low
        ]
        return linked
