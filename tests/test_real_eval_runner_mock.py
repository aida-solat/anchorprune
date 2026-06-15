"""Runner tests for the v0.8 harness — mock/fake providers only, no API keys."""

import sys

import pytest
from typer.testing import CliRunner

from anchorprune.cli import app
from anchorprune.evals import (
    ProviderUnavailableError,
    RealEvalConfig,
    build_provider,
    run_eval,
)
from anchorprune.evals.runner import resolve_policy_pack, resolve_scenario
from anchorprune.evals.trial import compose_final_contexts
from anchorprune.llm.base import LLMClient


def _cfg(**kw) -> RealEvalConfig:
    base = dict(
        provider="mock",
        model="mock-deterministic",
        scenarios=["coding_agent", "contract_review"],
        trials=2,
    )
    base.update(kw)
    return RealEvalConfig(**base)


def test_mock_real_eval_runs_without_api_keys(monkeypatch):
    # Ensure no provider keys are needed for the mock path.
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    summary, artifacts = run_eval(_cfg(), version="0.8.0")
    assert len(summary.results) == 2 * 2 * 4  # scenarios x trials x methods
    assert set(artifacts) == {"coding_agent", "contract_review"}


def test_build_provider_mock_and_local_are_offline():
    assert isinstance(build_provider("mock", "mock-deterministic"), LLMClient)
    assert isinstance(build_provider("local", "local-echo"), LLMClient)


def test_real_eval_records_provider_model_temperature():
    summary, _ = run_eval(_cfg(temperature=0.7), version="0.8.0")
    assert summary.provider == "mock"
    assert summary.model == "mock-deterministic"
    assert summary.temperature == 0.7
    assert summary.trials == 2


def test_real_eval_records_policy_pack_metadata():
    summary, _ = run_eval(_cfg(), version="0.8.0")
    assert summary.policy_packs["coding_agent"] == "coding_agent@0.1"
    assert summary.policy_packs["contract_review"] == "contract_review@0.1"


def test_policy_pack_none_disables_pack():
    summary, _ = run_eval(_cfg(policy_pack="none"), version="0.8.0")
    assert summary.policy_packs["coding_agent"] is None


def test_anchorprune_method_uses_policy_pack_runtime():
    # With a pack resolved, AnchorPrune's governed context carries a pack-seeded
    # anchor and stays uncontaminated, unlike the ungoverned full-history method.
    name, scenario = resolve_scenario("contract_review")
    pack = resolve_policy_pack(name, scenario, "auto")
    assert pack == "contract_review"
    scenario = {**scenario, "policy_pack": pack}
    contexts = compose_final_contexts(scenario, window=3)
    assert "liability" in contexts["anchorprune"].lower()

    summary, _ = run_eval(
        RealEvalConfig(
            provider="mock",
            model="mock-deterministic",
            scenarios=["contract_review"],
            trials=1,
        ),
        version="0.8.0",
    )
    by_method = {a.method: a for a in summary.aggregates}
    assert by_method["anchorprune"].context_validity_rate == 1.0
    assert by_method["anchorprune"].adversarial_contamination_rate == 0.0
    assert by_method["full_history"].adversarial_contamination_rate == 1.0


def test_missing_openai_sdk_gives_friendly_error(monkeypatch):
    # Force the optional SDK import to fail regardless of the environment.
    monkeypatch.setitem(sys.modules, "openai", None)
    with pytest.raises(ProviderUnavailableError) as exc:
        build_provider("openai", "gpt-4o-mini")
    msg = str(exc.value).lower()
    assert "openai" in msg and "pip install" in msg


def test_unknown_provider_raises_friendly_error():
    with pytest.raises(ProviderUnavailableError):
        build_provider("gemini", "x")


def test_resolve_scenario_unknown_name():
    with pytest.raises(FileNotFoundError):
        resolve_scenario("definitely_not_a_scenario")


def test_cli_real_eval_mock(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "real-eval",
            "--provider",
            "mock",
            "--model",
            "mock-deterministic",
            "--scenarios",
            "coding_agent,contract_review",
            "--trials",
            "2",
            "--out",
            str(tmp_path / "out"),
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "observational" in result.stdout.lower()
    assert (tmp_path / "out" / "results.json").exists()
    assert (tmp_path / "out" / "report.md").exists()
    assert (tmp_path / "out" / "metadata.json").exists()
