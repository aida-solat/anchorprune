"""Benchmark pack runner.

Runs the full set of benchmark scenarios and writes ``benchmark_report.md`` and
``results.json``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from anchorprune.benchmark.harness import BenchmarkResult, run_benchmark
from anchorprune.benchmark.report import build_markdown, build_results_json
from anchorprune.scenario import load_scenario

# Repo-relative default scenario set (Benchmark Pack v0.1).
_EXAMPLES = Path(__file__).resolve().parents[2] / "examples"
DEFAULT_SCENARIOS: Dict[str, Path] = {
    "supplier": _EXAMPLES / "supplier" / "scenario.json",
    "coding_agent": _EXAMPLES / "coding_agent" / "scenario.json",
    "contract_review": _EXAMPLES / "contract_review" / "scenario.json",
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
    pack = run_pack(scenarios, window=window)
    out_dir.mkdir(parents=True, exist_ok=True)

    report_path = out_dir / "benchmark_report.md"
    results_path = out_dir / "results.json"

    report_path.write_text(build_markdown(pack), encoding="utf-8")
    results_path.write_text(
        json.dumps(build_results_json(pack), indent=2), encoding="utf-8"
    )
    return [report_path, results_path]
