"""Config system builds the deterministic mock pipeline and enforces safety."""

from pathlib import Path

from anchorprune.anchors.extractors.heuristic import HeuristicAnchorExtractor
from anchorprune.config import build_pipeline, load_config
from anchorprune.config.models import AppConfig
from anchorprune.conflicts.detectors.heuristic import HeuristicConflictDetector
from anchorprune.embeddings.hash_adapter import HashEmbeddingClient
from anchorprune.llm.mock import MockLLM
from anchorprune.pruning.compressors.heuristic import HeuristicCompressor

CONFIG_DIR = Path(__file__).resolve().parent.parent / "configs"


def test_mock_config_builds_full_heuristic_pipeline():
    pipeline = build_pipeline(load_config(CONFIG_DIR / "mock.yaml"))
    assert isinstance(pipeline.llm, MockLLM)
    assert isinstance(pipeline.extractor, HeuristicAnchorExtractor)
    assert isinstance(pipeline.conflict_detector, HeuristicConflictDetector)
    assert isinstance(pipeline.compressor, HeuristicCompressor)
    assert isinstance(pipeline.embeddings, HashEmbeddingClient)


def test_deterministic_benchmark_mode_forces_heuristic_even_if_model_requested():
    # Ask for real-model components but keep the safety switch on.
    cfg = AppConfig.model_validate(
        {
            "llm": {"provider": "openai", "model": "gpt-4o-mini"},
            "extractor": {"mode": "hybrid"},
            "conflict_detector": {"mode": "hybrid"},
            "compressor": {"mode": "model_based"},
            "embeddings": {"provider": "hash"},
            "runtime": {"deterministic_benchmark_mode": True},
        }
    )
    pipeline = build_pipeline(cfg)
    # The factory must override everything back to deterministic/heuristic.
    assert isinstance(pipeline.llm, MockLLM)
    assert isinstance(pipeline.extractor, HeuristicAnchorExtractor)
    assert isinstance(pipeline.compressor, HeuristicCompressor)
    assert isinstance(pipeline.conflict_detector, HeuristicConflictDetector)


def test_example_configs_are_loadable():
    for name in ("openai.example.yaml", "anthropic.example.yaml"):
        cfg = load_config(CONFIG_DIR / name)
        # Example configs intentionally disable deterministic mode.
        assert cfg.runtime.deterministic_benchmark_mode is False
