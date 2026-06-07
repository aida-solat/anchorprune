# Release Notes

## v0.5.0 — Governed State Graph Dashboard

Adds a local, **read-only** Next.js dashboard for inspecting AnchorPrune
governed agent state. It is a microscope for governed state, not a SaaS shell.
No backend governance changed: the dashboard only reads the v0.4 FastAPI service.

### Core principle

> The dashboard observes governance. It does not perform governance.
>
> The UI only reads the API. It never prunes, approves anchors, detects
> conflicts, or edits policy.

### What shipped (`dashboard/`)

- **Next.js 14 + TypeScript + Tailwind**, with **Recharts** for charts and
  **@xyflow/react** for the state graph. Fully client-rendered, so `next build`
  needs no running API.
- **Read-only API client** (`lib/api.ts`) over `GET /health`, `/runs`,
  `/runs/{id}`, `/runs/{id}/state`, `/audit`, `/metrics`, with typed models that
  mirror the v0.4 responses exactly.
- **Pages:** `/` (positioning + live API health), `/runs` (persisted runs
  table), `/runs/[runId]` (the run microscope).
- **Run detail** — summary cards plus tabs: **Graph**, **Anchors** (class &
  critical filters), **Payloads** (state/flag filters), **Quarantine** (blocked
  payloads + conflict edges — the governance story), **Milestones**, **Audit**
  (expandable timeline), **Metrics**.
- **State graph** — grouped layout (anchors → milestones → payload), color-coded
  by class/state, drawing only the linkage the state graph declares.
- **Charts** — context growth, input/output tokens per step, state-object counts
  over steps, and a final-snapshot payload pruning breakdown.
- **Docs:** `docs/dashboard.md` + a README Dashboard section.

### Out of scope

- auth / RBAC / multi-tenancy
- billing / user management
- cloud deployment
- editing governance policies from the UI

### Compatibility & guarantees

- The Python package, FastAPI service, deterministic benchmark, and adapter
  layer are unchanged. `anchorprune pack --out benchmarks --window 2` still
  produces byte-identical artifacts; `pytest` and `ruff` stay green.
- `npm run typecheck` and `npm run build` pass.
- Only response-shape-compatible reads were used; **no API/DB/governance changes**.

---

## v0.4.0 — FastAPI Service and SQLite Persistence

Takes AnchorPrune from a CLI/library to a **local-first service**. Runs can now
be created, stepped, inspected, audited, and persisted over HTTP, while the
governed-state runtime, deterministic benchmark, and adapter layer are all
unchanged. No UI, auth, multi-tenancy, Postgres, background workers, or cloud
deployment.

### Core principle

> The service layer wraps the runtime. It does not redefine the method.
>
> Routes call services. Services call the runtime. The runtime owns the method.

### What shipped

- **FastAPI service with OpenAPI docs** (`anchorprune/api/`): `GET /health`,
  `POST /runs`, `GET /runs`, `GET /runs/{id}`, `POST /runs/{id}/payload`,
  `POST /runs/{id}/steps`, `GET /runs/{id}/state`, `GET /runs/{id}/audit`,
  `GET /runs/{id}/metrics`, `DELETE /runs/{id}`.
- **SQLite persistence** (`anchorprune/storage/`): `runs`, `state_snapshots`,
  `audit_events`, `step_metrics`. The governed state is stored as a lossless
  **JSON snapshot per step** rather than over-normalized tables; audit events are
  written with `INSERT OR IGNORE` (dedup by id).
- **Storage abstraction**: a `RunRepository` interface, a `sqlite3`-stdlib
  implementation, and `GovernedStateGraph` serialization helpers with a
  round-trip test (`graph -> JSON -> SQLite -> JSON -> graph`).
- **Service layer** (`anchorprune/services/`): `RunService` orchestrates
  persistence; `RuntimeService` builds new runtimes and rehydrates existing ones
  (graph + cumulative metrics + anchor registry) so a run can be continued after
  a process restart. No governance/pruning/model logic lives in routes or
  storage.
- **`anchorprune serve`** — `--host`, `--port`, `--db`; FastAPI/uvicorn are
  imported lazily so the command degrades gracefully without the extra.
- **Optional `[api]` dependency group** (`fastapi`, `uvicorn`). A core install
  never requires FastAPI.
- **`configs/service.mock.yaml`** — deterministic default for the service.
- **Docs**: `docs/service.md`, a README API-service section.

### Compatibility & guarantees

- `anchorprune pack --out benchmarks --window 2` still produces **byte-identical**
  artifacts; the benchmark depends on neither the API nor SQLite.
