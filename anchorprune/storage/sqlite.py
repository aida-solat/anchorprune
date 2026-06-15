"""SQLite implementation of the run repository.

Uses the ``sqlite3`` standard library with JSON columns stored as TEXT, keeping
the dependency surface minimal. Audit events are inserted with ``INSERT OR
IGNORE`` keyed on their stable id, so re-persisting a rehydrated runtime never
duplicates events.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import List, Optional

from anchorprune.storage.base import RunRepository
from anchorprune.storage.migrations import apply_schema
from anchorprune.storage.models import (
    AuditEventRecord,
    RunRecord,
    StateSnapshotRecord,
    StepMetricsRecord,
)


class SQLiteRunRepository(RunRepository):
    def __init__(self, database_path: str = ":memory:") -> None:
        self.database_path = database_path
        if database_path not in (":memory:", ""):
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False so the repository can be shared by FastAPI's
        # threadpool workers; a lock serializes access for safety.
        self._conn = sqlite3.connect(database_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._lock = threading.Lock()
        apply_schema(self._conn)

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # ---- runs -------------------------------------------------------------

    def create_run(self, run: RunRecord) -> RunRecord:
        with self._lock:
            self._conn.execute(
                "INSERT INTO runs (id, goal, domain, status, config_name, "
                "metadata_json, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run.id,
                    run.goal,
                    run.domain,
                    run.status,
                    run.config_name,
                    json.dumps(run.metadata),
                    run.created_at,
                    run.updated_at,
                ),
            )
            self._conn.commit()
        return run

    def get_run(self, run_id: str) -> Optional[RunRecord]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM runs WHERE id = ?", (run_id,)
            ).fetchone()
        return self._row_to_run(row) if row else None

    def update_run(self, run: RunRecord) -> RunRecord:
        with self._lock:
            self._conn.execute(
                "UPDATE runs SET goal = ?, domain = ?, status = ?, config_name = ?, "
                "metadata_json = ?, updated_at = ? WHERE id = ?",
                (
                    run.goal,
                    run.domain,
                    run.status,
                    run.config_name,
                    json.dumps(run.metadata),
                    run.updated_at,
                    run.id,
                ),
            )
            self._conn.commit()
        return run

    def list_runs(
        self, *, limit: int = 50, offset: int = 0, domain: Optional[str] = None
    ) -> List[RunRecord]:
        query = "SELECT * FROM runs"
        params: list = []
        if domain:
            query += " WHERE domain = ?"
            params.append(domain)
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, max(0, offset)])
        with self._lock:
            rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_run(row) for row in rows]

    def count_runs(self, *, domain: Optional[str] = None) -> int:
        query = "SELECT COUNT(*) FROM runs"
        params: list = []
        if domain:
            query += " WHERE domain = ?"
            params.append(domain)
        with self._lock:
            row = self._conn.execute(query, params).fetchone()
        return int(row[0]) if row else 0

    def delete_run(self, run_id: str) -> bool:
        with self._lock:
            cur = self._conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
            self._conn.commit()
            return cur.rowcount > 0

    # ---- state snapshots --------------------------------------------------

    def add_snapshot(self, snapshot: StateSnapshotRecord) -> StateSnapshotRecord:
        with self._lock:
            self._conn.execute(
                "INSERT INTO state_snapshots (id, run_id, step_index, state_json, "
                "created_at) VALUES (?, ?, ?, ?, ?)",
                (
                    snapshot.id,
                    snapshot.run_id,
                    snapshot.step_index,
                    json.dumps(snapshot.state),
                    snapshot.created_at,
                ),
            )
            self._conn.commit()
        return snapshot

    def latest_snapshot(self, run_id: str) -> Optional[StateSnapshotRecord]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM state_snapshots WHERE run_id = ? "
                "ORDER BY step_index DESC, created_at DESC LIMIT 1",
                (run_id,),
            ).fetchone()
        if not row:
            return None
        return StateSnapshotRecord(
            id=row["id"],
            run_id=row["run_id"],
            step_index=row["step_index"],
            state=json.loads(row["state_json"]),
            created_at=row["created_at"],
        )

    # ---- audit events -----------------------------------------------------

    def add_audit_events(self, events: List[AuditEventRecord]) -> None:
        if not events:
            return
        with self._lock:
            self._conn.executemany(
                "INSERT OR IGNORE INTO audit_events (id, run_id, event_type, "
                "step_index, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (
                        e.id,
                        e.run_id,
                        e.event_type,
                        e.step_index,
                        json.dumps(e.payload),
                        e.created_at,
                    )
                    for e in events
                ],
            )
            self._conn.commit()

    def list_audit_events(
        self, run_id: str, *, limit: Optional[int] = None, offset: int = 0
    ) -> List[AuditEventRecord]:
        query = (
            "SELECT * FROM audit_events WHERE run_id = ? "
            "ORDER BY created_at ASC, rowid ASC"
        )
        params: list = [run_id]
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, max(0, offset)])
        with self._lock:
            rows = self._conn.execute(query, params).fetchall()
        return [
            AuditEventRecord(
                id=row["id"],
                run_id=row["run_id"],
                event_type=row["event_type"],
                step_index=row["step_index"],
                payload=json.loads(row["payload_json"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def count_audit_events(self, run_id: str) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM audit_events WHERE run_id = ?", (run_id,)
            ).fetchone()
        return int(row[0]) if row else 0

    # ---- step metrics -----------------------------------------------------

    def add_step_metrics(self, metrics: StepMetricsRecord) -> StepMetricsRecord:
        with self._lock:
            self._conn.execute(
                "INSERT INTO step_metrics (id, run_id, step_index, metrics_json, "
                "created_at) VALUES (?, ?, ?, ?, ?)",
                (
                    metrics.id,
                    metrics.run_id,
                    metrics.step_index,
                    json.dumps(metrics.metrics),
                    metrics.created_at,
                ),
            )
            self._conn.commit()
        return metrics

    def list_step_metrics(
        self, run_id: str, *, limit: Optional[int] = None, offset: int = 0
    ) -> List[StepMetricsRecord]:
        query = "SELECT * FROM step_metrics WHERE run_id = ? ORDER BY step_index ASC"
        params: list = [run_id]
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, max(0, offset)])
        with self._lock:
            rows = self._conn.execute(query, params).fetchall()
        return [
            StepMetricsRecord(
                id=row["id"],
                run_id=row["run_id"],
                step_index=row["step_index"],
                metrics=json.loads(row["metrics_json"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def count_step_metrics(self, run_id: str) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM step_metrics WHERE run_id = ?", (run_id,)
            ).fetchone()
        return int(row[0]) if row else 0

    # ---- helpers ----------------------------------------------------------

    @staticmethod
    def _row_to_run(row: sqlite3.Row) -> RunRecord:
        return RunRecord(
            id=row["id"],
            goal=row["goal"],
            domain=row["domain"],
            status=row["status"],
            config_name=row["config_name"],
            metadata=json.loads(row["metadata_json"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
