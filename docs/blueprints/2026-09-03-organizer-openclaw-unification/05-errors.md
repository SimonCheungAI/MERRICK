# Phase 3 — Failure Semantics

| Code | Meaning | User-visible outcome | Recovery |
|---|---|---|---|
| `TASK_PARSE_AMBIGUOUS` | Multiple items/times cannot be paired | Ask one targeted question; write nothing uncertain | User selects or edits items |
| `ORGANIZER_WRITE_FAILED` | SQLite transaction did not commit | “I could not save that task.” | No automation is created; retry safely |
| `OPENCLAW_UNAVAILABLE` | Gateway cannot be reached | “Saved locally; OpenClaw sync is pending.” | Outbox retry after reconnect |
| `OPENCLAW_SYNC_PENDING` | Job request accepted locally but not confirmed | Same truthful partial receipt | Backoff, visible retry button |
| `OPENCLAW_JOB_MISSING` | Bound job cannot be found | Task remains visible; automation marked missing | User retry/recreate choice |
| `AUTOMATION_CONFLICT` | External job changed outside the binding | Show external state; do not overwrite it | User chooses local or external schedule |
| `NOTIFICATION_SCHEDULE_FAILED` | macOS notification was not registered | Task saved; local delivery unavailable | Retry native registration or use OpenClaw-only mode |
| `IDEMPOTENCY_REPLAY` | Final voice/text event repeats a request | Return original receipt | Do not create duplicate tasks/jobs |

## Invariants

1. A task exists only after the Organizer transaction commits.
2. A scheduled claim requires a stored provider external ID and confirmed provider state.
3. No failed task write may leave an unlinked cron job.
4. No provider error is replaced with a conversational “done.”
5. Reconciliation is read-only until a user-requested retry or a durable outbox operation is processed.
