# Release Notes

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
