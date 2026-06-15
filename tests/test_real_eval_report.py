"""Report-rendering tests for the v0.8 harness."""

from anchorprune.evals import RealEvalConfig, run_eval
from anchorprune.evals.report import build_report, build_results_payload


def _summary():
    cfg = RealEvalConfig(
        provider="mock",
        model="mock-deterministic",
        scenarios=["coding_agent", "contract_review"],
        trials=2,
    )
    summary, _ = run_eval(cfg, version="0.8.0")
    return summary


def test_real_eval_marks_observational_not_canonical():
    report = build_report(_summary())
    assert "observational" in report.lower()
    assert "not the canonical deterministic benchmark" in report.lower()
    # The canonical-benchmark caveat must appear in the limitations.
    assert "canonical AnchorPrune benchmark" in report


def test_report_separates_context_and_answer_validity():
    report = build_report(_summary())
    assert "Context Valid" in report
    assert "Model Answer Valid" in report


def test_report_lists_configuration_and_packs():
    summary = _summary()
    report = build_report(summary)
    assert "Provider:" in report
    assert "Temperature:" in report
    assert "contract_review@0.1" in report


def test_report_has_variance_and_limitations_sections():
    report = build_report(_summary())
    assert "## Variance Across Trials" in report
    assert "## Limitations" in report
    assert "may vary" in report.lower()


def test_results_payload_roundtrips():
    summary = _summary()
    payload = build_results_payload(summary)
    assert payload["observational"] is True
    assert payload["canonical_benchmark"] is False
    assert len(payload["results"]) == 2 * 2 * 4
