# AnchorPrune: The Method

## Central technical claim

> Long-running agent reliability is limited less by how much context is
> remembered than by whether that context is **governed**. AnchorPrune treats
> agent context as a **governed state graph** in which each object's ability to
> influence the next decision is determined by explicit governance rules —
> anchor linkage, evidence, conflict status, and risk — rather than by surface
> salience.

Concretely, AnchorPrune separates two things that summarization and naive memory
conflate:

- **Retention** — whether information is kept at all.
- **Influence** — whether information is allowed into the decision context.

A full-history buffer maximizes retention and ignores influence. A summary
optimizes for compact retention and treats influence as a side effect of which
sentences "sounded important." AnchorPrune makes influence a **first-class,
auditable decision**.

## Difference from summarization

Summarization shortens text. AnchorPrune assigns **governance status** to state.

- A summary may preserve a sentence because it _sounds_ important. AnchorPrune
  preserves a state object because it is **linked to a critical anchor, trusted
  evidence, or unresolved risk**.
- A summary may include an adversarial instruction verbatim. AnchorPrune can
  **quarantine it before it reaches the final decision context**.
- A summary is lossy in an uncontrolled way. AnchorPrune's losses are
  **typed**: preserve, compress (→ milestone), quarantine, or evict — each
  recorded in the audit log.

| Dimension             | Summarization   | AnchorPrune                        |
| --------------------- | --------------- | ---------------------------------- |
| Unit of work          | Text span       | Governed state object              |
| Why something is kept | Looks important | Linked to anchor / evidence / risk |
| Handling of conflicts | None            | Hard-gate quarantine               |
| Auditability          | Low             | Every decision logged              |
| Failure mode          | Silent erasure  | Typed, inspectable pruning         |

## Anchor-weighted state retention

The decision to keep, compress, or drop a state object is driven by anchors, not
by length. Two mechanisms cooperate:

1. **The anchor weighting equation** decides whether a _candidate constraint_
   becomes a governing anchor:

   ```
   anchor_weight = αA·authority + αR·risk + αE·evidence + αT·relevance
                   + αF·freshness − βC·conflict − βV·volatility
   ```

   A pre-scoring **hard gate** intercepts anything that conflicts with a
   critical system anchor and quarantines it before scoring — so a model cannot
   weaken its own guardrails.

2. **Anchor-aware pruning** decides each _payload block's_ fate by utility and
   linkage: blocks tied to critical anchors are non-evictable; low-utility,
   obsolete, or noisy blocks are evicted; the verbose-but-useful middle is
   compressed into durable milestones.

Coefficients and thresholds are **per-domain** (procurement, coding agent,
compliance, …), reflecting that "what must not be forgotten" differs by context.

## Benchmark interpretation

The Benchmark Pack v0.1 evaluates four memory strategies — full history, sliding
window, simple summary, and AnchorPrune — across three governed-state scenarios
(two of which include adversarial override payloads) using a deterministic
`MockLLM`. Because the LLM is fixed, observed differences are attributable to the
**memory strategy**, not to model variance.

Key reading guidance:

- **Full-history decision-context validity collapsing on adversarial scenarios
  is not an information problem.** Full history retains everything but governs
  nothing, so override payloads sit in the decision context beside verified
  anchors. The deterministic evaluator therefore flags the decision context as
  invalid. The lesson: _remembering is not governing._
- **Sliding-window and summary lose anchors** because they compress or drop
  older content; the constraints an agent must never forget are exactly what
  disappears first.
- **AnchorPrune's advantage is structural, not numerical luck.** It preserves
  critical anchors, quarantines override attempts before composition, and
  retains milestones — which is why it is the only evaluated strategy that holds
  all governance metrics at once.

### What the benchmark does _not_ claim

- It does **not** claim AnchorPrune produces better prose or reasoning — the LLM
  is a stub.
- It does **not** claim token savings on short tasks; governed-context
  formatting adds overhead on two-step examples. Token advantages are expected
  in long, multi-step workflows (see the roadmap's `long_run_*` benchmarks).
- It does **not** claim the heuristics generalize to production traffic; the
  scenarios are synthetic and designed to isolate state-governance failures.

The honest framing: _in this deterministic benchmark, AnchorPrune was the only
evaluated memory strategy with a governance mechanism — it preserved all
critical anchors and maintained 100% constraint adherence across all three
scenarios, and quarantined adversarial override attempts in every scenario where
such attempts were present (`coding_agent`, `contract_review`). Baselines have
no governance mechanism, so their quarantine rate is 0% where adversarial
payloads exist and N/A where they do not._
