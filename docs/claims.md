# Claims (v1.0)

This document freezes what AnchorPrune **does** and **does not** claim. It exists
so the project is evaluated honestly and never oversold.

> **AnchorPrune does not make models smarter. It governs what reaches them.**

## Core statement

AnchorPrune is an **application-layer governed-state pruning runtime** for
long-running AI agents. It does not summarize agent history; it governs which
state is allowed to influence future context.

- Summarization compresses text.
- AnchorPrune governs state influence.

## Allowed claims

These are accurate and supported by the deterministic benchmark and the codebase:

- AnchorPrune **governs application-layer agent state** (anchors, payloads,
  milestones, evidence, conflicts) before the model call.
- It **separates retention from influence** — state can be retained yet
  prevented from influencing the composed context.
- It **preserves critical anchors** in the deterministic benchmark scenarios.
- It **quarantines critical conflicts** (e.g. adversarial overrides of a system
  anchor) in the deterministic benchmark scenarios.
- It **keeps context growth below full-history** in long-run deterministic
  scenarios.
- It provides an **optional real-model evaluation** harness, which is
  **observational** (not the canonical benchmark).

## Forbidden claims

AnchorPrune must **not** be described with any of the following:

- Guarantees correctness of agent decisions.
- Improves an LLM's reasoning or makes a model "smarter".
- Solves long-context memory.
- Is a production-ready enterprise platform.
- Prevents all prompt injection.
- Replaces RAG or vector databases.
- Is a universal safety system.

## Why this matters

The honest, narrow claim is also the **defensible** one: AnchorPrune changes the
*input* a model receives by governing state deterministically. Anything about the
model's *output quality* is observational and provider-dependent. See
[`api_stability.md`](api_stability.md) and the canonical
[`../benchmarks/benchmark_report.md`](../benchmarks/benchmark_report.md).
