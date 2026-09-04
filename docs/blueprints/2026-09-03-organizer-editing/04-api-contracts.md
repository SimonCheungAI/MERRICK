# Phase 3 — API Contracts

## WebSocket: `organizer_update_task`

```json
{"type":"organizer_update_task","task_id":"task_…","title":"Prepare demo","due_at":"2026-09-04T09:00:00.000Z"}
```

- `due_at` may be `null` to remove a due time.
- Success: canonical Organizer snapshot.
- Errors: `organizer_error` with validation or missing-task message.

## WebSocket: `organizer_update_reminder`

```json
{"type":"organizer_update_reminder","reminder_id":"reminder_…","fire_at":"2026-09-04T09:00:00.000Z"}
```

- Success: old notification cancel event, replacement schedule event,
  canonical Organizer snapshot.

## Loopback OpenClaw bridge

- `action: "update_task"`: `taskId`, `title`, `dueAt`.
- `action: "update_reminder"`: `reminderId`, `fireAt`.

Both return `{ok:true, localState:"committed", ...}` only after SQLite writes
succeed. The existing secret header authenticates the bundled plugin.
