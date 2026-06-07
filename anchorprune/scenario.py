"""Scenario loading and execution.

A scenario is a JSON document describing a run: goal, domain, system anchors,
evidence, payload blocks, and a list of step instructions. This module wires a
scenario into an ``AnchorPruneRuntime`` so the CLI and benchmark harness share
one code path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from anchorprune.blocks.models import PayloadBlockType
from anchorprune.core.runtime import AnchorPruneRuntime, StepResult
from anchorprune.domains.profiles import get_domain_profile
from anchorprune.evidence.models import EvidenceRef, EvidenceSourceType
from anchorprune.llm.base import LLMClient
from anchorprune.llm.mock import MockLLM


def load_scenario(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_runtime(
    scenario: Dict[str, Any], llm: Optional[LLMClient] = None
) -> AnchorPruneRuntime:
    domain = scenario.get("domain", "default")
    profile = get_domain_profile(domain)
    runtime = AnchorPruneRuntime(llm or MockLLM(), domain_profile=profile)
    runtime.create_run(
        goal=scenario.get("goal", ""),
        system_anchors=scenario.get("system_anchors", []),
    )

    # Evidence first, so payload/anchors can link to it.
    label_to_id: Dict[str, str] = {}
    for ev in scenario.get("evidence", []):
        ref = EvidenceRef(
            source_type=EvidenceSourceType(ev.get("source_type", "document")),
            locator=ev["locator"],
            snippet=ev.get("snippet"),
            reliability=ev.get("reliability"),
            freshness_days=ev.get("freshness_days"),
        )
        runtime.add_evidence(ref)
        if "label" in ev:
            label_to_id[ev["label"]] = ref.id

    for item in scenario.get("payload", []):
        ev_refs = [label_to_id.get(lbl, lbl) for lbl in item.get("evidence_refs", [])]
        metadata = dict(item.get("metadata", {}))
        if item.get("adversarial"):
            metadata["adversarial"] = True
        if item.get("noise"):
            metadata["noise"] = True
        runtime.add_payload(
            item["content"],
            PayloadBlockType(item.get("block_type", "tool_output")),
            evidence_refs=ev_refs or None,
            decision_impact=item.get("decision_impact", 0.0),
            metadata=metadata or None,
        )

    return runtime


def run_scenario(
    scenario: Dict[str, Any], llm: Optional[LLMClient] = None
) -> tuple[AnchorPruneRuntime, List[StepResult]]:
    runtime = build_runtime(scenario, llm)
    output_schema = scenario.get("output_schema")
    steps = scenario.get("steps") or ["Complete the task using the governed context."]
    results = [runtime.run_step(instruction, output_schema) for instruction in steps]
    return runtime, results
