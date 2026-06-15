# Release Notes

## v1.0.0 — Stable Governed-State Runtime

AnchorPrune v1.0.0 marks the first stable release of the governed-state runtime
for long-running AI agents. It **freezes** the public runtime, middleware,
policy-pack, CLI, benchmark, service, dashboard, and evaluation surfaces
established across v0.1–v0.9. It is a **stabilization** release — no new
governance logic, no new benchmark claims, no new features.

### Core statement

> AnchorPrune does not make models smarter. It governs what reaches them.

AnchorPrune is an application-layer governed-state pruning runtime for
long-running AI agents. It does not summarize agent history; it governs which
state is allowed to influence future context. Summarization compresses text;
AnchorPrune governs state influence.

### What is frozen (stable for v1.x)

- **Runtime API** — `AnchorPruneRuntime` with `run_step`, `govern_and_compose`,
  `ingest_model_output`, `add_tool_output`, and `from_policy_pack`.
- **Middleware API** — `AnchorPruneMiddleware.before_model_call` /
  `after_model_call`.
- **Policy-pack API** — `get_policy_pack`, `list_policy_packs`,
  `validate_policy_pack`.
- **CLI command set** — `run`, `inspect`, `benchmark`, `pack`, `packs
list/show/validate`, `serve`, `real-eval`, `db migrate/info`, `doctor`.
- **API service shape** — stable error envelope `{"error": {code, message,
details}}` and `limit`/`offset`/`total` pagination.

See [`docs/api_stability.md`](docs/api_stability.md). Provider adapters,
provider-backed real-model eval results, and the dashboard UI layout are marked
**experimental**.

### What is retained (unchanged)

- The **deterministic benchmark suite** remains the canonical benchmark.
- The **API service and dashboard** remain local-first inspection tools.
- The **integration layer** (middleware, LangGraph, LlamaIndex) is retained.
- **Real-model evaluation** is retained as **observational**.

### Documentation & verification

- New: [`docs/api_stability.md`](docs/api_stability.md),
  [`docs/claims.md`](docs/claims.md) (allowed vs. forbidden claims),
  [`docs/examples.md`](docs/examples.md), and
  [`docs/release_checklist.md`](docs/release_checklist.md).
- Every example ships a `README.md` (purpose, command, expected output, what not
  to claim).
- One-button offline demo: `make demo` / `scripts/demo_v1.sh`.
- Version is `1.0.0` across the package, the API `/health`, `doctor`, and the
  dashboard.

### Compatibility

Backward compatible with v0.9. This is a stabilization release: the deterministic
benchmark is byte-for-byte unchanged and no public API was removed.

## v0.9.0 — Production Hardening

AnchorPrune v0.9.0 hardens the project ahead of v1.0. It focuses on reliability,
packaging, observability, error handling, local deployment, CI, and documentation
consistency. **It introduces no new governance claims and does not change the
deterministic benchmark.**

### Core principle

> v0.9 hardens the system. It does not expand the method.

No new governance logic, no new benchmark claims, no new dashboard features, no
auth/RBAC, no multi-tenancy, no cloud layer, no policy editor, no leaderboard.

### Highlights

- **Structured logging** (`anchorprune/observability/logging.py`) — human-readable
  by default, optional JSON (`--log-format json`), configurable level, secret
  redaction, and metadata truncation so full provider outputs are never logged.
- **Stable error taxonomy** (`anchorprune/errors.py`) — `AnchorPruneError` plus
  `ConfigError`, `PolicyPackError`, `PolicyPackValidationError`,
  `ProviderUnavailableError`, `RuntimeStateError`, `StorageError`,
  `SerializationError`, `EvaluationError`, `ApiError`. The API now returns a
  stable `{"error": {"code", "message", "details"}}` shape.
- **Config validation hardening** (`anchorprune/config/validation.py`) — friendly
  errors with "Did you mean …?" suggestions for unknown providers, policy packs,
  config keys, token budgets, eval trials, temperature, and database URLs.
- **SQLite migrations** (`anchorprune/storage/migrations.py`) — a `schema_migrations`
  table and an idempotent runner (`001_initial`, `002_add_indexes`,
  `003_add_version_metadata`) plus query indexes, exposed via `anchorprune db
migrate` and `anchorprune db info`.
- **API pagination + response stability** — `limit`/`offset`/`total` on the runs,
  audit, and metrics list endpoints, added **backward-compatibly** (existing
  `runs`/`count`, `events`, `steps`/`summary` fields are preserved; the dashboard
  is unchanged).
- **`anchorprune doctor`** — diagnoses version, Python, core import, policy packs,
  optional extras, examples, and dashboard presence.
- **Docker / dev compose** — `Dockerfile`, `dashboard/Dockerfile`,
  `docker-compose.yml`, `.dockerignore`, `.env.example`, and a `Makefile`
  (`dev`/`test`/`lint`/`bench`/`build`).
