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
from anchorprune.scenario import normalize_steps, run_scenario


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

    # ---- Benchmark Pack v0.2: long-run / context-growth metrics -----------
    # Per-step series (length == steps).
    context_tokens_by_step: List[int] = []
    anchor_retention_by_step: List[float] = []
    adversarial_contamination_by_step: List[float] = []
    obsolete_retention_by_step: List[float] = []
    state_size_by_step: List[int] = []

    # Final / aggregate context metrics.
    adversarial_contamination_rate: float = 0.0
    obsolete_payload_retention_rate: float = 0.0
    context_growth_slope: float = 0.0
    max_context_size: int = 0
    # Cross-method ratios (filled in once all methods have run).
    final_context_size_ratio_vs_full_history: Optional[float] = None
    # tokens spent per step whose composed context was decision-valid.
    tokens_per_valid_context: Optional[float] = None
    # Experimental composite (see report caveat). None == not computed.
    bounded_context_score: Optional[float] = None


def _critical_anchor_texts(scenario: Dict[str, Any]) -> List[str]:
    return [
        a["content"]
        for a in scenario.get("system_anchors", [])
        if a.get("priority", "critical") == "critical"
    ]


def _anchor_messages(scenario: Dict[str, Any]) -> List[str]:
    return [a["content"] for a in scenario.get("system_anchors", [])]


