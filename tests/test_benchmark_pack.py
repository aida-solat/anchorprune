import json
from pathlib import Path

from anchorprune.benchmark.pack import (
    DEFAULT_SCENARIOS,
    LONG_RUN_SCENARIOS,
    run_pack,
    write_pack,
)
from anchorprune.benchmark.report import build_markdown, build_results_json
from anchorprune.scenario import load_scenario

CODING = DEFAULT_SCENARIOS["coding_agent"]
CONTRACT = DEFAULT_SCENARIOS["contract_review"]


def test_default_scenarios_exist():
    for path in DEFAULT_SCENARIOS.values():
        assert Path(path).exists()


def test_coding_agent_anchorprune_quarantines_and_is_correct():
    from anchorprune.benchmark.harness import run_benchmark

    results = run_benchmark(load_scenario(CODING), window=2)
    ap = results["anchorprune"]
    full = results["baseline_a_full_history"]

    # AnchorPrune quarantines all adversarial payloads and keeps every anchor.
    assert ap.critical_conflict_quarantine_rate == 1.0
    assert ap.lost_anchor_rate == 0.0
    assert ap.constraint_adherence_rate == 1.0
    assert ap.milestone_retention_rate == 1.0
    assert ap.final_decision_context_valid == 1.0

    # Full history leaks adversarial instructions into the decision context.
    # Baselines have no governance mechanism, so they quarantine nothing.
    assert full.critical_conflict_quarantine_rate == 0.0
    assert full.final_decision_context_valid == 0.0


def test_contract_review_anchorprune_only_correct_method():
    from anchorprune.benchmark.harness import run_benchmark

    results = run_benchmark(load_scenario(CONTRACT), window=2)
    ap = results["anchorprune"]

    assert ap.final_decision_context_valid == 1.0
    assert ap.lost_anchor_rate == 0.0
    assert ap.critical_conflict_quarantine_rate == 1.0

    baselines = [
        results["baseline_a_full_history"],
        results["baseline_b_sliding_window"],
        results["baseline_c_summary"],
    ]
    # No baseline matches AnchorPrune on decision-context validity here.
    assert all(b.final_decision_context_valid == 0.0 for b in baselines)
    # Baselines cannot quarantine the adversarial override payloads.
    assert all(b.critical_conflict_quarantine_rate == 0.0 for b in baselines)


def test_supplier_quarantine_is_not_applicable():
    from anchorprune.benchmark.harness import run_benchmark

    # The supplier scenario has no adversarial payloads, so the quarantine
    # metric must be N/A (None) for every method -- never a misleading 100%.
    results = run_benchmark(load_scenario(DEFAULT_SCENARIOS["supplier"]), window=2)
    for res in results.values():
        assert res.critical_conflict_quarantine_rate is None


def test_all_metric_rates_in_range():
    pack = run_pack(window=2)
    fields = [
        "lost_anchor_rate",
        "constraint_adherence_rate",
        "payload_eviction_rate",
        "milestone_retention_rate",
        "final_decision_context_valid",
    ]
    for methods in pack.values():
        for res in methods.values():
            for f in fields:
                assert 0.0 <= getattr(res, f) <= 1.0
            # Quarantine rate is either N/A (None) or a rate in [0, 1].
            q = res.critical_conflict_quarantine_rate
            assert q is None or 0.0 <= q <= 1.0
            assert len(res.token_count_by_step) == res.steps


def test_write_pack_outputs(tmp_path):
    report, results, csv = write_pack(tmp_path, window=2)
    assert report.name == "benchmark_report.md"
    assert results.name == "results.json"
    assert csv.name == "long_run_results.csv"
    assert report.exists() and results.exists() and csv.exists()

    data = json.loads(results.read_text(encoding="utf-8"))
    assert data["version"] == "0.2"
    assert set(data["short_scenarios"]) == set(DEFAULT_SCENARIOS)
    assert set(data["long_run_scenarios"]) == set(LONG_RUN_SCENARIOS)

    md = report.read_text(encoding="utf-8")
    assert "Benchmark Pack v0.1" in md
    assert "Long-Run Benchmark Pack v0.2" in md
    assert "coding_agent" in md
    assert "Critical Conflict Quarantine" in md
    assert "Context Growth Slope" in md

    csv_text = csv.read_text(encoding="utf-8")
    assert csv_text.startswith("scenario,method,step,context_tokens")
    assert "long_run_coding_20_steps" in csv_text


def test_report_builders_are_pure():
    pack = run_pack(window=2)
    md = build_markdown(pack)
    js = build_results_json(pack)
    assert "contract_review" in md
    assert "scenarios" in js and len(js["scenarios"]) == 3


def test_long_run_scenarios_exist():
    for path in LONG_RUN_SCENARIOS.values():
        assert Path(path).exists()


def test_long_run_anchorprune_is_bounded_and_governed():
    from anchorprune.benchmark.harness import run_benchmark

    for path in LONG_RUN_SCENARIOS.values():
        results = run_benchmark(load_scenario(path), window=2)
        ap = results["anchorprune"]
        full = results["baseline_a_full_history"]

        # Governance holds over the whole run.
        assert ap.lost_anchor_rate == 0.0
        assert ap.constraint_adherence_rate == 1.0
        assert ap.adversarial_contamination_rate == 0.0
        assert ap.critical_conflict_quarantine_rate == 1.0
        assert ap.milestone_retention_rate == 1.0
        assert ap.final_decision_context_valid == 1.0

        # Context growth is controlled: slower than unbounded full history.
        assert ap.context_growth_slope < full.context_growth_slope
        # Per-step series are aligned with the step count.
        assert len(ap.context_tokens_by_step) == ap.steps
        assert len(ap.anchor_retention_by_step) == ap.steps


def test_tokens_per_valid_context_is_na_for_invalid_final_context():
    from anchorprune.benchmark.report import build_long_run_markdown

    long_pack = run_pack(LONG_RUN_SCENARIOS, window=2)
    md = build_long_run_markdown(long_pack)
    # Full history ends with an adversarial-contaminated (invalid) context, so its
    # Tokens / Valid Context cell must be guarded rather than shown as a small,
    # misleadingly attractive number.
    assert "N/A (invalid context)" in md

    # The guard must hold in BOTH the rendered tables and the machine-readable
    # result: an invalid final context can never present a tokens-per-valid
    # number, in markdown or JSON. Conversely a valid method keeps its number.
    for methods in long_pack.values():
        for res in methods.values():
            if res.final_decision_context_valid < 1.0:
                assert res.tokens_per_valid_context is None
            else:
                assert res.tokens_per_valid_context is not None

    coding = long_pack["long_run_coding_20_steps"]
    full = coding["baseline_a_full_history"]
    assert full.final_decision_context_valid == 0.0
    assert full.tokens_per_valid_context is None
    # AnchorPrune delivers a valid governed context, so its number stands.
    assert coding["anchorprune"].tokens_per_valid_context is not None


def test_long_run_baselines_show_their_failure_modes():
    from anchorprune.benchmark.harness import run_benchmark

    results = run_benchmark(
        load_scenario(LONG_RUN_SCENARIOS["long_run_coding_20_steps"]), window=2
    )
    full = results["baseline_a_full_history"]
    window = results["baseline_b_sliding_window"]

    # Full history: strong retention but unbounded growth + contamination.
    assert full.lost_anchor_rate == 0.0
    assert full.adversarial_contamination_rate > 0.0
    assert full.context_growth_slope > 0.0
    # Sliding window: bounded but forgets critical anchors.
    assert window.lost_anchor_rate > 0.0
