"""Output writers for real-model evaluation (v0.8).

Owns the on-disk layout of an evaluation run. Everything is written under the
configured ``out_dir`` and **never** under ``benchmarks/`` — the canonical
deterministic benchmark is untouched by real evaluation.

    real_eval_results/
      results.json
      report.md
      metadata.json
      raw_outputs/<scenario>/trial_001_<method>.txt
      contexts/<scenario>/trial_001_<method>_context.txt
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from anchorprune.evals.models import RealEvalConfig


def ensure_dirs(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "raw_outputs").mkdir(exist_ok=True)
    (out_dir / "contexts").mkdir(exist_ok=True)


def _trial_stub(trial_index: int, method: str) -> str:
    return f"trial_{trial_index:03d}_{method}"


def write_raw_output(
    out_dir: Path, scenario: str, trial_index: int, method: str, text: str
) -> str:
    """Write a model output and return its path relative to ``out_dir``."""

    rel = Path("raw_outputs") / scenario / f"{_trial_stub(trial_index, method)}.txt"
    path = out_dir / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return str(rel)


def write_context(
    out_dir: Path, scenario: str, trial_index: int, method: str, context: str
) -> str:
    """Write a composed context and return its path relative to ``out_dir``."""

    rel = (
        Path("contexts")
        / scenario
        / f"{_trial_stub(trial_index, method)}_context.txt"
    )
    path = out_dir / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(context, encoding="utf-8")
    return str(rel)


def build_metadata(
    config: RealEvalConfig,
    *,
    version: str,
    policy_packs: Dict[str, Optional[str]],
    created_at: Optional[str] = None,
) -> dict:
    """Assemble the ``metadata.json`` payload (pinned, observational)."""

    return {
        "anchorprune_version": version,
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "provider": config.provider,
        "model": config.model,
        "temperature": config.temperature,
        "trials": config.trials,
        "seed": config.seed,
        "scenarios": list(config.scenarios),
        "policy_packs": policy_packs,
        "canonical_benchmark": False,
        "observational": True,
    }


def write_metadata(out_dir: Path, metadata: dict) -> Path:
    path = out_dir / "metadata.json"
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return path


def write_results_json(out_dir: Path, payload: dict) -> Path:
    path = out_dir / "results.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_report_md(out_dir: Path, text: str) -> Path:
    path = out_dir / "report.md"
    path.write_text(text, encoding="utf-8")
    return path