- **CI workflow** — Python (lint, tests, deterministic benchmark, offline mock
  eval), packaging (`python -m build` + `twine check` + wheel import), and the
  dashboard (`npm run typecheck` + `npm run build`).
- **Packaging verification** — built-in policy-pack YAMLs ship in the wheel; local
  and generated artifacts (`real_eval_results`, `.next`, `node_modules`) do not.
- **Docs consistency** — `docs/index.md`, `docs/security.md` (do not expose the
  API publicly; local-first), and `docs/v1_readiness.md` (pre-1.0 checklist).

### Compatibility

Backward compatible and additive. The deterministic benchmark
(`anchorprune pack --out benchmarks --window 2`) is byte-for-byte unchanged. The
only response-shape change is the API error body, which moved to the stable
`{"error": {code, message, details}}` form.

## v0.8.0 — Real-Model Evaluation Harness

Adds an **optional, observational** harness that runs AnchorPrune and the three
memory baselines against real or mock LLM providers — while the deterministic
benchmark in `benchmarks/` remains the canonical source of truth. No leaderboard,
no SaaS, no required API keys, and OpenAI/Anthropic stay optional.

### Core principle

> Real-model evaluation is observational. Deterministic benchmarks remain
> canonical.
>
> AnchorPrune changes what reaches the model by governing state before the model
> call. It does **not** make the underlying model reason better, and v0.8 makes
> no such claim.

### What shipped

- **`anchorprune real-eval` command.** Options: `--provider mock|openai|anthropic|local`,
  `--model`, `--scenarios`, `--trials`, `--temperature`, `--policy-pack auto|none|<name>`,
  `--out`, `--window`, `--seed`, `--save-contexts/--no-save-contexts`,
  `--save-raw-outputs/--no-save-raw-outputs`.
- **`anchorprune.evals` package.** `models` (`RealEvalConfig`, `TrialResult`,
  `MethodAggregate`, `RealEvalSummary`), `evaluators` (deterministic), `trial`
  (context composition + single-trial execution), `runner` (provider/scenario/
  pack resolution + loop), `report`, `outputs`, and `real_eval` orchestration.
- **Four methods compared:** `full_history`, `sliding_window`, `summary`,
  `anchorprune`. Context composition is deterministic for all four; only the
  provider's answer is observational.
- **Separate validity signals.** `context_validity_rate` vs
  `model_answer_validity_rate`, plus `adversarial_contamination_rate`,
  `constraint_violation_rate`, `required_anchor_mention_rate`,
  `forbidden_content_mention_rate`, and `variance_across_trials`.
- **Provider behavior.** `mock`/`local` run fully offline with no keys;
  `openai`/`anthropic` use the optional v0.3 adapters; a missing SDK/API key
  yields a friendly, actionable error. Tests never call real providers.
- **Policy-pack-aware.** `--policy-pack auto` uses the scenario's pack or a
  built-in pack matching the scenario name; AnchorPrune's governed context is
  composed by the pack-configured runtime.
- **Output directory** (`real_eval_results/`, separate from `benchmarks/`):
  `results.json`, `report.md` (clearly observational, not canonical),
  `metadata.json` (pinned provider/model/temperature/trials/policy packs,
  `canonical_benchmark: false`, `observational: true`), plus per-trial
  `raw_outputs/` and `contexts/`.
- **Docs + example.** `docs/real_model_eval.md`, `examples/real_eval/`, and a
  README section.

### Compatibility

Fully backward compatible and additive. The deterministic benchmark
(`anchorprune pack --out benchmarks --window 2`) is byte-for-byte unchanged, and
real eval never reads-modifies-writes `benchmarks/`. The core install gains no
new dependency.

## v0.7.0 — Domain Policy Packs

Adds reusable, local, validated **domain policy packs** so a high-stakes
workflow can be governed by name (`policy_pack="contract_review"`) instead of
hand-wiring system anchors, weights, and conflict patterns per run. Closes the
v0.6 gap where unknown domains (e.g. `contract_review`) silently fell back to the
default profile.

### Core principle

> Policy packs configure governance. They do not perform governance.
>
> A pack configures the Anchor Governor, pruner, freshness scoring, and conflict
> detection. It never approves an anchor or quarantines a payload directly — the
> runtime's Anchor Governor still makes every decision.

### What shipped

- **Pack schema.** `anchorprune.policy_packs.DomainPolicyPack` — name/version,
  domain profile (weights, token budget, preserve/compress/milestone/eviction
  thresholds), system & domain anchors, freshness rules, conflict patterns,
  expected milestone patterns, and decision-context rules.
- **Loader + validator.** `load_policy_pack(path)` (YAML/JSON) and `validate_pack`
  enforce snake_case names, semantic versions, unique anchor/pattern ids, valid
  `conflicts_with` references, ordered thresholds, a critical system anchor,
  compilable regexes, and non-empty decision-context rules. Every built-in is
  validated on load.
