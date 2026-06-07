from pathlib import Path

from typer.testing import CliRunner

from anchorprune.cli import app

runner = CliRunner()
EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "supplier" / "scenario.json"


def test_init_command():
    result = runner.invoke(app, ["init", "--domain", "procurement"])
    assert result.exit_code == 0
    assert "procurement" in result.stdout


def test_run_then_inspect(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["run", "--input", str(EXAMPLE)])
    assert result.exit_code == 0, result.stdout

    runs = list((tmp_path / ".anchorprune" / "runs").glob("*.json"))
    assert runs
    run_id = runs[0].stem

    inspected = runner.invoke(app, ["inspect", "--run-id", run_id])
    assert inspected.exit_code == 0
    assert "Anchors" in inspected.stdout


def test_benchmark_command():
    result = runner.invoke(app, ["benchmark", "--input", str(EXAMPLE)])
    assert result.exit_code == 0
    assert "AnchorPrune" in result.stdout
