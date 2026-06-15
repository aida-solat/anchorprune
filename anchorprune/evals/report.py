"""Observational report rendering for real-model evaluation (v0.8).

The report is explicit, repeatedly, that it is **observational and not the
canonical deterministic benchmark**. It separates context validity from model
answer validity and surfaces variance and failure cases.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from anchorprune.evals.models import MethodAggregate, RealEvalSummary, TrialResult

_METHOD_LABEL = {
    "full_history": "Full history",
    "sliding_window": "Sliding window",
    "summary": "Simple summary",
    "anchorprune": "AnchorPrune",
}


def _pct(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    return f"{value:.0%}"


def _fmt_packs(policy_packs: Dict[str, Optional[str]]) -> str:
    if not policy_packs:
        return "none"
    return ", ".join(
        f"`{scen}` → {pack or 'none'}" for scen, pack in policy_packs.items()
    )


def build_results_payload(summary: RealEvalSummary) -> dict:
    return summary.model_dump()


def _aggregates_by_scenario(
    summary: RealEvalSummary,
) -> Dict[str, List[MethodAggregate]]:
    grouped: Dict[str, List[MethodAggregate]] = {}
    for agg in summary.aggregates:
        grouped.setdefault(agg.scenario, []).append(agg)
    return grouped


def _failure_cases(summary: RealEvalSummary) -> List[TrialResult]:
    return [
        t
        for t in summary.results
        if t.adversarial_contaminated
        or t.constraint_violation
        or t.model_answer_valid is False
        or not t.context_valid
    ]


def build_report(summary: RealEvalSummary) -> str:
    lines: List[str] = [
        "# AnchorPrune Real-Model Evaluation Report",
        "",
        "## Status",
        "",
        "**This report is observational. It is not the canonical deterministic "
        "benchmark.** The canonical AnchorPrune benchmark lives in `benchmarks/` "
        "and is fully deterministic. Real-model results may vary across providers, "
        "model versions, temperatures, and dates.",
        "",
        "> AnchorPrune changes what reaches the model by governing state before "
        "the model call. It does not make the underlying model reason better.",
        "",
        "## Configuration",
        "",
        f"- **Provider:** {summary.provider}",
        f"- **Model:** {summary.model}",
        f"- **Temperature:** {summary.temperature}",
        f"- **Trials:** {summary.trials}",
        f"- **Scenarios:** {', '.join(summary.scenarios)}",
        f"- **Policy packs:** {_fmt_packs(summary.policy_packs)}",
        f"- **AnchorPrune version:** {summary.anchorprune_version}",
        f"- **Canonical benchmark:** {summary.canonical_benchmark}",
        f"- **Observational:** {summary.observational}",
        "",
        "## Methods compared",
        "",
        "- **Full history** — all history/payloads composed into the prompt; no "
        "quarantine, no pruning.",
        "- **Sliding window** — only the most recent N messages; can forget early "
        "critical anchors.",
        "- **Simple summary** — deterministic heuristic summary of all messages.",
        "- **AnchorPrune** — policy-pack-aware governed context (anchors kept, "
        "overrides quarantined, milestones preserved).",
        "",
        "## Metrics",
        "",
        "- **Context Valid** — did the strategy place the required facts (and no "
        "forbidden/adversarial content) into the context shown to the model?",
        "- **Model Answer Valid** — given that context, did the model's answer "
        "satisfy the scenario's decision rules? (`N/A` when the scenario declares "
        "no decision rules.)",
        "- **Constraint Violations** — share of trials whose answer contained a "
        "forbidden phrase.",
        "- **Adversarial Contamination** — share of trials whose context carried "
        "an adversarial payload.",
        "- **Variance Across Trials** — sample variance of answer validity (0 when "
        "deterministic).",
        "",
        "## Results Summary",
        "",
        "| Scenario | Method | Trials | Context Valid | Model Answer Valid | "
        "Constraint Violations | Adversarial Contamination |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]

    grouped = _aggregates_by_scenario(summary)
    for scenario, aggs in grouped.items():
        for agg in aggs:
            lines.append(
                f"| `{scenario}` | {_METHOD_LABEL.get(agg.method, agg.method)} "
                f"| {agg.trials} | {_pct(agg.context_validity_rate)} "
                f"| {_pct(agg.model_answer_validity_rate)} "
                f"| {_pct(agg.constraint_violation_rate)} "
                f"| {_pct(agg.adversarial_contamination_rate)} |"
            )

    lines += ["", "## Variance Across Trials", ""]
    lines += [
        "| Scenario | Method | Answer-Validity Variance | Distinct Outputs |",
        "|---|---|---:|---:|",
    ]
    for scenario, aggs in grouped.items():
        for agg in aggs:
            lines.append(
                f"| `{scenario}` | {_METHOD_LABEL.get(agg.method, agg.method)} "
                f"| {agg.variance_across_trials:.4f} | {agg.distinct_outputs} |"
            )

    lines += ["", "## Failure Cases", ""]
    failures = _failure_cases(summary)
    if not failures:
        lines.append("_No failure cases recorded for this run._")
    else:
        lines += [
            "| Scenario | Method | Trial | Context Valid | Answer Valid | "
            "Contaminated | Violation |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
        for t in failures:
            lines.append(
                f"| `{t.scenario}` | {_METHOD_LABEL.get(t.method, t.method)} "
                f"| {t.trial_index} | {t.context_valid} | {t.model_answer_valid} "
                f"| {t.adversarial_contaminated} | {t.constraint_violation} |"
            )

    lines += [
        "",
        "## Raw Outputs",
        "",
        "Per-trial model outputs are saved under `raw_outputs/<scenario>/` and the "
        "exact contexts under `contexts/<scenario>/`. Run metadata (provider, "
        "model, temperature, trials, policy packs) is pinned in `metadata.json`.",
        "",
        "## Limitations",
        "",
        "- Real model outputs may vary across calls, even at temperature 0.",
        "- Provider model versions may change without notice.",
        "- Results should not be compared across dates unless metadata is pinned.",
        "- The deterministic benchmark remains the canonical AnchorPrune benchmark.",
        "- The evaluator is deterministic phrase-matching; it does not judge "
        "reasoning quality. A model-based judge would be non-canonical.",
        "",
    ]
    return "\n".join(lines)
