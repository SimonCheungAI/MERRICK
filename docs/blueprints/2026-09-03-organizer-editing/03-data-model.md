# Phase 3 — Data Model

## Entity: Task

**Table:** `tasks`  
**Editable fields:** `title` (1–300 cleaned characters), `due_at` (nullable
ISO-8601 instant).  
**Identity/status:** stable `task-*` ID; UI edits only rows where
`status='open'`.

`updated_at` is rewritten on every successful edit. Existing indexes on
`status,due_at` remain sufficient for Work Calendar and overview ordering.

## Entity: Reminder

**Table:** `reminders`  
**Editable field:** `fire_at` (required ISO-8601 instant).  
**State change:** an edit sets `notification_state='pending'` and clears
`delivered_at`; it is allowed only while `status='pending'`.

The reminder keeps the same ID, so native notification cancellation and
rescheduling refer to one stable identifier.
