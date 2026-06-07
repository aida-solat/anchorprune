"""Evidence scoring helpers.

Thin wrapper around the weighting engine's evidence scorer so other modules can
depend on the ``evidence`` package rather than reaching into ``anchors``.
"""

from __future__ import annotations

from typing import Dict, Iterable

from anchorprune.evidence.models import EvidenceRef


def score_evidence_strength(
    evidence_ref_ids: Iterable[str],
    evidence_index: Dict[str, EvidenceRef],
) -> float:
    """Strength of supporting evidence in [0, 1].

    Combines the strongest source reliability with a small bonus for multiple
    corroborating references.
    """

    ids = [i for i in evidence_ref_ids if i in evidence_index]
    if not ids:
        return 0.0
    reliabilities = sorted(
        (evidence_index[i].effective_reliability for i in ids), reverse=True
    )
    base = reliabilities[0]
    corroboration_bonus = min(0.15, 0.05 * (len(reliabilities) - 1))
    return min(1.0, base + corroboration_bonus)
