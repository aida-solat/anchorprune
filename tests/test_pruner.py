from anchorprune.anchors.models import Anchor, AnchorClass, AnchorPriority
from anchorprune.blocks.models import PayloadBlock, PayloadBlockType, PruningState
from anchorprune.core.state_graph import GovernedStateGraph
from anchorprune.domains.profiles import get_domain_profile
from anchorprune.pruning.pruner import AnchorAwarePruner, PruningOp
from anchorprune.pruning.utility import score_payload_block


def _graph_with_critical_anchor():
    graph = GovernedStateGraph(goal="g")
    anchor = Anchor(
        content="critical policy",
        anchor_class=AnchorClass.SYSTEM,
        priority=AnchorPriority.CRITICAL,
        weight=1.0,
    )
    graph.add_anchor(anchor)
    return graph, anchor


def test_block_linked_to_critical_system_anchor_is_preserved():
    graph, anchor = _graph_with_critical_anchor()
    block = PayloadBlock(
        block_type=PayloadBlockType.TOOL_OUTPUT,
        content="evidence for the critical policy",
        linked_anchor_ids=[anchor.id],
    )
    graph.add_payload_block(block)

    actions = AnchorAwarePruner().prune(graph, get_domain_profile("procurement"))
    op = {a.block_id: a.op for a in actions}[block.id]
    assert op == PruningOp.PRESERVE
    assert block.pruning_state == PruningState.ACTIVE


def test_low_utility_unlinked_block_is_evicted():
    graph = GovernedStateGraph(goal="g")
    block = PayloadBlock(
        block_type=PayloadBlockType.RETRIEVED_CHUNK,
        content="irrelevant filler text",
        obsolete=True,
        redundancy=0.9,
    )
    graph.add_payload_block(block)

    actions = AnchorAwarePruner().prune(graph, get_domain_profile("default"))
    op = {a.block_id: a.op for a in actions}[block.id]
    assert op == PruningOp.EVICT
    assert block.pruning_state == PruningState.EVICTED


def test_quarantined_block_stays_quarantined():
    graph = GovernedStateGraph(goal="g")
    block = PayloadBlock(
        block_type=PayloadBlockType.MODEL_OUTPUT,
        content="unsafe override attempt",
        quarantined=True,
        pruning_state=PruningState.QUARANTINED,
    )
    graph.add_payload_block(block)

    actions = AnchorAwarePruner().prune(graph, get_domain_profile("default"))
    op = {a.block_id: a.op for a in actions}[block.id]
    assert op == PruningOp.QUARANTINE


def test_compression_creates_milestone():
    graph = GovernedStateGraph(goal="g")
    anchor = Anchor(
        content="runtime fact", anchor_class=AnchorClass.RUNTIME, weight=0.66
    )
    graph.add_anchor(anchor)
    block = PayloadBlock(
        block_type=PayloadBlockType.TOOL_OUTPUT,
        content=(
            "First sentence with detail. Second sentence requires approval. "
            "Third sentence is filler. Fourth sentence is also filler."
        ),
        linked_anchor_ids=[anchor.id],
        redundancy=0.6,
    )
    graph.add_payload_block(block)

    actions = AnchorAwarePruner().prune(graph, get_domain_profile("default"))
    op = {a.block_id: a.op for a in actions}[block.id]
    assert op == PruningOp.COMPRESS
    assert block.compressed
    assert len(graph.milestones) == 1


def test_utility_score_in_range():
    graph, anchor = _graph_with_critical_anchor()
    block = PayloadBlock(
        block_type=PayloadBlockType.TOOL_OUTPUT,
        content="x",
        linked_anchor_ids=[anchor.id],
        decision_impact=0.8,
    )
    graph.add_payload_block(block)
    score = score_payload_block(block, graph, graph.step_index)
    assert 0.0 <= score <= 1.0
