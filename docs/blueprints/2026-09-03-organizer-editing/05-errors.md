# Phase 3 — Error Handling

| Condition | UI/Tool result | State |
|---|---|---|
| Blank task title | `Task title is required.` | unchanged |
| Invalid/empty reminder time | `Reminder time is invalid.` | unchanged |
| Completed task or delivered reminder | `That item is no longer editable.` | unchanged |
| Unknown stable ID | `That item no longer exists.` | unchanged |
| Native notification scheduling failure | reminder remains pending; snapshot still shows the edited time | local edit preserved |

No failure is represented as “saved” unless OrganizerStore returned a row.
