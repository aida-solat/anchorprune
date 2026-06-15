"""Model/config tests for the v0.8 real-model evaluation harness."""

import pytest
from pydantic import ValidationError

from anchorprune.evals.models import (
    METHODS,
    MethodAggregate,
    RealEvalConfig,
    RealEvalSummary,
    TrialResult,
)


def test_real_eval_config_validation():
    cfg = RealEvalConfig(
        provider="mock", model="mock-deterministic", scenarios=["coding_agent"]
    )
    assert cfg.provider == "mock"
    assert cfg.trials == 3
    assert cfg.temperature == 0.0
    assert cfg.policy_pack == "auto"
    assert cfg.out_dir == "real_eval_results"
    assert cfg.save_contexts is True and cfg.save_raw_outputs is True


def test_real_eval_config_rejects_unknown_provider():
    with pytest.raises(ValidationError):
        RealEvalConfig(provider="gemini", model="x", scenarios=["coding_agent"])


def test_methods_are_the_four_strategies():
    assert METHODS == ["full_history", "sliding_window", "summary", "anchorprune"]


def test_trial_result_separates_context_from_answer_validity():
    t = TrialResult(
        scenario="coding_agent",
        method="anchorprune",
        trial_index=1,
        provider="mock",
        model="mock-deterministic",
        prompt_tokens_estimate=10,
        output_tokens_estimate=5,
        context_valid=True,
        model_answer_valid=None,
    )
    # Answer validity may be unknown (None) even when context validity is known.
    assert t.context_valid is True
    assert t.model_answer_valid is None


def test_summary_defaults_observational_not_canonical():
    summary = RealEvalSummary(
        anchorprune_version="0.8.0",
        provider="mock",
        model="mock-deterministic",
        temperature=0.0,
        trials=2,
        scenarios=["coding_agent"],
    )
    assert summary.canonical_benchmark is False
    assert summary.observational is True


def test_method_aggregate_optional_answer_rate():
    agg = MethodAggregate(scenario="x", method="summary", trials=3)
    assert agg.model_answer_validity_rate is None
    assert agg.context_validity_rate == 0.0
