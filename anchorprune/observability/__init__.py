"""Observability utilities for AnchorPrune (v0.9).

Currently exposes structured logging. This package is intentionally small and
dependency-free; it adds visibility without changing governance behavior.
"""

from anchorprune.observability.logging import (
    configure_logging,
    get_logger,
    log_event,
    redact_metadata,
)

__all__ = ["configure_logging", "get_logger", "log_event", "redact_metadata"]
