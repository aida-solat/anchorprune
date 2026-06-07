"""Config resolution shared by the service layer and integration layer.

Resolving a config by name, file path, or falling back to the deterministic
mock pipeline is needed in two places that must not depend on each other:

- the v0.4 service layer (:mod:`anchorprune.services.runtime_service`), and
- the v0.6 integration layer (:mod:`anchorprune.middleware`).

Keeping it here — next to the config models and loader — means the integration
middleware never has to import the persistence/service stack just to build a
runtime, and there is a single source of truth for resolution behaviour.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from anchorprune.config.loader import load_config
from anchorprune.config.models import AppConfig

# Directory of shipped example configs (resolved relative to the repo root).
_CONFIGS_DIR = Path("configs")


def resolve_config(
    config_name: Optional[str], *, domain: Optional[str] = None
) -> AppConfig:
    """Resolve a config by name, file path, or fall back to the deterministic
    mock pipeline. The resolved config's domain is overridden when provided."""

    config: Optional[AppConfig] = None
    if config_name:
        candidate = Path(config_name)
        search = [candidate] if candidate.suffix else []
        search += [
            _CONFIGS_DIR / f"{config_name}.yaml",
            _CONFIGS_DIR / f"{config_name}.yml",
        ]
        for path in search:
            if path.exists():
                config = load_config(path)
                break
    if config is None:
        # Deterministic mock pipeline by default (no network, no randomness).
        config = AppConfig()
    if domain:
        config = config.model_copy(deep=True)
        config.domain = domain
    return config
