"""SQLite migrations (v0.9)."""

import sqlite3

from anchorprune.storage.migrations import (
    MIGRATIONS,
    applied_versions,
    migration_status,
    run_migrations,
)


def _conn() -> sqlite3.Connection:
    return sqlite3.connect(":memory:")


def test_sqlite_migrations_apply_once():
    conn = _conn()
    first = run_migrations(conn)
    assert first == [m.version for m in MIGRATIONS]
    # Re-running applies nothing.
    second = run_migrations(conn)
    assert second == []
    # Each version recorded exactly once.
    versions = applied_versions(conn)
    assert versions == sorted(set(versions))
    assert versions == [m.version for m in MIGRATIONS]


def test_sqlite_migrations_records_names_and_timestamps():
    conn = _conn()
    run_migrations(conn)
    rows = conn.execute(
        "SELECT version, name, applied_at FROM schema_migrations ORDER BY version"
    ).fetchall()
    assert [r[1] for r in rows] == ["initial", "add_indexes", "add_version_metadata"]
    assert all(r[2] for r in rows)  # applied_at not empty


def test_sqlite_migrations_add_indexes():
    conn = _conn()
    run_migrations(conn)
    names = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index'"
        ).fetchall()
    }
    for expected in (
        "idx_runs_created_at",
        "idx_runs_domain",
        "idx_state_snapshots_run_step",
        "idx_audit_events_run_created",
        "idx_step_metrics_run_step",
    ):
        assert expected in names


def test_migration_status_reports_current_and_pending():
    conn = _conn()
    status_before = migration_status(conn)
    assert status_before["current_version"] == 0
    assert len(status_before["pending"]) == len(MIGRATIONS)
    run_migrations(conn)
    status_after = migration_status(conn)
    assert status_after["current_version"] == MIGRATIONS[-1].version
    assert status_after["pending"] == []


def test_apply_schema_is_migration_runner():
    from anchorprune.storage.migrations import apply_schema

    conn = _conn()
    apply_schema(conn)
    assert migration_status(conn)["current_version"] == MIGRATIONS[-1].version
    # db_metadata records the app version (migration 003).
    row = conn.execute(
        "SELECT value FROM db_metadata WHERE key = 'anchorprune_version'"
    ).fetchone()
    assert row is not None and row[0]
