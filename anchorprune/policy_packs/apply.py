"""Apply a policy pack to AnchorPrune runtime components.

This module is the only place that translates a declarative
:class:`DomainPolicyPack` into the concrete objects the runtime consumes: a
:class:`DomainProfile`, a ``contradiction_fn``, and seed anchor specs.

    Policy packs configure governance. They do not perform governance.

Nothing here approves anchors or quarantines payloads. It hands the Anchor
Governor, pruner, and conflict detector their configuration and steps aside.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from anchorprune.conflicts.detector import ContradictionFn
from anchorprune.domains.models import AnchorWeightConfig, DomainProfile
from anchorprune.policy_packs.models import DomainPolicyPack

if TYPE_CHECKING:  # pragma: no cover - typing only, avoids an import cycle
    from anchorprune.core.runtime import AnchorPruneRuntime


def resolve_pack(pack: Union[str, DomainPolicyPack]) -> DomainPolicyPack:
    """Resolve a pack name (built-in) or pass through a pack object."""

    if isinstance(pack, DomainPolicyPack):
        return pack
    from anchorprune.policy_packs.registry import get_policy_pack

    return get_policy_pack(pack)


def pack_to_weight_config(pack: DomainPolicyPack) -> AnchorWeightConfig:
    w = pack.domain_profile.weights
    return AnchorWeightConfig(
        authority=w.authority,
        risk=w.risk,
        evidence=w.evidence,
        relevance=w.relevance,
        freshness=w.freshness,
        conflict=w.conflict,
        volatility=w.volatility,
    )


def pack_to_domain_profile(pack: DomainPolicyPack) -> DomainProfile:
    """Build a runtime DomainProfile from the pack.

    Pack thresholds (preserve/compress/milestone/eviction) map onto the
    runtime's anchor/payload thresholds. Pack-only configuration that the core
    profile has no field for (freshness rules, decision-context and milestone
    expectations) is carried in ``metadata`` for components that consume it.
    """

    dp = pack.domain_profile
    # The pack's preserve/compress/milestone/eviction bands govern *payload*
    # pruning and milestone retention. The anchor-governance thresholds
    # (domain/runtime anchor promotion) are left at the DomainProfile defaults:
    # a pack tunes how payloads are kept/compressed/evicted, not how the governor
    # promotes anchors. ``preserve_threshold`` maps to the domain-anchor
    # threshold (the boundary above which a domain anchor is retained).
    return DomainProfile(
        name=pack.name,
        anchor_weight_config=pack_to_weight_config(pack),
        token_budget=dp.token_budget,
        domain_anchor_threshold=dp.preserve_threshold,
        milestone_threshold=dp.milestone_threshold,
        payload_compression_threshold=dp.compress_threshold,
        payload_eviction_threshold=dp.eviction_threshold,
        metadata={
            "policy_pack": pack.name,
            "policy_pack_version": pack.version,
            "freshness_rules": [r.model_dump() for r in pack.freshness_rules],
            "expected_milestone_patterns": list(pack.expected_milestone_patterns),
            "decision_context_rules": pack.decision_context_rules.model_dump(),
        },
    )


def compile_conflict_patterns(pack: DomainPolicyPack) -> List["re.Pattern"]:
    """Compile the pack's conflict patterns (case-insensitive)."""

    return [re.compile(cp.pattern, re.IGNORECASE) for cp in pack.conflict_patterns]


def pack_to_contradiction_fn(pack: DomainPolicyPack) -> Optional[ContradictionFn]:
    """Compile the pack's conflict patterns into a ``contradiction_fn``.

    The returned function flags a candidate as conflicting when its text matches
    any pack pattern. The Anchor Governor still decides what that means (a match
    against a critical system anchor is quarantined; otherwise it lowers weight).
    """

    compiled = compile_conflict_patterns(pack)
    if not compiled:
        return None

    def contradiction_fn(candidate: str, _anchor: str) -> bool:
        return any(rx.search(candidate) for rx in compiled)

    return contradiction_fn


def _anchor_specs(anchors) -> List[Dict[str, Any]]:
    return [
        {"content": a.content, "anchor_type": a.type, "priority": a.priority}
        for a in anchors
    ]


def pack_system_anchor_specs(pack: DomainPolicyPack) -> List[Dict[str, Any]]:
    return _anchor_specs(pack.system_anchors)


def pack_domain_anchor_specs(pack: DomainPolicyPack) -> List[Dict[str, Any]]:
    return _anchor_specs(pack.domain_anchors)


def seed_pack_anchors(runtime: "AnchorPruneRuntime", pack: DomainPolicyPack) -> None:
    """Seed the pack's pre-approved system and domain anchors into a runtime."""

    for spec in pack_system_anchor_specs(pack):
        runtime.register_system_anchor(spec)
    for spec in pack_domain_anchor_specs(pack):
        runtime.register_domain_anchor(spec)


def build_runtime_from_pack(
    pack: Union[str, DomainPolicyPack],
    *,
    llm=None,
    anchor_extractor=None,
    compressor=None,
    seed_anchors: bool = True,
) -> "AnchorPruneRuntime":
    """Construct a runtime configured by ``pack`` (profile + conflict patterns).

    Pack anchors are seeded immediately so they are present before ``create_run``.
    The runtime keeps a reference to the pack on ``runtime.policy_pack``.
    """

    from anchorprune.anchors.extractors.heuristic import HeuristicAnchorExtractor
    from anchorprune.core.runtime import AnchorPruneRuntime
    from anchorprune.llm.mock import MockLLM

    resolved = resolve_pack(pack)
    # When the caller does not inject an extractor, build the default heuristic
    # extractor but add the pack's conflict patterns as extra extraction
    # triggers, so a payload matching a pattern is surfaced to the governor,
    # which then quarantines it via the pack contradiction_fn. Configuration
    # only: the governor still makes the decision.
    if anchor_extractor is None:
        anchor_extractor = HeuristicAnchorExtractor(
            extra_directive_patterns=compile_conflict_patterns(resolved)
        )
    runtime = AnchorPruneRuntime(
        llm or MockLLM(),
        domain_profile=pack_to_domain_profile(resolved),
        contradiction_fn=pack_to_contradiction_fn(resolved),
        anchor_extractor=anchor_extractor,
        compressor=compressor,
    )
    runtime.policy_pack = resolved
    if seed_anchors:
        seed_pack_anchors(runtime, resolved)
    return runtime
