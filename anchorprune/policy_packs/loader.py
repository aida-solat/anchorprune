"""Policy pack loader.

Parses a YAML or JSON file into a :class:`DomainPolicyPack`. Loading is pure
parsing + schema coercion; semantic checks live in
:mod:`anchorprune.policy_packs.validator`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Union

import yaml

from anchorprune.policy_packs.models import DomainPolicyPack


class PackLoadError(ValueError):
    """Raised when a pack file cannot be read or parsed into the schema."""


def load_pack_dict(path: Union[str, Path]) -> Dict[str, Any]:
    """Read a pack file (YAML or JSON) into a plain dict."""

    p = Path(path)
    if not p.exists():
        raise PackLoadError(f"Policy pack file not found: {p}")
    text = p.read_text(encoding="utf-8")
    try:
        if p.suffix.lower() == ".json":
            data = json.loads(text)
        else:
            data = yaml.safe_load(text)
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        raise PackLoadError(f"Could not parse policy pack {p}: {exc}") from exc
    if not isinstance(data, dict):
        raise PackLoadError(f"Policy pack {p} must be a mapping at the top level.")
    return data


def load_pack(path: Union[str, Path]) -> DomainPolicyPack:
    """Load and schema-coerce a policy pack from a YAML/JSON file."""

    data = load_pack_dict(path)
    try:
        return DomainPolicyPack.model_validate(data)
    except Exception as exc:  # pydantic ValidationError
        raise PackLoadError(f"Policy pack {path} does not match the schema: {exc}") from exc
