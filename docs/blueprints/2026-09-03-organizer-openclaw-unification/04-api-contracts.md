# Phase 3 — API and Tool Contracts

All interfaces are loopback-only, authenticated by the existing native bridge/plugin capability, schema-validated, and unavailable to arbitrary browser pages.

## Application service contract

### `create_tasks`

**Purpose:** atomically persist one or many personal tasks and enqueue requested reminder/automation links.

```json
{
  "items": [
    {
      "title": "Practise LeetCode interview patterns",
      "dueAt": "2026-09-04T09:00:00+01:00",
      "priority": "high",
      "projectTitle": null,
      "reminder": {"at": "2026-09-04T09:00:00+01:00"}
    }
  ],
  "idempotencyKey": "owner-turn-derived-key",
  "source": "voice"
}
```

**Success:** `201` with ordered task IDs and one receipt describing `localState` and `automationState`.

### `complete_task`, `update_task`, `list_tasks`, `retry_task_automation`

These expose task IDs or a bounded title resolver, never raw SQL. Every mutation returns the same receipt shape. Lists support `status`, date range, project, and cursor pagination.

## OpenClaw plugin tools

| Tool | Effect | Arguments | Result invariant |
|---|---|---|---|
| `jarvis_tasks_create` | local R1 write | `items[]`, `idempotencyKey` | returns Organizer receipt; no invented scheduled state |
| `jarvis_tasks_list` | R0 read | filters, cursor | returns task/link projections |
| `jarvis_tasks_update` | local R1 write | task ID, patch, idempotency key | creates sync outbox when schedule changes |
| `jarvis_tasks_complete` | local R1 write | task ID | schedules linked automation cancellation |
| `jarvis_tasks_retry_sync` | local R1 write | link/receipt ID | retries only the identified failed operation |

The `automations` tool remains available for generic OpenClaw workflows. The system prompt says personal tasks/reminders must use `jarvis_tasks_*`, and only tool receipts may be quoted as saved/scheduled evidence.

## Events to the HUD

| Event | Payload |
|---|---|
| `organizer.task_receipt` | operation, task IDs, local/automation states, compact message |
| `organizer.automation_link_changed` | task ID, provider, job ID, status, retry action |
| `organizer.external_automations_changed` | paginated unlinked jobs summary |
| `organizer.sync_health` | Gateway health, pending count, last successful reconciliation |

## Error response envelope

```json
{
  "ok": false,
  "error": {
    "code": "OPENCLAW_SYNC_PENDING",
    "message": "Task saved locally; OpenClaw scheduling will retry.",
    "receiptId": "tor_...",
    "retryable": true
  }
}
```
