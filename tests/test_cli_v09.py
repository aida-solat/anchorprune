"""CLI hardening commands: doctor + db migrate/info (v0.9)."""

from typer.testing import CliRunner

from anchorprune.cli import app

runner = CliRunner()


def test_doctor_command():
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0, result.stdout
    out = result.stdout
    assert "AnchorPrune doctor" in out
    assert "Version" in out
    assert "Policy packs" in out
    assert "Core import" in out


def test_db_migrate_and_info(tmp_path):
    db = tmp_path / "v9.db"
    migrate = runner.invoke(app, ["db", "migrate", "--db", str(db)])
    assert migrate.exit_code == 0, migrate.stdout
    assert "Schema version" in migrate.stdout

    # Idempotent: second migrate applies nothing.
    again = runner.invoke(app, ["db", "migrate", "--db", str(db)])
    assert again.exit_code == 0
    assert "up to date" in again.stdout.lower()

    info = runner.invoke(app, ["db", "info", "--db", str(db)])
    assert info.exit_code == 0, info.stdout
    assert "Schema version" in info.stdout
    assert "initial" in info.stdout


def test_db_info_missing_database(tmp_path):
    result = runner.invoke(app, ["db", "info", "--db", str(tmp_path / "nope.db")])
    assert result.exit_code == 0
    assert "does not exist" in result.stdout.lower()
