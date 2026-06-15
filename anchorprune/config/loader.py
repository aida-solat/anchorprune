"""Config loading from YAML or JSON.

``load_config`` accepts a path (``.yaml``/``.yml``/``.json``) or a raw dict and
returns a validated :class:`AppConfig`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Union

from anchorprune.config.models import AppConfig
from anchorprune.errors import ConfigError


def load_config_dict(path: Union[str, Path]) -> Dict[str, Any]:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        import yaml  # pyyaml is a core dependency

        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ConfigError(
            f"Config at {path} must be a mapping, got {type(data).__name__}.",
            details={"path": str(path)},
        )
    return data


def parse_config(data: Dict[str, Any]) -> AppConfig:
    # Friendly, typed validation: unknown keys, then schema, then semantics.
    from anchorprune.config.validation import validate_app_config, validate_config_keys

    validate_config_keys(data)
    try:
        config = AppConfig.model_validate(data)
    except ValueError as exc:
        raise ConfigError(f"Invalid config: {exc}") from exc
    return validate_app_config(config)


def load_config(source: Union[str, Path, Dict[str, Any]]) -> AppConfig:
    if isinstance(source, dict):
        return parse_config(source)
    return parse_config(load_config_dict(source))
