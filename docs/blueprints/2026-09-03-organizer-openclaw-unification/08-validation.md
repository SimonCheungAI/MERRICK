# Phase 5 — Validation

## Architecture quality check

| Check | Result | Evidence / resolution |
|---|---|---|
| S1 | Pass | Link/outbox status and provider IDs are indexed. |
| S2 | Pass | Panel reads tasks with batched link projections. |
| S3 | Pass | Cache only Gateway automation snapshots; canonical SQLite remains fresh. |
| S4 | Pass | Durable state is SQLite/outbox, not session memory. |
| S5 | N/A | Single-owner local app; service port is replaceable if a host process is separated later. |
| S6 | Pass | Gateway work is queued off the request/TTS path. |
| SEC1 | Pass | Loopback API uses app-issued authenticated bridge capability. |
| SEC2 | Pass | Only the verified local owner bridge/plugin can mutate personal tasks. |
| SEC3 | Pass | Typed schema validates titles, dates, priorities, IDs, and pagination. |
| SEC4 | Pass | No secrets stored in task rows; tokens remain existing secret refs. |
| SEC5 | Pass | Existing Gateway token/keychain strategy is reused. |
| SEC6 | N/A | No internet-facing authentication endpoint. |
| M1 | Pass | New service/port/store/plugin boundaries are explicit. |
| M2 | Pass | Conversation parsing, task domain, sync port, and UI projection are separate. |
| M3 | Pass | Plugin depends on host contract; host does not import plugin code. |
| M4 | Pass | Retry/backoff and provider configuration are externalized. |
| M5 | Pass | Receipt IDs, link IDs, and stable error codes are logged. |
| M6 | Pass | Every failure maps to an actionable user-visible state. |
| P1 | Pass | 100 ms visible save; 250 ms local write targets defined. |
| P2 | Pass | Existing bounded SQLite connection-per-operation pattern remains appropriate. |
| P3 | Pass | Task/external automation lists use cursors. |
| P4 | N/A | No new static-asset delivery. |
| C1 | Pass | `jarvis_tasks_*` and `organizer.*` names are consistent. |
| C2 | Pass | One receipt/error envelope serves host, plugin, and HUD. |
| C3 | Pass | UTC ISO storage plus IANA display/schedule zone. |

## Validation plan before release

1. Unit test bulk parsing, idempotency, migration, outbox retry, and completion cancellation.
2. Contract-test the plugin against a fake authenticated host service and the Gateway RPC port.
3. Integration-test task create → job link → restart → reconcile → complete → automation cancellation.
4. Packaged-app test from `/Applications`: create the exact three tasks, assert task panel rows, job IDs, notification registration, and truthful response on forced Gateway failure.
5. Verify full quit leaves no app-owned Gateway process and that the UI does not imply Gateway delivery remains active.

**Result: PASS WITH ONE OPERATIONAL LIMIT.** OpenClaw schedules require the embedded Gateway to be running; macOS notification state must remain separately visible for full-quit reminder delivery. This limit is resolved in the architecture rather than hidden from the user.

## Implementation gate

All required phases pass. **Implementation may begin.**
