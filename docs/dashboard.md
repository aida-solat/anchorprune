# AnchorPrune Dashboard (v0.5)

A local, read-only Next.js dashboard for inspecting AnchorPrune governed state.
It is a **microscope for governed agent state**, not a SaaS shell.

## Purpose

The dashboard visualizes governed state. **It does not perform governance.**

> The dashboard observes governance. It does not perform governance.
>
> The UI only reads the API. It never prunes, approves anchors, detects
> conflicts, or edits policy.

It reads the v0.4 FastAPI service over HTTP and renders, for any run:

- which anchors were kept (system / domain / runtime)
- which payloads were quarantined and why
- what was compressed / evicted / kept active
- which reasoning milestones were retained
- how the context grew over steps
- which audit events occurred

## Pages

- **`/`** — project positioning and live API health (status dot + version).
- **`/runs`** — table of persisted runs (id, goal, domain, status, created /
  updated) with a link into each run.
- **`/runs/[runId]`** — the run microscope: summary cards plus tabs.

### Run detail tabs

| Tab            | Shows                                                           |
| -------------- | --------------------------------------------------------------- |
| **Graph**      | Grouped governed-state graph (anchors → milestones → payload)   |
| **Anchors**    | Class/type/priority/weight/status + class & critical filters    |
| **Payloads**   | Block type, pruning state, utility, tokens + state/flag filters |
| **Quarantine** | Quarantined blocks + conflict edges (the governance story)      |
| **Milestones** | Retained reasoning checkpoints with linkage counts              |
| **Audit**      | Expandable event timeline (raw JSON per event)                  |
| **Metrics**    | Context growth, token usage, state counts, pruning breakdown    |

## State graph

Built with [`@xyflow/react`](https://reactflow.dev). v0.5 uses a simple grouped
layout (three columns) rather than a force-directed graph:

- **Column 1 — anchors**, ordered system → domain → runtime, color-coded.
- **Column 2 — milestones**, linked back to anchors and source blocks.
- **Column 3 — payload blocks**, colored by pruning state; evicted hidden by
  default.

Edges are drawn only where the state graph declares them (payload→anchor,
milestone→anchor, milestone→source block, and conflict edges whose endpoints
resolve to real nodes). The UI never infers linkage.

## Panels

Each panel is a pure view over one slice of the `GET /runs/{id}/state`,
`/audit`, or `/metrics` response. The **Quarantine** panel is the key demo
surface: it shows payloads the Anchor Governor blocked from the decision context
and the conflict edges (including critical hard gates) that caused it.

## Metrics

Charts are built with [Recharts](https://recharts.org) from
`GET /runs/{id}/metrics` and the final state snapshot:

- **Context growth** — composed input tokens per step.
- **Token usage** — input vs output tokens per step.
- **State object counts** — anchors / payload / quarantined over steps.
- **Payload by state** — final-snapshot pruning breakdown (active / compressed /
  quarantined / evicted). The read-only API exposes pruning _state_ per block,
  not a per-step action log, so this is a snapshot breakdown.

> Charts become more informative on long-running runs. A two-step run looks
> flat by design; seed a 6–10 step run to see context growth, retention, and
> pruning trends develop.

## Local development

Start the API (v0.4):

```bash
pip install -e ".[api]"
anchorprune serve --db .anchorprune/anchorprune.db
# create some runs, e.g.
anchorprune run --input examples/supplier/scenario.json
```

Start the dashboard:

```bash
cd dashboard
npm install
npm run dev
# open http://localhost:3000
```

Point the dashboard at a non-default API URL:

```bash
NEXT_PUBLIC_ANCHORPRUNE_API_URL=http://127.0.0.1:8000
```

Verification:

```bash
npm run typecheck
npm run build
npm run lint
```

## Limitations

- **Read-only** — no mutation of governed state from the UI.
- **No auth, no RBAC, no multi-tenancy** — local-first only.
- **Not a SaaS product** — no billing, user management, or cloud deployment.
- The composed prompt is produced server-side and is not exposed by the
  read-only API in v0.5, so there is no "context preview" tab.
