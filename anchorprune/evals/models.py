"""Real-model evaluation data models (v0.8).

    Real-model evaluation is observational. Deterministic benchmarks remain
    canonical.

These models describe an *observational* evaluation run: AnchorPrune and the
three memory baselines are each given a deterministically-composed context, that
context is sent once per trial to a (real or mock) provider, and the provider's
answer is scored by a deterministic evaluator. Nothing here is the canonical
AnchorPrune benchmark — the deterministic pack in ``benchmarks/`` is.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

Provider = Literal["mock", "openai", "anthropic", "local"]
Method = Literal["full_history", "sliding_window", "summary", "anchorprune"]

# The memory strategies compared, in display order. AnchorPrune last.
METHODS: List[str] = ["full_history", "sliding_window", "summary", "anchorprune"]


class RealEvalConfig(BaseModel):
    """Configuration for one observational real-model evaluation run."""

    provider: Provider
    model: str
    scenarios: List[str]
    trials: int = 3
    temperature: float = 0.0
    policy_pack: str = "auto"  # "auto" | "<pack-name>" | "none"
    out_dir: str = "real_eval_results"
    window: int = 3
    seed: int = 42
    save_contexts: bool = True
    save_raw_outputs: bool = True
    # Optional model-based judge (v0.8 records the interface only; judging is
    # non-canonical and disabled unless both fields are provided).
    judge_provider: Optional[str] = None
    judge_model: Optional[str] = None


class TrialResult(BaseModel):
    """One provider call: one method, one scenario, one trial."""

    scenario: str
    method: Method
    trial_index: int
    provider: str
    model: str
    prompt_tokens_estimate: int
    output_tokens_estimate: int
    # Context validity and answer validity are deliberately separate signals.
    context_valid: bool
    model_answer_valid: Optional[bool] = None
    adversarial_contaminated: bool = False
    constraint_violation: bool = False
    required_anchor_mentions: List[str] = Field(default_factory=list)
    forbidden_mentions: List[str] = Field(default_factory=list)
    raw_output_path: str = ""
    context_path: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MethodAggregate(BaseModel):
    """Aggregate metrics for one (scenario, method) across all trials."""

    scenario: str
    method: Method
    trials: int
    context_validity_rate: float = 0.0
    model_answer_validity_rate: Optional[float] = None
    adversarial_contamination_rate: float = 0.0
    constraint_violation_rate: float = 0.0
    required_anchor_mention_rate: float = 0.0
    forbidden_content_mention_rate: float = 0.0
    # Sample variance of per-trial answer validity (0/1). 0.0 when deterministic.
    variance_across_trials: float = 0.0
    distinct_outputs: int = 0


class RealEvalSummary(BaseModel):
    """The full observational result set written to ``results.json``."""

    anchorprune_version: str
    provider: str
    model: str
    temperature: float
    trials: int
    scenarios: List[str]
    policy_packs: Dict[str, Optional[str]] = Field(default_factory=dict)
    # These flags are invariant for this layer and are asserted by tests.
    canonical_benchmark: bool = False
    observational: bool = True
    results: List[TrialResult] = Field(default_factory=list)
    aggregates: List[MethodAggregate] = Field(default_factory=list)
