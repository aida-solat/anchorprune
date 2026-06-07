"""Local / offline LLM adapters.

These adapters require no third-party dependencies and never touch the network,
so they are always importable. They are useful for wiring a custom local model
(or any Python callable) into the AnchorPrune pipeline without writing a full
adapter class.
"""

from __future__ import annotations

from typing import Callable, Optional

from anchorprune.blocks.parser import estimate_tokens
from anchorprune.llm.base import LLMClient, LLMRequest, LLMResponse


class CallableLLM(LLMClient):
    """Wrap any ``Callable[[LLMRequest], str]`` as an :class:`LLMClient`.

    This lets a user plug a locally hosted model (llama.cpp, vLLM, transformers,
    an HTTP call, etc.) into AnchorPrune by providing a single function, without
    adding a hard dependency to the core package.
    """

    provider = "local"

    def __init__(
        self,
        fn: Callable[[LLMRequest], str],
        *,
        model: str = "local-callable",
        output_tokens: Optional[int] = None,
    ) -> None:
        self._fn = fn
        self.model = model
        self._output_tokens = output_tokens

    def generate(self, request: LLMRequest) -> LLMResponse:
        text = self._fn(request)
        if not isinstance(text, str):
            raise TypeError(
                "CallableLLM function must return str, got "
                f"{type(text).__name__}"
            )
        return LLMResponse(
            text=text,
            input_tokens=estimate_tokens(request.prompt),
            output_tokens=(
                self._output_tokens
                if self._output_tokens is not None
                else estimate_tokens(text)
            ),
            model=self.model,
            provider=self.provider,
        )


class EchoLLM(LLMClient):
    """Trivial deterministic local adapter that echoes the instruction.

    Mainly a smoke/dev aid: it proves the adapter contract end-to-end with zero
    dependencies and no network. It is *not* used by the deterministic benchmark.
    """

    provider = "local"
    model = "local-echo"

    def generate(self, request: LLMRequest) -> LLMResponse:
        text = f"[echo] {request.prompt.strip()[:280]}"
        return LLMResponse(
            text=text,
            input_tokens=estimate_tokens(request.prompt),
            output_tokens=estimate_tokens(text),
            model=self.model,
            provider=self.provider,
        )
