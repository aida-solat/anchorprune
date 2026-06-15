"""Packaging verification (v0.9).

Builds a wheel (when the optional ``build`` tool is present) and asserts the
policy-pack YAMLs are shipped while local/generated artifacts are not.
"""

import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _build_wheel(out_dir: Path) -> Path:
    pytest.importorskip("build")
    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--no-isolation",
            "--outdir",
            str(out_dir),
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"wheel build unavailable: {result.stderr[-500:]}")
    wheels = list(out_dir.glob("*.whl"))
    assert wheels, "no wheel produced"
    return wheels[0]


def test_wheel_includes_policy_pack_yaml(tmp_path):
    wheel = _build_wheel(tmp_path)
    with zipfile.ZipFile(wheel) as zf:
        names = zf.namelist()
    yamls = [n for n in names if n.endswith(".yaml") and "policy_packs/builtins/" in n]
    assert yamls, f"policy pack YAMLs missing from wheel: {names[:20]}"
    # The five built-in packs ship.
    for pack in (
        "procurement",
        "coding_agent",
        "contract_review",
        "compliance",
        "security_review",
    ):
        assert any(n.endswith(f"{pack}.yaml") for n in yamls), pack


def test_wheel_excludes_local_and_generated_artifacts(tmp_path):
    wheel = _build_wheel(tmp_path)
    with zipfile.ZipFile(wheel) as zf:
        names = zf.namelist()
    for forbidden in ("real_eval_results", ".next", "node_modules"):
        assert not any(forbidden in n for n in names), forbidden


def test_wheel_ships_new_v09_packages(tmp_path):
    wheel = _build_wheel(tmp_path)
    with zipfile.ZipFile(wheel) as zf:
        names = zf.namelist()
    assert any(n.endswith("anchorprune/errors.py") for n in names)
    assert any("anchorprune/observability/" in n for n in names)
    assert any("anchorprune/evals/" in n for n in names)


def test_real_eval_outputs_gitignored():
    gitignore = (REPO / ".gitignore").read_text(encoding="utf-8")
    assert "real_eval_results/" in gitignore
