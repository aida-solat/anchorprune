"""Generic governance middleware for agent loops (v0.6).

This is the universal integration primitive. It lets any agent loop — custom
tool loops, LangGraph nodes, LlamaIndex memory, coding-agent pipelines — wrap an
AnchorPrune governed step around *its own* model call:

    from anchorprune import AnchorPruneMiddleware

    mw = AnchorPruneMiddleware(domain="procurement")
    mw.create_run(run_id="run_123", goal="Decide whether approval is allowed.")

    governed = mw.before_model_call(
        run_id="run_123",
        new_payloads=[{"tool_name": "erp", "content": "...", "metadata": {...}}],
        instruction="Decide whether approval is allowed.",
    )
    output = llm(governed.prompt)            # your model, your call
    mw.after_model_call(run_id="run_123", model_output=output)

The middleware owns no governance logic. ``before_model_call`` delegates to
:meth:`AnchorPruneRuntime.govern_and_compose` and ``after_model_call`` to
:meth:`AnchorPruneRuntime.ingest_model_output`; every anchor decision, conflict
quarantine, and pruning action is still made by the runtime's Anchor Governor.
AnchorPrune is not the agent — it is the governor around the agent's memory.

Runtimes are held in memory keyed by ``run_id``. Durable persistence is a
separate concern provided by the v0.4 service layer; the middleware is a thin,
dependency-light seam for embedding governance into an existing loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from anchorprune.blocks.models import PayloadBlock, PayloadBlockType
from anchorprune.config import build_runtime
from anchorprune.config.resolve import resolve_config
from anchorprune.core.runtime import AnchorPruneRuntime, StepComposition, StepResult

# A payload can be supplied as a plain string (treated as a tool output), a
# ready-made PayloadBlock, or a dict describing one.
PayloadSpec = Union[str, PayloadBlock, Dict[str, Any]]


@dataclass
class GovernedContext:
    """The governed context handed back to the caller before its model call.

    ``prompt`` is the composed, governed string to send to the model. The other
    fields expose what governance did to produce it, for logging or assertions.
    ``str(governed_context)`` returns the prompt for ergonomic use.
    """

    prompt: str
    token_estimate: int
    included_block_ids: List[str] = field(default_factory=list)
    dropped_block_ids: List[str] = field(default_factory=list)
    sections: List[str] = field(default_factory=list)
    state_summary: Dict[str, int] = field(default_factory=dict)

    def __str__(self) -> str:  # so `llm(str(ctx))` and logging just work
        return self.prompt


class UnknownRunError(KeyError):
    """Raised when a run_id has not been created on this middleware instance."""


class AnchorPruneMiddleware:
    """Wrap a governed AnchorPrune step around an external model call.

    Parameters mirror the runtime/config system:

    - ``domain``: a built-in domain profile name (e.g. ``"procurement"``,
      ``"coding_agent"``). Unknown names fall back to the default profile.
    - ``config``: an optional config name or path (e.g. ``"configs/mock.yaml"``).
      Defaults to the deterministic mock pipeline — no network, no randomness.
    - ``system_anchors`` / ``goal``: defaults applied to runs created without
      their own values.
    """

    def __init__(
        self,
        domain: str = "default",
        config: Optional[str] = None,
        *,
        goal: str = "",
        system_anchors: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.domain = domain
        self.config_name = config
        self._default_goal = goal
        self._default_system_anchors = system_anchors or []
        self._runtimes: Dict[str, AnchorPruneRuntime] = {}
        self._pending: Dict[str, StepComposition] = {}

    # ---- run lifecycle ----------------------------------------------------

    def create_run(
        self,
        run_id: Optional[str] = None,
        *,
        goal: Optional[str] = None,
        system_anchors: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Create a new governed run and return its id."""

        runtime = self._build_runtime()
        if run_id:
            runtime.graph.run_id = run_id
        runtime.create_run(
            goal=self._default_goal if goal is None else goal,
            system_anchors=(
                self._default_system_anchors
                if system_anchors is None
                else system_anchors
            ),
        )
        rid = runtime.graph.run_id
        self._runtimes[rid] = runtime
        return rid

    def get_runtime(self, run_id: str) -> AnchorPruneRuntime:
        try:
            return self._runtimes[run_id]
        except KeyError as exc:
            raise UnknownRunError(run_id) from exc

    def has_run(self, run_id: str) -> bool:
        return run_id in self._runtimes

    # ---- the governed step seam ------------------------------------------

    def before_model_call(
        self,
        run_id: str,
        *,
        new_payloads: Optional[List[PayloadSpec]] = None,
        instruction: str = "",
        output_schema: Optional[str] = None,
        goal: Optional[str] = None,
        system_anchors: Optional[List[Dict[str, Any]]] = None,
    ) -> GovernedContext:
        """Ingest new payloads, govern state, and return the governed context.

        The run is created on first use if it does not exist yet. The composed
        context is what should be sent to the model. The in-flight step state is
        retained until :meth:`after_model_call` ingests the model output.
        """

        runtime = self._get_or_create(run_id, goal=goal, system_anchors=system_anchors)
        for spec in new_payloads or []:
            self._ingest_payload(runtime, spec)
        composition = runtime.govern_and_compose(instruction, output_schema)
        self._pending[run_id] = composition
        composed = composition.composed
        return GovernedContext(
            prompt=composed.prompt,
            token_estimate=composed.token_estimate,
            included_block_ids=list(composed.included_block_ids),
            dropped_block_ids=list(composed.dropped_block_ids),
            sections=list(composed.sections),
            state_summary=runtime.graph.summary(),
        )

    def after_model_call(
        self,
        run_id: str,
        model_output: str,
        *,
        proposed_anchors: Optional[List[str]] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> StepResult:
        """Hand the model output back for governed ingestion and finalize.

        Must be preceded by a :meth:`before_model_call` for the same ``run_id``.
        The model output is ingested as ordinary payload and still passes through
        the Anchor Governor — proposing an anchor is not the same as creating one.
        """

        runtime = self.get_runtime(run_id)
        composition = self._pending.pop(run_id, None)
        if composition is None:
            raise RuntimeError(
                f"after_model_call({run_id!r}) called without a matching "
                "before_model_call. Call before_model_call first."
            )
        return runtime.ingest_model_output(
            model_output,
            composition=composition,
            proposed_anchor_texts=proposed_anchors,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    # ---- internals --------------------------------------------------------

    def _build_runtime(self) -> AnchorPruneRuntime:
        config = resolve_config(self.config_name, domain=self.domain)
        return build_runtime(config)

    def _get_or_create(
        self,
        run_id: str,
        *,
        goal: Optional[str] = None,
        system_anchors: Optional[List[Dict[str, Any]]] = None,
    ) -> AnchorPruneRuntime:
        if run_id in self._runtimes:
            return self._runtimes[run_id]
        self.create_run(run_id, goal=goal, system_anchors=system_anchors)
        return self._runtimes[run_id]

    @staticmethod
    def _ingest_payload(runtime: AnchorPruneRuntime, spec: PayloadSpec) -> PayloadBlock:
        if isinstance(spec, PayloadBlock):
            runtime.graph.add_payload_block(spec)
            return spec
        if isinstance(spec, str):
            return runtime.add_payload(spec, PayloadBlockType.TOOL_OUTPUT)

        data = dict(spec)
        content = data["content"]
        metadata = data.get("metadata")
        decision_impact = float(data.get("decision_impact", 0.0))
        evidence_refs = data.get("evidence_refs")
        tool_name = data.get("tool_name")
        if tool_name:
            block_type = PayloadBlockType(data.get("block_type", "tool_output"))
            return runtime.add_tool_output(
                tool_name,
                content,
                metadata=metadata,
                decision_impact=decision_impact,
                evidence_refs=evidence_refs,
                block_type=block_type,
            )
        block_type = PayloadBlockType(data.get("block_type", "tool_output"))
        return runtime.add_payload(
            content,
            block_type,
            evidence_refs=evidence_refs,
            decision_impact=decision_impact,
            metadata=metadata,
        )
