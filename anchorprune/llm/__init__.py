"""LLM client abstraction and a deterministic mock implementation.

Real-provider adapters (``OpenAILLM``, ``AnthropicLLM``) live in their own
modules and are imported lazily so their optional dependencies never affect a
core install. Import them explicitly, e.g.
``from anchorprune.llm.openai_adapter import OpenAILLM``.
"""

from anchorprune.llm.base import LLMClient, LLMRequest, LLMResponse, LLMResult
from anchorprune.llm.local_adapter import CallableLLM, EchoLLM
from anchorprune.llm.mock import MockLLM

__all__ = [
    "LLMClient",
    "LLMRequest",
    "LLMResponse",
    "LLMResult",
    "MockLLM",
    "CallableLLM",
    "EchoLLM",
]
