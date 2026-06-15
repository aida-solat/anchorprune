"""Config validation hardening (v0.9).

Turns the growing config surface (v0.3 pipeline modes, v0.4 service, v0.7 policy
packs, v0.8 eval) into *friendly, actionable* errors instead of opaque tracebacks
or a silent fallback. Every failure raises :class:`ConfigError` with a clear
message and, where possible, a "Did you mean …?" suggestion.

This module performs **validation only**; it never changes governance behavior.
"""

from __future__ import annotations

import difflib
from typing import Any, Dict, Iterable, Optional

from anchorprune.config.models import AppConfig, LLMProvider
from anchorprune.errors import ConfigError

KNOWN_PROVIDERS = tuple(p.value for p in LLMProvider)
# Providers whose SDKs are optional extras.
_OPTIONAL_PROVIDER_EXTRAS = {"openai": "openai", "anthropic": "anthropic"}


def suggest(name: str, candidates: Iterable[str]) -> Optional[str]:
    """Return the closest candidate to ``name``, or ``None``."""

    matches = difflib.get_close_matches(name, list(candidates), n=1, cutoff=0.5)
    return matches[0] if matches else None


def _with_suggestion(message: str, name: str, candidates: Iterable[str]) -> str:
    candidates = list(candidates)
    guess = suggest(name, candidates)
    if guess:
        return f"{message} Did you mean '{guess}'?"
    if candidates:
        return f"{message} Available: {', '.join(sorted(candidates))}."
    return message


def validate_provider(name: str) -> None:
    if name not in KNOWN_PROVIDERS:
        raise ConfigError(
            _with_suggestion(
                f"Unknown LLM provider '{name}'.", name, KNOWN_PROVIDERS
            ),
            details={"provider": name, "known": list(KNOWN_PROVIDERS)},
        )


def check_provider_dependency(name: str) -> None:
    """Raise a friendly :class:`ConfigError` if an optional provider SDK is absent.

    ``mock``/``echo``/``local`` are always available. ``openai``/``anthropic``
    require their optional extras.
    """

    extra = _OPTIONAL_PROVIDER_EXTRAS.get(name)
    if not extra:
        return
    try:
        __import__(extra)
    except ImportError as exc:
        raise ConfigError(
            f"Provider '{name}' requires the optional '{extra}' dependency. "
            f"Install it with: pip install -e \".[{extra}]\".",
            details={"provider": name, "extra": extra},
        ) from exc


def validate_policy_pack(name: Optional[str]) -> None:
    if not name:
        return
    from anchorprune.policy_packs import has_policy_pack, list_policy_packs

    if not has_policy_pack(name):
        raise ConfigError(
            _with_suggestion(
                f"Unknown policy pack '{name}'.", name, list_policy_packs()
            ),
            details={"policy_pack": name, "known": list_policy_packs()},
        )


def validate_token_budget(value: int) -> None:
    if value <= 0:
        raise ConfigError(
            f"token_budget must be a positive integer (got {value}).",
            details={"token_budget": value},
        )


def validate_eval_trials(value: int) -> None:
    if value < 1:
        raise ConfigError(
            f"eval trials must be >= 1 (got {value}).",
            details={"trials": value},
        )


def validate_temperature(value: float) -> None:
    if not 0.0 <= value <= 2.0:
        raise ConfigError(
            f"temperature must be within [0.0, 2.0] (got {value}).",
            details={"temperature": value},
        )


def validate_database_url(url: str) -> None:
    """Validate a SQLite database target (path or ``:memory:``).

    AnchorPrune is local-first and SQLite-only in v0.9. A non-SQLite URL scheme
    (e.g. ``postgres://``) is rejected with a clear message.
    """

    if not url or not url.strip():
        raise ConfigError(
            "database path must be a non-empty SQLite path or ':memory:'.",
            details={"database": url},
        )
    if "://" in url and not url.startswith("sqlite"):
        scheme = url.split("://", 1)[0]
        raise ConfigError(
            f"unsupported database scheme '{scheme}://'. AnchorPrune v0.9 is "
            "SQLite-only; pass a file path or ':memory:'.",
            details={"database": url, "scheme": scheme},
        )


def validate_config_keys(raw: Dict[str, Any]) -> None:
    """Warn about unknown top-level config keys with a suggestion.

    Pydantic silently ignores extra keys; this surfaces likely typos early.
    """

    known = set(AppConfig.model_fields)
    unknown = [k for k in raw if k not in known]
    for key in unknown:
        raise ConfigError(
            _with_suggestion(f"Unknown config key '{key}'.", key, known),
            details={"key": key, "known": sorted(known)},
        )


def validate_app_config(config: AppConfig) -> AppConfig:
    """Validate a parsed :class:`AppConfig`, raising :class:`ConfigError`.

    Provider *availability* is not enforced here (a config may be authored on a
    machine without the SDK); use :func:`check_provider_dependency` at call time.
    """

    validate_provider(config.llm.provider.value)
    validate_policy_pack(config.policy_pack)
    validate_token_budget(config.runtime.token_budget)
    validate_temperature(config.llm.temperature)
    return config


__all__ = [
    "KNOWN_PROVIDERS",
    "suggest",
    "validate_provider",
    "check_provider_dependency",
    "validate_policy_pack",
    "validate_token_budget",
    "validate_eval_trials",
    "validate_temperature",
    "validate_database_url",
    "validate_config_keys",
    "validate_app_config",
]
