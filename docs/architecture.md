# AnchorPrune Architecture

This document walks through each component of the AnchorPrune runtime. For the
one-paragraph positioning and the central claim, see [`method.md`](method.md).

## Pipeline overview

```mermaid
flowchart TD
    IN["User goal / documents / tool outputs"] --> BP[Block Parser]
    BP --> EX[Anchor Candidate Extractor]
    EX --> EL[Evidence Linker]
    EL --> CD[Conflict Detector]
    CD --> GOV{{Anchor Governor}}

    SYS["System anchors<br/>(immutable)"] --> GOV
    GOV -->|hard gate: conflict| Q[(Quarantine)]
    GOV -->|approve| REG["Hybrid Anchor Registry<br/>System / Domain / Runtime"]

    REG --> US[Utility Scorer]
    US --> PR[Anchor-Aware Pruner]
    PR --> ME[Milestone Extractor]
    PR --> SG[(Governed State Graph)]
    ME --> SG
    SG --> CC[Context Composer]
    CC --> LLM[LLM / agent step]
    LLM --> AUD[Audit Log + Metrics]
    LLM -->|new outputs| BP
```

Each agent step runs this loop (`anchorprune/core/runtime.py`,
`AnchorPruneRuntime.run_step`):

1. Parse new inputs into payload blocks.
2. Extract candidate anchors and link evidence.
3. Detect conflicts and pass candidates through the governor.
4. Score utility and prune the state graph.
5. Compose a governed context and call the LLM.
6. Record audit events and metrics.

## Governed State Graph

`anchorprune/core/state_graph.py` — `GovernedStateGraph`.

The state graph is the single source of truth for a run. It holds:

- **Anchors** keyed by id, partitioned into system / domain / runtime classes.
- **Payload blocks** — tool outputs, retrieved chunks, model outputs, drafts —
  each with a `pruning_state` (`ACTIVE`, `COMPRESSED`, `QUARANTINED`, `EVICTED`).
- **Evidence references** linked to anchors and payload blocks.
- **Conflict edges** between candidates and existing anchors.
- **Milestones** — compressed, durable reasoning checkpoints.

Unlike a transcript, the graph is **mutated by governance**: objects change
status as the run proceeds rather than simply accumulating.

## Hybrid Anchor Registry

`anchorprune/anchors/registry.py` — `HybridAnchorRegistry`.

Anchors come in three classes with different survival rules:

| Class       | Source                       | Mutability | Lifetime                 |
| ----------- | ---------------------------- | ---------- | ------------------------ |
| **System**  | Human-defined                | Immutable  | Whole run; never evicted |
| **Domain**  | Trusted docs/tools, reviewed | Reviewable | Whole run                |
| **Runtime** | Discovered during the run    | Soft       | Expires at run end       |

The separation is the safety boundary: a model can influence runtime anchors,
but it cannot promote anything to a system anchor.

## Anchor Governor

`anchorprune/anchors/governor.py` — `AnchorGovernor`.

The governor is the heart of the method. A model may _propose_ candidate
anchors; it may not directly create critical ones. Every candidate is evaluated
in two stages:

1. **Pre-scoring hard gate.** If a candidate conflicts with a critical system
   anchor (including override attempts such as "ignore the policy"), it is
   **quarantined** immediately with weight `0` and reason
   `CRITICAL_CONFLICT_WITH_SYSTEM_ANCHOR`. It never reaches scoring.
2. **Anchor weighting equation.** Surviving candidates are scored:

   ```
   anchor_weight = αA·authority + αR·risk + αE·evidence + αT·relevance
                   + αF·freshness − βC·conflict − βV·volatility
   ```

   The weight maps to a decision: approve as domain anchor, approve as runtime
   anchor, retain as milestone, or reject. Thresholds and coefficients are
   **per-domain** (`anchorprune/domains/profiles.py`).

Supporting modules:

- `anchors/extractor.py` — heuristic candidate extraction (directive and
  override cues).
- `anchors/weighting.py` — authority ladder, freshness sensitivity by anchor
  type, and the weighting equation.
- `conflicts/detector.py` — override-attempt and polarity-conflict detection.
- `evidence/linker.py`, `evidence/scorer.py` — evidence linking and reliability.

## Anchor-Aware Pruner

`anchorprune/pruning/pruner.py` — `AnchorAwarePruner`; utility in
`pruning/utility.py`; compression in `pruning/compression.py`.

The pruner decides each payload block's fate, in priority order:

