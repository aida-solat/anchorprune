"""Embedding client interface.

Embeddings power optional relevance/redundancy scoring. The interface is kept
deliberately small. A deterministic :class:`HashEmbeddingClient` is provided for
tests and offline use; an optional OpenAI-backed client lives in
``openai_adapter`` behind an optional dependency.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import List


class EmbeddingClient(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Return the embedding vector for a single text."""
        raise NotImplementedError

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Return embedding vectors for a batch of texts."""
        raise NotImplementedError


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity helper, safe for zero vectors and length mismatch."""

    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    dot = sum(a[i] * b[i] for i in range(n))
    na = math.sqrt(sum(x * x for x in a[:n]))
    nb = math.sqrt(sum(x * x for x in b[:n]))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)
