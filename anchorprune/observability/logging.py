"""Structured logging for AnchorPrune (v0.9).

One small, dependency-free logging layer for runtime / service / eval components.

Goals:

- **Human-readable by default**, optional machine-readable **JSON**.
- **Configurable level** (CLI ``--log-level`` / env ``ANCHORPRUNE_LOG_LEVEL``).
- **No secrets in logs**: values under secret-like keys are redacted.
- **No full provider outputs by default**: long metadata strings are truncated.

Consistent event fields:

    timestamp, level, component, event, run_id, step_index, policy_pack,
    message, metadata
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

LOGGER_NAME = "anchorprune"
_REDACTED = "***REDACTED***"
# Keys whose values must never be logged verbatim.
_SECRET_KEY_HINTS = (
    "api_key",
    "apikey",
    "authorization",
    "auth",
    "token",
    "secret",
    "password",
    "passwd",
    "credential",
)
# Default cap for metadata string values so full provider outputs never leak.
_MAX_METADATA_STR = 200

# Structured fields we attach to a LogRecord via ``extra``.
_STRUCTURED_FIELDS = (
    "component",
    "event",
    "run_id",
    "step_index",
    "policy_pack",
    "ap_metadata",
)


def _looks_secret(key: str) -> bool:
    low = key.lower()
    return any(hint in low for hint in _SECRET_KEY_HINTS)


def redact_metadata(
    metadata: Optional[Dict[str, Any]], *, max_str: int = _MAX_METADATA_STR
) -> Dict[str, Any]:
    """Return a copy of ``metadata`` with secrets redacted and long values cut.

    Secret-like keys are replaced with a redaction marker; long strings are
    truncated so full provider outputs are never written to logs by default.
    """

    if not metadata:
        return {}
    clean: Dict[str, Any] = {}
    for key, value in metadata.items():
        if _looks_secret(str(key)):
            clean[key] = _REDACTED
        elif isinstance(value, str) and len(value) > max_str:
            clean[key] = value[:max_str] + "…[truncated]"
        elif isinstance(value, dict):
            clean[key] = redact_metadata(value, max_str=max_str)
        else:
            clean[key] = value
    return clean


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per record with the canonical structured fields."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "component": getattr(record, "component", record.name),
            "event": getattr(record, "event", record.funcName),
            "run_id": getattr(record, "run_id", None),
            "step_index": getattr(record, "step_index", None),
            "policy_pack": getattr(record, "policy_pack", None),
            "message": record.getMessage(),
            "metadata": getattr(record, "ap_metadata", {}) or {},
        }
        if record.exc_info:
            payload["metadata"]["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class HumanFormatter(logging.Formatter):
    """Readable single-line format for local development."""

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime(
            "%H:%M:%S"
        )
        component = getattr(record, "component", record.name)
        event = getattr(record, "event", None)
        run_id = getattr(record, "run_id", None)
        bits = [f"{ts}", f"{record.levelname:<5}", f"[{component}]"]
        if event:
            bits.append(event)
        if run_id:
            bits.append(f"run={run_id}")
        prefix = " ".join(bits)
        meta = getattr(record, "ap_metadata", None)
        suffix = f"  {json.dumps(meta, default=str)}" if meta else ""
        return f"{prefix}  {record.getMessage()}{suffix}"


def configure_logging(
    *, level: Optional[str] = None, fmt: Optional[str] = None
) -> logging.Logger:
    """Configure the ``anchorprune`` logger. Idempotent (replaces handlers).

    ``level``: one of debug/info/warning/error (env ``ANCHORPRUNE_LOG_LEVEL``).
    ``fmt``: ``human`` (default) or ``json`` (env ``ANCHORPRUNE_LOG_FORMAT``).
    """

    level_name = (level or os.environ.get("ANCHORPRUNE_LOG_LEVEL") or "info").upper()
    fmt_name = (fmt or os.environ.get("ANCHORPRUNE_LOG_FORMAT") or "human").lower()

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(getattr(logging, level_name, logging.INFO))
    logger.propagate = False

    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(JsonFormatter() if fmt_name == "json" else HumanFormatter())

    logger.handlers = [handler]
    return logger


def get_logger(component: str = "anchorprune") -> logging.Logger:
    """Return the (child) logger for a component, configuring on first use."""

    root = logging.getLogger(LOGGER_NAME)
    if not root.handlers:
        configure_logging()
    return root.getChild(component) if component != LOGGER_NAME else root


def log_event(
    component: str,
    event: str,
    message: str,
    *,
    level: str = "info",
    run_id: Optional[str] = None,
    step_index: Optional[int] = None,
    policy_pack: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Emit one structured event with redacted, truncated metadata."""

    logger = get_logger(component)
    log_fn = getattr(logger, level.lower(), logger.info)
    log_fn(
        message,
        extra={
            "component": component,
            "event": event,
            "run_id": run_id,
            "step_index": step_index,
            "policy_pack": policy_pack,
            "ap_metadata": redact_metadata(metadata),
        },
    )


__all__ = [
    "configure_logging",
    "get_logger",
    "log_event",
    "redact_metadata",
    "JsonFormatter",
    "HumanFormatter",
    "LOGGER_NAME",
]
