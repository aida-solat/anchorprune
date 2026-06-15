"""Context composition and single-trial execution (v0.8).

Context composition is **deterministic** for all four methods — it is the
governed/ungoverned state each strategy makes available to the model. Only the
provider's *answer* to that context is observational and may vary across trials.

This is the heart of the honest v0.8 claim:

    AnchorPrune changes what reaches the model by governing state before the
    model call. It does not make the underlying model reason better.
"""

from __future__ import annotations

import statistics
from typing import Any, Dict, List, Tuple

from anchorprune.blocks.parser import estimate_tokens
from anchorprune.evals.evaluators import EvalCriteria, evaluate_answer, evaluate_context
from anchorprune.evals.models import MethodAggregate, TrialResult
from anchorprune.llm.base import LLMClient, LLMRequest
from anchorprune.llm.mock import MockLLM
from anchorprune.pruning.compression import compress_text
from anchorprune.scenario import normalize_steps, run_scenario


def _all_message_contents(scenario: Dict[str, Any]) -> List[str]:
    anchors = [a["content"] for a in scenario.get("system_anchors", [])]
    payloads = [p["content"] for p in scenario.get("payload", [])]
    for _instruction, step_payloads in normalize_steps(scenario):
        payloads.extend(p["content"] for p in step_payloads)
    return anchors + payloads


def _final_instruction(scenario: Dict[str, Any]) -> str:
    steps = normalize_steps(scenario)
    return steps[-1][0] if steps else "Complete the task."


def compose_final_contexts(
    scenario: Dict[str, Any], *, window: int = 3
) -> Dict[str, str]:
    """Deterministically compose each method's final-step context.

    The three baselines mirror the canonical benchmark's composition exactly;
    AnchorPrune uses its policy-pack-aware governed runtime (driven by a
    deterministic mock so the *context* is reproducible across trials).
    """

    goal = scenario.get("goal", "")
    instruction = _final_instruction(scenario)
    messages = _all_message_contents(scenario)

    full_history = (
        f"# History\n{chr(10).join(messages)}\n\n# Goal\n{goal}\n\n# Step\n{instruction}"
    )
    sliding = (
        f"# Recent\n{chr(10).join(messages[-window:])}\n\n# Goal\n{goal}\n\n"
        f"# Step\n{instruction}"
    )
    summary_text = compress_text(" ".join(messages), max_sentences=3)
    summary = f"# Summary\n{summary_text}\n\n# Goal\n{goal}\n\n# Step\n{instruction}"

    _runtime, results = run_scenario(scenario, MockLLM())
    anchorprune = results[-1].composed_prompt if results else ""

    return {
        "full_history": full_history,
        "sliding_window": sliding,
        "summary": summary,
        "anchorprune": anchorprune,
    }


def run_trial(
    *,
    provider_llm: LLMClient,
    provider: str,
    model: str,
    scenario_name: str,
    method: str,
    trial_index: int,
    context: str,
    criteria: EvalCriteria,
    temperature: float,
) -> Tuple[TrialResult, str]:
    """Send one context to the provider once and score the answer.

    Returns the scored ``TrialResult`` and the full model output text (so the
    caller can persist the raw output). Paths are filled in by the caller after
    the artifacts are written.
    """

    response = provider_llm.generate(
        LLMRequest(prompt=context, temperature=temperature)
    )
    output = response.text or ""

    ctx_eval = evaluate_context(criteria, context)
    ans_eval = evaluate_answer(criteria, output)

    result = TrialResult(
        scenario=scenario_name,
        method=method,  # type: ignore[arg-type]
        trial_index=trial_index,
        provider=provider,
        model=model,
        prompt_tokens_estimate=response.input_tokens or estimate_tokens(context),
        output_tokens_estimate=response.output_tokens or estimate_tokens(output),
        context_valid=ctx_eval["context_valid"],
        model_answer_valid=ans_eval["model_answer_valid"],
        adversarial_contaminated=ctx_eval["adversarial_contaminated"],
        constraint_violation=ans_eval["constraint_violation"],
        required_anchor_mentions=ans_eval["required_anchor_mentions"],
        forbidden_mentions=ans_eval["forbidden_mentions"],
        metadata={
            "required_anchor_mention_rate": ans_eval["required_anchor_mention_rate"],
            "output_preview": output[:200],
        },
    )
    return result, output


def _rate(flags: List[bool]) -> float:
    return round(sum(1 for f in flags if f) / len(flags), 4) if flags else 0.0


def aggregate_trials(
    scenario_name: str, method: str, trials: List[TrialResult]
) -> MethodAggregate:
    """Roll per-trial results into one (scenario, method) aggregate."""

    n = len(trials)
    answer_flags = [t.model_answer_valid for t in trials if t.model_answer_valid is not None]
    answer_rate = (
        round(sum(1 for f in answer_flags if f) / len(answer_flags), 4)
        if answer_flags
        else None
    )
    variance = (
        round(statistics.pvariance([1.0 if f else 0.0 for f in answer_flags]), 4)
        if len(answer_flags) >= 1
        else 0.0
    )
    mention_rates = [
        t.metadata.get("required_anchor_mention_rate", 0.0) for t in trials
    ]
    distinct = len({t.metadata.get("output_preview", "") for t in trials})

    return MethodAggregate(
        scenario=scenario_name,
        method=method,  # type: ignore[arg-type]
        trials=n,
        context_validity_rate=_rate([t.context_valid for t in trials]),
        model_answer_validity_rate=answer_rate,
        adversarial_contamination_rate=_rate(
            [t.adversarial_contaminated for t in trials]
        ),
        constraint_violation_rate=_rate([t.constraint_violation for t in trials]),
        required_anchor_mention_rate=(
            round(sum(mention_rates) / n, 4) if n else 0.0
        ),
        forbidden_content_mention_rate=_rate(
            [bool(t.forbidden_mentions) for t in trials]
        ),
        variance_across_trials=variance,
        distinct_outputs=distinct,
    )
