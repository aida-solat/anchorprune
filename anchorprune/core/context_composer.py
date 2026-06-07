"""Context Composer.

Builds the final prompt for the LLM from the governed state graph. Section order
(implementation spec section 9):

    1. System Anchors
    2. Domain Anchors relevant to task
    3. Runtime Anchors relevant to current step
    4. Reasoning Milestones
    5. High-utility Payload Blocks
    6. Current User Goal / Current Step Instruction
    7. Output Schema

If the token budget is exceeded, payload is dropped first; anchors are never
evicted. Critical system anchors are always retained.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from anchorprune.anchors.models import Anchor
from anchorprune.blocks.models import PayloadBlock, PruningState
from anchorprune.blocks.parser import estimate_tokens
from anchorprune.core.state_graph import GovernedStateGraph
from anchorprune.domains.models import DomainProfile
from anchorprune.milestones.models import ReasoningMilestone


class ComposedContext(BaseModel):
    prompt: str
    token_estimate: int
    included_block_ids: List[str]
    dropped_block_ids: List[str]
    sections: List[str]


def _format_anchor(anchor: Anchor) -> str:
    return f"- [{anchor.priority.value}] {anchor.content}"


def _format_milestone(ms: ReasoningMilestone) -> str:
    return f"- ({ms.stage}, conf={ms.confidence:.2f}) {ms.finding}"


def _format_block(block: PayloadBlock) -> str:
    return f"- [{block.block_type.value} u={block.utility_score:.2f}] {block.content}"


class ContextComposer:
    def compose(
        self,
        graph: GovernedStateGraph,
        domain_profile: DomainProfile,
        current_step_instruction: str,
        output_schema: Optional[str] = None,
    ) -> ComposedContext:
        budget = domain_profile.token_budget
        sections: List[str] = []
        section_names: List[str] = []

        # Sections 1-4: anchors + milestones are non-evictable here.
        system = graph.system_anchors()
        domain = sorted(graph.domain_anchors(), key=lambda a: a.weight, reverse=True)
        runtime = sorted(graph.runtime_anchors(), key=lambda a: a.weight, reverse=True)
        milestones = sorted(
            graph.milestones.values(), key=lambda m: m.confidence, reverse=True
        )

        if system:
            sections.append(
                "# System Anchors (non-negotiable)\n"
                + "\n".join(_format_anchor(a) for a in system)
            )
            section_names.append("system_anchors")
        if domain:
            sections.append(
                "# Domain Anchors\n" + "\n".join(_format_anchor(a) for a in domain)
            )
            section_names.append("domain_anchors")
        if runtime:
            sections.append(
                "# Runtime Anchors\n" + "\n".join(_format_anchor(a) for a in runtime)
            )
            section_names.append("runtime_anchors")
        if milestones:
            sections.append(
                "# Reasoning Milestones\n"
                + "\n".join(_format_milestone(m) for m in milestones)
            )
            section_names.append("milestones")

        fixed_text = "\n\n".join(sections)
        goal_text = f"# Goal\n{graph.goal}\n\n# Current Step\n{current_step_instruction}"
        schema_text = f"\n\n# Output Schema\n{output_schema}" if output_schema else ""
        fixed_tokens = estimate_tokens(fixed_text + goal_text + schema_text)

        # Section 5: high-utility payload blocks, fit into remaining budget.
        remaining = max(0, budget - fixed_tokens)
        ranked_blocks = sorted(
            (
                b
                for b in graph.payload_blocks.values()
                if b.pruning_state not in (PruningState.EVICTED, PruningState.QUARANTINED)
            ),
            key=lambda b: b.utility_score,
            reverse=True,
        )

        included: List[str] = []
        dropped: List[str] = []
        block_lines: List[str] = []
        used = 0
        for block in ranked_blocks:
            cost = estimate_tokens(_format_block(block))
            if used + cost <= remaining:
                block_lines.append(_format_block(block))
                included.append(block.id)
                used += cost
            else:
                dropped.append(block.id)

        if block_lines:
            payload_section = "# Relevant Payload\n" + "\n".join(block_lines)
            # Insert payload before goal/schema.
            sections.append(payload_section)
            section_names.append("payload")

        sections.append(goal_text)
        section_names.append("goal_and_step")
        if output_schema:
            sections.append(f"# Output Schema\n{output_schema}")
            section_names.append("output_schema")

        prompt = "\n\n".join(sections)
        return ComposedContext(
            prompt=prompt,
            token_estimate=estimate_tokens(prompt),
            included_block_ids=included,
            dropped_block_ids=dropped,
            sections=section_names,
        )
