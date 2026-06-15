# Real-Model Evaluation (v0.8)

> Real-model evaluation is observational. Deterministic benchmarks remain
> canonical.

## Purpose

The real-model evaluation harness runs AnchorPrune and the three memory
baselines against real or mock LLM providers and records what happens. It exists
to *observe* how each memory strategy changes the context a model receives — and
the model's resulting answer — on real providers, without disturbing the
canonical deterministic benchmark.

> Real-model evaluation measures how different memory strategies affect the
> context shown to a model and the model's resulting answer. It does not prove
> that AnchorPrune improves the underlying model.

## Why real eval is observational

Real LLM output is non-deterministic. Provider, model version, temperature,
prompt drift, network conditions, and safety layers can all change a result.
Therefore v0.8 makes **no** claim that AnchorPrune improves model intelligence,
makes GPT/Claude reason better, or guarantees real-model correctness. The honest
claim is narrow and verifiable:

> AnchorPrune changes what reaches the model by governing state before the model
> call.

## Difference between deterministic benchmark and real eval

| | Deterministic benchmark (`benchmarks/`) | Real eval (`real_eval_results/`) |
|---|---|---|
| LLM | Fixed `MockLLM` | Real or mock provider |
| Reproducible | Byte-for-byte | Only the *context* is; answers may vary |
| Canonical | **Yes** | No (observational) |
| Network | Never | Optional (openai/anthropic) |
| Purpose | Prove governance behavior | Observe provider behavior |

The deterministic benchmark is the source of truth for AnchorPrune claims. Real
eval is a complementary, observational lens.

## Methods compared

1. **full_history** — all history/payloads composed into the prompt; no
   quarantine, no pruning.
2. **sliding_window** — only the most recent N messages; can forget early
   critical anchors.
3. **summary** — deterministic heuristic summary of all messages (not a
   model-written summary, for comparability).
4. **anchorprune** — the policy-pack-aware governed runtime composes the context.

Context composition is deterministic for all four methods; only the provider's
answer to that context is observational.

## Metrics

- **context_validity_rate** — did the strategy place the required facts (and no
  forbidden/adversarial content) into the context shown to the model?
- **model_answer_validity_rate** — given that context, did the model's answer
  satisfy the scenario's decision rules? (`N/A` when no decision rules exist.)
- **adversarial_contamination_rate** — share of trials whose context carried an
  adversarial payload.
- **constraint_violation_rate** — share of trials whose answer contained a
  forbidden phrase.
- **required_anchor_mention_rate** — fraction of required phrases mentioned in
  the answer.
- **forbidden_content_mention_rate** — share of trials mentioning forbidden or
  adversarial content in the answer.
- **variance_across_trials** — sample variance of answer validity (0 when
  deterministic).

Context validity and model-answer validity are deliberately separate: a governed
context can still yield a poor answer, and a contaminated context can still yield
a lucky-correct one.

## Running mock eval (offline, no API keys)

```bash
anchorprune real-eval \
  --provider mock \
  --model mock-deterministic \
  --scenarios coding_agent,contract_review \
  --trials 3 \
  --out real_eval_results
```

## Running provider eval

```bash
pip install -e ".[openai]"
export OPENAI_API_KEY=...
anchorprune real-eval \
  --provider openai \
  --model gpt-4.1-mini \
  --scenarios coding_agent,contract_review \
  --policy-pack auto \
  --trials 5 \
  --out real_eval_results
```

```bash
pip install -e ".[anthropic]"
export ANTHROPIC_API_KEY=...
anchorprune real-eval \
  --provider anthropic \
  --model claude-3-5-sonnet-latest \
  --scenarios contract_review \
  --trials 3 \
  --out real_eval_results
```

A missing optional SDK or API key produces a friendly, actionable error — it
never crashes the harness, and the test suite never requires real providers.

## Output files

```
real_eval_results/
  results.json        # RealEvalSummary: per-trial results + aggregates
  report.md           # observational report (clearly not canonical)
  metadata.json       # pinned provider/model/temperature/trials/policy packs
  raw_outputs/<scenario>/trial_001_<method>.txt
  contexts/<scenario>/trial_001_<method>_context.txt
```

`metadata.json` always records `"canonical_benchmark": false` and
`"observational": true`.

## Interpreting results

- Read **context validity** and **adversarial contamination** first — that is
  where governance shows up and is the most reliable signal.
- Read **model answer validity** as observational: it depends on the provider and
  may vary across trials and dates.
- Use **variance_across_trials** to judge how stable a provider's answers were.

## Limitations

- Real model outputs may vary across calls, even at temperature 0.
- Provider model versions may change without notice.
- The evaluator is deterministic phrase-matching; it does not judge reasoning
  quality. A model-based judge (`--judge-provider`, `--judge-model`) is described
  as an interface only and would be non-canonical.
- The deterministic benchmark remains the canonical AnchorPrune benchmark.

## Reproducibility notes

- The mock provider is fully deterministic and offline; mock runs are
  reproducible.
- For provider runs, **do not compare results across dates or model versions
  unless metadata is pinned.** `metadata.json` exists precisely so a run can be
  pinned and cited.
- Real eval writes only under its `--out` directory and never modifies
  `benchmarks/`.
