# Phase 4 — Risks

| Risk | Mitigation |
|---|---|
| User sees stale calendar after edit | Broadcast canonical snapshot after every mutation. |
| Old reminder fires after time changes | Cancel stable notification ID before rescheduling it. |
| Task edit changes a separate reminder accidentally | Keep task due time and reminder fire time independent. |
| OpenClaw claims success without a write | Typed tool returns only OrganizerStore receipt. |
| Compact UI becomes crowded | Use existing inline editor pattern from project cards and keep it collapsible. |
