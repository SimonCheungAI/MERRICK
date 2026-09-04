# Phase 4 — Development Roadmap

## Milestone 1 — Truthful local task capture (MVP, 1 day)

- [ ] Add bulk task-intent parsing for natural Mandarin/English day lists.
- [ ] Add receipt and idempotency tables/migration to `OrganizerStore`.
- [ ] Return Assistant snapshots and evidence-based speech for local writes.
- [ ] Regression-test the exact 3 September three-task request.

**Deliverable:** “Tomorrow: A, B, C” creates three local Assistant tasks and never claims reminders exist unless they do.

## Milestone 2 — Linked OpenClaw automation (MVP, 1–2 days)

- [ ] Add `GatewayAutomationPort` to the existing authenticated RPC client.
- [ ] Add automation-link/outbox store and reconciler.
- [ ] Bundle `jarvis-organizer` plugin with typed task tools that use the host service.
- [ ] Add OpenClaw prompt/tool guidance and plugin contract tests.

**Deliverable:** a task reminder has one visible OpenClaw job ID, retry state, and run projection.

## Milestone 3 — Unified control surface (V1, 1–2 days)

- [ ] Show linked and external automation sections in Assistant.
- [ ] Add pause/resume/retry/complete controls and bilingual copy.
- [ ] Add startup reconciliation and post-run state update.
- [ ] Add packaged-app end-to-end test: create, restart, list, complete, and verify no duplicate job.

**Deliverable:** MERRICK and OpenClaw manage one visible operational picture without hidden cron jobs.

## Later

- External task-provider adapters (Todoist/TickTick/Asana) use the same task port and binding model.
- Recurrence, dependencies, assignees, and shared projects stay outside this repair until local semantics are proven.
