# Domain Policy Packs (v0.7)

> Policy packs configure governance. They do not perform governance.

A **domain policy pack** is a reusable, local, static description of how
AnchorPrune should govern a particular high-stakes workflow. Instead of writing

```python
mw = AnchorPruneMiddleware(domain="default")
```

a caller can write

```python
mw = AnchorPruneMiddleware(policy_pack="contract_review")
```

and AnchorPrune knows the domain's critical anchors, scoring weights, conflict
patterns, freshness rules, and what a valid decision context must contain.

## Why policy packs exist

Before v0.7, an unknown domain such as `contract_review` silently fell back to
the default profile — no domain anchors, no domain-specific conflict patterns.
Policy packs close that gap with curated, validated governance configuration for
common domains, without turning AnchorPrune into an agent framework or a policy
server.

## What a pack contains

| Field | Purpose |
| --- | --- |
| `name`, `version`, `description` | Identity and semantic version. |
| `domain_profile` | Token budget, anchor-weight coefficients, and pruning thresholds (`preserve >= compress >= milestone >= eviction`). |
| `system_anchors` | Pre-approved critical constraints seeded into every run. |
| `domain_anchors` | Pre-approved domain-level anchors (optional). |
| `freshness_rules` | Advisory time-sensitivity per kind of state. |
| `conflict_patterns` | Regex patterns whose match signals a governance conflict, each referencing the anchor id(s) it protects. |
| `expected_milestone_patterns` | Reasoning milestones worth retaining. |
| `decision_context_rules` | What a valid composed context must / must not contain. |
| `metadata` | Free-form, non-semantic annotations. |

## Built-in packs

| Pack | Focus |
| --- | --- |
| `procurement` | Supplier/vendor decisions: approval thresholds, verified compliance, sanctions screening, scoring confidentiality. |
| `coding_agent` | Coding agents: never disable auth/security, no hardcoded secrets, stable public API schema, tests must pass. |
| `contract_review` | Liability caps, auto-renewal approval, GDPR/data-processing language, termination notice, required clauses. |
| `compliance` | Cited policy sources, no unverified claims as policy, escalation, surfacing missing evidence. |
| `security_review` | No bypassing controls, secret protection, privilege-escalation review, active authn/authz. |

```bash
anchorprune packs list
anchorprune packs show contract_review
anchorprune packs validate anchorprune/policy_packs/builtins/contract_review.yaml
```

## How packs affect runtime

When a pack configures a run, it:

- **sets the domain profile** — anchor-weight coefficients, token budget, and
  payload pruning/milestone thresholds;
- **seeds system (and domain) anchors** as pre-approved constraints;
- **adds its conflict patterns** both as extra extraction triggers (so a
  matching payload is surfaced as a candidate) and as the runtime's
  `contradiction_fn` (so the Anchor Governor can quarantine it);
- **carries freshness rules, milestone patterns, and decision-context rules** in
  the profile metadata for components and evaluators that consume them.

Entry points:

```python
# Runtime
rt = AnchorPruneRuntime.from_policy_pack(llm=MockLLM(), policy_pack="contract_review")

# Middleware
mw = AnchorPruneMiddleware(policy_pack="contract_review")

# Scenario / CLI
#   scenario.json: {"policy_pack": "contract_review", ...}
anchorprune run --input scenario.json --policy-pack contract_review

# Config
#   app config: {"policy_pack": "contract_review"}
```

## How packs do **not** affect runtime

A pack never approves an anchor, never quarantines a payload, and never composes
context. Those remain the jobs of the Anchor Governor, the pruner, and the
context composer. Concretely:

> Policy packs configure the Anchor Governor, pruner, freshness scoring, and
> conflict detection. They do not approve anchors directly and they do not
> bypass runtime governance.

A pattern match makes a payload *eligible for evaluation*; the governor still
decides whether it conflicts with a critical anchor and is quarantined.

## Pack schema

See `anchorprune/policy_packs/models.py` (`DomainPolicyPack`). A pack is a YAML
or JSON file; built-ins live in `anchorprune/policy_packs/builtins/*.yaml`.

## Validation rules

`anchorprune packs validate` (and every built-in load) enforces:

- `name` is snake_case; `version` is semantic (`0.1`, `1.2.3`).
- anchor ids are unique; conflict-pattern ids are unique.
- every `conflicts_with` reference points to a real anchor id.
- weights are non-negative; thresholds are in `[0, 1]` and ordered
  `preserve >= compress >= milestone >= eviction`; token budget is positive.
- at least one **critical system anchor** exists.
- every regex pattern compiles.
- `decision_context_rules` is non-empty (so the pack is benchmark-usable).

## CLI usage

```bash
anchorprune packs list                 # names + versions + descriptions
anchorprune packs show <name>          # full pack as JSON
anchorprune packs validate <name|path> # validate a built-in or a file
anchorprune run --input s.json --policy-pack <name>
```

## Custom packs

Author a YAML file following the schema, then load it from a path:

```python
from anchorprune.policy_packs import load_policy_pack
pack = load_policy_pack("my_packs/legal_review.yaml")  # validated on load
rt = AnchorPruneRuntime.from_policy_pack(llm=MockLLM(), policy_pack=pack)
```

## Limitations

- Packs are **local and static**. There is no remote registry, marketplace,
  cloud sync, policy-editor UI, auth, or multi-tenant policy management — and
  none is planned for this layer.
- `freshness_rules` are **advisory**: the freshness *coefficient* is applied via
  the domain weights, but per-type freshness sensitivity uses the built-in RFC
  table; packs do not mutate global scoring state (that would break the
  deterministic benchmark).
- Conflict patterns are deterministic regex, not learned classifiers.
- The deterministic benchmark remains the source of truth: enabling the
  `contract_review` pack changes only that scenario's governed run (now
  configured by the pack) and records the pack in `results.json`.
