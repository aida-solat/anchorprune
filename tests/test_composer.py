from anchorprune.anchors.models import Anchor, AnchorClass, AnchorPriority
from anchorprune.blocks.models import PayloadBlock, PayloadBlockType
from anchorprune.core.context_composer import ContextComposer
from anchorprune.core.state_graph import GovernedStateGraph
from anchorprune.domains.models import DomainProfile


def _graph():
    graph = GovernedStateGraph(goal="Pick the safest supplier")
    graph.add_anchor(
        Anchor(
            content="CRITICAL SYSTEM RULE",
            anchor_class=AnchorClass.SYSTEM,
            priority=AnchorPriority.CRITICAL,
            weight=1.0,
        )
    )
    graph.add_anchor(
        Anchor(content="domain rule", anchor_class=AnchorClass.DOMAIN, weight=0.8)
    )
    return graph


def test_section_order_and_content():
    graph = _graph()
    composed = ContextComposer().compose(
        graph, DomainProfile(), "Do the step", output_schema="{}"
    )
    assert "system_anchors" in composed.sections
    assert composed.sections.index("system_anchors") < composed.sections.index(
        "domain_anchors"
    )
    assert composed.sections[-1] == "output_schema"
    assert "CRITICAL SYSTEM RULE" in composed.prompt


def test_payload_dropped_under_tight_budget_but_anchors_kept():
    graph = _graph()
    for i in range(20):
        graph.add_payload_block(
            PayloadBlock(
                block_type=PayloadBlockType.TOOL_OUTPUT,
                content=f"payload block number {i} " * 20,
                utility_score=0.1,
            )
        )
    tiny_budget = DomainProfile(token_budget=120)
    composed = ContextComposer().compose(graph, tiny_budget, "step")
    # Critical anchor survives even when payload is dropped.
    assert "CRITICAL SYSTEM RULE" in composed.prompt
    assert len(composed.dropped_block_ids) > 0


def test_higher_utility_blocks_included_first():
    graph = GovernedStateGraph(goal="g")
    low = PayloadBlock(
        block_type=PayloadBlockType.TOOL_OUTPUT, content="low " * 30, utility_score=0.1
    )
    high = PayloadBlock(
        block_type=PayloadBlockType.TOOL_OUTPUT, content="high " * 30, utility_score=0.9
    )
    graph.add_payload_block(low)
    graph.add_payload_block(high)
    composed = ContextComposer().compose(graph, DomainProfile(token_budget=120), "step")
    assert high.id in composed.included_block_ids
