"""LLM client interface.

AnchorPrune is model-agnostic. The runtime depends only on this small contract,
so a mock, an OpenAI client, or an Anthropic client are interchangeable.

v0.3 formalizes the adapter contract around :class:`LLMRequest` /
:class:`LLMResponse` and a single abstract primitive, :meth:`LLMClient.generate`.
The legacy :meth:`LLMClient.complete` helper (returning :class:`LLMResult`) is
preserved as a thin, non-abstract wrapper so the deterministic runtime and
benchmark keep working unchanged. New real-provider adapters only need to
implement ``generate``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LLMRequest(BaseModel):
    """A provider-agnostic generation request."""

    prompt: str
    system: Optional[str] = None
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    """A provider-agnostic generation response."""

    text: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LLMResult(BaseModel):
    """Legacy runtime-facing result.

    Retained for backward compatibility with the deterministic runtime and
    benchmark, which consume ``text``, token counts, and ``proposed_anchor_texts``.
    """

    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    # Optional structured constraints the model claims it relied on / proposes.
    proposed_anchor_texts: List[str] = Field(default_factory=list)


class LLMClient(ABC):
    """Abstract LLM adapter.

    Implementations only need to provide :meth:`generate`. ``complete`` is a
    backward-compatible convenience that adapts an :class:`LLMResponse` into the
    legacy :class:`LLMResult` the runtime consumes; proposed anchor texts, if
    any, are read from ``response.metadata['proposed_anchor_texts']``.
    """

    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Return a completion for the given request."""
        raise NotImplementedError

    def complete(self, prompt: str) -> LLMResult:
        """Legacy helper used by the deterministic runtime and benchmark."""

        response = self.generate(LLMRequest(prompt=prompt))
        proposed = response.metadata.get("proposed_anchor_texts", []) or []
        return LLMResult(
            text=response.text,
            input_tokens=response.input_tokens or 0,
            output_tokens=response.output_tokens or 0,
            proposed_anchor_texts=list(proposed),
        )
