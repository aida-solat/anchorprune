# Example: supplier (procurement)

## What this shows

Procurement governance on a EUR 120,000 request: a critical system anchor
("a supplier cannot be recommended without verified compliance documentation")
is preserved through the run, and conflicting/adversarial payloads do not
silently override it.

## Command

```bash
anchorprune run --input examples/supplier/scenario.json
```

## Expected output

A governed run that:
- keeps the critical compliance anchor in the composed context,
- surfaces conflicts/quarantine in the audit trail,
- reports state and token metrics per step.

Inspect a saved run with `anchorprune inspect --run-id <run_id>`.

## What not to claim

This shows **governance behavior** on a crafted scenario. It does not show that
the model's recommendation is correct, nor that AnchorPrune prevents all bad
procurement decisions. See [`../../docs/claims.md`](../../docs/claims.md).
