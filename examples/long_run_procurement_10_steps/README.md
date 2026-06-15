# Example: long_run_procurement_10_steps

## What this shows

A 10-step procurement evaluation of two suppliers. The focus is **context
growth** over a multi-step run: AnchorPrune keeps the composed context below
naive full-history while preserving the critical compliance anchor.

## Command

```bash
anchorprune run --input examples/long_run_procurement_10_steps/scenario.json
```

Compare strategies with:

```bash
anchorprune benchmark --input examples/long_run_procurement_10_steps/scenario.json
```

## Expected output

Per-step metrics showing bounded context growth relative to full-history, with
the critical compliance anchor retained across all steps.

## What not to claim

This shows **bounded context growth and anchor retention** on a deterministic
scenario. It does not show that any supplier recommendation is correct. See
[`../../docs/claims.md`](../../docs/claims.md).
