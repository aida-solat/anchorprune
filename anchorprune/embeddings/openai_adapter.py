"""OpenAI embedding adapter (optional).

The ``openai`` package is an *optional* dependency. Importing this module is
always safe; the dependency is only needed when constructing
:class:`OpenAIEmbeddingClient`. Install with ``pip install 'anchorprune[openai]'``.
"""

from __future__ import annotations

import os
from typing import Any, List, Optional

from anchorprune.embeddings.base import EmbeddingClient


class OpenAIEmbeddingClient(EmbeddingClient):
    def __init__(
        self,
        model: str = "text-embedding-3-small",
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
                "The 'openai' package is required for OpenAIEmbeddingClient. "
                "Install it with `pip install 'anchorprune[openai]'`."
            ) from exc
        self._client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    def embed_text(self, text: str) -> List[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        response = self._client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]
