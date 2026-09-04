# Phase 1 — Requirements

## Functional requirements

| ID | Requirement | Acceptance condition |
|---|---|---|
| FR-1 | Natural English and Chinese task requests, including a list for a day, create separate Organizer tasks. | “Tomorrow: A, B, and C” produces three visible tasks. |
| FR-2 | One request may carry priority, project, due time, and reminder time per item. | Parsed fields are shown before/with the receipt; no silent invented schedule. |
| FR-3 | MERRICK Organizer and OpenClaw share stable bindings for linked reminders, recurring work, and automation runs. | A task card shows local state plus linked automation state and job ID. |
| FR-4 | Host voice/text commands and OpenClaw agent tools use the same application service. | Creating, completing, rescheduling, or listing through either path changes one ledger. |
| FR-5 | A completed task cancels/suppresses its linked future reminder; a cancelled automation never deletes the task. | State transitions are deterministic and visible. |
| FR-6 | The Assistant panel shows open tasks, due times, local notification state, OpenClaw schedule state, and a recoverable sync error. | No hidden cron-only task exists. |
| FR-7 | A spoken confirmation is evidence-based. | “Saved and scheduled” is emitted only after durable Organizer and Gateway receipts exist. |
| FR-8 | Existing generic OpenClaw automations remain available and are displayed as external automations when unlinked. | The integration does not remove the full OpenClaw tool profile. |
| FR-9 | Reconciliation restores bindings after restart and never creates duplicate jobs. | Repeating a request with the same idempotency key results in one task and at most one active linked job. |

## Non-functional requirements

| ID | Target |
|---|---|
| NFR-1 | Local task write and Assistant refresh under 250 ms, excluding model parsing. |
| NFR-2 | Task requests show a visible “saving” state within 100 ms. |
| NFR-3 | Gateway sync starts asynchronously and does not block normal dialogue or TTS. |
| NFR-4 | Restart reconciliation completes within 10 s of a healthy Gateway. |
| NFR-5 | Logs contain IDs and state only; they never contain gateway tokens or raw private task details beyond the existing local audit retention policy. |

## Constraints and resolved conflicts

- The user wants OpenClaw broadly capable. The solution does **not** remove its native `automations` tool. Instead, personal task requests use a stronger canonical MERRICK tool and generic jobs remain visible as unlinked external automations.
- The user also requires a full quit to stop the app. Therefore an embedded Gateway cannot be the only source of one-shot reminder delivery; macOS notification scheduling remains part of a completed reminder receipt.
- This is single-owner, local macOS software. SQLite and loopback authenticated APIs are appropriate; no remote multi-tenant service is introduced.
