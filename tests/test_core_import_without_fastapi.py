"""A core install must not require FastAPI.

We prove this by importing the core in a subprocess where ``fastapi`` and
``uvicorn`` are made unimportable, regardless of whether they happen to be
installed in the dev environment.
"""

import subprocess
import sys

_SCRIPT = """
import sys, importlib

class _Blocker:
    BLOCKED = {"fastapi", "uvicorn", "starlette"}
    def find_spec(self, name, path=None, target=None):
        top = name.split(".")[0]
        if top in self.BLOCKED:
            raise ImportError(f"blocked: {name}")
        return None

sys.meta_path.insert(0, _Blocker())
for mod in list(sys.modules):
    if mod.split(".")[0] in _Blocker.BLOCKED:
        del sys.modules[mod]

# Core + storage + services + integrations must import with FastAPI absent.
for module in (
    "anchorprune",
    "anchorprune.core.runtime",
    "anchorprune.config",
    "anchorprune.storage",
    "anchorprune.services",
    "anchorprune.middleware",
    "anchorprune.integrations",
    "anchorprune.integrations.langgraph",
    "anchorprune.integrations.llamaindex",
    "anchorprune.policy_packs",
):
    importlib.import_module(module)

# Policy packs (v0.7) must load and configure a runtime with FastAPI absent.
from anchorprune.policy_packs import get_policy_pack, list_policy_packs

assert "contract_review" in list_policy_packs()
get_policy_pack("contract_review")

# The integration layer must work end-to-end with FastAPI absent.
from anchorprune import AnchorPruneMiddleware

mw = AnchorPruneMiddleware(domain="default")
rid = mw.create_run(goal="g")
governed = mw.before_model_call(rid, new_payloads=["obs"], instruction="proceed")
assert governed.prompt
mw.after_model_call(rid, "done")

# A run can be created, stepped, and persisted with no FastAPI involved.
from anchorprune.storage import SQLiteRunRepository
from anchorprune.services import RunService

svc = RunService(SQLiteRunRepository(":memory:"))
run = svc.create_run(goal="g", domain="default", config_name="mock")
svc.run_step(run.id, instruction="proceed")
assert svc.get_metrics(run.id)["summary"]["total_steps"] == 1

# Confirm FastAPI really was not imported.
assert "fastapi" not in sys.modules
print("OK")
"""


def test_core_import_without_fastapi():
    result = subprocess.run(
        [sys.executable, "-c", _SCRIPT],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


def test_importing_api_requires_fastapi_only_then():
    # The API package import path is separate from the core; importing it in
    # the dev env (where FastAPI is present) must succeed.
    import importlib

    assert importlib.import_module("anchorprune.api") is not None
