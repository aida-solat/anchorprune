"""Compression.

Compresses a payload block into a compact milestone-style summary. The MVP uses
a deterministic extractive summary (lead + salient directive sentences) so it is
testable without an LLM. A production version could delegate to a model.
"""

from __future__ import annotations

import re
from typing import List

from anchorprune.blocks.models import PayloadBlock

_SALIENT_CUES = (
    "must",
    "require",
    "cannot",
    "missing",
    "failed",
    "error",
    "approval",
    "recommend",
    "risk",
    "compliance",
)


def _sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def compress_text(content: str, max_sentences: int = 2) -> str:
    sentences = _sentences(content)
    if len(sentences) <= max_sentences:
        return content.strip()

    salient = [s for s in sentences if any(c in s.lower() for c in _SALIENT_CUES)]
    chosen: List[str] = []
    if sentences:
        chosen.append(sentences[0])
    for s in salient:
        if s not in chosen:
            chosen.append(s)
        if len(chosen) >= max_sentences:
            break
    return " ".join(chosen[:max_sentences])


def compress_block(block: PayloadBlock) -> str:
    return compress_text(block.content)
