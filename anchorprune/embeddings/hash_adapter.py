"""Deterministic hash-based embeddings.

A dependency-free, network-free embedding client that maps text to a fixed-size
pseudo-vector using a hashed bag-of-tokens. It is fully deterministic (stable
across processes via :func:`hashlib`), which makes it ideal for tests and for
deterministic-benchmark mode. It is a cheap stand-in, not a semantic model.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import List

from anchorprune.embeddings.base import EmbeddingClient

_TOKEN = re.compile(r"[a-z0-9]+")


class HashEmbeddingClient(EmbeddingClient):
    def __init__(self, dim: int = 64) -> None:
        if dim <= 0:
            raise ValueError("dim must be positive")
        self.dim = dim

    def embed_text(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        for token in _TOKEN.findall(text.lower()):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dim
            # Sign bit derived from a different byte for a slightly richer space.
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[index] += sign
        norm = math.sqrt(sum(x * x for x in vec))
        if norm == 0.0:
            return vec
        return [x / norm for x in vec]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]
