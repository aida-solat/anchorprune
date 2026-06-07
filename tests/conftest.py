import json
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "supplier" / "scenario.json"


@pytest.fixture
def supplier_scenario() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


@pytest.fixture
def api_repo(tmp_path):
    """A fresh SQLite repository backed by a temp database file."""
    from anchorprune.storage import SQLiteRunRepository

    repo = SQLiteRunRepository(str(tmp_path / "api.db"))
    yield repo
    repo.close()


@pytest.fixture
def api_client(api_repo):
    """A FastAPI TestClient wired to a temp-database RunService."""
    from fastapi.testclient import TestClient

    from anchorprune.api.app import create_app

    app = create_app(repository=api_repo)
    with TestClient(app) as client:
        yield client
