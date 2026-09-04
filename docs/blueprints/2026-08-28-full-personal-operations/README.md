# MERRICK Full Personal Operations Blueprint

Status: validated with milestone-specific warnings; implementation may begin at Milestone 0.

Implementation progress (2026-08-28): Milestone 0 slice 1 is complete. The
existing Dashboard now receives a redacted, versioned capability snapshot for
Work, Mail, Calendar and Travel; it shows the real connection/execution state
and the R1–R3 boundary in English and Chinese. Local organizer data is delivered
before OpenClaw prewarm, and failed gateway reconnects use capped exponential
backoff. Provider connections and external execution remain disabled until the
approval kernel and OAuth/Keychain connection layer are implemented.

Capability-adapter assessment (2026-08-29): the pinned OpenClaw 2026.7.1
runtime reports 69 plugins and 54 skills on this Mac, but only 9 plugins are
enabled and 19 skills are ready. Google Workspace (`gog`) and IMAP/SMTP
(`himalaya`) are present only as ineligible skills with missing binaries. This
confirms that inventory, enablement and execution readiness are different
states. The next safe increment is a canonical, risk-aware capability adapter;
bulk-enabling or automatically installing marketplace results is explicitly
out of scope.

Implementation progress (2026-08-29): Capability Adapter Slice CA-1 is
complete. The live catalog now exposes separate discovery, enablement,
dependency readiness, review, connection and authorization states; known
mail/calendar candidates carry conservative, non-executable risk metadata.
The enriched response is explicitly feature-flagged, uses a versioned
permissions-restricted last-safe snapshot, and falls back without blocking
other assistant functions. `gog` and `himalaya` remain unreviewed and
non-executable until their later connector gates pass.

| Attribute | Decision |
|---|---|
| Project | MERRICK Full Personal Operations |
| Date | 2026-08-28 |
| Complexity | Complex |
| Verdict | PROCEED |
| Architecture | Local modular monolith with durable workflows and typed connectors |
| Delivery estimate | 4–6 weeks for a useful mail/calendar MVP; 12–18 engineering weeks for V1; public travel-booking distribution depends on provider approval |

## Feasibility

OpenClaw is a suitable orchestration foundation because it already provides typed tools, plugins, skills, isolated browser automation, persistent automations, background tasks, memory and approval-aware workflows. It is not, by itself, a complete office assistant: mail, calendar, task and travel execution still require provider credentials, stable connectors, domain policy, idempotency, user confirmation and audit.

The project is feasible as an extension of the existing MERRICK modular monolith. It must not be implemented by granting the conversational agent unrestricted host authority. “Full capability” means complete workflow coverage with narrowly scoped execution authority.

## Product boundary

MERRICK may autonomously read, search, classify, summarize and prepare work within user-configured standing rules. External communication, destructive changes, cancellations and purchases cross progressively stronger approval gates. Payment, identity verification, CAPTCHA and acceptance of legal terms remain a user handoff.

## Blueprint package

| Document | Purpose |
|---|---|
| [requirements.md](requirements.md) | Functional, non-functional and implicit requirements |
| [architecture.md](architecture.md) | Components, trust boundaries and key flows |
| [data-model.md](data-model.md) | Local entities, relationships, indexes and state machines |
| [api-contracts.md](api-contracts.md) | Local HTTP, WebSocket and OpenClaw tool contracts |
| [errors.md](errors.md) | Error taxonomy, retry and recovery behaviour |
| [roadmap.md](roadmap.md) | Thin delivery milestones with verification |
| [risk-register.md](risk-register.md) | Product, security and provider risks |
| [validation.md](validation.md) | 25-check architecture validation |

## Non-negotiable decisions

1. API-first for mail, calendar and task systems; isolated browser automation only when a stable API is unavailable.
2. The model proposes actions; the host-owned policy engine authorizes and executes them.
3. OAuth refresh tokens and provider secrets remain in macOS Keychain or a dedicated local secret broker and never enter prompts, logs or SQLite.
4. Voice recognition alone cannot authorize a purchase, legal acceptance, credential entry or sensitive outbound message.
5. Every write has an idempotency key, an audit event and, where supported, a compensation or undo path.
6. Personal Chrome is never silently attached. Browser work uses a dedicated OpenClaw profile unless the user explicitly chooses a visible handoff.