- `pip install anchorprune` does not require FastAPI; importing the core works
  with the `[api]` extras absent (verified by a subprocess test that blocks
  `fastapi`/`uvicorn`/`starlette`).
- Governance is preserved end-to-end: an override payload submitted over HTTP is
  quarantined by the Anchor Governor exactly as under the CLI.
- SQLite persists runs across process restarts (verified by restarting the app
  against the same database file and continuing the run).

### Quality

- Full suite passing (deterministic core + adapter contracts + new API,
  persistence, state-round-trip, core-import-without-FastAPI, and
  benchmark-determinism tests). Lint clean (`ruff check .`).

---

## v0.3.0 — Pluggable Adapter Layer

Turns AnchorPrune from a fully deterministic prototype into a runtime that can
connect to real models — **without** compromising the deterministic benchmark.
v0.3 introduces optional real-provider adapters while preserving deterministic
benchmark mode as the source of truth. No API, DB, UI, auth, or deployment.

### Core principle (unchanged)

> Deterministic governance remains the source of truth. Model-based adapters may
> propose, enrich, or compress state, but they do not bypass the Anchor Governor.
>
> LLM proposes. Anchor Governor disposes.

### What shipped

- **LLM adapter interface.** Formal `LLMRequest` / `LLMResponse` / `LLMClient.generate`,
  with the legacy `complete()` preserved as a wrapper so the runtime and
  benchmark are byte-for-byte unchanged. Adapters: `MockLLM` (default),
  `EchoLLM` / `CallableLLM` (local, dependency-free), and optional `OpenAILLM` /
  `AnthropicLLM` behind import guards.
- **Embedding adapter interface.** `EmbeddingClient` with a deterministic
  `HashEmbeddingClient` for tests/offline and an optional `OpenAIEmbeddingClient`.
- **Anchor extractors.** `AnchorExtractor` with `Heuristic` (default),
  `ModelBased` (emits `CandidateAnchor`s only — never approved anchors), and
  `Hybrid`. Model output always flows through the Anchor Governor.
- **Conflict detectors.** `ConflictDetector` with `Heuristic`, `ModelAssisted`,
  and `Hybrid`. Heuristic system-anchor conflicts are authoritative hard gates;
  a model can add non-critical signals but can never assert or clear a hard gate.
- **Compressors.** `Compressor` with `Heuristic` (default) and `ModelBased`.
  Linkage (`linked_anchor_ids`, `evidence_refs`, `source_block_id`) is preserved
  structurally, not left to the model.
- **Config system.** `AppConfig` + YAML/JSON loader + pipeline `factory`.
  `configs/mock.yaml` plus `openai.example.yaml` / `anthropic.example.yaml`.
  CLI gains `anchorprune run --config <file>`.
- **`deterministic_benchmark_mode` safety switch.** When true (the default for
  mock/benchmark configs), the factory forces every stage to heuristic and the
  provider to `mock`, so a config can never contaminate benchmark numbers with a
  real model, randomness, or the network.
- **`examples/real_llm_smoke/`.** Adapter-compatibility smoke example, explicitly
  **not** part of the deterministic benchmark claims.
- **Optional dependencies.** `pip install anchorprune` never pulls in
  `openai`/`anthropic`; importing an adapter module is always safe, and only
  constructing a real client requires its extra.

### Compatibility & guarantees

- All v0.1/v0.2 deterministic benchmarks are unchanged:
  `anchorprune pack --out benchmarks --window 2` regenerates byte-identical
  artifacts using `MockLLM` + heuristic components.
- Existing benchmark results depend on no network, API keys, randomness, or real
  models.

### Quality

- Full test suite passing (deterministic core + new adapter-contract,
  optional-import-safety, governance-passthrough, hard-gate, compressor-linkage,
  and config tests). Lint clean (`ruff check .`).

---

## v0.2 — Long-Run Benchmark Pack

Extends the benchmark to long-running agent memory behavior over 10–20 steps,
with payloads injected over time. No new product surface (no API, DB, or UI).

### Highlights

- **Three long-run scenarios.** `long_run_coding_20_steps`,
  `long_run_contract_15_steps`, `long_run_procurement_10_steps` — each injects
  useful, obsolete, noisy, and adversarial payloads across many steps.
- **Multi-step scenario format.** Steps may be objects with per-step `payloads`,
  so information arrives over time. The v0.1 string-step format still works
  (backward compatible).
