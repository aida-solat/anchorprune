"""Benchmark pack runner.

Runs the full set of benchmark scenarios and writes ``benchmark_report.md`` and
``results.json``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from anchorprune.benchmark.harness import BenchmarkResult, run_benchmark
from anchorprune.benchmark.report import (
    build_full_report,
    build_full_results,
    build_long_run_csv,
)
from anchorprune.scenario import load_scenario

# Repo-relative default scenario set (Benchmark Pack v0.1, short adversarial).
_EXAMPLES = Path(__file__).resolve().parents[2] / "examples"
DEFAULT_SCENARIOS: Dict[str, Path] = {
    "supplier": _EXAMPLES / "supplier" / "scenario.json",
    "coding_agent": _EXAMPLES / "coding_agent" / "scenario.json",
    "contract_review": _EXAMPLES / "contract_review" / "scenario.json",
}

# Benchmark Pack v0.2 long-run scenarios (10-20 steps, context-growth focus).
LONG_RUN_SCENARIOS: Dict[str, Path] = {
    "long_run_coding_20_steps": _EXAMPLES / "long_run_coding_20_steps" / "scenario.json",
    "long_run_contract_15_steps": _EXAMPLES / "long_run_contract_15_steps" / "scenario.json",
    "long_run_procurement_10_steps": _EXAMPLES
    / "long_run_procurement_10_steps"
    / "scenario.json",
}


def run_pack(
    scenarios: Optional[Dict[str, Path]] = None,
    *,
    window: int = 3,
) -> Dict[str, Dict[str, BenchmarkResult]]:
    scenarios = scenarios or DEFAULT_SCENARIOS
    pack: Dict[str, Dict[str, BenchmarkResult]] = {}
    for name, path in scenarios.items():
        scenario = load_scenario(path)
        pack[name] = run_benchmark(scenario, window=window)
    return pack


def write_pack(
    out_dir: Path,
    scenarios: Optional[Dict[str, Path]] = None,
    *,
    window: int = 3,
) -> List[Path]:
    """Run the short (v0.1) and long-run (v0.2) packs and write all artifacts.

    Writes ``benchmark_report.md`` (both sections), ``results.json`` (both
    packs, machine-readable), and ``long_run_results.csv`` (per-step context
    growth). Returns ``[report, results, csv]``.
    """

    short_pack = run_pack(scenarios or DEFAULT_SCENARIOS, window=window)
    long_pack = run_pack(LONG_RUN_SCENARIOS, window=window)
    out_dir.mkdir(parents=True, exist_ok=True)

    report_path = out_dir / "benchmark_report.md"
    results_path = out_dir / "results.json"
    csv_path = out_dir / "long_run_results.csv"

    report_path.write_text(
        build_full_report(short_pack, long_pack), encoding="utf-8"
    )
    results_path.write_text(
        json.dumps(build_full_results(short_pack, long_pack), indent=2),
        encoding="utf-8",
    )
    csv_path.write_text(build_long_run_csv(long_pack), encoding="utf-8")
    return [report_path, results_path, csv_path]
