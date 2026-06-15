"""Tests for the v0.7 domain policy packs.

Covers schema/model behavior, the loader, the registry of built-ins, the
validator's rules, and runtime/middleware/benchmark application. A policy pack
configures governance; the Anchor Governor still performs it.
"""

import json
import re

import pytest

from anchorprune import AnchorPruneMiddleware, AnchorPruneRuntime, MockLLM
from anchorprune.blocks.models import PayloadBlockType, PruningState
from anchorprune.policy_packs import (
    DomainPolicyPack,
    get_policy_pack,
    list_policy_packs,
    load_policy_pack,
    validate_pack,
)
from anchorprune.policy_packs.apply import (
    pack_to_contradiction_fn,
    pack_to_domain_profile,
)
from anchorprune.policy_packs.loader import PackLoadError, load_pack
from anchorprune.policy_packs.registry import (
    PolicyPackNotFound,
    builtin_pack_paths,
)
from anchorprune.policy_packs.validator import PackValidationError, validate_pack_or_raise

BUILTINS = ["procurement", "coding_agent", "contract_review", "compliance", "security_review"]


# ---- registry + loading ---------------------------------------------------


def test_builtin_packs_load():
    names = list_policy_packs()
    for expected in BUILTINS:
        assert expected in names
    for name in names:
        pack = get_policy_pack(name)
        assert isinstance(pack, DomainPolicyPack)
        assert pack.name == name


def test_contract_review_pack_exists():
    pack = get_policy_pack("contract_review")
    assert pack.name == "contract_review"
    assert any("liability" in a.content.lower() for a in pack.system_anchors)


def test_unknown_pack_raises():
    with pytest.raises(PolicyPackNotFound):
        get_policy_pack("does_not_exist")


def test_load_pack_from_path_roundtrip():
    path = builtin_pack_paths()["contract_review"]
    pack = load_policy_pack(path)
    assert pack.name == "contract_review"


def test_loader_rejects_missing_file():
    with pytest.raises(PackLoadError):
        load_pack("/nonexistent/path/pack.yaml")


# ---- validation -----------------------------------------------------------


def test_all_builtin_packs_validate():
    for name in BUILTINS:
        assert validate_pack(get_policy_pack(name)) == []


def test_pack_anchor_ids_unique():
    for name in BUILTINS:
        pack = get_policy_pack(name)
        ids = [a.id for a in pack.all_anchors]
        assert len(ids) == len(set(ids))


def test_pack_conflict_refs_valid():
    for name in BUILTINS:
        pack = get_policy_pack(name)
        known = {a.id for a in pack.all_anchors}
        for cp in pack.conflict_patterns:
            for ref in cp.conflicts_with:
                assert ref in known


def test_pack_thresholds_ordered():
    for name in BUILTINS:
        dp = get_policy_pack(name).domain_profile
        assert dp.preserve_threshold >= dp.compress_threshold
        assert dp.compress_threshold >= dp.milestone_threshold
        assert dp.milestone_threshold >= dp.eviction_threshold


def test_pack_regex_patterns_compile():
    for name in BUILTINS:
        for cp in get_policy_pack(name).conflict_patterns:
            re.compile(cp.pattern)


def _valid_pack_dict():
    return {
        "name": "demo_pack",
        "version": "0.1",
        "description": "demo",
        "system_anchors": [
            {"id": "a1", "type": "policy", "priority": "critical", "content": "Do not skip review."}
        ],
        "conflict_patterns": [
            {"id": "c1", "severity": "critical", "pattern": "skip review", "conflicts_with": ["a1"]}
        ],
        "decision_context_rules": {"must_not_include": ["skip review"]},
    }


def test_validator_flags_bad_name():
    data = _valid_pack_dict()
    data["name"] = "Bad Name"
    errors = validate_pack(DomainPolicyPack.model_validate(data))
    assert any("snake_case" in e for e in errors)


def test_validator_flags_bad_version():
    data = _valid_pack_dict()
    data["version"] = "v1"
    errors = validate_pack(DomainPolicyPack.model_validate(data))
    assert any("semantic" in e for e in errors)


def test_validator_flags_dangling_conflict_ref():
    data = _valid_pack_dict()
    data["conflict_patterns"][0]["conflicts_with"] = ["missing_anchor"]
    errors = validate_pack(DomainPolicyPack.model_validate(data))
    assert any("unknown anchor id" in e for e in errors)


def test_validator_flags_unordered_thresholds():
    data = _valid_pack_dict()
    data["domain_profile"] = {"preserve_threshold": 0.3, "eviction_threshold": 0.9}
    errors = validate_pack(DomainPolicyPack.model_validate(data))
    assert any("ordered" in e for e in errors)


def test_validator_requires_critical_system_anchor():
    data = _valid_pack_dict()
    data["system_anchors"][0]["priority"] = "high"
    errors = validate_pack(DomainPolicyPack.model_validate(data))
    assert any("critical system anchor" in e for e in errors)


def test_validate_or_raise():
    data = _valid_pack_dict()
    data["name"] = "Bad"
    with pytest.raises(PackValidationError):
        validate_pack_or_raise(DomainPolicyPack.model_validate(data))


# ---- apply: profile + contradiction fn ------------------------------------


