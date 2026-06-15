# Example: long_run_contract_15_steps

## What this shows

A 15-step contract/compliance review. The focus is **context growth** over a long
run: AnchorPrune keeps the composed context below naive full-history while
preserving critical compliance anchors.

## Command

```bash
anchorprune run --input examples/long_run_contract_15_steps/scenario.json
```

Compare strategies with:

```bash
anchorprune benchmark --input examples/long_run_contract_15_steps/scenario.json
```

## Expected output

Per-step metrics showing bounded context growth relative to full-history, with
critical anchors retained across all steps.

## What not to claim

This shows **bounded context growth and anchor retention** on a deterministic
scenario. It does not show legal correctness of any decision. See
[`../../docs/claims.md`](../../docs/claims.md).
