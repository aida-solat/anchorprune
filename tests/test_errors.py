"""Stable error taxonomy (v0.9)."""

import pytest

from anchorprune.errors import (
    AnchorPruneError,
    ApiError,
    ConfigError,
    EvaluationError,
    PolicyPackError,
    PolicyPackValidationError,
    ProviderUnavailableError,
    RuntimeStateError,
    SerializationError,
    StorageError,
    error_payload,
)


def test_error_taxonomy_codes():
    expected = {
        AnchorPruneError: "ANCHORPRUNE_ERROR",
        ConfigError: "CONFIG_ERROR",
        PolicyPackError: "POLICY_PACK_ERROR",
        PolicyPackValidationError: "POLICY_PACK_VALIDATION_ERROR",
        ProviderUnavailableError: "PROVIDER_UNAVAILABLE",
        RuntimeStateError: "RUNTIME_STATE_ERROR",
        StorageError: "STORAGE_ERROR",
        SerializationError: "SERIALIZATION_ERROR",
        EvaluationError: "EVALUATION_ERROR",
        ApiError: "API_ERROR",
    }
    for cls, code in expected.items():
        assert cls.code == code
        assert issubclass(cls, AnchorPruneError)


def test_subclassing_hierarchy():
    assert issubclass(PolicyPackValidationError, PolicyPackError)
    assert issubclass(PolicyPackError, AnchorPruneError)


def test_to_dict_shape():
    exc = PolicyPackValidationError(
        "Conflict pattern references unknown anchor id.",
        details={"pattern": "p1"},
    )
    payload = exc.to_dict()
    assert payload == {
        "error": {
            "code": "POLICY_PACK_VALIDATION_ERROR",
            "message": "Conflict pattern references unknown anchor id.",
            "details": {"pattern": "p1"},
        }
    }


def test_error_payload_helper():
    assert error_payload("X", "msg") == {
        "error": {"code": "X", "message": "msg", "details": {}}
    }


def test_provider_unavailable_is_raisable():
    with pytest.raises(AnchorPruneError):
        raise ProviderUnavailableError("missing sdk")


def test_evals_reexports_central_provider_error():
    from anchorprune.evals import ProviderUnavailableError as EvalsErr

    assert EvalsErr is ProviderUnavailableError
