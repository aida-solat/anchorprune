# Release Notes

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
