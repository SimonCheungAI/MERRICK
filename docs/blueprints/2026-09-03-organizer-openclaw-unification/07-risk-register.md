# Phase 4 — Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---:|---:|---|
| Gateway ends when the app fully quits | Certain | High for Gateway-only reminders | Register macOS notification separately; display execution availability honestly. |
| Model calls generic `automations` instead of task tool | Medium | Medium | Canonical plugin tool, prompt guidance, reconciliation displays unlinked jobs, and no success claim without receipt. |
| Voice final event repeats | Medium | High duplicate risk | Idempotency key per semantic request and receipt replay. |
| Gateway restart during outbox dispatch | Medium | Medium | Persist pending row before RPC; reconcile job ID before retry. |
| Manual Control UI edits linked job | Medium | Medium | Detect revision/state mismatch; mark conflict rather than overwriting. |
| Plugin/runtime version drift | Medium | Medium | Versioned contracts and capability health check during startup. |
| Notification authorization denied | Low | Medium | Store task regardless; surface delivery-disabled state and retry guidance. |

## Explicit non-goals

- Replacing OpenClaw’s scheduler.
- Letting an arbitrary OpenClaw agent directly mutate Organizer SQLite.
- Pretending the app can deliver Gateway automations after a user-selected full quit.
