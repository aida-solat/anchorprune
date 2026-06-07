"""Runtime construction and rehydration.

This service is the *only* place that knows how to turn a config + a stored
state snapshot back into a live :class:`AnchorPruneRuntime`. It builds runtimes
through the existing :mod:`anchorprune.config.factory`, so the governed method is
never redefined here — the service merely wires and restores state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from anchorprune.anchors.registry import HybridAnchorRegistry
from anchorprune.config import build_runtime, load_config
from anchorprune.config.models import AppConfig
from anchorprune.core.runtime import AnchorPruneRuntime
from anchorprune.storage.serialization import graph_from_dict

# Directory of shipped example configs (resolved relative to the repo root).
_CONFIGS_DIR = Path("configs")


def resolve_config(config_name: Optional[str], *, domain: Optional[str] = None) -> AppConfig:
    """Resolve a config by name, file path, or fall back to the deterministic
    mock pipeline. The resolved config's domain is overridden when provided."""

    config: Optional[AppConfig] = None
    if config_name:
        candidate = Path(config_name)
        search = [candidate] if candidate.suffix else []
        search += [_CONFIGS_DIR / f"{config_name}.yaml", _CONFIGS_DIR / f"{config_name}.yml"]
        for path in search:
            if path.exists():
                config = load_config(path)
                break
    if config is None:
        # Deterministic mock pipeline by default (no network, no randomness).
        config = AppConfig()
    if domain:
        config = config.model_copy(deep=True)
        config.domain = domain
    return config


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
