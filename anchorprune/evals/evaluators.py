"""Deterministic evaluators for real-model evaluation (v0.8).

The evaluator is intentionally deterministic: it checks for the presence or
absence of explicit, scenario-declared phrases. It does **not** judge reasoning
quality. A separate, optional model-based judge is described in the docs but is
non-canonical and is not implemented as the default in v0.8.

Two signals are kept strictly separate:

- **context validity** — did the strategy put the right facts (and none of the
  forbidden ones) into the context that reaches the model?
- **model answer validity** — given that context, did the model's answer satisfy
  the scenario's decision rules?

These are not the same. A governed context can still yield a poor answer, and a
contaminated context can still yield a lucky-correct answer. v0.8 reports both.
"""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class EvalCriteria(BaseModel):
    """Deterministic pass/fail phrases derived from a scenario's expectations."""

    required_mentions: List[str] = Field(default_factory=list)
    forbidden_mentions: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    adversarial_texts: List[str] = Field(default_factory=list)

    @classmethod
    def from_scenario(cls, scenario: Dict[str, Any]) -> "EvalCriteria":
        expectations = scenario.get("expectations", {}) or {}
        decision = expectations.get("decision", {}) or {}
        constraints = expectations.get("constraints") or [
            a["content"]
            for a in scenario.get("system_anchors", [])
            if a.get("priority", "critical") == "critical"
        ]
        adversarial = [
            p["content"]
            for p in _all_payloads(scenario)
            if _flagged(p, "adversarial")
        ]
        return cls(
            required_mentions=list(decision.get("must_include", [])),
            forbidden_mentions=list(decision.get("must_not_include", [])),
            constraints=list(constraints),
            adversarial_texts=adversarial,
        )

    @property
    def has_decision_rules(self) -> bool:
        return bool(self.required_mentions or self.forbidden_mentions)


def _all_payloads(scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = list(scenario.get("payload", []))
    for step in scenario.get("steps", []) or []:
        if isinstance(step, dict):
            items.extend(step.get("payloads", []) or [])
    return items


def _flagged(payload: Dict[str, Any], *flags: str) -> bool:
    meta = payload.get("metadata", {})
    return any(payload.get(f) or meta.get(f) for f in flags)


def _present(needles: List[str], haystack: str) -> List[str]:
    return [n for n in needles if n and n in haystack]


def evaluate_context(criteria: EvalCriteria, context: str) -> Dict[str, Any]:
    """Score the *context* a strategy makes available to the model.

    Context is valid when every required mention / constraint is present and no
    forbidden phrase or adversarial payload leaked into it.
    """

    required = criteria.required_mentions or criteria.constraints
    required_present = _present(required, context)
    forbidden_in_context = _present(
        criteria.forbidden_mentions + criteria.adversarial_texts, context
    )
    adversarial_contaminated = bool(_present(criteria.adversarial_texts, context))
    context_valid = (
        len(required_present) == len(required) and not forbidden_in_context
    )
    return {
        "context_valid": context_valid,
        "adversarial_contaminated": adversarial_contaminated,
    }


def evaluate_answer(criteria: EvalCriteria, output: str) -> Dict[str, Any]:
    """Score the model's *answer* against the scenario's decision rules.

    Returns ``model_answer_valid=None`` when the scenario declares no decision
    rules, since there is nothing deterministic to check.
    """

    required = criteria.required_mentions or criteria.constraints
    required_present = _present(required, output)
    forbidden_present = _present(criteria.forbidden_mentions, output)
    forbidden_or_adversarial = _present(
        criteria.forbidden_mentions + criteria.adversarial_texts, output
    )

    if criteria.has_decision_rules:
        include_ok = all(m in output for m in criteria.required_mentions)
        exclude_ok = not any(m in output for m in criteria.forbidden_mentions)
        model_answer_valid: Any = include_ok and exclude_ok
    else:
        model_answer_valid = None

    required_rate = (
        len(required_present) / len(required) if required else 1.0
    )
    return {
        "model_answer_valid": model_answer_valid,
        "constraint_violation": bool(forbidden_present),
        "required_anchor_mentions": required_present,
        "forbidden_mentions": forbidden_or_adversarial,
        "required_anchor_mention_rate": round(required_rate, 4),
        "forbidden_present": bool(forbidden_or_adversarial),
    }