1. **Preserve** — linked to a critical/system anchor (non-evictable).
2. **Quarantine** — flagged as conflicting or an override attempt.
3. **Compress** — useful but verbose, or moderate utility → produces a milestone.
4. **Evict** — low utility, obsolete, redundant, or noise.

Utility combines decision impact, evidence strength, anchor linkage, recency,
redundancy, and obsolescence, scored against per-domain thresholds.

## Context Composer

`anchorprune/core/context_composer.py` — `ContextComposer`.

Composes the prompt from the **governed** state, in a fixed section order:

```
system_anchors → domain_anchors → runtime_anchors → milestones
→ active_payload → goal → step_instruction → output_schema
```

Critical system anchors are always included. Remaining sections are filled by
utility under the domain token budget; quarantined and evicted blocks are never
composed. This is where "what is allowed to matter" is enforced.

## Audit Log + Metrics

`anchorprune/core/audit.py` — `AuditLog`.

Every governance decision (anchor approved, candidate quarantined, block
evicted, milestone created) is recorded as an audit event, and per-step metrics
(token counts, state summary, pruning summary) are tracked on the runtime.
`anchorprune inspect --run-id <id>` renders this trail.

## Domains

`anchorprune/domains/profiles.py` — built-in profiles `default`, `procurement`,
`coding_agent`, `healthcare`, `compliance`. A profile sets the weighting
coefficients, decision thresholds, and token budget. Governance is therefore
_tunable per domain_ rather than relying on universal constants.

## LLM interface

`anchorprune/llm/base.py` defines `LLMClient`; `llm/mock.py` provides the
deterministic `MockLLM` used by tests and the benchmark. Real model clients can
be added behind the same interface without touching the governance pipeline.

## Adapter layer (v0.3)

v0.3 makes each stage of the pipeline selectable between a deterministic
heuristic (the default, and the benchmark's basis) and a model-based adapter.
The constitutional rule is enforced in code, not just documented:

> **Deterministic governance remains the source of truth. Model-based adapters
> may propose, enrich, or compress state, but they do not bypass the Anchor
> Governor.** LLM proposes. Anchor Governor disposes.

### Adapter packages

- **LLM** — `anchorprune/llm/`: formal `LLMRequest` / `LLMResponse` /
  `LLMClient.generate`. `complete()` is kept as a backward-compatible wrapper so
  the runtime/benchmark are byte-identical. Adapters: `MockLLM` (default),
  `EchoLLM` / `CallableLLM` (local, dependency-free), optional `OpenAILLM` /
  `AnthropicLLM` behind import guards.
- **Embeddings** — `anchorprune/embeddings/`: `EmbeddingClient`, deterministic
  `HashEmbeddingClient`, optional `OpenAIEmbeddingClient`.
- **Anchor extractors** — `anchorprune/anchors/extractors/`: `AnchorExtractor`
  with `Heuristic` / `ModelBased` / `Hybrid`. The model-based extractor emits
  `CandidateAnchor`s only and forces a `model_*` source — it can never
  self-promote to a trusted source or create an approved anchor. Every candidate
  still passes through the Anchor Governor.
- **Conflict detectors** — `anchorprune/conflicts/detectors/`: `ConflictDetector`
  with `Heuristic` / `ModelAssisted` / `Hybrid`. **Hard gates are heuristic and
  authoritative.** Model edges are always non-critical; the hybrid detector
  preserves every heuristic critical edge and never lets a model add or clear a
  system-anchor hard gate. The governor's pre-scoring hard gate
  (`conflicts/detector.py`) remains the enforcement point.
- **Compressors** — `anchorprune/pruning/compressors/`: `Compressor` with
  `Heuristic` (default, reproduces the v0.1/v0.2 summary) and `ModelBased`.
  `enforce_linkage()` rebuilds the compressed block from the source, so
  `linked_anchor_ids`, `evidence_refs`, and `source_block_id` are preserved
  structurally regardless of the backend.

### Config and the deterministic safety switch

`anchorprune/config/` provides `AppConfig` (`models.py`), a YAML/JSON
`loader.py`, and a `factory.py` that builds a `Pipeline` and a wired
`AnchorPruneRuntime`. When `runtime.deterministic_benchmark_mode` is true (the
default in `configs/mock.yaml`), the factory forces every stage to its heuristic
implementation and the provider to `mock` — a config can never contaminate the
benchmark with a real model, randomness, or the network. The CLI exposes this
via `anchorprune run --config <file>`.

Optional provider SDKs are never required by a core install: importing an
adapter module is always safe, and only constructing a real client needs its
extra (`anchorprune[openai]`, `anchorprune[anthropic]`).
