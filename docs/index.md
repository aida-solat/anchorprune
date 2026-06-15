# AnchorPrune documentation index

A map of the docs and what each one is for. AnchorPrune is **local-first** and
the deterministic benchmark remains the **canonical** benchmark; real-model
evaluation is observational.

## Start here

- [`../README.md`](../README.md) — what AnchorPrune is, what it is not,
  quickstart, and the roadmap to v1.0.
- [`method.md`](method.md) — the central technical claim and how governed
  anchored state pruning differs from summarization.
- [`architecture.md`](architecture.md) — component-by-component design.

## Running it

- [`service.md`](service.md) — the local FastAPI service (runs, payloads, steps,
  state, audit, metrics) and its data model.
- [`dashboard.md`](dashboard.md) — the read-only Next.js state-graph dashboard.
- [`integrations.md`](integrations.md) — middleware, LangGraph, LlamaIndex.

## Configuring governance

- [`policy_packs.md`](policy_packs.md) — v0.7 domain policy packs (schema,
  built-ins, validation, application).

## Evaluating

- [`../benchmarks/benchmark_report.md`](../benchmarks/benchmark_report.md) — the
  canonical deterministic benchmark report.
- [`real_model_eval.md`](real_model_eval.md) — the v0.8 observational real-model
  evaluation harness.

## Operating and hardening (v0.9)

- [`security.md`](security.md) — local-first security/safety notes. **Do not
  expose the API to the public internet.**
- [`v1_readiness.md`](v1_readiness.md) — the pre-1.0 readiness checklist.

## Reference

- [`../RELEASE_NOTES.md`](../RELEASE_NOTES.md) — what shipped in each version.

## Operational quick reference (v0.9)

```bash
anchorprune doctor                              # diagnose the install + extras
anchorprune db migrate --db .anchorprune/anchorprune.db
anchorprune db info --db .anchorprune/anchorprune.db
anchorprune serve --log-format json --log-level info
anchorprune real-eval --provider mock --scenarios coding_agent --log-format json
```
