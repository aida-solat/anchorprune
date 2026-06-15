"""Real-model evaluation runner (v0.8).

Resolves providers, scenarios, and policy packs, composes each method's context
once per scenario, then calls the provider ``trials`` times per method. The
deterministic benchmark is never invoked or modified here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from anchorprune.evals.evaluators import EvalCriteria
from anchorprune.evals.models import (
    METHODS,
    MethodAggregate,
    RealEvalConfig,
    RealEvalSummary,
    TrialResult,
)
from anchorprune.evals.trial import aggregate_trials, compose_final_contexts, run_trial
from anchorprune.llm.base import LLMClient
from anchorprune.scenario import load_scenario


class ProviderUnavailableError(RuntimeError):
    """Raised when a provider's optional SDK or API key is unavailable."""


def build_provider(provider: str, model: str) -> LLMClient:
    """Construct an LLM client for a provider, with friendly errors.

    ``mock`` and ``local`` never touch the network and need no API key, so the
    offline test suite and CI always work. ``openai``/``anthropic`` require their
    optional extras; a missing SDK raises a clear, actionable error.
    """

    provider = provider.lower()
    if provider == "mock":
        from anchorprune.llm.mock import MockLLM

        return MockLLM()
    if provider == "local":
        from anchorprune.llm.local_adapter import EchoLLM

        return EchoLLM()
    if provider == "openai":
        try:
            from anchorprune.llm.openai_adapter import OpenAILLM

            return OpenAILLM(model or "gpt-4o-mini")
        except ImportError as exc:
            raise ProviderUnavailableError(
                "Provider 'openai' requires the optional extra and an API key.\n"
                "  pip install -e \".[openai]\"\n"
                "  export OPENAI_API_KEY=...\n"
                f"({exc})"
            ) from exc
    if provider == "anthropic":
        try:
            from anchorprune.llm.anthropic_adapter import AnthropicLLM

            return AnthropicLLM(model or "claude-3-5-sonnet-latest")
        except ImportError as exc:
            raise ProviderUnavailableError(
                "Provider 'anthropic' requires the optional extra and an API key.\n"
                "  pip install -e \".[anthropic]\"\n"
                "  export ANTHROPIC_API_KEY=...\n"
                f"({exc})"
            ) from exc
    raise ProviderUnavailableError(
        f"Unknown provider '{provider}'. Use mock|openai|anthropic|local."
    )


def _scenario_paths() -> Dict[str, Path]:
    """Built-in scenario name -> path, reusing the benchmark scenario set."""

    from anchorprune.benchmark.pack import DEFAULT_SCENARIOS, LONG_RUN_SCENARIOS

    return {**DEFAULT_SCENARIOS, **LONG_RUN_SCENARIOS}


def resolve_scenario(name_or_path: str) -> Tuple[str, dict]:
    """Resolve a scenario name (built-in) or a path into ``(name, dict)``."""

    paths = _scenario_paths()
    if name_or_path in paths:
        return name_or_path, load_scenario(paths[name_or_path])
    path = Path(name_or_path)
    if path.exists():
        return path.stem, load_scenario(path)
    raise FileNotFoundError(
        f"Unknown scenario '{name_or_path}'. Known: {', '.join(sorted(paths))}, "
        "or pass a path to a scenario JSON file."
    )


def resolve_policy_pack(
    scenario_name: str, scenario: dict, requested: str
) -> Optional[str]:
    """Resolve which policy pack governs a scenario for this eval.

    - ``"none"`` -> no pack.
    - ``"auto"`` -> the scenario's own ``policy_pack``, else a built-in pack
      whose name matches the scenario name, else none.
    - otherwise -> the named pack (validated by the registry on use).
    """

    if requested == "none":
        return None
    if requested != "auto":
        return requested

    if scenario.get("policy_pack"):
        return scenario["policy_pack"]
    from anchorprune.policy_packs import has_policy_pack

    if has_policy_pack(scenario_name):
        return scenario_name
    return None


def _pack_label(pack_name: Optional[str]) -> Optional[str]:
    if not pack_name:
        return None
    from anchorprune.policy_packs import get_policy_pack

    pack = get_policy_pack(pack_name)
    return f"{pack.name}@{pack.version}"


def run_eval(
    config: RealEvalConfig, *, version: str
) -> Tuple[RealEvalSummary, Dict[str, Dict[str, List[Tuple[TrialResult, str, str]]]]]:
    """Execute the evaluation.

    Returns the summary plus, per scenario/method, the list of
    ``(trial_result, context, output)`` so the caller can write artifacts.
    """

    provider_llm = build_provider(config.provider, config.model)
    model_name = getattr(provider_llm, "model", config.model)

    all_trials: List[TrialResult] = []
    aggregates: List[MethodAggregate] = []
    policy_packs: Dict[str, Optional[str]] = {}
    # scenario -> method -> [(trial_result, context, output_text)]
    artifacts: Dict[str, Dict[str, List[Tuple[TrialResult, str, str]]]] = {}

    for raw_name in config.scenarios:
        scenario_name, scenario = resolve_scenario(raw_name)
        pack_name = resolve_policy_pack(scenario_name, scenario, config.policy_pack)
        policy_packs[scenario_name] = _pack_label(pack_name)

        # Inject the resolved pack so AnchorPrune's governed runtime uses it.
        scenario = dict(scenario)
        if pack_name:
            scenario["policy_pack"] = pack_name

        criteria = EvalCriteria.from_scenario(scenario)
        contexts = compose_final_contexts(scenario, window=config.window)
        artifacts[scenario_name] = {}

        for method in METHODS:
            context = contexts[method]
            method_trials: List[TrialResult] = []
            artifacts[scenario_name][method] = []
            for trial_index in range(1, config.trials + 1):
                trial, output = run_trial(
                    provider_llm=provider_llm,
                    provider=config.provider,
                    model=model_name,
                    scenario_name=scenario_name,
                    method=method,
                    trial_index=trial_index,
                    context=context,
                    criteria=criteria,
                    temperature=config.temperature,
                )
                method_trials.append(trial)
                all_trials.append(trial)
                artifacts[scenario_name][method].append((trial, context, output))
            aggregates.append(
                aggregate_trials(scenario_name, method, method_trials)
            )

    summary = RealEvalSummary(
        anchorprune_version=version,
        provider=config.provider,
        model=model_name,
        temperature=config.temperature,
        trials=config.trials,
        scenarios=[resolve_scenario(s)[0] for s in config.scenarios],
        policy_packs=policy_packs,
        results=all_trials,
        aggregates=aggregates,
    )
    return summary, artifacts
