# Requirements

## Functional requirements

| ID | Requirement | Acceptance condition |
|---|---|---|
| FR-001 | An expanded MERRICK HUD exposes Plan Mode without replacing the ordinary composer. | The panel opens automatically for an OpenClaw-classified segmented task and remains manually available while normal voice/text controls remain usable. |
| FR-002 | A natural-language goal produces selectable approaches. | The backend returns one to three structured approaches, each with ordered, readable steps. |
| FR-003 | Planning is separate from execution. | Generating or choosing a plan does not invoke OpenClaw tools or desktop actions. |
| FR-004 | The user can run the next pending step or all remaining steps. | The selected step(s) execute in order through the existing OpenClaw main-session route. |
| FR-005 | Progress is visible independently of answer text. | The panel shows planned, running, succeeded, failed, cancelled or blocked states and optional step result text. |
| FR-006 | Cancellation is meaningful. | Cancel stops future Plan Mode steps, asks the Task Flow adapter to cancel active work, and returns the ordinary HUD to an interactive state. |
| FR-007 | Existing capabilities are not narrowed. | Plan steps receive the same configured OpenClaw tools, GUI, browser, document and computer-use capabilities as a comparable direct user command. |
| FR-008 | OpenClaw decides whether a task benefits from a reviewed plan. | For eligible work turns it returns `direct` or a structured `plan`; a `direct` decision continues the existing execution route. |
| FR-009 | Accepted plan steps appear in work management. | Selecting an approach creates an Organizer project and one open task per selected step; completed steps complete their matching task. |
| FR-010 | A user can revise before execution. | The panel keeps the goal editable; re-planning replaces the unaccepted draft and creates no Organizer tasks until a new approach is selected. |

## Non-functional requirements

| ID | Target |
|---|---|
| NFR-001 | Opening and closing the panel requires no provider round trip. |
| NFR-002 | The planning router adds no work to greetings or ordinary conversational turns; an unavailable router immediately falls back to the existing route. |
| NFR-003 | Backend plan-state logic is independently unit-testable without FastAPI, WebSocket, a running gateway or a macOS host. |
| NFR-004 | The WebSocket contract validates unknown/invalid Plan Mode requests without corrupting current plan state. |
| NFR-005 | The panel remains scrollable and does not alter point-cloud layout or the three-line transcript area. |

## Explicitly out of scope for Slice 1

- Replacing OpenClaw's own tool permission model or macOS TCC prompts.
- A new local action schema, verb table, additional approval gate, or action
  capability whitelist.
- Rewriting the existing voice interruption, research Display or native host.
- Scheduling plans for future execution; Task Flow remains available for a
  later scheduling slice.

## Dependencies

- `server/main.py`: compatibility WebSocket boundary and session lifecycle.
- New `server/plan_mode.py`: plan domain/application workflow.
- `server/openclaw_client.py`: OpenClaw planning/execution adapter seam.
- `web/index.html`, `web/plan-mode.js`, `web/style.css`: panel and typed event
  presentation.
- The existing OpenClaw main-session execution route. Task Flow is the
  durability dependency for Slice 2.
