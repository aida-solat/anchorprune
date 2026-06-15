# Security & safety notes (v0.9)

This is **not** a full security audit. It documents the local-first security
posture of AnchorPrune v0.9 and the basic safety guarantees the codebase upholds.

## The one rule that matters most

> **Do not expose the AnchorPrune v0.9 API service directly to the public internet.**

The service has **no authentication, no authorization, and no multi-tenancy** in
v0.9. It is designed for local or trusted-network use (a developer machine, a
private VPC, behind your own authenticated gateway). Binding it to a public
interface would expose run data and management endpoints to anyone.

## Secrets

- **No secrets in logs.** The structured logger redacts values under secret-like
  keys (`api_key`, `authorization`, `token`, `secret`, `password`, …) and
  truncates long metadata strings, so full provider outputs are not logged by
  default. See `anchorprune/observability/logging.py`.
- **Provider keys are read from the environment only** (`OPENAI_API_KEY`,
  `ANTHROPIC_API_KEY`). Keys are never written to config files, never logged,
  and never persisted to the database. Use `.env` (gitignored) locally; see
  `.env.example`.

## Data & storage

- **Local-first SQLite.** Run state is stored in a local SQLite file. There is
  no remote datastore, no telemetry, and no outbound calls unless you explicitly
  run a real provider.
- **Observational eval output is gitignored.** `real_eval_results/` is never
  committed and is never written under `benchmarks/`.

## Dashboard

- The dashboard is **read-only**: it only issues `GET` requests and never mutates
  governed state.
- **CORS** is permissive for localhost origins only (the API allows
  `http(s)://localhost|127.0.0.1[:port]`) so the browser dashboard can read
  responses during local development. Credentials are not used.

## Determinism & governance integrity

- The deterministic benchmark cannot be contaminated by a real model: when
  `deterministic_benchmark_mode` is true, the pipeline factory forces heuristic
  components and the mock LLM everywhere.
- Real-model evaluation is **observational** and never alters governance logic or
  the canonical benchmark.

## Reporting

This is a research prototype. If you find a security issue, please open a private
report to the maintainers rather than a public issue.
