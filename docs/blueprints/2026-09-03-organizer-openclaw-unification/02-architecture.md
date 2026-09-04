# Phase 2 — Architecture

## Pattern

Extend the existing **modular monolith** with a domain-owned synchronization adapter. Microservices are rejected: the Organizer, FastAPI coordinator, native app, and app-owned OpenClaw Gateway all run on one Mac and need low-latency, inspectable local state.

## Ownership

| Component | Owns | Does not own |
|---|---|---|
| Organizer SQLite | Tasks, projects, due dates, priorities, reminder intent, local receipts | OpenClaw job execution state |
| TaskAutomationService | Mutation orchestration, idempotency, outbox, reconciliation, truthful result envelopes | Natural language planning |
| OpenClaw Gateway | Automation scheduling, tool execution, automation run history | Canonical task title/status |
| `jarvis-organizer` plugin | Typed OpenClaw task tools backed by the host API | Direct database access or gateway credentials |
| Native host | macOS notification scheduling/delivery, visible panel | Task semantics or model decisions |
| Web HUD | Assistant view, sync state, actionable retry controls | Authority to manufacture success |

## Component diagram

```text
Voice / text / Assistant panel / OpenClaw agent
                    │
                    ▼
          Task intent + typed task tool
                    │
                    ▼
       TaskAutomationService (FastAPI)
        ├─ OrganizerStore ───────────────► jarvis-organizer.db
        ├─ Local notification bridge ────► macOS notification centre
        ├─ transactional outbox ─────────► task_automation_outbox
        └─ GatewayAutomationPort ────────► OpenClaw Gateway RPC
                                               │
                                               ▼
                                      OpenClaw cron / run history
                                               │
                           linked IDs + status │
                                               ▼
                                  reconciler → Assistant projection
```

## Key flow: “Tomorrow: A, B, C; remind me at 09:00, 13:00, 16:00”

1. The task-intent adapter extracts three items and their explicit local dates/times. Ambiguous fields remain unset rather than guessed.
2. One SQLite transaction creates tasks, reminder intents, automation-link rows in `pending`, audit receipts, and outbox records.
3. The Assistant panel immediately renders the three local tasks as **saved**.
4. The outbox submits one linked automation per requested reminder through the Gateway port and registers macOS notification delivery.
5. Returned OpenClaw job IDs are stored on the matching links. Only then does the receipt become **scheduled**.
6. If Gateway sync fails, tasks remain visible as saved with **OpenClaw sync pending** and are retried; the answer must say exactly that.

## Key flow: OpenClaw asks to create or complete a task

1. The model calls `jarvis_tasks_mutate`, provided by the bundled plugin.
2. The plugin makes a localhost authenticated request to TaskAutomationService using an app-issued capability token; it does not open SQLite or invoke generic cron directly.
3. The service performs the same transaction/outbox workflow and returns the durable receipt.
4. The model may report only receipt state returned by the tool.

## Reconciliation

- At application launch and after a Gateway reconnect, list linked OpenClaw jobs by stable job ID.
- Gateway job state updates the link projection (`scheduled`, `paused`, `completed`, `missing`, `failed`) but never overwrites the Organizer task status by itself.
- A completed task disables/cancels linked future automations through an outbox operation.
- A missing job marks the binding degraded and offers retry; it never silently recreates a job without its original task binding and idempotency key.
- Unlinked native OpenClaw jobs are shown in the Assistant as **external automations**, so users can see them without pretending they are tasks.

## Performance and portability

The SQLite write happens synchronously in a worker thread; Gateway work is queued. The service is independent of AppKit and may later be reused by Windows/Linux notification adapters. The native app only consumes typed events.
