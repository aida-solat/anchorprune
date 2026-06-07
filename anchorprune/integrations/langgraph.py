"""LangGraph integration (v0.6).

``AnchorPruneNode`` is a plain callable node you drop into a LangGraph (or any
state-dict graph) to insert governance between agent steps:

    agent step  ->  AnchorPrune governance  ->  governed context  ->  model/tool

Usage with LangGraph (LangGraph itself is *not* a dependency of AnchorPrune):

    from langgraph.graph import StateGraph
    from anchorprune.integrations.langgraph import AnchorPruneNode

    node = AnchorPruneNode(domain="coding_agent", config="configs/mock.yaml")

    graph = StateGraph(MyState)
    graph.add_node("govern", node)            # composes governed context
    graph.add_node("model", my_model_node)    # your model reads state["governed_context"]
    graph.add_node("observe", node.observe)   # ingests state["model_output"]
    ...

The node holds no governance logic — it reads payloads/instruction from the
graph state, asks :class:`AnchorPruneMiddleware` to govern and compose, and
writes the governed context back into the state. Every anchor decision and
quarantine is still made by the runtime's Anchor Governor.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from anchorprune.middleware import AnchorPruneMiddleware


class AnchorPruneNode:
    """A governance node for LangGraph-style state-dict graphs.

    State keys (all configurable):

    - ``instruction_key`` (default ``"instruction"``): the current step instruction.
    - ``payloads_key`` (default ``"new_payloads"``): a list of payload specs
      (strings, dicts, or PayloadBlocks) to ingest this step.
    - ``run_id_key`` (default ``"run_id"``): per-run id; falls back to ``run_id``.
    - ``output_key`` (default ``"governed_context"``): where the composed,
      governed prompt is written.
    - ``model_output_key`` (default ``"model_output"``): read by :meth:`observe`.
    - ``summary_key`` (default ``"anchorprune_state"``): governed-state summary.
    """

    def __init__(
        self,
        domain: str = "default",
        config: Optional[str] = None,
        *,
        goal: str = "",
        system_anchors: Optional[List[Dict[str, Any]]] = None,
        run_id: str = "langgraph",
        middleware: Optional[AnchorPruneMiddleware] = None,
        instruction_key: str = "instruction",
        payloads_key: str = "new_payloads",
        run_id_key: str = "run_id",
        output_key: str = "governed_context",
        model_output_key: str = "model_output",
        summary_key: str = "anchorprune_state",
    ) -> None:
        self.middleware = middleware or AnchorPruneMiddleware(
            domain, config, goal=goal, system_anchors=system_anchors
        )
        self.default_run_id = run_id
        self.instruction_key = instruction_key
        self.payloads_key = payloads_key
        self.run_id_key = run_id_key
        self.output_key = output_key
        self.model_output_key = model_output_key
        self.summary_key = summary_key

    def _run_id(self, state: Dict[str, Any]) -> str:
        return state.get(self.run_id_key, self.default_run_id)

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Govern current state and write the governed context into the state."""

        run_id = self._run_id(state)
        instruction = state.get(self.instruction_key, "") or ""
        payloads = state.get(self.payloads_key) or []
        governed = self.middleware.before_model_call(
            run_id,
            new_payloads=payloads,
            instruction=instruction,
        )
        return {
            self.output_key: governed.prompt,
            self.summary_key: governed.state_summary,
        }

    def observe(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Post-model node: ingest ``state[model_output_key]`` as governed payload."""

        run_id = self._run_id(state)
        model_output = state.get(self.model_output_key, "") or ""
        proposed = state.get("proposed_anchors") or None
        result = self.middleware.after_model_call(
            run_id, model_output, proposed_anchors=proposed
        )
        return {self.summary_key: result.state_summary}
