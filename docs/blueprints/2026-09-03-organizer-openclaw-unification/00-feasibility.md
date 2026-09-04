# Phase 0 — Feasibility

## Verdict: PROCEED

**Complexity:** Moderate. The product already has a local SQLite Organizer, an authenticated Gateway RPC client, an embedded OpenClaw runtime, a native notification bridge, and an OpenClaw plugin surface. The missing piece is a domain adapter and durable synchronization protocol, not a new platform.

**Effort:** 3 small vertical milestones, approximately 3–5 focused engineering days including packaged-app verification.

## Evidence from the incident

The 3 September conversation was retained in daily memory and Gateway logs said cron jobs were added, but `jarvis-organizer.db` contained no matching tasks/reminders and the active OpenClaw state had no jobs. The systems had separate ownership and no binding or receipt.

## Feasible architecture

- Retain the existing local SQLite Organizer as the canonical task store.
- Add an application-owned task/automation adapter and SQLite outbox.
- Bundle a small `jarvis-organizer` OpenClaw plugin that exposes typed task tools; it calls the loopback MERRICK API, never writes the database directly.
- Link reminders/recurrences to OpenClaw job IDs and reconcile their state in the background.
- Keep macOS notification scheduling as the reliable one-shot reminder channel while the application is not running; OpenClaw automations cannot fire after a full app quit because the app-owned Gateway also exits.

No external account, public server, or cloud database is required.
