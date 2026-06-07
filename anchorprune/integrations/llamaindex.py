"""LlamaIndex integration (v0.6).

``AnchorPruneMemory`` is a governed memory you can place in a LlamaIndex-style
document/RAG workflow. Retrieved chunks become governed payload with evidence
links; querying returns a governed context rather than a raw concatenation:

    retrieved chunks  ->  evidence links  ->  anchor candidates  ->  governed memory

Usage (LlamaIndex itself is *not* a dependency of AnchorPrune):

    from anchorprune.integrations.llamaindex import AnchorPruneMemory

    memory = AnchorPruneMemory(domain="contract_review")
    for node in retriever.retrieve(query):
        memory.put(node.get_content(), source=node.node_id)

    governed_context = memory.get(instruction=query)
    answer = llm(governed_context)

The memory owns no governance logic; ``put`` ingests chunks through the runtime
and ``get`` delegates to the governed compose step. Quarantined or evicted
chunks never reach the governed context — that is the point.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from anchorprune.anchors.models import Anchor
from anchorprune.blocks.models import PayloadBlockType
from anchorprune.evidence.models import EvidenceRef, EvidenceSourceType
from anchorprune.middleware import AnchorPruneMiddleware, GovernedContext
from anchorprune.milestones.models import ReasoningMilestone

ChunkSpec = Union[str, Dict[str, Any]]


class AnchorPruneMemory:
    """Governed memory for document/RAG workflows.

    - ``put`` ingests a retrieved chunk as a governed ``retrieved_chunk`` payload
      block, attaching a document evidence reference.
    - ``get`` returns the governed context string for an instruction.
    - ``anchors`` / ``milestones`` expose what governance retained.
    """

    def __init__(
        self,
        domain: str = "default",
        config: Optional[str] = None,
        *,
        run_id: str = "llamaindex",
        goal: str = "",
        system_anchors: Optional[List[Dict[str, Any]]] = None,
        middleware: Optional[AnchorPruneMiddleware] = None,
        default_decision_impact: float = 0.3,
    ) -> None:
        self.middleware = middleware or AnchorPruneMiddleware(
            domain, config, goal=goal, system_anchors=system_anchors
        )
        self.run_id = run_id
        self._goal = goal
        self._system_anchors = system_anchors
        self._default_impact = default_decision_impact
        if not self.middleware.has_run(run_id):
            self.middleware.create_run(
                run_id, goal=goal, system_anchors=system_anchors
            )

    @property
    def runtime(self):
        return self.middleware.get_runtime(self.run_id)

    def put(
        self,
        content: str,
        *,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        decision_impact: Optional[float] = None,
    ) -> str:
        """Ingest a retrieved chunk as governed payload with an evidence link."""

        runtime = self.runtime
        meta = dict(metadata or {})
        locator = source or meta.get("source", "retrieved")
        evidence = EvidenceRef(
            source_type=EvidenceSourceType.DOCUMENT,
            locator=str(locator),
            snippet=content[:160],
        )
        runtime.add_evidence(evidence)
        block = runtime.add_payload(
            content,
            PayloadBlockType.RETRIEVED_CHUNK,
            evidence_refs=[evidence.id],
            decision_impact=(
                self._default_impact if decision_impact is None else decision_impact
            ),
            metadata=meta or None,
        )
        return block.id

    def add_chunks(self, chunks: List[ChunkSpec]) -> List[str]:
        """Ingest multiple chunks. Each may be a string or a dict with
        ``content`` plus optional ``source``/``metadata``/``decision_impact``."""

        ids: List[str] = []
        for chunk in chunks:
            if isinstance(chunk, str):
                ids.append(self.put(chunk))
            else:
                data = dict(chunk)
                ids.append(
                    self.put(
                        data["content"],
                        source=data.get("source"),
                        metadata=data.get("metadata"),
                        decision_impact=data.get("decision_impact"),
                    )
                )
        return ids

    def get(self, instruction: str = "", *, output_schema: Optional[str] = None) -> str:
        """Return the governed context string for an instruction/query."""

        return self.governed_context(instruction, output_schema=output_schema).prompt

    def governed_context(
        self, instruction: str = "", *, output_schema: Optional[str] = None
    ) -> GovernedContext:
        """Return the full :class:`GovernedContext` (prompt plus governance metadata)."""

        return self.middleware.before_model_call(
            self.run_id,
            instruction=instruction,
            output_schema=output_schema,
        )

    def anchors(self) -> List[Anchor]:
        return list(self.runtime.graph.anchors.values())

    def milestones(self) -> List[ReasoningMilestone]:
        return list(self.runtime.graph.milestones.values())

    def reset(self) -> None:
        """Drop all governed state and start a fresh run under the same id."""

        self.middleware.create_run(
            self.run_id, goal=self._goal, system_anchors=self._system_anchors
        )