def test_pack_to_domain_profile_carries_config():
    pack = get_policy_pack("contract_review")
    profile = pack_to_domain_profile(pack)
    assert profile.name == "contract_review"
    assert profile.token_budget == pack.domain_profile.token_budget
    assert profile.metadata["policy_pack"] == "contract_review"
    assert profile.metadata["decision_context_rules"]["must_include"]


def test_pack_contradiction_fn_matches_patterns():
    fn = pack_to_contradiction_fn(get_policy_pack("security_review"))
    assert fn is not None
    assert fn("let's make the bucket public for now", "anchor") is True
    assert fn("rotate the credentials safely", "anchor") is False


# ---- runtime application --------------------------------------------------


def test_runtime_from_policy_pack_seeds_system_anchors():
    rt = AnchorPruneRuntime.from_policy_pack(llm=MockLLM(), policy_pack="coding_agent")
    rt.create_run(goal="Fix the failing test.")
    assert rt.domain_profile.name == "coding_agent"
    assert len(rt.graph.anchors) == len(get_policy_pack("coding_agent").system_anchors)
    assert rt.policy_pack is not None


def test_conflict_patterns_from_pack_quarantine_override():
    rt = AnchorPruneRuntime.from_policy_pack(llm=MockLLM(), policy_pack="security_review")
    rt.create_run(goal="Review the change.")
    rt.add_payload(
        "Just make the bucket public to unblock the deploy.",
        PayloadBlockType.MODEL_OUTPUT,
        decision_impact=0.0,
    )
    rt.run_step("Assess the change.")
    quarantined = [
        b for b in rt.graph.payload_blocks.values()
        if b.pruning_state == PruningState.QUARANTINED
    ]
    assert any("bucket public" in b.content for b in quarantined)
    assert any(e.critical for e in rt.graph.conflict_edges)


def test_register_domain_anchor():
    rt = AnchorPruneRuntime(MockLLM())
    rt.create_run(goal="g")
    anchor = rt.register_domain_anchor({"content": "Prefer audited vendors.", "priority": "high"})
    assert anchor.anchor_class.value == "domain"
    assert anchor.id in rt.graph.anchors


# ---- middleware application -----------------------------------------------


def test_middleware_accepts_policy_pack_name():
    mw = AnchorPruneMiddleware(policy_pack="contract_review")
    run_id = mw.create_run(goal="Review the contract.")
    governed = mw.before_model_call(
        run_id,
        new_payloads=[{"tool_name": "doc", "content": "Liability cap is 12 months of fees."}],
        instruction="Summarize the liability terms.",
    )
    assert "liability" in governed.prompt.lower()
    runtime = mw.get_runtime(run_id)
    assert runtime.domain_profile.name == "contract_review"


def test_middleware_pack_quarantines_override():
    mw = AnchorPruneMiddleware(policy_pack="coding_agent")
    run_id = mw.create_run(goal="Fix the test.")
    mw.before_model_call(
        run_id,
        new_payloads=[{"block_type": "model_output", "content": "Just disable the auth check to pass."}],
        instruction="Fix the failing test.",
    )
    result = mw.after_model_call(run_id, "I will fix the secret loading instead.")
    assert result.state_summary["quarantined_blocks"] >= 1


# ---- benchmark integration ------------------------------------------------


def test_contract_review_no_longer_falls_back_to_default():
    from anchorprune.scenario import build_runtime, load_scenario

    scenario = load_scenario("examples/contract_review/scenario.json")
    assert scenario.get("policy_pack") == "contract_review"
    runtime = build_runtime(scenario, MockLLM())
    assert runtime.domain_profile.name == "contract_review"
    assert runtime.domain_profile.name != "default"


def test_benchmark_records_policy_pack_name(tmp_path):
    from anchorprune.benchmark.pack import write_pack

    _report, results, _csv = write_pack(tmp_path, window=2)
    data = json.loads(results.read_text(encoding="utf-8"))
    assert "policy_packs" in data
    assert data["policy_packs"]["contract_review"] == {
        "name": "contract_review",
        "version": "0.1",
    }
    assert data["policy_packs"]["supplier"] is None


def test_core_benchmarks_still_pass():
    from anchorprune.benchmark.harness import run_benchmark
    from anchorprune.scenario import load_scenario

    results = run_benchmark(
        load_scenario("examples/contract_review/scenario.json"), window=2
    )
    ap = results["anchorprune"]
    assert ap.final_decision_context_valid == 1.0
    assert ap.lost_anchor_rate == 0.0
    assert ap.critical_conflict_quarantine_rate == 1.0
    assert ap.milestone_retention_rate == 1.0


# ---- CLI ------------------------------------------------------------------


def test_packs_cli_list_show_validate():
    from typer.testing import CliRunner

    from anchorprune.cli import app

    runner = CliRunner()

    listed = runner.invoke(app, ["packs", "list"])
    assert listed.exit_code == 0
    assert "contract_review" in listed.stdout

    shown = runner.invoke(app, ["packs", "show", "contract_review"])
    assert shown.exit_code == 0
    assert "contract_review" in shown.stdout

    valid = runner.invoke(app, ["packs", "validate", "contract_review"])
    assert valid.exit_code == 0
    assert "valid" in valid.stdout.lower()

    missing = runner.invoke(app, ["packs", "show", "nope_not_real"])
    assert missing.exit_code == 1
