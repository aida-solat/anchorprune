"""The canonical deterministic benchmark must be untouched by real eval (v0.8).

Real-model evaluation is observational. It must write only under its own output
directory and must never read-modify-write anything in ``benchmarks/``.
"""

import hashlib
from pathlib import Path

from anchorprune.evals import RealEvalConfig, run_real_eval

REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"


def _snapshot(directory: Path) -> dict:
    snap = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            snap[str(path.relative_to(directory))] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
    return snap


def test_real_eval_does_not_modify_benchmarks(tmp_path):
    before = _snapshot(BENCHMARKS)

    out_dir = tmp_path / "real_eval_results"
    cfg = RealEvalConfig(
        provider="mock",
        model="mock-deterministic",
        scenarios=["coding_agent", "contract_review"],
        trials=2,
        out_dir=str(out_dir),
    )
    run_real_eval(cfg)

    after = _snapshot(BENCHMARKS)
    assert before == after, "real eval must not modify benchmarks/"

    # And the eval must write only under its own out_dir.
    assert out_dir.exists()
    assert BENCHMARKS.resolve() not in out_dir.resolve().parents
    assert out_dir.resolve() != BENCHMARKS.resolve()
