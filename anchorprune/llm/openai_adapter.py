"""OpenAI LLM adapter (optional).

The ``openai`` package is an *optional* dependency. Importing this module is
always safe; the dependency is only required when you actually construct an
:class:`OpenAILLM`. Install with ``pip install 'anchorprune[openai]'``.

This adapter performs real network calls and is therefore never used by the
deterministic benchmark pack.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from anchorprune.llm.base import LLMClient, LLMRequest, LLMResponse


class OpenAILLM(LLMClient):
    provider = "openai"

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        *,
        api_key: Optional[str] = None,
        client: Any = None,
    ) -> None:
        self.model = model
        if client is not None:
            self._client = client
            return
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:  # pragma: no cover - exercised via guard test
            raise ImportError(
                "The 'openai' package is required for OpenAILLM. Install it with "
                "`pip install 'anchorprune[openai]'`."
            ) from exc
        self._client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    def generate(self, request: LLMRequest) -> LLMResponse:
        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})

        completion = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        choice = completion.choices[0]
        usage = getattr(completion, "usage", None)
        return LLMResponse(
            text=choice.message.content or "",
            input_tokens=getattr(usage, "prompt_tokens", None),
            output_tokens=getattr(usage, "completion_tokens", None),
            model=getattr(completion, "model", self.model),
            provider=self.provider,
        )
