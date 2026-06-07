"""LLM client interface.

AnchorPrune is model-agnostic. The runtime depends only on this small contract,
so a mock, an OpenAI client, or an Anthropic client are interchangeable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from pydantic import BaseModel, Field


class LLMResult(BaseModel):
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    # Optional structured constraints the model claims it relied on / proposes.
    proposed_anchor_texts: List[str] = Field(default_factory=list)


class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> LLMResult:
        """Return a completion for the composed prompt."""
        raise NotImplementedError
