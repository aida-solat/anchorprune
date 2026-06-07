"""Persistence layer for the AnchorPrune service (v0.4).

SQLite-backed storage of runs, governed-state snapshots, audit events, and
per-step metrics. The layer persists records only — it holds no governance,
pruning, or model logic.
"""

from anchorprune.storage.base import RunRepository
from anchorprune.storage.models import (
    AuditEventRecord,
    RunRecord,
    StateSnapshotRecord,
    StepMetricsRecord,
)
from anchorprune.storage.serialization import (
    graph_from_dict,
    graph_to_dict,
    serialize_runtime,
)
from anchorprune.storage.sqlite import SQLiteRunRepository

__all__ = [
    "RunRepository",
    "SQLiteRunRepository",
    "RunRecord",
    "StateSnapshotRecord",
    "AuditEventRecord",
    "StepMetricsRecord",
    "graph_to_dict",
    "graph_from_dict",
    "serialize_runtime",
]
