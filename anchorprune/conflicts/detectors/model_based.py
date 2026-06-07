"""Model-assisted conflict detector.

Uses an LLM to surface *semantic* conflicts the lexical heuristics may miss
(e.g. paraphrased contradictions). Critically, every edge it produces is
**non-critical**: a model can raise a signal, but it can never assert a
system-anchor hard gate on its own, and it can never clear one. Hard gates are
owned exclusively by the heuristic detector.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from anchorprune.anchors.models import CandidateAnchor
from anchorprune.anchors.registry import HybridAnchorRegistry
from anchorprune.conflicts.detectors.base import ConflictDetector
from anchorprune.conflicts.models import ConflictEdge, ConflictKind
from anchorprune.llm.base import LLMClient, LLMRequest

_SYSTEM = (
    "You are a conflict auditor. Given a candidate statement and a list of "
    "existing anchors, identify which anchors the candidate semantically "
    "contradicts. Respond with ONLY JSON: "
    '{"conflicts": [{"anchor_id": str, "confidence": number, "reason": str}]}.'
)

# A model-assisted signal is capped below the heuristic hard-gate severity so it
# can never be mistaken for an authoritative system conflict.
_MAX_MODEL_SEVERITY = 0.6


def _parse(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return None
    return None


class ModelAssistedConflictDetector(ConflictDetector):
    def __init__(self, llm: LLMClient, *, temperature: float = 0.0) -> None:
        self.llm = llm
        self.temperature = temperature

    def detect(
        self, candidate: CandidateAnchor, registry: HybridAnchorRegistry
    ) -> List[ConflictEdge]:
        anchors = registry.all_anchors()
        if not anchors:
            return []
        by_id = {a.id: a for a in anchors}
        listing = "\n".join(f"- {a.id}: {a.content}" for a in anchors)
        response = self.llm.generate(
            LLMRequest(
                prompt=(
                    f"Candidate: {candidate.content}\n\nAnchors:\n{listing}\n\n"
                    "Return JSON only."
                ),
                system=_SYSTEM,
                temperature=self.temperature,
                metadata={"task": "conflict_detection"},
            )
        )
        parsed = _parse(response.text)
        if not parsed or not isinstance(parsed.get("conflicts"), list):
            return []

        edges: List[ConflictEdge] = []
        for item in parsed["conflicts"]:
            if not isinstance(item, dict):
                continue
            anchor = by_id.get(str(item.get("anchor_id", "")))
            if anchor is None:
                continue
            confidence = item.get("confidence", 0.5)
            try:
                severity = max(0.0, min(_MAX_MODEL_SEVERITY, float(confidence)))
            except (TypeError, ValueError):
                severity = 0.3
            edges.append(
                ConflictEdge(
                    source_ref=candidate.content[:64],
                    target_ref=anchor.id,
                    kind=ConflictKind.PAYLOAD,
                    severity=severity,
                    critical=False,  # never a hard gate
                    reason=f"model_semantic:{str(item.get('reason', ''))[:80]}",
                )
            )
        return edges
