"""Pipeline factory.

Builds runtime components from an :class:`AppConfig`. The constitutional rule of
v0.3 is enforced here:

    Deterministic governance remains the source of truth. Model-based adapters
    may propose, enrich, or compress state, but they never bypass the Anchor
    Governor.

When ``runtime.deterministic_benchmark_mode`` is true, every stage is forced to
its heuristic implementation regardless of other settings, so a config can never
contaminate the deterministic benchmark with a real model, randomness, or the
network.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from anchorprune.anchors.extractors.base import AnchorExtractor
from anchorprune.anchors.extractors.heuristic import HeuristicAnchorExtractor
from anchorprune.anchors.extractors.hybrid import HybridAnchorExtractor
from anchorprune.anchors.extractors.model_based import ModelBasedAnchorExtractor
from anchorprune.config.models import (
    AppConfig,
    CompressorMode,
    ConflictMode,
    EmbeddingProvider,
    ExtractorMode,
    LLMProvider,
)
from anchorprune.conflicts.detectors.base import ConflictDetector
from anchorprune.conflicts.detectors.heuristic import HeuristicConflictDetector
from anchorprune.conflicts.detectors.hybrid import HybridConflictDetector
from anchorprune.conflicts.detectors.model_based import ModelAssistedConflictDetector
from anchorprune.core.runtime import AnchorPruneRuntime
from anchorprune.domains.profiles import get_domain_profile
from anchorprune.embeddings.base import EmbeddingClient
from anchorprune.embeddings.hash_adapter import HashEmbeddingClient
from anchorprune.evidence.linker import EvidenceLinker
from anchorprune.llm.base import LLMClient
from anchorprune.llm.local_adapter import EchoLLM
from anchorprune.llm.mock import MockLLM
from anchorprune.pruning.compressors.base import Compressor
from anchorprune.pruning.compressors.heuristic import HeuristicCompressor
from anchorprune.pruning.compressors.model_based import ModelBasedCompressor


@dataclass
class Pipeline:
    """Constructed runtime components for a given config."""

    config: AppConfig
    llm: LLMClient
    embeddings: EmbeddingClient
    extractor: AnchorExtractor
    conflict_detector: ConflictDetector
    compressor: Compressor


def build_llm(config: AppConfig) -> LLMClient:
    provider = config.llm.provider
    model = config.llm.model
    if provider == LLMProvider.MOCK:
        return MockLLM()
    if provider in (LLMProvider.LOCAL, LLMProvider.ECHO):
        return EchoLLM()
    if provider == LLMProvider.OPENAI:
        from anchorprune.llm.openai_adapter import OpenAILLM

        return OpenAILLM(model or "gpt-4o-mini")
    if provider == LLMProvider.ANTHROPIC:
        from anchorprune.llm.anthropic_adapter import AnthropicLLM

        return AnthropicLLM(model or "claude-3-5-sonnet-latest")
    raise ValueError(f"Unsupported LLM provider: {provider}")


def build_embeddings(config: AppConfig) -> EmbeddingClient:
    if config.embeddings.provider == EmbeddingProvider.HASH:
        return HashEmbeddingClient(dim=config.embeddings.dim)
    from anchorprune.embeddings.openai_adapter import OpenAIEmbeddingClient

    return OpenAIEmbeddingClient(config.embeddings.model or "text-embedding-3-small")


def build_extractor(config: AppConfig, llm: LLMClient) -> AnchorExtractor:
    linker = EvidenceLinker()
    mode = config.extractor.mode
    if mode == ExtractorMode.HEURISTIC:
        return HeuristicAnchorExtractor(linker=linker)
    if mode == ExtractorMode.MODEL_ASSISTED:
        return ModelBasedAnchorExtractor(llm, temperature=config.llm.temperature)
    return HybridAnchorExtractor(llm, linker=linker, temperature=config.llm.temperature)


def build_conflict_detector(config: AppConfig, llm: LLMClient) -> ConflictDetector:
    mode = config.conflict_detector.mode
    if mode == ConflictMode.HEURISTIC:
        return HeuristicConflictDetector()
    if mode == ConflictMode.MODEL_ASSISTED:
        return ModelAssistedConflictDetector(llm, temperature=config.llm.temperature)
    return HybridConflictDetector(llm, temperature=config.llm.temperature)


def build_compressor(config: AppConfig, llm: LLMClient) -> Compressor:
    if config.compressor.mode == CompressorMode.HEURISTIC:
        return HeuristicCompressor()
    return ModelBasedCompressor(llm, temperature=config.llm.temperature)


def build_pipeline(config: AppConfig) -> Pipeline:
    # Hard safety gate: deterministic benchmark mode forces heuristic everywhere.
    if config.runtime.deterministic_benchmark_mode:
        config = config.model_copy(deep=True)
        config.extractor.mode = ExtractorMode.HEURISTIC
        config.conflict_detector.mode = ConflictMode.HEURISTIC
        config.compressor.mode = CompressorMode.HEURISTIC
        config.llm.provider = LLMProvider.MOCK

    llm = build_llm(config)
    return Pipeline(
        config=config,
        llm=llm,
        embeddings=build_embeddings(config),
        extractor=build_extractor(config, llm),
        conflict_detector=build_conflict_detector(config, llm),
        compressor=build_compressor(config, llm),
    )


def build_runtime(
    config: AppConfig, *, pipeline: Optional[Pipeline] = None
) -> AnchorPruneRuntime:
    """Construct a governed runtime wired with config-selected components.

    Note: the Anchor Governor's hard-gate conflict logic remains heuristic and
    authoritative. The model-assisted conflict detector is available on the
    Pipeline as an additive signal layer; it never replaces the governor.
    """

    pipeline = pipeline or build_pipeline(config)
    if config.policy_pack:
        # A policy pack configures the domain profile, conflict patterns, and
        # seed anchors. The config-selected LLM/extractor/compressor are still
        # used; the pack only supplies governance configuration.
        from anchorprune.policy_packs.apply import build_runtime_from_pack

        return build_runtime_from_pack(
            config.policy_pack,
            llm=pipeline.llm,
            anchor_extractor=pipeline.extractor,
            compressor=pipeline.compressor,
        )
    profile = get_domain_profile(config.domain)
    return AnchorPruneRuntime(
        pipeline.llm,
        domain_profile=profile,
        anchor_extractor=pipeline.extractor,
        compressor=pipeline.compressor,
    )
