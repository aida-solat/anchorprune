"""AnchorPrune Runtime.

The main agent execution loop. Each step:

    1. Extract candidate anchors from new payload, govern them.
    2. Prune the state graph (anchor-aware).
    3. Compose a governed context.
    4. Call the LLM.
    5. Ingest the model output as payload and govern any proposed anchors.
    6. Record audit events and metrics.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from anchorprune.anchors.extractors.base import AnchorExtractor
from anchorprune.anchors.extractors.heuristic import HeuristicAnchorExtractor
from anchorprune.anchors.governor import AnchorGovernor
from anchorprune.anchors.models import (
    Anchor,
    AnchorClass,
    AnchorDecision,
    AnchorDecisionAction,
    AnchorPriority,
    AnchorSource,
    AnchorStatus,
    AnchorType,
    CandidateAnchor,
)
from anchorprune.anchors.registry import HybridAnchorRegistry
from anchorprune.blocks.models import PayloadBlock, PayloadBlockType, PruningState
from anchorprune.blocks.parser import BlockParser
from anchorprune.conflicts.detector import ContradictionFn
from anchorprune.conflicts.models import ConflictEdge, ConflictKind
from anchorprune.core.audit import AuditEventType, AuditLog
from anchorprune.core.context_composer import ContextComposer
from anchorprune.core.state_graph import GovernedStateGraph
from anchorprune.domains.models import DomainProfile
from anchorprune.domains.profiles import get_domain_profile
from anchorprune.evidence.linker import EvidenceLinker
from anchorprune.evidence.models import EvidenceRef
from anchorprune.llm.base import LLMClient
from anchorprune.milestones.extractor import MilestoneExtractor
from anchorprune.pruning.compressors.base import Compressor
from anchorprune.pruning.pruner import AnchorAwarePruner, PruningAction, PruningOp


class StepResult(BaseModel):
    run_id: str
    step_index: int
    model_output: str
    composed_prompt: str
    state_summary: Dict[str, int]
    pruning_summary: Dict[str, int]
    anchor_decisions: List[AnchorDecision] = Field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0


class AnchorPruneRuntime:
    def __init__(
        self,
        llm: LLMClient,
        domain_profile: Optional[DomainProfile] = None,
        *,
        contradiction_fn: Optional[ContradictionFn] = None,
        anchor_extractor: Optional[AnchorExtractor] = None,
        compressor: Optional[Compressor] = None,
    ) -> None:
        self.llm = llm
        self.domain_profile = domain_profile or get_domain_profile("default")

        self.parser = BlockParser()
        self.linker = EvidenceLinker()
        # Pluggable components default to the deterministic heuristic pipeline,
        # so the runtime and benchmark behave exactly as in v0.1/v0.2 unless a
        # model-based adapter is explicitly injected (e.g. via config.factory).
        self.extractor = anchor_extractor or HeuristicAnchorExtractor(linker=self.linker)
        self.governor = AnchorGovernor(contradiction_fn=contradiction_fn)
        self.milestone_extractor = MilestoneExtractor()
        self.pruner = AnchorAwarePruner(
            milestone_extractor=self.milestone_extractor, compressor=compressor
        )
        self.composer = ContextComposer()

        self.graph = GovernedStateGraph(domain=self.domain_profile.name)
        self.registry = HybridAnchorRegistry()
        self.audit = AuditLog()

        # Cumulative benchmark metrics.
        self.metrics: Dict[str, Any] = {
            "steps": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "blocks_preserved": 0,
            "blocks_compressed": 0,
            "blocks_evicted": 0,
            "blocks_quarantined": 0,
            "anchors_approved": 0,
            "candidates_rejected": 0,
        }

    # ---- run lifecycle ----------------------------------------------------

    def create_run(
        self,
        goal: str,
        system_anchors: Optional[List[Dict[str, Any]]] = None,
    ) -> GovernedStateGraph:
        self.graph.goal = goal
        for spec in system_anchors or []:
            self.register_system_anchor(spec)
        self.audit.record(
            AuditEventType.RUN_CREATED,
            self.graph.step_index,
            run_id=self.graph.run_id,
            goal=goal,
            domain=self.domain_profile.name,
        )
        return self.graph

    def register_system_anchor(self, spec: Dict[str, Any]) -> Anchor:
        anchor = Anchor(
            content=spec["content"],
            anchor_class=AnchorClass.SYSTEM,
            anchor_type=AnchorType(spec.get("anchor_type", "policy")),
            priority=AnchorPriority(spec.get("priority", "critical")),
            source=AnchorSource.HUMAN,
            weight=1.0,
            status=AnchorStatus.APPROVED,
        )
        self.graph.add_anchor(anchor)
        self.registry.add(anchor)
        return anchor

    # ---- evidence & payload ----------------------------------------------

    def add_evidence(self, evidence: EvidenceRef) -> EvidenceRef:
        return self.graph.add_evidence(evidence)

    def add_payload(
        self,
        content: str,
        block_type: PayloadBlockType,
        *,
        evidence_refs: Optional[List[str]] = None,
        decision_impact: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PayloadBlock:
        block = self.parser.parse(
            content,
            block_type,
            step_index=self.graph.step_index,
            evidence_refs=evidence_refs,
            metadata=metadata,
        )
        block.decision_impact = decision_impact
        if not block.evidence_refs:
            block.evidence_refs = self.linker.link(content, self.graph.evidence_refs)
        self.graph.add_payload_block(block)
        self.audit.record(
            AuditEventType.PAYLOAD_ADDED,
            self.graph.step_index,
            block_id=block.id,
            block_type=block_type.value,
        )
        return block

    # ---- governance -------------------------------------------------------

    def ingest_candidate(self, candidate: CandidateAnchor) -> AnchorDecision:
        self.audit.record(
            AuditEventType.ANCHOR_PROPOSED,
            self.graph.step_index,
            content=candidate.content,
            source=candidate.source.value,
        )
        decision = self.governor.evaluate_candidate_anchor(
            candidate,
            self.registry,
            self.domain_profile,
            evidence_index=self.graph.evidence_refs,
        )
        self._apply_decision(candidate, decision)
        self.audit.record(
            AuditEventType.ANCHOR_DECISION,
            self.graph.step_index,
            content=candidate.content,
            action=decision.action.value,
            weight=round(decision.weight, 4),
            reason=decision.reason,
        )
        return decision

    def _apply_decision(self, candidate: CandidateAnchor, decision: AnchorDecision) -> None:
        action = decision.action
        if action in (
            AnchorDecisionAction.APPROVE_DOMAIN_ANCHOR,
            AnchorDecisionAction.APPROVE_RUNTIME_ANCHOR,
        ):
            anchor = self.governor.decision_to_anchor(candidate, decision)
            if anchor is not None:
                self.graph.add_anchor(anchor)
                self.registry.add(anchor)
                self.metrics["anchors_approved"] += 1
                for block_id in candidate.linked_block_ids:
                    block = self.graph.payload_blocks.get(block_id)
                    if block and anchor.id not in block.linked_anchor_ids:
                        block.linked_anchor_ids.append(anchor.id)
        elif action == AnchorDecisionAction.QUARANTINE:
            self.registry.quarantine(candidate)
            edge = ConflictEdge(
                source_ref=candidate.content[:64],
                target_ref="system",
                kind=ConflictKind.SYSTEM_ANCHOR,
                severity=1.0,
                critical=True,
                reason=decision.reason,
            )
            self.graph.add_conflict(edge)
            self.audit.record(
                AuditEventType.CONFLICT_DETECTED,
                self.graph.step_index,
                content=candidate.content,
                reason=decision.reason,
            )
            for block_id in candidate.linked_block_ids:
                block = self.graph.payload_blocks.get(block_id)
                if block:
                    block.quarantined = True
                    block.pruning_state = PruningState.QUARANTINED
                    block.conflict_severity = 1.0
        elif action == AnchorDecisionAction.RETAIN_AS_MILESTONE:
            milestone = self.milestone_extractor.from_candidate(
                candidate, weight=decision.weight, step_index=self.graph.step_index
            )
            self.graph.add_milestone(milestone)
        else:  # REJECT
            self.metrics["candidates_rejected"] += 1

    # ---- step -------------------------------------------------------------

    def run_step(
        self, instruction: str, output_schema: Optional[str] = None
    ) -> StepResult:
        # 1. Extract & govern candidates from current active payload.
        active_blocks = [
            b
            for b in self.graph.payload_blocks.values()
            if b.pruning_state == PruningState.ACTIVE
        ]
        candidates = self.extractor.extract_candidates(
            active_blocks, self.graph, self.domain_profile
        )
        decisions = [self.ingest_candidate(c) for c in candidates]

        # 2. Anchor-aware pruning.
        actions = self.pruner.prune(self.graph, self.domain_profile)
        self._record_pruning(actions)

        # 3. Compose governed context.
        composed = self.composer.compose(
            self.graph, self.domain_profile, instruction, output_schema
        )
        self.audit.record(
            AuditEventType.CONTEXT_COMPOSED,
            self.graph.step_index,
            token_estimate=composed.token_estimate,
            included_blocks=len(composed.included_block_ids),
            dropped_blocks=len(composed.dropped_block_ids),
        )

        # 4. Call the LLM.
        result = self.llm.complete(composed.prompt)
        self.metrics["total_input_tokens"] += result.input_tokens
        self.metrics["total_output_tokens"] += result.output_tokens

        # 5. Ingest model output as payload and govern proposed anchors.
        output_block = self.add_payload(result.text, PayloadBlockType.MODEL_OUTPUT)
        for text in result.proposed_anchor_texts:
            self.ingest_candidate(
                CandidateAnchor(
                    content=text,
                    anchor_type=AnchorType.FACT,
                    source=AnchorSource.MODEL_SINGLE,
                    task_relevance=0.6,
                    volatility=0.5,
                    linked_block_ids=[output_block.id],
                )
            )

        # 6. Finalize step.
        pruning_summary = self._pruning_summary(actions)
        self.metrics["steps"] += 1
        self.audit.record(
            AuditEventType.STEP_COMPLETED,
            self.graph.step_index,
            pruning_summary=pruning_summary,
        )

        step_result = StepResult(
            run_id=self.graph.run_id,
            step_index=self.graph.step_index,
            model_output=result.text,
            composed_prompt=composed.prompt,
            state_summary=self.graph.summary(),
            pruning_summary=pruning_summary,
            anchor_decisions=decisions,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        )
        self.graph.step_index += 1
        return step_result

    # ---- helpers ----------------------------------------------------------

    def _record_pruning(self, actions: List[PruningAction]) -> None:
        for action in actions:
            self.audit.record(
                AuditEventType.PRUNING_ACTION,
                self.graph.step_index,
                block_id=action.block_id,
                op=action.op.value,
                utility=round(action.utility_score, 4),
                reason=action.reason,
            )
        self.metrics["blocks_preserved"] += sum(
            1 for a in actions if a.op == PruningOp.PRESERVE
        )
        self.metrics["blocks_compressed"] += sum(
            1 for a in actions if a.op == PruningOp.COMPRESS
        )
        self.metrics["blocks_evicted"] += sum(
            1 for a in actions if a.op == PruningOp.EVICT
        )
        self.metrics["blocks_quarantined"] += sum(
            1 for a in actions if a.op == PruningOp.QUARANTINE
        )

    @staticmethod
    def _pruning_summary(actions: List[PruningAction]) -> Dict[str, int]:
        return {
            "preserved": sum(1 for a in actions if a.op == PruningOp.PRESERVE),
            "compressed": sum(1 for a in actions if a.op == PruningOp.COMPRESS),
            "evicted": sum(1 for a in actions if a.op == PruningOp.EVICT),
            "quarantined": sum(1 for a in actions if a.op == PruningOp.QUARANTINE),
        }

    def benchmark_metrics(self) -> Dict[str, Any]:
        summary = self.graph.summary()
        return {
            **self.metrics,
            "final_state_size": summary["payload_blocks"]
            + summary["anchors"]
            + summary["milestones"],
            "state_summary": summary,
        }
