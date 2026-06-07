"""Pluggable compressors (heuristic / model-based)."""

from anchorprune.pruning.compressors.base import Compressor, enforce_linkage
from anchorprune.pruning.compressors.heuristic import HeuristicCompressor
from anchorprune.pruning.compressors.model_based import ModelBasedCompressor

__all__ = [
    "Compressor",
    "enforce_linkage",
    "HeuristicCompressor",
    "ModelBasedCompressor",
]
