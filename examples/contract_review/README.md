# Example: contract_review (policy pack)

## What this shows

Contract-review governance driven by the built-in `contract_review` policy pack:
liability/threshold anchors are seeded by the pack and preserved, and conflicting
clauses are surfaced as the run decides whether the contract can be approved.

## Command

```bash
anchorprune run --input examples/contract_review/scenario.json
```

The scenario sets `"policy_pack": "contract_review"`, so the pack configures the
domain profile, seed anchors, and conflict patterns automatically.

## Expected output

A governed run that:
- seeds the pack's critical anchors (e.g. liability cap),
- preserves them in the composed context,
- records conflicts and decisions in the audit trail.

## What not to claim

This shows **governance configuration via a policy pack**. Policy packs configure
governance; they do not perform it, and this does not show that any approval
decision is legally correct. See [`../../docs/claims.md`](../../docs/claims.md).
