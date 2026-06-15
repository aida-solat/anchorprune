"""Policy pack validator.

Semantic checks beyond schema coercion. A pack may parse cleanly yet still be
invalid (duplicate anchor ids, dangling conflict references, un-ordered
thresholds, uncompilable regex). The validator never mutates a pack.

    Policy packs configure governance. They do not perform governance.

Validation guarantees a pack is internally consistent before it is allowed to
configure a runtime.
"""

from __future__ import annotations

import re
from typing import List

from anchorprune.errors import PolicyPackValidationError
from anchorprune.policy_packs.models import DomainPolicyPack

_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_SEMVER_RE = re.compile(r"^\d+\.\d+(\.\d+)?$")


class PackValidationError(PolicyPackValidationError):
    """Raised when a policy pack fails semantic validation."""


def validate_pack(pack: DomainPolicyPack) -> List[str]:
    """Return a list of human-readable validation errors (empty == valid)."""

    errors: List[str] = []

    if not _NAME_RE.match(pack.name):
        errors.append(
            f"pack name '{pack.name}' must be snake_case (lowercase, digits, underscores)."
        )
    if not _SEMVER_RE.match(pack.version):
        errors.append(f"pack version '{pack.version}' must be semantic (e.g. '0.1' or '1.2.3').")

    anchors = pack.all_anchors
    ids = [a.id for a in anchors]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        errors.append(f"duplicate anchor ids: {', '.join(duplicates)}.")

    known_ids = set(ids)
    for cp in pack.conflict_patterns:
        for ref in cp.conflicts_with:
            if ref not in known_ids:
                errors.append(
                    f"conflict pattern '{cp.id}' references unknown anchor id '{ref}'."
                )
        try:
            re.compile(cp.pattern)
        except re.error as exc:
            errors.append(f"conflict pattern '{cp.id}' has invalid regex: {exc}.")

    cp_ids = [cp.id for cp in pack.conflict_patterns]
    cp_dupes = sorted({i for i in cp_ids if cp_ids.count(i) > 1})
    if cp_dupes:
        errors.append(f"duplicate conflict pattern ids: {', '.join(cp_dupes)}.")

    weights = pack.domain_profile.weights
    for field_name, value in weights.model_dump().items():
        if value < 0:
            errors.append(f"weight '{field_name}' must be non-negative (got {value}).")

    dp = pack.domain_profile
    ordered = [
        ("preserve", dp.preserve_threshold),
        ("compress", dp.compress_threshold),
        ("milestone", dp.milestone_threshold),
        ("eviction", dp.eviction_threshold),
    ]
    for (hi_name, hi), (lo_name, lo) in zip(ordered, ordered[1:]):
        if hi < lo:
            errors.append(
                f"thresholds must be ordered preserve >= compress >= milestone "
                f">= eviction; '{hi_name}' ({hi}) < '{lo_name}' ({lo})."
            )
    for name, value in ordered:
        if not 0.0 <= value <= 1.0:
            errors.append(f"threshold '{name}' must be in [0, 1] (got {value}).")

    if dp.token_budget <= 0:
        errors.append(f"token_budget must be positive (got {dp.token_budget}).")

    has_critical = any(a.priority == "critical" for a in pack.system_anchors)
    if not has_critical:
        errors.append("pack must define at least one critical system anchor.")

    if not (
        pack.decision_context_rules.must_include
        or pack.decision_context_rules.must_not_include
    ):
        errors.append(
            "decision_context_rules must define at least one must_include or "
            "must_not_include term so the pack is benchmark-usable."
        )

    return errors


def validate_pack_or_raise(pack: DomainPolicyPack) -> DomainPolicyPack:
    """Validate ``pack`` and raise :class:`PackValidationError` on any error."""

    errors = validate_pack(pack)
    if errors:
        raise PackValidationError(
            f"policy pack '{pack.name}' is invalid:\n  - " + "\n  - ".join(errors)
        )
    return pack
