"""Top-level orchestration for real-model evaluation (v0.8).

Ties the runner, evaluators, output writers, and report together. Writes all
artifacts under ``config.out_dir`` and never under ``benchmarks/``.

    Real-model evaluation is observational. Deterministic benchmarks remain
    canonical.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from anchorprune.evals.models import RealEvalConfig, RealEvalSummary
from anchorprune.evals.outputs import (
    build_metadata,
    ensure_dirs,
    write_context,
    write_metadata,
    write_raw_output,
    write_report_md,
    write_results_json,
)
from anchorprune.evals.report import build_report, build_results_payload
from anchorprune.evals.runner import run_eval


def _version() -> str:
    from anchorprune import __version__

    return __version__


def run_real_eval(config: RealEvalConfig) -> Tuple[RealEvalSummary, List[Path]]:
    """Run an observational evaluation and write all artifacts.

    Returns the summary and the list of top-level artifact paths
    (``results.json``, ``report.md``, ``metadata.json``).
    """

    version = _version()
    summary, artifacts = run_eval(config, version=version)

    out_dir = Path(config.out_dir)
    ensure_dirs(out_dir)

    # Persist raw outputs / contexts, recording their relative paths back onto
    # the corresponding TrialResult so results.json points at the artifacts.
    for scenario_name, methods in artifacts.items():
        for method, entries in methods.items():
            for trial, context, output in entries:
                if config.save_raw_outputs:
                    trial.raw_output_path = write_raw_output(
                        out_dir, scenario_name, trial.trial_index, method, output
                    )
                if config.save_contexts:
                    trial.context_path = write_context(
                        out_dir, scenario_name, trial.trial_index, method, context
                    )

    metadata = build_metadata(
        config, version=version, policy_packs=summary.policy_packs
    )
    results_path = write_results_json(out_dir, build_results_payload(summary))
    report_path = write_report_md(out_dir, build_report(summary))
    metadata_path = write_metadata(out_dir, metadata)

    return summary, [results_path, report_path, metadata_path]
