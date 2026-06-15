"""Import / dependency boundary tests (v0.9).

The core install must not require FastAPI, OpenAI, Anthropic, LangGraph, or
LlamaIndex. These run in clean subprocesses so import side effects are isolated.
"""

import subprocess
import sys


def _run(code: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )


def test_core_import_boundaries():
    # Importing the core package must not pull heavy optional deps.
    code = (
        "import sys, anchorprune\n"
        "from anchorprune.core.runtime import AnchorPruneRuntime\n"
        "heavy = [m for m in ('fastapi','openai','anthropic','langgraph','llama_index')"
        " if m in sys.modules]\n"
        "assert heavy == [], heavy\n"
        "print('ok')\n"
    )
    result = _run(code)
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


def test_core_import_without_openai_anthropic():
    # Block the optional SDKs entirely; core + mock runtime must still work.
    code = (
        "import sys\n"
        "sys.modules['openai'] = None\n"
        "sys.modules['anthropic'] = None\n"
        "import anchorprune\n"
        "from anchorprune.llm.mock import MockLLM\n"
        "from anchorprune.domains.profiles import get_domain_profile\n"
        "from anchorprune.core.runtime import AnchorPruneRuntime\n"
        "rt = AnchorPruneRuntime(MockLLM(), domain_profile=get_domain_profile('default'))\n"
        "rt.create_run(goal='g')\n"
        "rt.run_step('proceed')\n"
        "print('ok')\n"
    )
    result = _run(code)
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


def test_integrations_do_not_import_langgraph_or_llamaindex():
    code = (
        "import sys\n"
        "import anchorprune.integrations\n"
        "import anchorprune.integrations.langgraph\n"
        "import anchorprune.integrations.llamaindex\n"
        "leaked = [m for m in ('langgraph','llama_index') if m in sys.modules]\n"
        "assert leaked == [], leaked\n"
        "print('ok')\n"
    )
    result = _run(code)
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


def test_real_eval_mock_no_provider_sdk():
    code = (
        "import sys\n"
        "sys.modules['openai'] = None\n"
        "sys.modules['anthropic'] = None\n"
        "from anchorprune.evals import RealEvalConfig, run_eval\n"
        "summary, _ = run_eval(RealEvalConfig(provider='mock',"
        " model='mock-deterministic', scenarios=['coding_agent'], trials=1),"
        " version='0.0.0')\n"
        "assert summary.observational and not summary.canonical_benchmark\n"
        "print('ok')\n"
    )
    result = _run(code)
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout
