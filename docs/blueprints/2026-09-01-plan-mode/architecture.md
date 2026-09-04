# Architecture

## Pattern

Plan Mode is a review workflow beside the existing per-turn conversation route.
`Session` remains the compatibility entry point: it asks a tool-free OpenClaw
router whether an eligible work turn is direct or a reviewed plan, delegates
state to a coordinator, and sends typed contract events.

```text
Eligible spoken or typed task
   -> OpenClaw planning router (tool-free)
   -> direct -> existing main execution route
   -> plan   -> PlanDraft -> independent Plan panel

Plan panel goal (manual or edited)
   -> plan_mode_create WebSocket event
   -> Session compatibility delegate
   -> PlanModeCoordinator
      -> OpenClaw planning adapter (no tools) -> PlanDraft
      -> PlanModeCoordinator                     -> in-session plan state
   -> plan_mode_state WebSocket event
   -> independent Plan panel

Choose approach
   -> PlanModeCoordinator -> Organizer adapter
   -> one Organizer project + selected step task records
   -> organizer_snapshot (does not force the panel open)

Run next / Run all (Slice 1)
   -> PlanModeCoordinator
   -> existing OpenClaw main-session capability route
   -> plan_mode_step events -> panel and matching Organizer task completion
   -> ordinary model answer events remain ordinary answer events
```

## Responsibility boundaries

| Component | Owns | Does not own |
|---|---|---|
| `plan_mode.py` | Draft parsing, auto-route decision, selected approach, ordered state transitions and Organizer task identifiers | FastAPI/WebSocket transport, model-specific HTTP, DOM or desktop actions |
| `OpenClaw planning adapter` | Return either a direct-route decision or a structured tool-free plan | Plan ordering, UI state, Organizer persistence or action policy |
| `Organizer adapter` | Create selected-plan work records and complete matching records | Planning decisions or tool execution |
| Future Task Flow adapter | Durable status/revision/child-task lifecycle after Slice 2 | User presentation or tool interpretation |
| `Session` | Message compatibility, per-session coordinator wiring and event send callback | Plan business logic |
| `web/plan-mode.js` | Isolated panel rendering, local selection and typed outgoing events | Normal transcript, speech recognition, TTS or point-cloud rendering |
| `web/app.js` | Existing socket dispatch calls into the plan panel module | Plan DOM implementation |

## Execution semantics

1. For an eligible work turn, OpenClaw's tool-free router returns either
   `direct` or a structured plan. A router error uses the normal direct route.
2. The planner receives a goal and emits JSON only. It cannot call tools.
3. The selected approach is displayed and materialized as Organizer work before
   any execution begins.
4. `Run next` executes precisely the first pending step. `Run all` repeatedly
   executes the next pending step until a terminal status, cancellation, or a
   blocked/failed step.
5. Each execution prompt carries the goal, selected approach and current step;
   it uses the normal OpenClaw main-session tool route. No MERRICK
   pre-filter limits which configured capabilities the step may use.
6. Slice 1 holds only live per-session state and delegates a selected step to
   the unchanged main OpenClaw route. Slice 2 replaces that compatibility
   runner with Task Flow for restart-safe state and cancellation.

## Compatibility and rollback

- The automatic router affects only eligible work turns and fails open to the
  previous direct route. Manual Plan Mode remains available as an explicit UI
  affordance.
- A `PLAN_MODE_ENABLED` compatibility switch can hide the panel and reject new
  Plan Mode messages while leaving all ordinary routes unchanged.
- Rollback is L1 `git revert` or L2 setting that switch false; no data schema
  migration occurs in Slice 1.

## Future extension points

- persisted resume/history view backed by Task Flow lookup;
- plan editing and re-planning from a failed step;
- task dependencies/parallel branches;
- scheduled plans using Task Flow plus OpenClaw automation.
