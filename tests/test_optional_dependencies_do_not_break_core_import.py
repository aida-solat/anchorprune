"""Optional provider SDKs must never break a core install.

Importing an adapter module is always safe; only *constructing* the client
without its optional dependency should raise a clear ImportError.
"""

import importlib
import importlib.util

import pytest


def test_core_imports_do_not_require_optional_sdks():
    # These must import with only the core dependencies installed.
    for module in (
        "anchorprune",
        "anchorprune.llm",
        "anchorprune.embeddings",
        "anchorprune.config",
        "anchorprune.core.runtime",
    ):
        assert importlib.import_module(module) is not None


def test_optional_adapter_modules_are_importable_without_their_sdk():
    # Importing the module is safe even if the SDK is absent.
    for module in (
        "anchorprune.llm.openai_adapter",
        "anchorprune.llm.anthropic_adapter",
        "anchorprune.embeddings.openai_adapter",
    ):
        assert importlib.import_module(module) is not None


@pytest.mark.skipif(
    importlib.util.find_spec("openai") is not None,
    reason="openai is installed; the ImportError guard cannot be exercised",
)
def test_constructing_openai_adapter_without_sdk_raises_clear_error():
    from anchorprune.llm.openai_adapter import OpenAILLM

    with pytest.raises(ImportError, match="anchorprune\\[openai\\]"):
        OpenAILLM()


@pytest.mark.skipif(
    importlib.util.find_spec("anthropic") is not None,
    reason="anthropic is installed; the ImportError guard cannot be exercised",
)
def test_constructing_anthropic_adapter_without_sdk_raises_clear_error():
    from anchorprune.llm.anthropic_adapter import AnthropicLLM

    with pytest.raises(ImportError, match="anchorprune\\[anthropic\\]"):
        AnthropicLLM()


def test_adapters_accept_injected_client_without_sdk():
    # A user can inject a pre-built client/transport, bypassing the SDK guard.
    from anchorprune.llm.openai_adapter import OpenAILLM

    class _DummyClient:
        pass

    adapter = OpenAILLM(client=_DummyClient())
    assert adapter.provider == "openai"
