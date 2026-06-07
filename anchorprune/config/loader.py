"""Config loading from YAML or JSON.

``load_config`` accepts a path (``.yaml``/``.yml``/``.json``) or a raw dict and
returns a validated :class:`AppConfig`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Union

from anchorprune.config.models import AppConfig


def load_config_dict(path: Union[str, Path]) -> Dict[str, Any]:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        import yaml  # pyyaml is a core dependency

        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"Config at {path} must be a mapping, got {type(data).__name__}")
    return data


def parse_config(data: Dict[str, Any]) -> AppConfig:
    return AppConfig.model_validate(data)


def load_config(source: Union[str, Path, Dict[str, Any]]) -> AppConfig:
    if isinstance(source, dict):
        return parse_config(source)
    return parse_config(load_config_dict(source))
