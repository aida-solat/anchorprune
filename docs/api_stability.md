# API stability (v1.0)

> APIs documented in this file are considered **stable for the v1.x series**
> except where marked **experimental**.

v1.0 freezes the public shape of AnchorPrune. Stable APIs will not change in a
backward-incompatible way within the v1.x series. Experimental surfaces may
change between minor versions.

> AnchorPrune does not make models smarter. It governs what reaches them.

## Stable: runtime

```python
from anchorprune import AnchorPruneRuntime, MockLLM
```

- `AnchorPruneRuntime(llm, *, domain_profile=..., anchor_extractor=..., compressor=...)`
- `AnchorPruneRuntime.from_policy_pack(name, *, llm=...)` — build a runtime governed by a policy pack.
- `AnchorPruneRuntime.create_run(*, goal, system_anchors=...)`
- `AnchorPruneRuntime.add_payload(...)` / `AnchorPruneRuntime.add_tool_output(...)`
- `AnchorPruneRuntime.govern_and_compose(instruction, output_schema=None)` — phase 1: govern state and compose the context (no model call).
- `AnchorPruneRuntime.ingest_model_output(...)` — phase 2: observe the model's output and update state.
- `AnchorPruneRuntime.run_step(instruction, output_schema=None)` — convenience: govern + compose + model call + ingest.

`StepResult` and the governed-state models (`Anchor`, `PayloadBlock`,
`ReasoningMilestone`, `ConflictEdge`, `GovernedStateGraph`, `DomainProfile`) are
stable data shapes.

## Stable: middleware

```python
from anchorprune import AnchorPruneMiddleware
```

- `AnchorPruneMiddleware(domain="…" | policy_pack="…")`
- `AnchorPruneMiddleware.create_run(*, goal, system_anchors=...)`
- `AnchorPruneMiddleware.before_model_call(run_id, *, new_payloads=..., instruction=...)` — returns a `GovernedContext`.
- `AnchorPruneMiddleware.after_model_call(run_id, model_output)`

## Stable: policy packs

```python
from anchorprune.policy_packs import (
    get_policy_pack, list_policy_packs, validate_policy_pack
)
```

- `list_policy_packs() -> list[str]`
- `get_policy_pack(name) -> DomainPolicyPack`
- `validate_policy_pack(pack | name | path) -> DomainPolicyPack`

## Stable: CLI commands

| Command | Purpose |
|---|---|
| `anchorprune run` | Run a scenario through the governed runtime |
| `anchorprune inspect` | Inspect a saved run's anchors / milestones / audit |
| `anchorprune benchmark` | Benchmark one scenario vs. baselines |
| `anchorprune pack` | Generate the deterministic benchmark pack |
| `anchorprune packs list/show/validate` | Inspect and validate policy packs |
| `anchorprune serve` | Start the local-first API service |
| `anchorprune real-eval` | Observational real-model evaluation |
| `anchorprune db migrate/info` | SQLite migrations and status |
| `anchorprune doctor` | Diagnose the install |

CLI **command names and their primary options** are stable for v1.x. Output
formatting (table layout, colors) is not part of the stability contract.

## Stable: API service shape

- The error response shape `{"error": {"code", "message", "details"}}`.
- List endpoints expose `limit`/`offset`/`total` alongside their existing
  fields (`runs`/`count`, `events`, `steps`/`summary`).
- The API has **no authentication** and is **local-first**; see
  [`security.md`](security.md).

## Experimental (may change in v1.x)

- **Real-model, provider-backed evaluation results** — observational only; the
  numbers depend on provider/model/version/temperature/date.
- **Provider adapters** (`OpenAILLM`, `AnthropicLLM`, local callables) — optional
  and may evolve with upstream SDKs.
- **Dashboard UI layout** — a read-only inspection aid, not a stable contract.
- **A model-based judge**, if added later, would be non-canonical and
  experimental.

## What "stable" does not mean

Stability is about the **public shape**, not new guarantees. See
[`claims.md`](claims.md) for what AnchorPrune does and does not claim, and
[`../benchmarks/benchmark_report.md`](../benchmarks/benchmark_report.md) for the
canonical deterministic benchmark.
