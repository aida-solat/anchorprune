"""Runtime construction and rehydration.

This service is the *only* place that knows how to turn a config + a stored
state snapshot back into a live :class:`AnchorPruneRuntime`. It builds runtimes
through the existing :mod:`anchorprune.config.factory`, so the governed method is
never redefined here — the service merely wires and restores state.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from anchorprune.anchors.registry import HybridAnchorRegistry
from anchorprune.config import build_runtime
from anchorprune.config.resolve import resolve_config
from anchorprune.core.runtime import AnchorPruneRuntime
from anchorprune.storage.serialization import graph_from_dict

# Re-exported for backward compatibility; the canonical implementation now lives
# in :mod:`anchorprune.config.resolve` so the integration layer can reuse it
# without importing the persistence/service stack.
__all__ = ["RuntimeService", "resolve_config"]


class RuntimeService:
    """Builds new runtimes and rehydrates existing ones from persisted state."""

    def build_new(
        self, *, domain: str, config_name: Optional[str]
    ) -> AnchorPruneRuntime:
        config = resolve_config(config_name, domain=domain)
        return build_runtime(config)

    def rehydrate(
        self,
        *,
        domain: str,
        config_name: Optional[str],
        snapshot_state: Dict[str, Any],
    ) -> AnchorPruneRuntime:
        """Reconstruct a runtime and restore its governed state.

        The graph, cumulative metrics, and anchor registry are restored so the
        run can be stepped further exactly as if it had never left memory. Audit
        events are not reloaded into the runtime: they already live in storage
        and are re-persisted idempotently (dedup by id).
        """

        config = resolve_config(config_name, domain=domain)
        runtime = build_runtime(config)
        runtime.graph = graph_from_dict(snapshot_state["graph"])
        if "metrics" in snapshot_state:
            runtime.metrics = dict(snapshot_state["metrics"])
        runtime.registry = HybridAnchorRegistry.from_anchors(
            list(runtime.graph.anchors.values())
        )
        return runtime
