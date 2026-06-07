"""State serialization helpers.

v0.4 persists the governed state as a JSON snapshot rather than normalizing it
into many tables. The :class:`GovernedStateGraph` is a Pydantic model, so the
round-trip is lossless:

    GovernedStateGraph -> dict -> JSON (SQLite TEXT) -> dict -> GovernedStateGraph

The runtime snapshot additionally carries the cumulative metrics dict so a run
can be rehydrated and continued across process restarts with no loss of state.

This module owns *serialization only*. It never makes governance, pruning, or
model decisions — that logic stays in the runtime.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Dict

from anchorprune.core.state_graph import GovernedStateGraph

if TYPE_CHECKING:  # pragma: no cover - typing only
    from anchorprune.core.runtime import AnchorPruneRuntime


def graph_to_dict(graph: GovernedStateGraph) -> Dict[str, Any]:
    """Serialize a governed state graph to a JSON-safe dict."""

    return graph.model_dump(mode="json")


def graph_from_dict(data: Dict[str, Any]) -> GovernedStateGraph:
    """Reconstruct a governed state graph from a serialized dict."""

    return GovernedStateGraph.model_validate(data)


def serialize_runtime(runtime: "AnchorPruneRuntime") -> Dict[str, Any]:
    """Capture the persistable state of a runtime (graph + cumulative metrics)."""

    return {
        "graph": graph_to_dict(runtime.graph),
        "metrics": dict(runtime.metrics),
    }


def runtime_snapshot_json(runtime: "AnchorPruneRuntime") -> str:
    return json.dumps(serialize_runtime(runtime), sort_keys=True)
