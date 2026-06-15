"""Scenario loading and execution.

A scenario is a JSON document describing a run: goal, domain, system anchors,
evidence, payload blocks, and a list of step instructions. This module wires a
scenario into an ``AnchorPruneRuntime`` so the CLI and benchmark harness share
one code path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from anchorprune.anchors.extractors.base import AnchorExtractor
from anchorprune.blocks.models import PayloadBlockType
from anchorprune.core.runtime import AnchorPruneRuntime, StepResult
from anchorprune.domains.profiles import get_domain_profile
from anchorprune.evidence.models import EvidenceRef, EvidenceSourceType
from anchorprune.llm.base import LLMClient
from anchorprune.llm.mock import MockLLM
from anchorprune.pruning.compressors.base import Compressor


def load_scenario(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


# A normalized step is (instruction, [payload_dict, ...]). v0.1 scenarios use
# bare-string steps with all payloads supplied up front; v0.2 long-run scenarios
# use step objects that inject payloads over time.
NormalizedStep = Tuple[str, List[Dict[str, Any]]]


def normalize_steps(scenario: Dict[str, Any]) -> List[NormalizedStep]:
    """Return steps as ``(instruction, payloads)`` pairs, supporting both formats.

    - v0.1: ``steps`` is a list of instruction strings; per-step payloads empty.
    - v0.2: ``steps`` is a list of objects ``{"instruction": str,
      "payloads": [block, ...]}`` so payloads can be injected over time.
    """

    steps = scenario.get("steps")
    if not steps:
        return [("Complete the task using the governed context.", [])]

    normalized: List[NormalizedStep] = []
    for step in steps:
        if isinstance(step, str):
            normalized.append((step, []))
        else:
            instruction = step.get("instruction", "")
            payloads = step.get("payloads", []) or []
            normalized.append((instruction, payloads))
    return normalized


def build_runtime(
    scenario: Dict[str, Any],
    llm: Optional[LLMClient] = None,
    *,
    anchor_extractor: Optional[AnchorExtractor] = None,
    compressor: Optional[Compressor] = None,
) -> AnchorPruneRuntime:
    pack_name = scenario.get("policy_pack")
    if pack_name:
        # A policy pack configures the domain profile, conflict patterns, and
        # seed anchors. The pack's anchors are seeded at build time; scenario
        # system anchors are added on top. Governance is unchanged.
        from anchorprune.policy_packs.apply import build_runtime_from_pack

        runtime = build_runtime_from_pack(
            pack_name,
            llm=llm,
            anchor_extractor=anchor_extractor,
            compressor=compressor,
        )
    else:
        profile = get_domain_profile(scenario.get("domain", "default"))
        runtime = AnchorPruneRuntime(
            llm or MockLLM(),
            domain_profile=profile,
            anchor_extractor=anchor_extractor,
            compressor=compressor,
        )
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

    runtime._label_to_id = label_to_id  # type: ignore[attr-defined]
    for item in scenario.get("payload", []):
        inject_payload(runtime, item, label_to_id)

    return runtime


def inject_payload(
    runtime: AnchorPruneRuntime,
    item: Dict[str, Any],
    label_to_id: Optional[Dict[str, str]] = None,
) -> None:
    """Add a single payload block to the runtime, honoring adversarial/noise/
    obsolete metadata flags and evidence-label references."""

    label_to_id = label_to_id or {}
    ev_refs = [label_to_id.get(lbl, lbl) for lbl in item.get("evidence_refs", [])]
    metadata = dict(item.get("metadata", {}))
    for flag in ("adversarial", "noise", "obsolete"):
        if item.get(flag):
            metadata[flag] = True
    runtime.add_payload(
        item["content"],
        PayloadBlockType(item.get("block_type", "tool_output")),
        evidence_refs=ev_refs or None,
        decision_impact=item.get("decision_impact", 0.0),
        metadata=metadata or None,
    )


def run_scenario(
    scenario: Dict[str, Any],
    llm: Optional[LLMClient] = None,
    *,
    anchor_extractor: Optional[AnchorExtractor] = None,
    compressor: Optional[Compressor] = None,
) -> tuple[AnchorPruneRuntime, List[StepResult]]:
    runtime = build_runtime(
        scenario, llm, anchor_extractor=anchor_extractor, compressor=compressor
    )
    output_schema = scenario.get("output_schema")
    label_to_id = getattr(runtime, "_label_to_id", {})
    results: List[StepResult] = []
    for instruction, payloads in normalize_steps(scenario):
        # Inject this step's payloads before composing the governed context, so
        # long-run scenarios receive new information over time.
        for item in payloads:
            inject_payload(runtime, item, label_to_id)
        results.append(runtime.run_step(instruction, output_schema))
    return runtime, results
