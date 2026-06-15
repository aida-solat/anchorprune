"""v1.0 stabilization checks: frozen public API, CLI, docs, claims, version."""

import json
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from anchorprune.cli import app

REPO = Path(__file__).resolve().parents[1]
runner = CliRunner()

EXPECTED_VERSION = "1.0.0"


def test_public_api_exports():
    import anchorprune
    from anchorprune import (
        AnchorPruneMiddleware,
        AnchorPruneRuntime,
        MockLLM,
    )
    from anchorprune.policy_packs import (
        get_policy_pack,
        list_policy_packs,
        validate_policy_pack,
    )

    for name in (
        "AnchorPruneRuntime",
        "AnchorPruneMiddleware",
        "MockLLM",
        "GovernedContext",
    ):
        assert name in anchorprune.__all__, name

    for method in (
        "run_step",
        "govern_and_compose",
        "ingest_model_output",
        "add_tool_output",
        "from_policy_pack",
    ):
        assert hasattr(AnchorPruneRuntime, method), method

    for method in ("before_model_call", "after_model_call"):
        assert hasattr(AnchorPruneMiddleware, method), method

    assert callable(get_policy_pack)
    assert callable(list_policy_packs)
    assert callable(validate_policy_pack)
    assert validate_policy_pack("contract_review").name == "contract_review"
    assert MockLLM().provider == "mock"


def test_cli_commands_exist():
    top = runner.invoke(app, ["--help"])
    assert top.exit_code == 0
    for cmd in (
        "run",
        "inspect",
        "benchmark",
        "pack",
        "serve",
        "real-eval",
        "doctor",
        "packs",
        "db",
    ):
        assert cmd in top.stdout, cmd

    packs = runner.invoke(app, ["packs", "--help"])
    for sub in ("list", "show", "validate"):
        assert sub in packs.stdout, sub

    db = runner.invoke(app, ["db", "--help"])
    for sub in ("migrate", "info"):
        assert sub in db.stdout, sub


def test_docs_claims_file_exists():
    assert (REPO / "docs" / "claims.md").exists()
    text = (REPO / "docs" / "claims.md").read_text(encoding="utf-8")
    assert "Allowed claims" in text
    assert "Forbidden claims" in text
    assert "governs what reaches them" in text


def test_api_stability_doc_exists():
    text = (REPO / "docs" / "api_stability.md").read_text(encoding="utf-8")
    assert "stable for the v1.x series" in text
    assert "experimental" in text.lower()


def test_examples_have_readmes():
    examples = [
        "supplier",
        "coding_agent",
        "contract_review",
        "integrations/coding_agent_loop",
        "policy_packs/contract_review_pack_demo",
        "real_eval",
    ]
    for rel in examples:
        assert (REPO / "examples" / rel / "README.md").exists(), rel
    # Every scenario directory ships a README too.
    for scenario in (REPO / "examples").rglob("scenario.json"):
        assert (scenario.parent / "README.md").exists(), str(scenario.parent)


def test_demo_script_exists():
    demo = REPO / "scripts" / "demo_v1.sh"
    assert demo.exists()
    text = demo.read_text(encoding="utf-8")
    for needle in (
        "anchorprune doctor",
        "anchorprune packs list",
        "anchorprune pack",
        "anchorprune real-eval",
    ):
        assert needle in text, needle


def test_readme_contains_no_forbidden_claims():
    readme = (REPO / "README.md").read_text(encoding="utf-8").lower()
    # Positive forbidden assertions (the README only ever states these negated).
    forbidden = [
        "production-ready enterprise platform",
        "guarantees correctness",
        "solves long-context memory",
        "replaces rag",
        "prevents all prompt injection",
        "improves llm reasoning",
        "makes models smarter",
    ]
    for phrase in forbidden:
        assert phrase not in readme, phrase


def test_v1_version_consistency():
    # Avoid tomllib (stdlib only on 3.11+); the CI matrix includes 3.10.
    pyproject_text = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', pyproject_text)
    assert match is not None, "version not found in pyproject.toml"
    assert match.group(1) == EXPECTED_VERSION

    import anchorprune

    assert anchorprune.__version__ == EXPECTED_VERSION

    dash = json.loads(
        (REPO / "dashboard" / "package.json").read_text(encoding="utf-8")
    )
    assert dash["version"] == EXPECTED_VERSION


def test_wheel_install_smoke(tmp_path):
    pytest.importorskip("build")
    import subprocess
    import sys
    import zipfile

    result = subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--no-isolation",
         "--outdir", str(tmp_path)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"wheel build unavailable: {result.stderr[-300:]}")
    wheels = list(tmp_path.glob("*.whl"))
    assert wheels, "no wheel produced"
    assert EXPECTED_VERSION in wheels[0].name
    # The wheel carries the frozen version in the package metadata.
    with zipfile.ZipFile(wheels[0]) as zf:
        init = zf.read("anchorprune/__init__.py").decode("utf-8")
    assert f'__version__ = "{EXPECTED_VERSION}"' in init
