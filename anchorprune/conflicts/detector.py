"""Conflict detector.

Lightweight, dependency-free heuristics that flag contradictions between a
candidate anchor (or payload block) and existing anchors. The MVP uses two
signals:

1. Override attempts: language that tries to weaken/ignore governance.
2. Polarity mismatch: high keyword overlap with an anchor but opposite negation
   polarity (e.g. "require approval" vs "no approval required").

The detector is intentionally pluggable: callers may pass a custom
``contradiction_fn`` for domain-specific logic.
"""

from __future__ import annotations

import re
from typing import Callable, List, Optional

from anchorprune.anchors.models import Anchor, AnchorClass, CandidateAnchor
from anchorprune.conflicts.models import ConflictEdge, ConflictKind

_NEGATIONS = {
    "not",
    "no",
    "without",
    "never",
    "cannot",
    "cant",
    "dont",
    "doesnt",
    "isnt",
    "arent",
    "none",
    "exempt",
    "skip",
}

_OVERRIDE_TERMS = {
    "ignore",
    "override",
    "bypass",
    "disregard",
    "overrule",
    "disable",
    "circumvent",
    "supersede",
}

_GOVERNANCE_TERMS = {
    "policy",
    "policies",
    "rule",
    "rules",
    "system",
    "anchor",
    "approval",
    "security",
    "compliance",
    "constraint",
    "guardrail",
}

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
    "be",
    "must",
    "should",
    "this",
    "that",
    "with",
    "in",
    "on",
    "at",
    "by",
    "it",
    "as",
    "if",
    "any",
    "all",
    "can",
    "will",
    "may",
}

ContradictionFn = Callable[[str, str], bool]


def _tokens(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _content_terms(text: str) -> set[str]:
    return {t for t in _tokens(text) if t not in _STOPWORDS and t not in _NEGATIONS}


def _negation_count(tokens: List[str]) -> int:
    return sum(1 for t in tokens if t in _NEGATIONS)


def is_override_attempt(text: str) -> bool:
    tokens = set(_tokens(text))
    return bool(tokens & _OVERRIDE_TERMS) and bool(tokens & _GOVERNANCE_TERMS)


def polarity_conflict(a: str, b: str, *, overlap_threshold: float = 0.34) -> bool:
    """True when two statements share topic but disagree on negation polarity."""

    ta, tb = _tokens(a), _tokens(b)
    terms_a, terms_b = _content_terms(a), _content_terms(b)
    if not terms_a or not terms_b:
        return False
    shared = terms_a & terms_b
    overlap = len(shared) / min(len(terms_a), len(terms_b))
    if overlap < overlap_threshold:
        return False
    return (_negation_count(ta) % 2) != (_negation_count(tb) % 2)


def detect_conflict(
    candidate_content: str,
    anchor: Anchor,
    contradiction_fn: Optional[ContradictionFn] = None,
) -> Optional[ConflictEdge]:
    """Return a ConflictEdge if the candidate conflicts with ``anchor``."""

    critical = anchor.anchor_class == AnchorClass.SYSTEM

    if contradiction_fn is not None and contradiction_fn(candidate_content, anchor.content):
        return _edge(candidate_content, anchor, critical, "custom_contradiction")

    if is_override_attempt(candidate_content):
        return _edge(candidate_content, anchor, critical, "override_attempt")

    if polarity_conflict(candidate_content, anchor.content):
        return _edge(candidate_content, anchor, critical, "polarity_mismatch")

    return None


def _kind_for(anchor: Anchor) -> ConflictKind:
    if anchor.anchor_class == AnchorClass.SYSTEM:
        return ConflictKind.SYSTEM_ANCHOR
    if anchor.anchor_class == AnchorClass.DOMAIN:
        return ConflictKind.DOMAIN_ANCHOR
    return ConflictKind.PAYLOAD


def _edge(content: str, anchor: Anchor, critical: bool, reason: str) -> ConflictEdge:
    return ConflictEdge(
        source_ref=content[:64],
        target_ref=anchor.id,
        kind=_kind_for(anchor),
        severity=1.0 if critical else 0.6,
        critical=critical,
        reason=reason,
    )


class ConflictDetector:
    """Stateful wrapper that scans a candidate against a set of anchors."""

    def __init__(self, contradiction_fn: Optional[ContradictionFn] = None) -> None:
        self.contradiction_fn = contradiction_fn

    def check_system_conflict(
        self, candidate: CandidateAnchor, system_anchors: List[Anchor]
    ) -> Optional[ConflictEdge]:
        for anchor in system_anchors:
            edge = detect_conflict(candidate.content, anchor, self.contradiction_fn)
            if edge is not None and edge.critical:
                return edge
        return None

    def non_critical_conflict_severity(
        self, candidate: CandidateAnchor, anchors: List[Anchor]
    ) -> float:
        severities = []
        for anchor in anchors:
            if anchor.anchor_class == AnchorClass.SYSTEM:
                continue
            edge = detect_conflict(candidate.content, anchor, self.contradiction_fn)
            if edge is not None:
                severities.append(edge.severity)
        return max(severities) if severities else 0.0
