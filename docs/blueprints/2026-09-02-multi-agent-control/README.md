# MERRICK Multi-Agent Control Plane

## Summary

- Complexity: Complex feature inside the existing modular monolith.
- Verdict: PROCEED.
- Estimated effort: five thin vertical slices; two to three focused engineering days.
- Scope: deterministic OpenClaw persistent-session spawning, durable run
  observation, accurate Plan Mode outcomes, and a responsive in-app Agent
  Board with direct terminal navigation and per-agent lifecycle controls.

## Feasibility

OpenClaw 2026.8.1 already provides `sessions_spawn`, `agents_wait`, a durable
task ledger, cancellation, and task events. MERRICK already owns an authenticated
loopback Gateway RPC connection and a WebSocket UI. The feature therefore needs
an adapter and presentation layer, not a second agent runtime.

The current failure is architectural rather than provider-related: Plan Mode
routes orchestration prose back through generic intent detection, catches local
Library errors as spoken notices, and then marks the step successful merely
because the coroutine returned. The replacement must make OpenClaw receipts and
terminal task records the only source of truth.

The control extension is feasible without a second runtime. OpenClaw visible
children are persistent sessions: every accepted receipt includes the exact
`sessionUrl`, and the same session can receive later instructions in the native
Control UI. Closing is a recoverable archive operation guarded by the durable
`sessionId`; OpenClaw fences admission and cancels that exact session before the
archive commits.

## Package

- `requirements.md`
- `architecture.md`
- `data-model.md`
- `api-contracts.md`
- `errors.md`
- `risk-register.md`
- `roadmap.md`
- `validation.md`

Implementation may begin after the validation checklist passes. This package
passes with the bounded warnings recorded in `validation.md`.
