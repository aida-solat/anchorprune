"""Configuration models for the AnchorPrune pipeline.

A config selects, per stage, whether to use a deterministic heuristic component
or a model-based adapter. ``deterministic_benchmark_mode`` is a hard safety
switch: when true, the factory forces heuristic components everywhere regardless
of other settings, guaranteeing the benchmark cannot be contaminated by a real
model, randomness, or the network.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    MOCK = "mock"
    ECHO = "echo"
    LOCAL = "local"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class ExtractorMode(str, Enum):
    HEURISTIC = "heuristic"
    MODEL_ASSISTED = "model_assisted"
    HYBRID = "hybrid"


class ConflictMode(str, Enum):
    HEURISTIC = "heuristic"
    MODEL_ASSISTED = "model_assisted"
    HYBRID = "hybrid"


class CompressorMode(str, Enum):
    HEURISTIC = "heuristic"
    MODEL_BASED = "model_based"


class EmbeddingProvider(str, Enum):
    HASH = "hash"
    OPENAI = "openai"


class LLMConfig(BaseModel):
    provider: LLMProvider = LLMProvider.MOCK
    model: Optional[str] = None
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    api_key_env: Optional[str] = None


class ExtractorConfig(BaseModel):
    mode: ExtractorMode = ExtractorMode.HEURISTIC


class ConflictDetectorConfig(BaseModel):
    mode: ConflictMode = ConflictMode.HEURISTIC


class CompressorConfig(BaseModel):
    mode: CompressorMode = CompressorMode.HEURISTIC


class EmbeddingsConfig(BaseModel):
    provider: EmbeddingProvider = EmbeddingProvider.HASH
    model: Optional[str] = None
    dim: int = 64


class RuntimeConfig(BaseModel):
    token_budget: int = 32000
    deterministic_benchmark_mode: bool = True


class AppConfig(BaseModel):
    domain: str = "default"
    # Optional built-in policy pack name. When set, the pack configures the
    # domain profile, conflict patterns, and seed anchors (v0.7).
    policy_pack: Optional[str] = None
    llm: LLMConfig = Field(default_factory=LLMConfig)
    extractor: ExtractorConfig = Field(default_factory=ExtractorConfig)
    conflict_detector: ConflictDetectorConfig = Field(
        default_factory=ConflictDetectorConfig
    )
    compressor: CompressorConfig = Field(default_factory=CompressorConfig)
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
