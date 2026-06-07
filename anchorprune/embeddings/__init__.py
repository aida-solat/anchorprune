"""Embedding adapters.

The OpenAI-backed client lives in ``openai_adapter`` and is imported lazily so
its optional dependency never affects a core install.
"""

from anchorprune.embeddings.base import EmbeddingClient, cosine_similarity
from anchorprune.embeddings.hash_adapter import HashEmbeddingClient

__all__ = ["EmbeddingClient", "cosine_similarity", "HashEmbeddingClient"]
