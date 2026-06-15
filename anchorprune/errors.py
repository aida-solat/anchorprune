"""Stable error taxonomy for AnchorPrune (v0.9).

A single, dependency-free hierarchy so every layer (config, policy packs,
providers, runtime, storage, serialization, evaluation, API) raises a typed
error with a **stable machine-readable code**. The API layer maps these to a
stable response shape:

    {
      "error": {
        "code": "POLICY_PACK_VALIDATION_ERROR",
        "message": "Conflict pattern references unknown anchor id.",
        "details": {}
      }
    }

This module must not import anything from the rest of ``anchorprune`` so it can
be imported from any layer without cycles.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class AnchorPruneError(Exception):
    """Base class for all AnchorPrune errors.

    Carries a stable ``code`` (SCREAMING_SNAKE_CASE), a human-readable message,
    optional structured ``details``, and a default HTTP ``status_code`` used by
    the API layer.
    """

    code: str = "ANCHORPRUNE_ERROR"
    status_code: int = 500

    def __init__(
        self, message: str = "", *, details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.message = message or self.__class__.__name__
        self.details: Dict[str, Any] = dict(details or {})

    def to_dict(self) -> Dict[str, Any]:
        """Return the stable ``{"error": {...}}`` payload for API responses."""

        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class ConfigError(AnchorPruneError):
    code = "CONFIG_ERROR"
    status_code = 400


class PolicyPackError(AnchorPruneError):
    code = "POLICY_PACK_ERROR"
    status_code = 400


class PolicyPackValidationError(PolicyPackError):
    code = "POLICY_PACK_VALIDATION_ERROR"
    status_code = 400


class ProviderUnavailableError(AnchorPruneError):
    code = "PROVIDER_UNAVAILABLE"
    status_code = 503


class RuntimeStateError(AnchorPruneError):
    code = "RUNTIME_STATE_ERROR"
    status_code = 409


class StorageError(AnchorPruneError):
    code = "STORAGE_ERROR"
    status_code = 500


class NotFoundError(AnchorPruneError):
    code = "NOT_FOUND"
    status_code = 404


class SerializationError(AnchorPruneError):
    code = "SERIALIZATION_ERROR"
    status_code = 500


class EvaluationError(AnchorPruneError):
    code = "EVALUATION_ERROR"
    status_code = 500


class ApiError(AnchorPruneError):
    code = "API_ERROR"
    status_code = 400


def error_payload(
    code: str, message: str, details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Build a stable error payload from raw parts (for non-exception paths)."""

    return {"error": {"code": code, "message": message, "details": details or {}}}


__all__ = [
    "AnchorPruneError",
    "ConfigError",
    "PolicyPackError",
    "PolicyPackValidationError",
    "ProviderUnavailableError",
    "RuntimeStateError",
    "StorageError",
    "NotFoundError",
    "SerializationError",
    "EvaluationError",
    "ApiError",
    "error_payload",
]
