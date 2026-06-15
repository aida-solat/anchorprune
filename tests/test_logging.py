"""Structured logging (v0.9)."""

import json
import logging

from anchorprune.observability.logging import (
    JsonFormatter,
    configure_logging,
    log_event,
    redact_metadata,
)


def test_redact_metadata_redacts_secret_like_keys():
    clean = redact_metadata(
        {
            "api_key": "sk-secret",
            "authorization": "Bearer abc",
            "OPENAI_API_KEY": "sk-x",
            "safe": "value",
        }
    )
    assert clean["api_key"] == "***REDACTED***"
    assert clean["authorization"] == "***REDACTED***"
    assert clean["OPENAI_API_KEY"] == "***REDACTED***"
    assert clean["safe"] == "value"


def test_redact_metadata_truncates_long_values():
    clean = redact_metadata({"output": "x" * 500}, max_str=200)
    assert clean["output"].endswith("[truncated]")
    assert len(clean["output"]) < 500


def _format_record(metadata) -> dict:
    record = logging.LogRecord(
        name="anchorprune.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    record.component = "runtime"
    record.event = "anchor_candidate_quarantined"
    record.run_id = "run_123"
    record.step_index = 2
    record.policy_pack = "contract_review"
    record.ap_metadata = redact_metadata(metadata)
    return json.loads(JsonFormatter().format(record))


def test_logging_json_format_redacts_secret_like_values():
    payload = _format_record({"api_key": "sk-supersecret", "reason": "CRITICAL"})
    assert payload["component"] == "runtime"
    assert payload["event"] == "anchor_candidate_quarantined"
    assert payload["run_id"] == "run_123"
    assert payload["step_index"] == 2
    assert payload["policy_pack"] == "contract_review"
    assert payload["message"] == "hello"
    assert payload["metadata"]["api_key"] == "***REDACTED***"
    assert "sk-supersecret" not in json.dumps(payload)
    # Canonical field set is present.
    for field in ("timestamp", "level", "component", "event", "message", "metadata"):
        assert field in payload


def test_configure_logging_json_emits_parseable_lines(capsys):
    configure_logging(level="info", fmt="json")
    log_event(
        "eval",
        "trial_completed",
        "done",
        run_id="run_9",
        metadata={"token": "secret-token", "n": 1},
    )
    err = capsys.readouterr().err.strip().splitlines()[-1]
    parsed = json.loads(err)
    assert parsed["component"] == "eval"
    assert parsed["metadata"]["token"] == "***REDACTED***"
    assert parsed["metadata"]["n"] == 1
    # Reset to default to avoid leaking config into other tests.
    configure_logging(level="info", fmt="human")
