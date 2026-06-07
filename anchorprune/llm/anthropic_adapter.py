"""Anthropic LLM adapter (optional).

The ``anthropic`` package is an *optional* dependency. Importing this module is
always safe; the dependency is only required when you actually construct an
:class:`AnthropicLLM`. Install with ``pip install 'anchorprune[anthropic]'``.

This adapter performs real network calls and is therefore never used by the
deterministic benchmark pack.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from anchorprune.llm.base import LLMClient, LLMRequest, LLMResponse


class AnthropicLLM(LLMClient):
    provider = "anthropic"

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-latest",
        *,
        api_key: Optional[str] = None,
        max_tokens: int = 1024,
        client: Any = None,
    ) -> None:
        self.model = model
        self._default_max_tokens = max_tokens
        if client is not None:
            self._client = client
            return
        try:
            from anthropic import Anthropic  # type: ignore
        except ImportError as exc:  # pragma: no cover - exercised via guard test
            raise ImportError(
                "The 'anthropic' package is required for AnthropicLLM. Install it "
                "with `pip install 'anchorprune[anthropic]'`."
            ) from exc
        self._client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def generate(self, request: LLMRequest) -> LLMResponse:
        message = self._client.messages.create(
            model=self.model,
            system=request.system or "",
            max_tokens=request.max_tokens or self._default_max_tokens,
            temperature=request.temperature,
            messages=[{"role": "user", "content": request.prompt}],
        )
        text = "".join(
            getattr(block, "text", "") for block in getattr(message, "content", [])
        )
        usage = getattr(message, "usage", None)
        return LLMResponse(
            text=text,
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
            model=getattr(message, "model", self.model),
            provider=self.provider,
        )
