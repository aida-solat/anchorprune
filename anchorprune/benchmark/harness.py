"""Benchmark harness.

Compares AnchorPrune against three memory baselines on the same scenario:

    Baseline A: full conversation history
    Baseline B: sliding-window memory
    Baseline C: simple summarization memory
    Method:     AnchorPrune governed state graph

Naive baselines treat system anchors as ordinary history messages, so they can
lose critical constraints under compression -- which is exactly what AnchorPrune
prevents. The mock LLM keeps the comparison deterministic.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from anchorprune.blocks.models import PruningState
from anchorprune.blocks.parser import estimate_tokens
from anchorprune.llm.base import LLMClient
from anchorprune.llm.mock import MockLLM
from anchorprune.pruning.compression import compress_text
from anchorprune.scenario import run_scenario


class BenchmarkResult(BaseModel):
    method: str
    steps: int
    total_input_tokens: int
    total_output_tokens: int
    final_context_tokens: int
    token_count_by_step: List[int] = []

    critical_anchors_total: int = 0
    critical_anchors_retained: int = 0

    # Benchmark Pack v0.1 metrics (rates in [0, 1]).
    lost_anchor_rate: float = 0.0
    constraint_adherence_rate: float = 1.0
    # None == not applicable (no adversarial payloads in the scenario).
    critical_conflict_quarantine_rate: Optional[float] = None
    payload_eviction_rate: float = 0.0
    milestone_retention_rate: float = 1.0
    final_decision_context_valid: float = 0.0


def _critical_anchor_texts(scenario: Dict[str, Any]) -> List[str]:
    return [
        a["content"]
        for a in scenario.get("system_anchors", [])
        if a.get("priority", "critical") == "critical"
    ]


def _messages(scenario: Dict[str, Any]) -> List[str]:
    msgs = [a["content"] for a in scenario.get("system_anchors", [])]
    msgs += [p["content"] for p in scenario.get("payload", [])]
    return msgs


def _steps(scenario: Dict[str, Any]) -> List[str]:
    return scenario.get("steps") or ["Complete the task using the available context."]


def _retained(prompt: str, anchor_texts: List[str]) -> int:
    return sum(1 for a in anchor_texts if a in prompt)


def _expectations(scenario: Dict[str, Any]) -> Dict[str, Any]:
    return scenario.get("expectations", {}) or {}


def _expected_constraints(scenario: Dict[str, Any]) -> List[str]:
    exp = _expectations(scenario)
    return exp.get("constraints") or _critical_anchor_texts(scenario)


def _expected_milestones(scenario: Dict[str, Any]) -> List[str]:
    return _expectations(scenario).get("milestones", [])


def _adversarial_payload(scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        p
        for p in scenario.get("payload", [])
        if p.get("adversarial") or p.get("metadata", {}).get("adversarial")
    ]


def _fraction_present(items: List[str], haystack: str) -> float:
    if not items:
        return 1.0
    present = sum(1 for s in items if s in haystack)
    return round(present / len(items), 4)


def _decision_correctness(scenario: Dict[str, Any], final_context: str) -> float:
    decision = _expectations(scenario).get("decision")
    if not decision:
        return 1.0
    must_include = decision.get("must_include", [])
    must_not_include = decision.get("must_not_include", [])
    include_ok = all(s in final_context for s in must_include)
    exclude_ok = not any(s in final_context for s in must_not_include)
    return 1.0 if (include_ok and exclude_ok) else 0.0


def _build_result(
    *,
    method: str,
    scenario: Dict[str, Any],
    final_context: str,
    token_steps: List[int],
    total_out: int,
    payload_eviction_rate: float,
    quarantine_rate: Optional[float],
    milestone_haystack: str,
) -> BenchmarkResult:
    """Assemble a BenchmarkResult from a method's final context + governance facts.

    Anchor, constraint, milestone, and decision metrics are read from what the
    model could actually see (``final_context``); eviction and quarantine are
    supplied by the caller since only AnchorPrune governs them structurally.
    """

    anchor_texts = _critical_anchor_texts(scenario)
    retained = _retained(final_context, anchor_texts)
    total = len(anchor_texts)
    lost_rate = round((total - retained) / total, 4) if total else 0.0

    return BenchmarkResult(
        method=method,
        steps=len(token_steps),
        total_input_tokens=sum(token_steps),
        total_output_tokens=total_out,
        final_context_tokens=estimate_tokens(final_context),
        token_count_by_step=token_steps,
        critical_anchors_total=total,
        critical_anchors_retained=retained,
        lost_anchor_rate=lost_rate,
        constraint_adherence_rate=_fraction_present(
            _expected_constraints(scenario), final_context
        ),
        critical_conflict_quarantine_rate=quarantine_rate,
        payload_eviction_rate=round(payload_eviction_rate, 4),
        milestone_retention_rate=_fraction_present(
            _expected_milestones(scenario), milestone_haystack
        ),
        final_decision_context_valid=_decision_correctness(scenario, final_context),
    )


def _run_baseline(
    method: str,
    scenario: Dict[str, Any],
    compose,
    llm: LLMClient,
    *,
    window: Optional[int] = None,
    summary: bool = False,
) -> BenchmarkResult:
    messages = _messages(scenario)
    goal = scenario.get("goal", "")
    steps = _steps(scenario)

    token_steps: List[int] = []
    total_out = 0
    last_prompt = ""
    for instruction in steps:
        prompt = compose(messages, goal, instruction)
        last_prompt = prompt
        result = llm.complete(prompt)
        token_steps.append(result.input_tokens)
        total_out += result.output_tokens

    payload_items = scenario.get("payload", [])
    n_payload = len(payload_items)
    if summary:
        eviction_rate = 1.0  # no payload block survives individually
    elif window is not None and n_payload:
        window_slice = "\n".join(messages[-window:])
        retained_payload = sum(1 for p in payload_items if p["content"] in window_slice)
        eviction_rate = (n_payload - retained_payload) / n_payload
    else:
        eviction_rate = 0.0  # full history keeps everything

    return _build_result(
        method=method,
        scenario=scenario,
        final_context=last_prompt,
        token_steps=token_steps,
        total_out=total_out,
        payload_eviction_rate=eviction_rate,
        # No adversarial payloads -> metric not applicable (None). Otherwise
        # naive baselines have no governance, so they quarantine nothing (0.0).
        quarantine_rate=None if not _adversarial_payload(scenario) else 0.0,
        milestone_haystack=last_prompt,
    )


def _full_history(messages: List[str], goal: str, instruction: str) -> str:
    body = "\n".join(messages)
    return f"# History\n{body}\n\n# Goal\n{goal}\n\n# Step\n{instruction}"


def _sliding_window(window: int):
    def compose(messages: List[str], goal: str, instruction: str) -> str:
        body = "\n".join(messages[-window:])
        return f"# Recent\n{body}\n\n# Goal\n{goal}\n\n# Step\n{instruction}"

    return compose


def _summary(messages: List[str], goal: str, instruction: str) -> str:
    summary = compress_text(" ".join(messages), max_sentences=3)
    return f"# Summary\n{summary}\n\n# Goal\n{goal}\n\n# Step\n{instruction}"


def _run_anchorprune(scenario: Dict[str, Any], llm: LLMClient) -> BenchmarkResult:
    runtime, results = run_scenario(scenario, llm)
    graph = runtime.graph

    token_steps = [r.input_tokens for r in results]
    total_out = sum(r.output_tokens for r in results)
    final_prompt = results[-1].composed_prompt if results else ""

    # Payload eviction rate over the scenario's input payload blocks.
    input_count = len(scenario.get("payload", [])) or 1
    evicted = sum(
        1
        for b in graph.payload_blocks.values()
        if b.pruning_state == PruningState.EVICTED
    )
    eviction_rate = min(1.0, evicted / input_count)

    # Critical-conflict quarantine rate over adversarial payload blocks.
    # None when the scenario has no adversarial payloads (metric not applicable).
    adversarial = _adversarial_payload(scenario)
    if adversarial:
        quarantined = sum(
            1
            for b in graph.payload_blocks.values()
            if b.metadata.get("adversarial")
            and b.pruning_state == PruningState.QUARANTINED
        )
        quarantine_rate: Optional[float] = min(1.0, quarantined / len(adversarial))
    else:
        quarantine_rate = None

    # Milestones retained as governed objects count toward milestone retention,
    # in addition to anything visible in the composed context.
    milestone_text = "\n".join(m.finding for m in graph.milestones.values())
    runtime_anchor_text = "\n".join(a.content for a in graph.runtime_anchors())
    milestone_haystack = f"{final_prompt}\n{milestone_text}\n{runtime_anchor_text}"

    return _build_result(
        method="AnchorPrune",
        scenario=scenario,
        final_context=final_prompt,
        token_steps=token_steps,
        total_out=total_out,
        payload_eviction_rate=eviction_rate,
        quarantine_rate=quarantine_rate,
        milestone_haystack=milestone_haystack,
    )


def run_benchmark(
    scenario: Dict[str, Any],
    *,
    window: int = 3,
    llm: Optional[LLMClient] = None,
) -> Dict[str, BenchmarkResult]:
    llm = llm or MockLLM()
    return {
        "baseline_a_full_history": _run_baseline(
            "Baseline A: full history", scenario, _full_history, llm
        ),
        "baseline_b_sliding_window": _run_baseline(
            "Baseline B: sliding window",
            scenario,
            _sliding_window(window),
            llm,
            window=window,
        ),
        "baseline_c_summary": _run_baseline(
            "Baseline C: simple summary", scenario, _summary, llm, summary=True
        ),
        "anchorprune": _run_anchorprune(scenario, llm),
    }
