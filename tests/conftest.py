import json
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "supplier" / "scenario.json"


@pytest.fixture
def supplier_scenario() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))
