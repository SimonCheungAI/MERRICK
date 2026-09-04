# Adaptive Memory Lifecycle Blueprint

Status: validated for implementation on 2026-08-31.

## Phase 0 — Feasibility

- **Complexity:** Moderate. The change crosses owner-gated persistence,
  retrieval, prompt construction and OpenClaw projection, but remains inside
  the existing local modular monolith.
- **Effort:** Three thin slices, approximately 1–2 engineering days including
  migration and regression tests.
- **Verdict:** **PROCEED**.

The existing episode store, observation candidates and materialized memory
cards already provide most of the required seams. The missing boundary is a
durable lifecycle projection that records candidate/proposed/active state and
prevents superseded preferences from re-entering an answer through historical
retrieval.

## Package

| Document | Purpose |
|---|---|
| [requirements.md](requirements.md) | Behaviour, privacy and compatibility requirements |
| [architecture.md](architecture.md) | Components, authority and data flows |
| [data-model.md](data-model.md) | Additive SQLite lifecycle schema |
| [api-contracts.md](api-contracts.md) | Internal store and prompt-projection contracts |
| [errors.md](errors.md) | Fail-safe behaviour and diagnostics |
| [risk-register.md](risk-register.md) | Principal product and migration risks |
| [roadmap.md](roadmap.md) | Independently verifiable implementation slices |
| [validation.md](validation.md) | 25-point validation and implementation gate |

## Decision

The write path may retain evidence and lifecycle history. The serving path
reads one materialized latest value per preference key. Superseded values are
excluded from ordinary recall, prompt injection and OpenClaw wiki projection.
They are available only to a future explicit history-review surface; a forget
operation removes the relevant lifecycle records.

**Implementation may begin.**
