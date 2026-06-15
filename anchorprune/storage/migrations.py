"""SQLite schema and a tiny, dependency-free migration runner (v0.9).

The governed state is stored as a JSON snapshot per step rather than normalized
into anchor/payload/milestone tables. v0.9 adds an explicit, ordered migration
system (no Alembic) so schema changes are tracked in a ``schema_migrations``
table and applied exactly once.

    Migrations are additive and idempotent. Re-running ``apply_schema`` /
    ``run_migrations`` on an up-to-date database is a no-op.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List

_MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL
);
"""

# 001 — base tables (CREATE IF NOT EXISTS so it adopts pre-v0.9 databases).
_M001_INITIAL = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    goal TEXT NOT NULL,
    domain TEXT NOT NULL,
    status TEXT NOT NULL,
    config_name TEXT,
    metadata_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS state_snapshots (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    step_index INTEGER NOT NULL,
    state_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    step_index INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS step_metrics (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    step_index INTEGER NOT NULL,
    metrics_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
);
"""

# 002 — query indexes for the dashboard / pagination read paths.
_M002_ADD_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs(created_at);
CREATE INDEX IF NOT EXISTS idx_runs_domain ON runs(domain);
CREATE INDEX IF NOT EXISTS idx_state_snapshots_run_step
    ON state_snapshots(run_id, step_index);
CREATE INDEX IF NOT EXISTS idx_audit_events_run_created
    ON audit_events(run_id, created_at);
CREATE INDEX IF NOT EXISTS idx_step_metrics_run_step
    ON step_metrics(run_id, step_index);
"""

# 003 — a small key/value table for schema/app version metadata.
_M003_ADD_VERSION_METADATA = """
CREATE TABLE IF NOT EXISTS db_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    sql: str


MIGRATIONS: List[Migration] = [
    Migration(1, "initial", _M001_INITIAL),
    Migration(2, "add_indexes", _M002_ADD_INDEXES),
    Migration(3, "add_version_metadata", _M003_ADD_VERSION_METADATA),
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_migrations_table(conn: sqlite3.Connection) -> None:
    conn.executescript(_MIGRATIONS_TABLE)


def applied_versions(conn: sqlite3.Connection) -> List[int]:
    _ensure_migrations_table(conn)
    rows = conn.execute(
        "SELECT version FROM schema_migrations ORDER BY version ASC"
    ).fetchall()
    return [int(r[0]) for r in rows]


def run_migrations(conn: sqlite3.Connection) -> List[int]:
    """Apply all pending migrations in order. Returns the versions applied now."""

    _ensure_migrations_table(conn)
    done = set(applied_versions(conn))
    newly_applied: List[int] = []
    for migration in MIGRATIONS:
        if migration.version in done:
            continue
        conn.executescript(migration.sql)
        conn.execute(
            "INSERT INTO schema_migrations (version, name, applied_at) "
            "VALUES (?, ?, ?)",
            (migration.version, migration.name, _now_iso()),
        )
        newly_applied.append(migration.version)
    # Record the app version that last migrated the DB (best-effort).
    if 3 in done or 3 in newly_applied:
        try:
            from anchorprune import __version__

            conn.execute(
                "INSERT INTO db_metadata (key, value) VALUES ('anchorprune_version', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (__version__,),
            )
        except Exception:  # pragma: no cover - metadata is best-effort
            pass
    conn.commit()
    return newly_applied


def migration_status(conn: sqlite3.Connection) -> Dict[str, object]:
    """Return current schema version, applied migrations, and pending ones."""

    _ensure_migrations_table(conn)
    rows = conn.execute(
        "SELECT version, name, applied_at FROM schema_migrations ORDER BY version ASC"
    ).fetchall()
    applied = [
        {"version": int(r[0]), "name": r[1], "applied_at": r[2]} for r in rows
    ]
    done = {a["version"] for a in applied}
    pending = [
        {"version": m.version, "name": m.name}
        for m in MIGRATIONS
        if m.version not in done
    ]
    current = max((a["version"] for a in applied), default=0)
    return {
        "current_version": current,
        "latest_version": MIGRATIONS[-1].version,
        "applied": applied,
        "pending": pending,
    }


def apply_schema(conn: sqlite3.Connection) -> None:
    """Backward-compatible entry point used by the repository at open time."""

    run_migrations(conn)
