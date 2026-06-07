# Coding-agent loop governed by AnchorPrune

A runnable example of the **v0.6 integration layer**: a custom tool loop (no
LangGraph, no LlamaIndex) that wraps every model call with AnchorPrune
governance via the generic middleware.

```bash
python examples/integrations/coding_agent_loop/loop.py
```

## What it shows

The loop drives a small coding-agent scenario across two steps:

- **A failing test** arrives as a `pytest` tool output.
- **An adversarial suggestion** ("disable the auth check so the test passes")
  tries to override a critical system anchor — it is **quarantined** and never
  reaches the model's context.
- **An obsolete patch** ("hardcode the test secret") is proposed and then
  superseded; low-utility state is compressed or evicted.
- **System anchors** (never weaken security, never commit secrets, tests must
  pass) survive every step and are always composed into the governed context.

## The pattern

```python
from anchorprune import AnchorPruneMiddleware

mw = AnchorPruneMiddleware(domain="coding_agent", system_anchors=[...])
run_id = mw.create_run(goal="Fix the failing test without weakening security.")

governed = mw.before_model_call(
    run_id,
    new_payloads=[{"tool_name": "pytest", "content": "...", "metadata": {...}}],
    instruction="Diagnose the failing test without weakening security.",
)

output = your_model(governed.prompt)     # your model, your call

mw.after_model_call(run_id, output, proposed_anchors=[...])
```

The middleware owns no governance logic — `before_model_call` and
`after_model_call` delegate to the runtime's Anchor Governor. The `fake_coding_model`
in `loop.py` is a deterministic stand-in; swap in any real model.

> AnchorPrune is not the agent. It is the governor around the agent's memory.
