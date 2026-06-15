"""Config validation hardening (v0.9)."""

import pytest

from anchorprune.config.loader import load_config
from anchorprune.config.validation import (
    validate_database_url,
    validate_eval_trials,
    validate_policy_pack,
    validate_provider,
    validate_token_budget,
)
from anchorprune.errors import ConfigError


def test_config_validation_unknown_policy_pack_suggestion():
    with pytest.raises(ConfigError) as exc:
        validate_policy_pack("contracts")
    msg = str(exc.value)
    assert "Unknown policy pack 'contracts'" in msg
    assert "contract_review" in msg  # suggestion present


def test_validate_unknown_provider_suggestion():
    with pytest.raises(ConfigError) as exc:
        validate_provider("openai_")
    assert "openai" in str(exc.value)


def test_validate_token_budget_rejects_non_positive():
    with pytest.raises(ConfigError):
        validate_token_budget(0)
    validate_token_budget(1024)  # ok


def test_validate_eval_trials():
    with pytest.raises(ConfigError):
        validate_eval_trials(0)
    validate_eval_trials(3)  # ok


def test_validate_database_url_rejects_non_sqlite_scheme():
    with pytest.raises(ConfigError) as exc:
        validate_database_url("postgres://localhost/db")
    assert "SQLite-only" in str(exc.value)
    validate_database_url(":memory:")  # ok
    validate_database_url(".anchorprune/anchorprune.db")  # ok


def test_load_config_rejects_unknown_key_with_suggestion():
    with pytest.raises(ConfigError) as exc:
        load_config({"domian": "default"})  # typo of 'domain'
    assert "Unknown config key 'domian'" in str(exc.value)
    assert "domain" in str(exc.value)


def test_load_config_rejects_unknown_policy_pack():
    with pytest.raises(ConfigError):
        load_config({"policy_pack": "contracts"})


def test_valid_config_loads():
    cfg = load_config({"domain": "coding_agent", "llm": {"provider": "mock"}})
    assert cfg.domain == "coding_agent"
