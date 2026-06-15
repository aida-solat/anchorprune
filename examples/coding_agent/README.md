# Example: coding_agent

## What this shows

Coding-agent governance: while fixing a failing authentication test, a critical
security constraint is preserved and an adversarial "just disable auth / skip the
check" payload is quarantined rather than allowed to influence the context.

## Command

```bash
anchorprune run --input examples/coding_agent/scenario.json
```

## Expected output

A governed run that:
- preserves the security anchor across steps,
- quarantines the adversarial override (visible in the audit trail),
- composes a context that excludes the quarantined content.

## What not to claim

This shows **what reaches the model** under governance on a crafted scenario. It
does not show that the model writes a correct fix, nor that AnchorPrune prevents
all prompt injection. See [`../../docs/claims.md`](../../docs/claims.md).
