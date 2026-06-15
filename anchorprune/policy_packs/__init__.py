"""Domain policy packs (v0.7).

Reusable, local, static governance configuration for common high-stakes agent
workflows (procurement, coding agents, contract review, compliance, security
review).

    Policy packs configure governance. They do not perform governance.

Public API:

    from anchorprune.policy_packs import get_policy_pack, list_policy_packs

    pack = get_policy_pack("contract_review")
"""

from __future__ import annotations

from anchorprune.policy_packs.apply import (
    build_runtime_from_pack,
    pack_to_contradiction_fn,
    pack_to_domain_profile,
    resolve_pack,
    seed_pack_anchors,
)
from anchorprune.policy_packs.loader import PackLoadError, load_pack
from anchorprune.policy_packs.models import (
    ConflictPattern,
    DecisionContextRules,
    DomainPolicyPack,
    FreshnessRule,
    PackAnchor,
    PackDomainProfile,
    PackWeightConfig,
)
from anchorprune.policy_packs.registry import (
    PolicyPackNotFound,
    get_policy_pack,
    has_policy_pack,
    list_policy_packs,
    load_policy_pack,
)
from anchorprune.policy_packs.validator import (
    PackValidationError,
    validate_pack,
    validate_pack_or_raise,
)


def validate_policy_pack(pack_or_name):
    """Validate a policy pack and return it (stable v1.0 public API).

    Accepts a :class:`DomainPolicyPack`, a built-in pack name, or a path to a
    pack file. Raises :class:`PackValidationError` on any semantic error.
    """

    from pathlib import Path

    if isinstance(pack_or_name, DomainPolicyPack):
        return validate_pack_or_raise(pack_or_name)
    if isinstance(pack_or_name, (str, Path)):
        text = str(pack_or_name)
        if not isinstance(pack_or_name, Path) and has_policy_pack(text):
            return get_policy_pack(text)
        return load_policy_pack(pack_or_name)
    raise TypeError(
        "validate_policy_pack expects a DomainPolicyPack, a built-in pack name, "
        f"or a path; got {type(pack_or_name).__name__}."
    )


__all__ = [
    "DomainPolicyPack",
    "PackDomainProfile",
    "PackWeightConfig",
    "PackAnchor",
    "FreshnessRule",
    "ConflictPattern",
    "DecisionContextRules",
    "get_policy_pack",
    "list_policy_packs",
    "has_policy_pack",
    "load_policy_pack",
    "load_pack",
    "PackLoadError",
    "PolicyPackNotFound",
    "validate_pack",
    "validate_pack_or_raise",
    "validate_policy_pack",
    "PackValidationError",
    "resolve_pack",
    "pack_to_domain_profile",
    "pack_to_contradiction_fn",
    "seed_pack_anchors",
    "build_runtime_from_pack",
]
