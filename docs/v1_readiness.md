# v1.0 readiness checklist

> **Status: v1.0.0 released — Stable Governed-State Runtime.** The public
> runtime, middleware, policy-pack, CLI, benchmark, service, dashboard, and
> evaluation surfaces are frozen for the v1.x series. See
> [`api_stability.md`](api_stability.md) and [`claims.md`](claims.md).

v0.9 hardened AnchorPrune ahead of v1.0; v1.0 stabilizes it. Neither release
**expands the method** — no new governance logic, no new benchmark claims, no new
UI features, no cloud layer, no auth/RBAC. This checklist frames what "1.0"
requires and where the project stands.

## Status legend

- **Done** — complete and verified in v0.9.
- **Partial** — in place but with documented limitations.
- **Planned** — targeted for v1.0.

## Checklist

| Area                      | Item                                                                                 | Status                                         |
| ------------------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------- |
| Public API stability      | Stable error taxonomy + `{"error": {code, message, details}}` shape                  | Done                                           |
| Public API stability      | List endpoints paginated (`limit`/`offset`/`total`) without breaking existing fields | Done                                           |
| Public API stability      | Versioned API prefix (e.g. `/v1`)                                                    | Planned                                        |
| Schema stability          | SQLite migrations with `schema_migrations` + idempotent runner                       | Done                                           |
| Schema stability          | Documented snapshot/state JSON schema                                                | Partial                                        |
| Benchmark reproducibility | Deterministic benchmark byte-identical, mock-only                                    | Done                                           |
| Benchmark reproducibility | Real-model eval clearly observational, metadata pinned                               | Done                                           |
| Observability             | Structured logging (human + JSON), secret redaction, configurable level              | Done                                           |
| Config                    | Friendly config validation with suggestions                                          | Done                                           |
| Docs completeness         | Docs index, security notes, per-feature docs                                         | Done                                           |
| Examples runnable         | Examples + offline mock eval run without keys                                        | Done                                           |
| Package install verified  | `python -m build` + wheel import + policy-pack YAML included                         | Done                                           |
| Import boundaries         | Core install avoids FastAPI/OpenAI/Anthropic/LangGraph/LlamaIndex                    | Done                                           |
| Dashboard                 | `npm run typecheck` + `npm run build` pass                                           | Done                                           |
| Local deployment          | Dockerfile + docker-compose for API + dashboard                                      | Done                                           |
| CI                        | GitHub Actions: python, packaging, dashboard                                         | Done                                           |
| Security                  | `doctor` diagnostics; "do not expose publicly" documented                            | Done                                           |
| Security                  | Authentication / RBAC                                                                | Planned (explicitly out of scope until needed) |

## Known limitations carried into v1.0 planning

- No authentication/authorization; the service is local-first only.
- SQLite-only storage; no Postgres/remote backend.
- The deterministic evaluator is phrase-matching; a model-based judge would be
  non-canonical.
- The API is unversioned (no `/v1` prefix yet); pagination was added
  backward-compatibly to avoid a breaking change before v1.0.

## What "1.0" means for AnchorPrune

A dependable, installable, observable, and documented governed-state-pruning
library + local service whose **deterministic benchmark is the canonical source
of truth**, with stable public contracts (errors, pagination, schema) and a
clear, honest scope.
