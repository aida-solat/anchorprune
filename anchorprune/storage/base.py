"""Repository interface.

The service layer talks to storage exclusively through this interface, so an
alternative backend could be dropped in without touching services or routes. The
repository persists records only; it contains no governance or pruning logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from anchorprune.storage.models import (
    AuditEventRecord,
    RunRecord,
    StateSnapshotRecord,
    StepMetricsRecord,
)


class RunRepository(ABC):
    # ---- runs -------------------------------------------------------------

    @abstractmethod
    def create_run(self, run: RunRecord) -> RunRecord: ...

    @abstractmethod
    def get_run(self, run_id: str) -> Optional[RunRecord]: ...

    @abstractmethod
    def update_run(self, run: RunRecord) -> RunRecord: ...

    @abstractmethod
    def list_runs(
        self, *, limit: int = 50, domain: Optional[str] = None
    ) -> List[RunRecord]: ...

    @abstractmethod
    def delete_run(self, run_id: str) -> bool: ...

    # ---- state snapshots --------------------------------------------------

    @abstractmethod
    def add_snapshot(self, snapshot: StateSnapshotRecord) -> StateSnapshotRecord: ...

    @abstractmethod
    def latest_snapshot(self, run_id: str) -> Optional[StateSnapshotRecord]: ...

    # ---- audit events -----------------------------------------------------

    @abstractmethod
    def add_audit_events(self, events: List[AuditEventRecord]) -> None: ...

    @abstractmethod
    def list_audit_events(self, run_id: str) -> List[AuditEventRecord]: ...

    # ---- step metrics -----------------------------------------------------

    @abstractmethod
    def add_step_metrics(self, metrics: StepMetricsRecord) -> StepMetricsRecord: ...

    @abstractmethod
    def list_step_metrics(self, run_id: str) -> List[StepMetricsRecord]: ...
