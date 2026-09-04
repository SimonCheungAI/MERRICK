# MERRICK Plan Mode

## Decision

- Complexity: **Moderate**
- Verdict: **PROCEED**
- Pattern: a modular-monolith Plan Mode workflow with a typed WebSocket
  contract, an OpenClaw planning router, and an Organizer projection. It
  enriches task turns without altering ordinary conversation or direct
  execution routes.
- Delivery: three thin vertical slices.

## Outcome

When OpenClaw identifies a task as genuinely multi-step, MERRICK opens
Plan Mode with one to three visible approaches. The user may edit the goal and
re-plan, select an approach, then run the next step or the complete selected
plan. Selecting an approach projects its steps into the Assistant Organizer;
the same records become complete as their plan steps complete.

## Architectural invariants

1. Planning never executes a tool. The user's Run next or Run all choice is
   the Plan Mode execution decision; MERRICK adds no step-by-step action
   allowlist or confirmation layer.
2. Ordinary conversation, greetings and single-step work retain their current
   routes. Router failure falls back to that route rather than blocking a turn.
3. Plan state and progress use typed Plan Mode events, never assistant answer
   deltas or TTS progress text.
4. OpenClaw remains the task and tool authority. The plan coordinator owns only
   plan state, ordering and the Organizer record projection.
5. A failed or cancelled plan is contained to its plan run and cannot leave
   the ordinary conversation loop stuck in a busy state.

## Package

1. `requirements.md`
2. `architecture.md`
3. `data-model.md`
4. `api-contracts.md`
5. `errors.md`
6. `risk-register.md`
7. `roadmap.md`
8. `validation.md`

Implementation status: architecture validation **PASS WITH WARNINGS**. Slice
1 may begin.
