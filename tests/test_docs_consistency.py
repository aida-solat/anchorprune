"""Docs + CI consistency pass (v0.9)."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_docs_commands_exist():
    for rel in (
        "docs/index.md",
        "docs/security.md",
        "docs/v1_readiness.md",
        "docs/real_model_eval.md",
        "docs/policy_packs.md",
    ):
        assert (REPO / rel).exists(), rel


def test_security_doc_warns_not_to_expose_api():
    text = " ".join(
        (REPO / "docs" / "security.md").read_text(encoding="utf-8").lower().split()
    )
    assert "do not expose" in text
    assert "public internet" in text
    assert "no auth" in text or "no authentication" in text


def test_ci_commands_documented():
    ci = (REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    for needle in (
        "pytest",
        "ruff check",
        "anchorprune pack",
        "python -m build",
        "twine check",
        "npm run typecheck",
        "npm run build",
    ):
        assert needle in ci, needle


def test_readme_has_v09_section():
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    assert "doctor" in readme
    assert "db migrate" in readme


def test_release_notes_have_v09():
    notes = (REPO / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "v0.9.0" in notes


def test_compose_and_docker_present():
    for rel in ("Dockerfile", "docker-compose.yml", ".dockerignore", ".env.example"):
        assert (REPO / rel).exists(), rel
