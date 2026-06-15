# Example: long_run_coding_20_steps

## What this shows

A 20-step coding debugging session. The focus is **context growth**: AnchorPrune
keeps the composed context below naive full-history while preserving the critical
security anchor across many steps.

## Command

```bash
anchorprune run --input examples/long_run_coding_20_steps/scenario.json
```

Compare strategies on this scenario with:

```bash
anchorprune benchmark --input examples/long_run_coding_20_steps/scenario.json
```

## Expected output

Per-step state and token metrics showing context size staying bounded relative to
full-history, with the security anchor retained throughout.

## What not to claim

This shows **bounded context growth and anchor retention** on a deterministic
scenario. It does not show model correctness or that governance fixes the bug.
See [`../../docs/claims.md`](../../docs/claims.md).
