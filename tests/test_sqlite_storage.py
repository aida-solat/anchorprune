"""SQLite persistence: CRUD, snapshots, audit dedup, and cross-restart durability."""

from anchorprune.storage import SQLiteRunRepository
from anchorprune.storage.models import (
    AuditEventRecord,
    RunRecord,
    StateSnapshotRecord,
    StepMetricsRecord,
)


def _repo(tmp_path):
    return SQLiteRunRepository(str(tmp_path / "store.db"))


def test_run_crud_roundtrip(tmp_path):
    repo = _repo(tmp_path)
    run = RunRecord(id="run_x", goal="g", domain="procurement", status="created", config_name="mock")
    repo.create_run(run)

    fetched = repo.get_run("run_x")
    assert fetched is not None
    assert fetched.goal == "g"
    assert fetched.domain == "procurement"

    fetched.status = "active"
    repo.update_run(fetched)
    assert repo.get_run("run_x").status == "active"

    assert [r.id for r in repo.list_runs()] == ["run_x"]
    assert repo.delete_run("run_x") is True
    assert repo.get_run("run_x") is None


def test_list_runs_filters_by_domain(tmp_path):
    repo = _repo(tmp_path)
    repo.create_run(RunRecord(id="a", goal="g", domain="coding_agent", status="created", config_name="mock"))
    repo.create_run(RunRecord(id="b", goal="g", domain="procurement", status="created", config_name="mock"))
    ids = {r.id for r in repo.list_runs(domain="procurement")}
    assert ids == {"b"}


def test_latest_snapshot_returns_highest_step(tmp_path):
    repo = _repo(tmp_path)
    repo.create_run(RunRecord(id="r", goal="g", domain="default", status="created", config_name="mock"))
    repo.add_snapshot(StateSnapshotRecord(id="s0", run_id="r", step_index=0, state={"graph": {"step_index": 0}}))
    repo.add_snapshot(StateSnapshotRecord(id="s1", run_id="r", step_index=1, state={"graph": {"step_index": 1}}))
    latest = repo.latest_snapshot("r")
    assert latest.step_index == 1


def test_audit_events_dedup_by_id(tmp_path):
    repo = _repo(tmp_path)
    repo.create_run(RunRecord(id="r", goal="g", domain="default", status="created", config_name="mock"))
    event = AuditEventRecord(id="audit_1", run_id="r", event_type="run_created", step_index=0, payload={})
    repo.add_audit_events([event])
    repo.add_audit_events([event])  # idempotent re-persist
    assert len(repo.list_audit_events("r")) == 1


def test_step_metrics_persist_in_order(tmp_path):
    repo = _repo(tmp_path)
    repo.create_run(RunRecord(id="r", goal="g", domain="default", status="created", config_name="mock"))
    repo.add_step_metrics(StepMetricsRecord(id="m1", run_id="r", step_index=0, metrics={"step": 1}))
    repo.add_step_metrics(StepMetricsRecord(id="m2", run_id="r", step_index=1, metrics={"step": 2}))
    steps = [m.metrics["step"] for m in repo.list_step_metrics("r")]
    assert steps == [1, 2]


def test_sqlite_persists_across_reconnect(tmp_path):
    db = str(tmp_path / "persist.db")
    repo = SQLiteRunRepository(db)
    repo.create_run(RunRecord(id="run_keep", goal="g", domain="default", status="created", config_name="mock"))
    repo.add_snapshot(StateSnapshotRecord(id="s", run_id="run_keep", step_index=0, state={"graph": {}}))
    repo.close()

    # Simulate a process restart by opening a fresh connection to the same file.
    repo2 = SQLiteRunRepository(db)
    assert repo2.get_run("run_keep") is not None
    assert repo2.latest_snapshot("run_keep") is not None
