"""Anchor Candidate Extractor.

Scans payload blocks for constraint-like statements and turns them into
candidate anchors. The MVP uses deterministic linguistic heuristics; a real
deployment could swap in an LLM extractor that emits the same CandidateAnchor
schema.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from anchorprune.anchors.models import AnchorSource, AnchorType, CandidateAnchor
from anchorprune.blocks.models import PayloadBlock, PayloadBlockType
from anchorprune.evidence.linker import EvidenceLinker
from anchorprune.evidence.models import EvidenceRef

# Modal / directive cues that suggest a constraint worth anchoring.
_DIRECTIVE_CUES = (
    "must",
    "must not",
    "cannot",
    "can not",
    "require",
    "required",
    "requires",
    "shall",
    "should",
    "do not",
    "never",
    "always",
    "only",
    "prohibited",
    "not allowed",
    "needs approval",
    "is missing",
    # Override / governance-weakening language must also be governed (and
    # typically quarantined by the hard gate).
    "ignore",
    "override",
    "bypass",
    "disregard",
    "disable",
    "auto-approve",
    "approve everything",
)

# Type hints keyed by salient terms in the statement.
_TYPE_HINTS = {
    AnchorType.SECURITY: ("credential", "secret", "password", "prompt", "expose"),
    AnchorType.COMPLIANCE_CERTIFICATE: ("compliance", "certificate", "iso", "certified"),
    AnchorType.RUNTIME_ERROR: ("error", "failed", "exception", "traceback"),
    AnchorType.TEST_RESULT: ("test", "passed", "failing", "coverage"),
    AnchorType.SUPPLIER_STOCK_STATUS: ("stock", "inventory", "availability"),
    AnchorType.POLICY: ("policy", "approval", "approve", "threshold"),
    AnchorType.SCHEMA: ("schema", "format", "field", "json"),
}

# Source mapping from the block that produced the statement.
_SOURCE_BY_BLOCK = {
    PayloadBlockType.USER_INPUT: AnchorSource.HUMAN,
    PayloadBlockType.TOOL_OUTPUT: AnchorSource.TRUSTED_TOOL,
    PayloadBlockType.RETRIEVED_CHUNK: AnchorSource.POLICY_DOCUMENT,
    PayloadBlockType.MODEL_OUTPUT: AnchorSource.MODEL_SINGLE,
    PayloadBlockType.INTERMEDIATE_DRAFT: AnchorSource.MODEL_SINGLE,
    PayloadBlockType.ERROR_LOG: AnchorSource.TRUSTED_TOOL,
    PayloadBlockType.CODE_ATTEMPT: AnchorSource.MODEL_SINGLE,
}

_VOLATILE_TYPES = {
    AnchorType.RUNTIME_ERROR,
    AnchorType.TEST_RESULT,
    AnchorType.SUPPLIER_STOCK_STATUS,
}


def _split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _infer_type(sentence: str) -> AnchorType:
    low = sentence.lower()
    for anchor_type, cues in _TYPE_HINTS.items():
        if any(cue in low for cue in cues):
            return anchor_type
    return AnchorType.CONSTRAINT


def _is_directive(sentence: str) -> bool:
    low = sentence.lower()
    return any(cue in low for cue in _DIRECTIVE_CUES)


class AnchorCandidateExtractor:
    def __init__(self, linker: Optional[EvidenceLinker] = None) -> None:
        self.linker = linker or EvidenceLinker()

    def extract_from_block(
        self,
        block: PayloadBlock,
        evidence_index: Optional[Dict[str, EvidenceRef]] = None,
    ) -> List[CandidateAnchor]:
        evidence_index = evidence_index or {}
        source = _SOURCE_BY_BLOCK.get(block.block_type, AnchorSource.MODEL_SINGLE)
        candidates: List[CandidateAnchor] = []

        for sentence in _split_sentences(block.content):
            if not _is_directive(sentence):
                continue
            anchor_type = _infer_type(sentence)
            ev = block.evidence_refs or self.linker.link(sentence, evidence_index)
            volatility = 0.7 if anchor_type in _VOLATILE_TYPES else 0.3
            candidates.append(
                CandidateAnchor(
                    content=sentence,
                    anchor_type=anchor_type,
                    source=source,
                    evidence_refs=list(ev),
                    task_relevance=0.6,
                    risk_impact=0.6 if anchor_type == AnchorType.POLICY else 0.4,
                    volatility=volatility,
                    linked_block_ids=[block.id],
                )
            )
        return candidates

    def extract(
        self,
        blocks: List[PayloadBlock],
        evidence_index: Optional[Dict[str, EvidenceRef]] = None,
    ) -> List[CandidateAnchor]:
        out: List[CandidateAnchor] = []
        for block in blocks:
            out.extend(self.extract_from_block(block, evidence_index))
        return out
