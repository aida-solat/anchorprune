from anchorprune.benchmark.harness import run_benchmark
from anchorprune.scenario import build_runtime, run_scenario


def test_run_supplier_scenario(supplier_scenario):
    runtime, results = run_scenario(supplier_scenario)
    assert len(results) == len(supplier_scenario["steps"])
    summary = results[-1].state_summary
    assert summary["system_anchors"] == 3
    # The irrelevant retrieved chunk should be pruned (compressed or evicted).
    assert summary["payload_blocks"] >= 1


def test_evidence_linking_in_scenario(supplier_scenario):
    runtime = build_runtime(supplier_scenario)
    # Payload referencing the compliance registry should have an evidence link.
    linked = [b for b in runtime.graph.payload_blocks.values() if b.evidence_refs]
    assert linked


def test_benchmark_anchorprune_keeps_critical_anchors(supplier_scenario):
    results = run_benchmark(supplier_scenario, window=2)
    ap = results["anchorprune"]
    window = results["baseline_b_sliding_window"]

    # AnchorPrune retains all critical anchors in the final context.
    assert ap.constraint_adherence_rate == 1.0
    # The sliding window baseline loses at least one critical anchor.
    assert window.lost_anchor_rate > 0.0


def test_benchmark_anchorprune_within_budget_and_beats_summary(supplier_scenario):
    from anchorprune.domains.profiles import get_domain_profile

    results = run_benchmark(supplier_scenario)
    ap = results["anchorprune"]
    summary = results["baseline_c_summary"]

    budget = get_domain_profile(supplier_scenario["domain"]).token_budget
    # AnchorPrune's governed context never exceeds the domain token budget.
    assert ap.final_context_tokens <= budget
    # And it adheres to constraints at least as well as the lossy summary baseline.
    assert ap.constraint_adherence_rate >= summary.constraint_adherence_rate
