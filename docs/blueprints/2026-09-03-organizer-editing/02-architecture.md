# Phase 2 — Architecture

## Pattern

Extend the existing modular monolith. UI, WebSocket handling, and the bundled
OpenClaw plugin are adapters around OrganizerStore; no new service or table is
needed.

```text
Inline Organizer editor / OpenClaw typed tool
                    │
                    ▼
       FastAPI WebSocket or loopback task bridge
                    │
                    ▼
               OrganizerStore
          ┌─────────┴─────────┐
          ▼                   ▼
      SQLite ledger    native notification refresh
          │                   │
          └──────► Organizer + Work Calendar snapshot
```

## Key flows

### Edit task

1. User opens the task card editor, changes title and/or optional due time.
2. `organizer_update_task` validates stable task ID, text, and ISO time.
3. OrganizerStore performs one SQLite update and returns the canonical row.
4. HUD receives a new snapshot; Work Calendar recomputes scheduled activity.

### Edit reminder

1. User changes a pending reminder's date/time.
2. OrganizerStore updates the reminder and resets notification state to
   `pending`.
3. Session cancels the old native notification ID, clears its local scheduling
   cache, and schedules the new time.
4. HUD receives the canonical snapshot.

## Security and performance

The existing authenticated desktop WebSocket and loopback plugin secret remain
the only mutation boundaries. Every write runs in a worker thread; no network
call is on the edit critical path. Stable IDs prevent title-based accidental
edits.
