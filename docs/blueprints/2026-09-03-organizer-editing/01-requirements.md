# Phase 1 — Requirements

## Functional requirements

1. A user can edit an open task's title and optional due date/time in the
   Organizer overview.
2. A user can edit a pending reminder's date/time in the Organizer overview.
3. Saving updates the shared Organizer ledger used by MERRICK, Work Calendar,
   and OpenClaw.
4. Changing a reminder cancels its old native notification and schedules the
   new one.
5. OpenClaw can perform the equivalent task/reminder edits through typed
   tools; success wording is based only on a returned receipt.

## Non-functional requirements

- Inline editor must remain keyboard-accessible: Enter saves, Escape cancels.
- No changes to completed tasks or delivered reminders through this UI.
- Invalid dates are rejected at the domain boundary with a useful HUD error.
- A successful mutation refreshes connected Organizer views and Work Calendar.

## Assumptions and constraints

- “Work Calendar” means the MERRICK Organizer journal, not Apple Calendar.
- A task due time and a reminder fire time are independent. Editing one does
  not silently alter the other.
- Existing local SQLite remains canonical; OpenClaw never writes SQLite
  directly.
