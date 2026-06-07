"""GovernedStateGraph round-trip: graph -> JSON -> SQLite -> JSON -> graph.

If state is corrupted on persistence, the whole service is worthless, so this
verifies anchors, payload blocks, milestones, and conflict edges all survive.
"""

from anchorprune.blocks.models import PayloadBlockType
from anchorprune.core.runtime import AnchorPruneRuntime
from anchorprune.domains.profiles import get_domain_profile
from anchorprune.llm.mock import MockLLM
from anchorprune.storage import SQLiteRunRepository, graph_from_dict, serialize_runtime
from anchorprune.storage.models import StateSnapshotRecord
from anchorprune.storage.serialization import graph_to_dict


def _seed_runtime() -> AnchorPruneRuntime:
    rt = AnchorPruneRuntime(MockLLM(), get_domain_profile("procurement"))
    rt.create_run(
        goal="Recommend the safest supplier.",
        system_anchors=[
            {
                "content": "A supplier cannot be recommended without verified compliance documentation.",
                "anchor_type": "policy",
                "priority": "critical",
            }
        ],
    )
    rt.add_payload(
        "Supplier A is missing ISO9001 compliance documentation.",
        PayloadBlockType.TOOL_OUTPUT,
        decision_impact=0.8,
    )
    rt.run_step("Recommend the safest supplier and state if action is allowed.")
    return rt


def test_state_graph_roundtrip_preserves_anchors_and_milestones():
    rt = _seed_runtime()
    original = rt.graph

    restored = graph_from_dict(graph_to_dict(original))

    assert restored.run_id == original.run_id
    assert restored.goal == original.goal
    assert restored.domain == original.domain
    assert set(restored.anchors) == set(original.anchors)
    assert set(restored.payload_blocks) == set(original.payload_blocks)
    assert set(restored.milestones) == set(original.milestones)
    assert len(restored.conflict_edges) == len(original.conflict_edges)
    assert restored.summary() == original.summary()


def test_state_snapshot_roundtrip_through_sqlite(tmp_path):
    rt = _seed_runtime()
    repo = SQLiteRunRepository(str(tmp_path / "rt.db"))
    from anchorprune.storage.models import RunRecord

    repo.create_run(
        RunRecord(
            id=rt.graph.run_id,
            goal=rt.graph.goal,
            domain=rt.domain_profile.name,
            status="active",
            config_name="mock",
        )
    )
    repo.add_snapshot(
        StateSnapshotRecord(
            id="snap_1",
            run_id=rt.graph.run_id,
            step_index=rt.graph.step_index,
            state=serialize_runtime(rt),
        )
    )

    snapshot = repo.latest_snapshot(rt.graph.run_id)
    restored = graph_from_dict(snapshot.state["graph"])

    assert restored.summary() == rt.graph.summary()
    assert snapshot.state["metrics"]["steps"] == rt.metrics["steps"]
    # System anchor content must survive the round-trip exactly.
    contents = {a.content for a in restored.system_anchors()}
    assert "A supplier cannot be recommended without verified compliance documentation." in contents