- **Registry + 5 built-ins.** `get_policy_pack` / `list_policy_packs` over
  `procurement`, `coding_agent`, `contract_review`, `compliance`, and
  `security_review` (shipped as `policy_packs/builtins/*.yaml`).
- **Runtime application.** `AnchorPruneRuntime.from_policy_pack(...)` and
  `register_domain_anchor(...)`. A pack sets the domain profile, seeds anchors,
  and supplies conflict patterns both as extra extraction triggers and as the
  runtime `contradiction_fn` — so a matching payload is surfaced to the governor,
  which then decides.
- **Everywhere a domain goes.** `AnchorPruneMiddleware(policy_pack=…)`, the config
  `policy_pack:` field, scenario `"policy_pack"`, and `anchorprune run
--policy-pack`.
- **CLI.** `anchorprune packs list | show <name> | validate <name|path>`.
- **Benchmark.** The `contract_review` scenario is now configured by its pack
  (no more default-profile fallback); `results.json` and the report record which
  pack governed each scenario. Behavioral claims are unchanged: lost-anchor 0%,
  constraint adherence 100%, critical-conflict quarantine 100%, milestone
  retention 100%, final decision context valid.
- **Example + docs.** `examples/policy_packs/contract_review_pack_demo/`,
  `docs/policy_packs.md`, and a README section.
- **Packaging.** Built-in pack YAML files ship in the wheel via
  `tool.setuptools.package-data`. Core install adds no new dependency
  (`pyyaml` was already required); `policy_packs` imports without FastAPI.

### Compatibility

Fully backward compatible. Runs without a pack behave exactly as in v0.6.
`results.json` gains an additive `policy_packs` map; the deterministic benchmark
was regenerated and remains reproducible.

## v0.6.0 — Integration Layer for Governed Agent Workflows

Makes AnchorPrune usable _inside_ existing agent workflows — LangGraph,
LlamaIndex, custom tool loops, and coding-agent pipelines — without AnchorPrune
becoming an agent framework itself. No SaaS, no auth, no dashboard changes.

### Core principle

> AnchorPrune is not the agent. It is the governor around the agent's memory.
>
> The integration layer adds primitives, not a framework. Every adapter
> delegates to the runtime's Anchor Governor; none of them performs governance.

### What shipped

- **Generic middleware (universal).** `from anchorprune import AnchorPruneMiddleware`
  with `before_model_call(run_id, new_payloads=…, instruction=…) -> GovernedContext`
  and `after_model_call(run_id, model_output, …)`. Wrap a governed step around
  _your own_ model call. Payloads may be strings, dicts, or `PayloadBlock`s.
- **Runtime governed-step seam.** `AnchorPruneRuntime.run_step` is split into
  `govern_and_compose` (phase 1, before the model) and `ingest_model_output`
  (phase 2, after the model). `run_step` is now exactly those two phases around
  the runtime's own LLM — behaviour is byte-for-byte unchanged.
- **Tool-output ingestion helper.** `runtime.add_tool_output(tool_name, content,
metadata=…)` attributes a tool result to its source and ingests it as ordinary
  governed payload (no privilege).
- **LangGraph adapter.** `anchorprune.integrations.langgraph.AnchorPruneNode` — a
  plain callable node that composes governed context into graph state, plus an
  `observe` node that ingests the model output.
- **LlamaIndex adapter.** `anchorprune.integrations.llamaindex.AnchorPruneMemory`
  — governed memory for document/RAG workflows: `put` retrieved chunks (with
  evidence links), `get` a governed context; quarantined/evicted chunks are
  excluded.
- **Example.** `examples/integrations/coding_agent_loop/` — a runnable custom
  loop (failing test, adversarial suggestion, obsolete patch) showing what
  governance preserves, compresses, and quarantines.
- **Docs.** `docs/integrations.md` + a README Integrations section.

### Architecture notes

- `resolve_config` moved to `anchorprune.config.resolve` (neutral location;
  re-exported from `anchorprune.services` for compatibility) so the middleware
  builds runtimes without importing the persistence/service stack.
- Integration modules import only the AnchorPrune core. Importing them never
  requires LangGraph, LlamaIndex, or FastAPI (verified in the import-safety test).

### Out of scope

- competing with LangGraph/CrewAI (AnchorPrune sits _on top of_ them)
- auth / RBAC / multi-tenancy / billing / cloud deployment
- new domain policy packs (planned for v0.7)

### Compatibility & guarantees

- The deterministic benchmark is unchanged: `anchorprune pack --out benchmarks
--window 2` produces byte-identical artifacts.
- `pytest` (97 tests) and `ruff` stay green. Nine new tests cover phase-split
  parity, the tool-output helper, the middleware, and both adapters.

---

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
