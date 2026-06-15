# Real-model evaluation example (v0.8)

> Real-model evaluation is observational. Deterministic benchmarks remain
> canonical.

This example shows how to run the observational real-model evaluation harness.
The **mock** provider runs fully offline with no API keys, so you can try it
immediately.

## Offline (mock) — works with no API keys

```bash
anchorprune real-eval \
  --provider mock \
  --model mock-deterministic \
  --scenarios coding_agent,contract_review \
  --trials 2 \
  --out real_eval_results
```

This writes:

```
real_eval_results/
  results.json
  report.md
  metadata.json
  raw_outputs/<scenario>/trial_001_<method>.txt
  contexts/<scenario>/trial_001_<method>_context.txt
```

Open `report.md` and look at the **Context Valid** and **Adversarial
Contamination** columns: AnchorPrune's governed context keeps the required
constraints and excludes the adversarial overrides, while `full_history` carries
the adversarial payloads straight into the context.

## OpenAI

```bash
pip install -e ".[openai]"
export OPENAI_API_KEY=...
anchorprune real-eval --provider openai --model gpt-4.1-mini \
  --scenarios coding_agent,contract_review --policy-pack auto --trials 5
```

## Anthropic

```bash
pip install -e ".[anthropic]"
export ANTHROPIC_API_KEY=...
anchorprune real-eval --provider anthropic --model claude-3-5-sonnet-latest \
  --scenarios contract_review --trials 3
```

## What this is (and is not)

- It **is** a way to observe how each memory strategy changes the context a real
  model sees, and the answer it produces.
- It is **not** the canonical AnchorPrune benchmark (that is the deterministic
  pack in `benchmarks/`), and it makes **no** claim that AnchorPrune improves the
  underlying model's reasoning.

See [`docs/real_model_eval.md`](../../docs/real_model_eval.md) for full details.
