"""Evidence linker.

Links payload blocks / candidate anchors to evidence references already present
in the state graph, using simple keyword overlap. In a production system this
would be a retrieval/embedding step; the MVP keeps it deterministic.
"""

from __future__ import annotations

import re
from typing import Dict, List

from anchorprune.evidence.models import EvidenceRef

_STOPWORDS = {
    "the",
    "a",
    "an",
    "of",
    "to",
    "and",
    "or",
    "for",
    "is",
    "are",
    "with",
    "in",
    "on",
    "at",
    "by",
}


def _terms(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOPWORDS}


class EvidenceLinker:
    def __init__(self, min_overlap: float = 0.15) -> None:
        self.min_overlap = min_overlap

    def link(self, content: str, evidence_index: Dict[str, EvidenceRef]) -> List[str]:
        """Return ids of evidence references relevant to ``content``."""

        content_terms = _terms(content)
        if not content_terms:
            return []

        linked: List[str] = []
        for ev_id, ev in evidence_index.items():
            haystack = f"{ev.locator} {ev.snippet or ''}"
            ev_terms = _terms(haystack)
            if not ev_terms:
                continue
            shared = content_terms & ev_terms
            overlap = len(shared) / min(len(content_terms), len(ev_terms))
            if overlap >= self.min_overlap:
                linked.append(ev_id)
        return linked
