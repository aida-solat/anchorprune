"""Adapter layer namespace (v0.3).

AnchorPrune's adapters are organized by concern under dedicated packages:

- ``anchorprune.llm`` — LLM provider adapters (mock, local, openai, anthropic)
- ``anchorprune.embeddings`` — embedding adapters (hash, openai)
- ``anchorprune.anchors.extractors`` — anchor extractors (heuristic/model/hybrid)
- ``anchorprune.conflicts.detectors`` — conflict detectors (heuristic/model/hybrid)
- ``anchorprune.pruning.compressors`` — compressors (heuristic/model)

This package is intentionally light; it exists as a stable namespace marker and
documentation anchor for the adapter layer.
"""
