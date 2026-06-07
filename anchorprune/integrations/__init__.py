"""Framework integrations (v0.6).

Thin adapters that let AnchorPrune sit as a governance layer inside existing
agent ecosystems — LangGraph, LlamaIndex, and any custom tool loop — without
AnchorPrune becoming an agent framework itself.

    AnchorPrune is not the agent. It is the governor around the agent's memory.

All adapters are built on :class:`anchorprune.AnchorPruneMiddleware` and depend
only on the AnchorPrune core: importing these modules never requires LangGraph,
LlamaIndex, or any third-party framework to be installed.
"""

from anchorprune.integrations.langgraph import AnchorPruneNode
from anchorprune.integrations.llamaindex import AnchorPruneMemory

__all__ = ["AnchorPruneNode", "AnchorPruneMemory"]
