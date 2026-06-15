"""Built-in policy pack registry.

Discovers the YAML packs shipped under ``builtins/`` and exposes them by name.
Packs are loaded lazily and cached. Built-in packs are validated on load, so a
malformed shipped pack fails loudly rather than silently misconfiguring a run.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Union

from anchorprune.policy_packs.loader import load_pack
from anchorprune.policy_packs.models import DomainPolicyPack
from anchorprune.policy_packs.validator import validate_pack_or_raise

_BUILTIN_DIR = Path(__file__).resolve().parent / "builtins"
_CACHE: Dict[str, DomainPolicyPack] = {}


class PolicyPackNotFound(KeyError):
    """Raised when a named policy pack does not exist."""


def builtin_pack_paths() -> Dict[str, Path]:
    """Map of built-in pack name -> YAML path (by file stem)."""

    return {p.stem: p for p in sorted(_BUILTIN_DIR.glob("*.yaml"))}


def list_policy_packs() -> List[str]:
    """Sorted names of all built-in policy packs."""

    return sorted(builtin_pack_paths())


def has_policy_pack(name: str) -> bool:
    return name in builtin_pack_paths()


def get_policy_pack(name: str) -> DomainPolicyPack:
    """Load (and cache) a built-in policy pack by name."""

    if name in _CACHE:
        return _CACHE[name]
    paths = builtin_pack_paths()
    if name not in paths:
        available = ", ".join(sorted(paths)) or "(none)"
        raise PolicyPackNotFound(
            f"no built-in policy pack named '{name}'. Available: {available}"
        )
    pack = validate_pack_or_raise(load_pack(paths[name]))
    _CACHE[name] = pack
    return pack


def load_policy_pack(path: Union[str, Path]) -> DomainPolicyPack:
    """Load and validate a policy pack from an arbitrary file path."""

    return validate_pack_or_raise(load_pack(path))