- **New per-step and aggregate metrics on `BenchmarkResult`:**
  `context_tokens_by_step`, `anchor_retention_by_step`,
  `adversarial_contamination_by_step`, `obsolete_retention_by_step`,
  `state_size_by_step`, `context_growth_slope`, `max_context_size`,
  `final_context_size_ratio_vs_full_history`, `tokens_per_valid_context`, and an
  experimental `bounded_context_score`. All v0.1 metrics are preserved.
- **Report split into two parts.** Part 1 = v0.1 short adversarial scenarios;
  Part 2 = v0.2 long-run pack with governance tables, per-step context-growth
  tables, interpretation, and explicit deterministic/synthetic caveats.
- **New artifact** `benchmarks/long_run_results.csv` (per-step series).

### Result (deterministic)

Across all three long-run scenarios, AnchorPrune holds `lost_anchor_rate = 0%`,
`adversarial_contamination = 0%`, `constraint_adherence = 100%`, a valid final
decision context, and a context-growth slope below full history.

> AnchorPrune is not the smallest memory strategy. It is the smallest governed
> memory strategy in the benchmark: it preserves critical anchors, prevents
> adversarial contamination, and keeps context growth below full-history memory
> over long-running workflows.

Token counts are only meaningful when the resulting decision context is valid, so
`tokens_per_valid_context` is reported as N/A wherever a method's final context
is invalid — a small but anchor-less or adversarial-contaminated context is a
cheaper _invalid_ context, not a better strategy.

### Quality

- 40 passing tests (`pytest`), lint clean (`ruff check .`).

---

## v0.1 — Public Release Pack

First public release of AnchorPrune: a governed-state runtime for long-running
AI agents, plus a deterministic benchmark that measures state governance under
adversarial context.

### Highlights

- **Governed state graph runtime.** Linear context is transformed into anchors,
  payload blocks, evidence references, conflict edges, milestones, and pruning
  actions (`anchorprune/core`).
- **Hybrid Anchor Registry.** System / domain / runtime anchors with distinct
  survival rules.
- **Anchor Governor.** A pre-scoring hard gate quarantines conflicts and
  override attempts; surviving candidates are scored by a per-domain anchor
  weighting equation.
- **Anchor-aware pruning.** Preserve / quarantine / compress / evict decisions
  driven by utility and anchor linkage, with milestone extraction.
- **Context Composer.** Fixed-order, budget-aware composition that never emits
  quarantined or evicted state and always includes critical system anchors.
- **Domain profiles.** `default`, `procurement`, `coding_agent`, `healthcare`,
  `compliance`.
- **CLI.** `init`, `run`, `inspect`, `benchmark`, `pack`.

### Benchmark Pack v0.1

- Three governed-state scenarios: `supplier`, `coding_agent`, `contract_review`,
  each with critical anchors and expected constraints/milestones; `coding_agent`
  and `contract_review` additionally include adversarial override payloads.
- Four memory strategies compared: full history, sliding window, simple summary,
  and AnchorPrune.
- Seven metrics: `lost_anchor_rate`, `constraint_adherence_rate`,
  `critical_conflict_quarantine_rate` (N/A when a scenario has no adversarial
  payloads), `payload_eviction_rate`, `milestone_retention_rate`,
  `token_count_by_step`, `final_decision_context_valid`.
- Generated artifacts: `benchmarks/benchmark_report.md`,
  `benchmarks/results.json`.

**Result (deterministic):** AnchorPrune was the only evaluated memory strategy
with a governance mechanism — it preserved all critical anchors and maintained
100% constraint adherence across all three scenarios, and quarantined adversarial
override attempts in every scenario where such attempts were present.

### Documentation

- Release-grade `README.md` (problem, method, why-not-summarization, Mermaid
  architecture diagram, benchmark summary, reproducibility, limitations,
  roadmap).
- `docs/method.md` — central technical claim and benchmark interpretation.
- `docs/architecture.md` — component-by-component design.

### Quality

- 37 passing tests (`pytest`).
- Lint clean (`ruff check .`).
- CI across Python 3.10 / 3.11 / 3.12.

### Known limitations

- Extraction, conflict detection, evidence linking, and compression are
  deterministic heuristics, not learned models.
- The benchmark evaluator is a deterministic `MockLLM`; it measures
  memory-strategy behavior, not frontier-model reasoning quality.
- No token advantage on tiny two-step scenarios due to governed-context
  formatting overhead.
- Scenarios are synthetic, designed to isolate state-governance failures.

### Not in this release (by design)

- No FastAPI service, no database, no UI.
- No long-run (10–20 step) benchmarks yet — planned for the next iteration.
