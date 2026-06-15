"""Real-model evaluation harness (v0.8).

    Real-model evaluation is observational. Deterministic benchmarks remain
    canonical.

This package runs AnchorPrune and the three memory baselines against real or
mock LLM providers and scores the results with a deterministic evaluator. It is
strictly observational: it never replaces or mutates the canonical deterministic
benchmark in ``benchmarks/``, and it makes no claim that AnchorPrune improves a
model's reasoning — only that it changes *what reaches the model*.
"""

from anchorprune.evals.evaluators import EvalCriteria, evaluate_answer, evaluate_context
from anchorprune.evals.models import (
    METHODS,
    MethodAggregate,
    RealEvalConfig,
    RealEvalSummary,
    TrialResult,
)
from anchorprune.evals.real_eval import run_real_eval
from anchorprune.evals.runner import (
    ProviderUnavailableError,
    build_provider,
    resolve_policy_pack,
    resolve_scenario,
    run_eval,
)

__all__ = [
    "RealEvalConfig",
    "TrialResult",
    "MethodAggregate",
    "RealEvalSummary",
    "METHODS",
    "EvalCriteria",
    "evaluate_answer",
    "evaluate_context",
    "run_real_eval",
    "run_eval",
    "build_provider",
    "resolve_scenario",
    "resolve_policy_pack",
    "ProviderUnavailableError",
]
