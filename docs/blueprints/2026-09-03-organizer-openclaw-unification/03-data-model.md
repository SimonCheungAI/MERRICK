# Phase 3 — Data Model

Existing `tasks`, `reminders`, and `projects` remain intact. All timestamps are ISO-8601 UTC with the user’s IANA timezone retained for display and schedule evaluation.

## Entity: Task automation link

**Table:** `task_automation_links`  
**Description:** One Organizer task’s relationship to one OpenClaw automation or notification operation.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `tal_` UUID |
| task_id | TEXT | FK tasks, indexed | Canonical task |
| reminder_id | TEXT | FK reminders, nullable | Exact reminder intent when applicable |
| provider | TEXT | `openclaw` or `macos_notification` | Execution surface |
| external_id | TEXT | nullable, unique with provider | OpenClaw job/notification ID |
| desired_revision | INTEGER | >= 1 | Latest local intent revision |
| applied_revision | INTEGER | >= 0 | Revision confirmed by provider |
| status | TEXT | indexed | `pending`, `scheduled`, `paused`, `completed`, `missing`, `failed`, `cancelled` |
| last_error_code | TEXT | nullable | Stable, non-secret code |
| last_synced_at | TEXT | nullable | Provider observation time |
| created_at / updated_at | TEXT | required | Audit ordering |

**Rules:** a linked OpenClaw reminder may not exist without an Organizer task; provider failure cannot delete or complete the task.

## Entity: Task automation outbox

**Table:** `task_automation_outbox`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `tao_` UUID |
| link_id | TEXT | FK link, indexed | Target relationship |
| operation | TEXT | indexed | `create`, `update`, `pause`, `resume`, `cancel`, `reconcile` |
| idempotency_key | TEXT | unique | Derived from link + desired revision + operation |
| payload_json | TEXT | bounded | Typed schedule data; no token |
| state | TEXT | indexed | `pending`, `running`, `succeeded`, `retryable_failed`, `terminal_failed` |
| attempts / next_attempt_at | INTEGER / TEXT | required | Bounded exponential retry |
| created_at / updated_at | TEXT | required | Durable recovery |

## Entity: Task operation receipt

**Table:** `task_operation_receipts`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | User-visible receipt ID |
| operation | TEXT | indexed | create/complete/reschedule/bulk-create |
| task_ids_json | TEXT | required | Ordered created/affected tasks |
| local_state | TEXT | required | `committed` or `failed` |
| automation_state | TEXT | required | `not_requested`, `pending`, `scheduled`, `degraded` |
| idempotency_key | TEXT | unique | Safe retry across voice replays |
| created_at | TEXT | required | Receipt history |

## Indexes and migration

- `task_automation_links(task_id, status)` and `(provider, external_id)` support panel and reconciliation reads.
- `task_automation_outbox(state, next_attempt_at)` supports bounded background draining without N+1 reads.
- Migration is additive, transactional, and idempotent. Existing tasks receive no automatic external job; their `automation_state` is `not_requested`.