def _all_payloads(scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Every payload block in the scenario: up-front plus any injected per step."""

    items = list(scenario.get("payload", []))
    for step in scenario.get("steps", []) or []:
        if isinstance(step, dict):
            items.extend(step.get("payloads", []) or [])
    return items


def _flagged(payload: Dict[str, Any], *flags: str) -> bool:
    meta = payload.get("metadata", {})
    return any(payload.get(f) or meta.get(f) for f in flags)


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
    return [p for p in _all_payloads(scenario) if _flagged(p, "adversarial")]


def _fraction_present(items: List[str], haystack: str) -> float:
    if not items:
        return 1.0
    present = sum(1 for s in items if s in haystack)
    return round(present / len(items), 4)


def _presence_rate(payloads: List[Dict[str, Any]], haystack: str) -> float:
    """Share of the given payload blocks whose content appears in ``haystack``.

    For adversarial payloads this is *contamination* (lower is better); for
    obsolete payloads it is *retention* (lower is better). Returns 0.0 when no
    payloads of that kind have been seen yet."""

    if not payloads:
        return 0.0
    present = sum(1 for p in payloads if p["content"] in haystack)
    return round(present / len(payloads), 4)


def _slope(values: List[int]) -> float:
    """Least-squares slope of ``values`` over step index (tokens per step)."""

    n = len(values)
    if n < 2:
        return 0.0
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(values) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values))
    den = sum((x - mean_x) ** 2 for x in xs)
    return round(num / den, 4) if den else 0.0


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
    context_tokens_by_step: List[int],
    anchor_retention_by_step: List[float],
    adversarial_contamination_by_step: List[float],
    obsolete_retention_by_step: List[float],
    state_size_by_step: List[int],
    valid_steps: int,
) -> BenchmarkResult:
    """Assemble a BenchmarkResult from a method's final context + governance facts.

    Anchor, constraint, milestone, and decision metrics are read from what the
    model could actually see (``final_context``); eviction and quarantine are
    supplied by the caller since only AnchorPrune governs them structurally. The
    per-step series carry the v0.2 long-run signals.
    """

    anchor_texts = _critical_anchor_texts(scenario)
    retained = _retained(final_context, anchor_texts)
    total = len(anchor_texts)
    lost_rate = round((total - retained) / total, 4) if total else 0.0

    total_in = sum(token_steps)
    # Tokens-per-valid-context is only meaningful when the method actually
    # delivers a valid final decision context. If the final context is invalid
    # (lost anchors or retained adversarial state), the metric is N/A (None) so a
    # small token count for an *invalid* context can never read as "cheaper and
    # better" -- in the JSON as well as the rendered tables.
    final_valid = _decision_correctness(scenario, final_context)
    tokens_per_valid = (
        round(total_in / valid_steps, 2)
        if (valid_steps and final_valid == 1.0)
        else None
    )

    return BenchmarkResult(
        method=method,
        steps=len(token_steps),
        total_input_tokens=total_in,
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
        final_decision_context_valid=final_valid,
        # v0.2 series + aggregates.
        context_tokens_by_step=context_tokens_by_step,
        anchor_retention_by_step=anchor_retention_by_step,
        adversarial_contamination_by_step=adversarial_contamination_by_step,
        obsolete_retention_by_step=obsolete_retention_by_step,
        state_size_by_step=state_size_by_step,
        adversarial_contamination_rate=(
            adversarial_contamination_by_step[-1]
            if adversarial_contamination_by_step
            else 0.0
        ),
        obsolete_payload_retention_rate=(
            obsolete_retention_by_step[-1] if obsolete_retention_by_step else 0.0
        ),
        context_growth_slope=_slope(context_tokens_by_step),
        max_context_size=max(context_tokens_by_step) if context_tokens_by_step else 0,
        tokens_per_valid_context=tokens_per_valid,
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
    goal = scenario.get("goal", "")
    anchor_texts = _critical_anchor_texts(scenario)
    initial_payloads = list(scenario.get("payload", []))
    step_specs = normalize_steps(scenario)

    messages: List[str] = _anchor_messages(scenario)
    seen: List[Dict[str, Any]] = []

    token_steps: List[int] = []
    context_tokens_by_step: List[int] = []
    anchor_retention_by_step: List[float] = []
    adversarial_by_step: List[float] = []
    obsolete_by_step: List[float] = []
    state_size_by_step: List[int] = []
    total_out = 0
    valid_steps = 0
    last_prompt = ""

    for i, (instruction, step_payloads) in enumerate(step_specs):
        inject = (initial_payloads if i == 0 else []) + list(step_payloads)
        for p in inject:
            messages.append(p["content"])
            seen.append(p)

        prompt = compose(messages, goal, instruction)
        last_prompt = prompt
        result = llm.complete(prompt)
        token_steps.append(result.input_tokens)
        total_out += result.output_tokens

        context_tokens_by_step.append(estimate_tokens(prompt))
        anchor_retention_by_step.append(_fraction_present(anchor_texts, prompt))
        adversarial_by_step.append(
            _presence_rate([p for p in seen if _flagged(p, "adversarial")], prompt)
        )
        obsolete_by_step.append(
            _presence_rate(
                [p for p in seen if _flagged(p, "obsolete", "noise")], prompt
            )
        )
        state_size_by_step.append(_baseline_state_size(messages, window, summary))
        if _decision_correctness(scenario, prompt) == 1.0:
            valid_steps += 1

    # Eviction: share of all injected payloads absent from the final context.
    all_payloads = _all_payloads(scenario)
    total_payload = len(all_payloads) or 1
    present = sum(1 for p in all_payloads if p["content"] in last_prompt)
    eviction_rate = (total_payload - present) / total_payload

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
        context_tokens_by_step=context_tokens_by_step,
        anchor_retention_by_step=anchor_retention_by_step,
        adversarial_contamination_by_step=adversarial_by_step,
        obsolete_retention_by_step=obsolete_by_step,
        state_size_by_step=state_size_by_step,
        valid_steps=valid_steps,
    )


def _baseline_state_size(
    messages: List[str], window: Optional[int], summary: bool
) -> int:
    """How many distinct context items the strategy keeps live this step."""

    if summary:
        return min(3, len(messages))  # compress_text keeps up to 3 sentences
    if window is not None:
        return min(window, len(messages))
    return len(messages)  # full history retains everything


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

    anchor_texts = _critical_anchor_texts(scenario)
    initial_payloads = list(scenario.get("payload", []))
    step_specs = normalize_steps(scenario)

    context_tokens_by_step: List[int] = []
    anchor_retention_by_step: List[float] = []
    adversarial_by_step: List[float] = []
    obsolete_by_step: List[float] = []
    state_size_by_step: List[int] = []
    seen: List[Dict[str, Any]] = []
    valid_steps = 0

    for i, r in enumerate(results):
        step_payloads = step_specs[i][1] if i < len(step_specs) else []
        seen.extend((initial_payloads if i == 0 else []) + list(step_payloads))
        prompt = r.composed_prompt
        context_tokens_by_step.append(estimate_tokens(prompt))
        anchor_retention_by_step.append(_fraction_present(anchor_texts, prompt))
        adversarial_by_step.append(
            _presence_rate([p for p in seen if _flagged(p, "adversarial")], prompt)
        )
        obsolete_by_step.append(
            _presence_rate(
                [p for p in seen if _flagged(p, "obsolete", "noise")], prompt
            )
        )
        ss = r.state_summary
        state_size_by_step.append(
            ss.get("anchors", 0) + ss.get("payload_blocks", 0) + ss.get("milestones", 0)
        )
        if _decision_correctness(scenario, prompt) == 1.0:
            valid_steps += 1

    # Payload eviction rate over the scenario's injected payload blocks.
    input_count = len(_all_payloads(scenario)) or 1
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
        context_tokens_by_step=context_tokens_by_step,
        anchor_retention_by_step=anchor_retention_by_step,
        adversarial_contamination_by_step=adversarial_by_step,
        obsolete_retention_by_step=obsolete_by_step,
        state_size_by_step=state_size_by_step,
        valid_steps=valid_steps,
    )


def _add_cross_method_metrics(results: Dict[str, BenchmarkResult]) -> None:
    """Fill in metrics that compare methods against each other in-place."""

    full = results.get("baseline_a_full_history")
    full_final = (full.final_context_tokens if full else 0) or 1
    max_ctx = max((r.max_context_size for r in results.values()), default=0) or 1

    for r in results.values():
        r.final_context_size_ratio_vs_full_history = round(
            r.final_context_tokens / full_final, 4
        )
        normalized_growth = r.max_context_size / max_ctx
        # Experimental composite: rewards governed retention with bounded growth.
        r.bounded_context_score = round(
            r.constraint_adherence_rate
            * (1.0 - r.lost_anchor_rate)
            * (1.0 - r.adversarial_contamination_rate)
            * (1.0 - normalized_growth),
            4,
        )


def run_benchmark(
    scenario: Dict[str, Any],
    *,
    window: int = 3,
    llm: Optional[LLMClient] = None,
) -> Dict[str, BenchmarkResult]:
    llm = llm or MockLLM()
    results = {
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
    _add_cross_method_metrics(results)
    return results
