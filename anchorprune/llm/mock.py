"""Deterministic mock LLM.

Produces reproducible output derived from the prompt so the runtime, CLI, and
tests work without network access or API keys. It echoes which anchors it saw
and proposes a runtime anchor when it spots a likely constraint, exercising the
governor end-to-end.
"""

from __future__ import annotations

import re
from typing import List

from anchorprune.blocks.parser import estimate_tokens
from anchorprune.llm.base import LLMClient, LLMRequest, LLMResponse

_ANCHOR_LINE = re.compile(r"^- \[(critical|high|medium|low)\]\s+(.*)$", re.MULTILINE)
_PROPOSAL_CUES = ("missing", "without", "exceeds", "failed", "requires approval")


class MockLLM(LLMClient):
    """Deterministic, network-free default adapter.

    Implements the v0.3 ``generate`` primitive; the legacy ``complete`` wrapper
    on :class:`LLMClient` reconstructs the same :class:`LLMResult` the runtime
    and benchmark consume, so deterministic results are unchanged.
    """

    provider = "mock"
    model = "mock-deterministic"

    def __init__(self, output_tokens: int = 120) -> None:
        self._output_tokens = output_tokens

    def generate(self, request: LLMRequest) -> LLMResponse:
        prompt = request.prompt
        anchors = [m.group(2).strip() for m in _ANCHOR_LINE.finditer(prompt)]

        instruction = self._extract_section(prompt, "Current Step")
        goal = self._extract_section(prompt, "Goal")

        lines: List[str] = []
        lines.append(f"Working on: {instruction or goal or 'the task'}.")
        if anchors:
            lines.append("Honoring constraints:")
            lines.extend(f"  - {a}" for a in anchors[:6])

        proposed = self._propose_anchor(prompt)
        if proposed:
            lines.append(f"Observation worth anchoring: {proposed}")

        text = "\n".join(lines)
        return LLMResponse(
            text=text,
            input_tokens=estimate_tokens(prompt),
            output_tokens=self._output_tokens,
            model=self.model,
            provider=self.provider,
            metadata={"proposed_anchor_texts": [proposed] if proposed else []},
        )

    @staticmethod
    def _extract_section(prompt: str, header: str) -> str:
        pattern = re.compile(rf"# {re.escape(header)}\n(.+?)(?:\n\n|\n#|\Z)", re.DOTALL)
        m = pattern.search(prompt)
        return m.group(1).strip() if m else ""

    @staticmethod
    def _propose_anchor(prompt: str) -> str:
        for line in prompt.splitlines():
            low = line.lower()
            if any(cue in low for cue in _PROPOSAL_CUES) and "payload" not in low:
                return line.lstrip("- ").strip()[:160]
        return ""
