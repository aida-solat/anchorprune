"""Output-structure tests for the v0.8 harness."""

import json
from pathlib import Path

from anchorprune.evals import RealEvalConfig, run_real_eval


def _run(tmp_path: Path, **kw) -> tuple:
    cfg = RealEvalConfig(
        provider="mock",
        model="mock-deterministic",
        scenarios=["coding_agent"],
        trials=2,
        out_dir=str(tmp_path / "real_eval_results"),
        **kw,
    )
    return run_real_eval(cfg), Path(cfg.out_dir)


def test_real_eval_writes_results_json(tmp_path):
    (summary, _paths), out = _run(tmp_path)
    results = out / "results.json"
    assert results.exists()
    data = json.loads(results.read_text(encoding="utf-8"))
    assert data["provider"] == "mock"
    assert len(data["results"]) == 1 * 2 * 4
    assert "aggregates" in data


def test_real_eval_writes_report_md(tmp_path):
    _result, out = _run(tmp_path)
    report = out / "report.md"
    assert report.exists()
    assert "Real-Model Evaluation Report" in report.read_text(encoding="utf-8")


def test_real_eval_writes_metadata_json(tmp_path):
    _result, out = _run(tmp_path)
    meta = json.loads((out / "metadata.json").read_text(encoding="utf-8"))
    assert meta["provider"] == "mock"
    assert meta["model"] == "mock-deterministic"
    assert meta["temperature"] == 0.0
    assert meta["trials"] == 2
    assert meta["canonical_benchmark"] is False
    assert meta["observational"] is True
    assert meta["policy_packs"]["coding_agent"] == "coding_agent@0.1"


def test_real_eval_writes_raw_outputs_and_contexts(tmp_path):
    _result, out = _run(tmp_path)
    raw = out / "raw_outputs" / "coding_agent" / "trial_001_anchorprune.txt"
    ctx = out / "contexts" / "coding_agent" / "trial_001_anchorprune_context.txt"
    assert raw.exists() and raw.read_text(encoding="utf-8")
    assert ctx.exists() and ctx.read_text(encoding="utf-8")


def test_trial_results_point_at_artifacts(tmp_path):
    (summary, _paths), out = _run(tmp_path)
    for trial in summary.results:
        assert (out / trial.raw_output_path).exists()
        assert (out / trial.context_path).exists()


def test_save_flags_disable_artifacts(tmp_path):
    _result, out = _run(tmp_path, save_contexts=False, save_raw_outputs=False)
    assert not (out / "raw_outputs" / "coding_agent").exists()
    assert not (out / "contexts" / "coding_agent").exists()
    # results.json / report.md are always written.
    assert (out / "results.json").exists()


def test_marks_observational_not_canonical(tmp_path):
    (summary, _paths), out = _run(tmp_path)
    data = json.loads((out / "results.json").read_text(encoding="utf-8"))
    assert data["canonical_benchmark"] is False
    assert data["observational"] is True
    assert summary.canonical_benchmark is False
    assert summary.observational is True
