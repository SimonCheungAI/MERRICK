# Roadmap

## Slice 1 — Truthful parallel execution (MVP)

Goal: three selected independent steps create three real OpenClaw child runs
and return evidence-backed terminal states.

- Add `execution_mode` with backward-compatible sequential default.
- Enable bounded OpenClaw Swarm execution.
- Add RPC spawn/wait adapters and `MultiAgentRunController`.
- Route parallel `RUN ALL` through the controller.
- Add unit and integration coverage for accepted, rejected, failed, and partial
  runs, including the prior Library false-positive regression.

Rollback: feature switch off or revert; no data migration.

## Slice 2 — Agent Board (V1)

Goal: users can see and manage the actual run in the MERRICK HUD.

- Add compact board trigger/panel, progress rail, responsive child cards,
  empty/loading/error/terminal states, refresh and whole-run cancel.
- Preserve long labels with wrapping and internal scrolling.
- Add desktop and 390 px browser screenshots plus visual lint.

Rollback: hide board while Slice 1 continues headlessly.

## Slice 3 — Recovery and packaged proof (V1)

Goal: reconnect, restart, and installed-app behavior remain truthful.

- Reconcile active state from `tasks.list` and task events.
- Build/install the signed app and repeat a real three-child task.
- Verify three distinct child ids, overlapping execution, aggregation,
  cancellation, no orphan process, and final HUD state.

Rollback: disable multi-agent switch; existing sequential Plan Mode remains.

## Slice 4 — Per-agent stop (V1)

Goal: the owner can terminate exactly one active child while siblings continue.

- Add run/child-scoped cancel command and controller transition.
- Resolve immutable run id to exact OpenClaw task id before cancellation.
- Add compact STOP control with cancelling and error states.
- Integration-test sibling preservation and completion races.

Rollback: hide per-card STOP; whole-run cancellation remains available.

## Slice 5 — Manual and dynamic launch (V1)

Goal: the owner can start an agent from the board or append one before an
active run reaches its completion barrier.

- Add validated inline label/task form and background command task.
- Recompute the controller wait set so appended children join synthesis.
- Enforce combined eight-child cap and keep prompts out of snapshots.
- Repeat desktop/390 px visual QA and a real launch/stop Gateway test.

Rollback: hide NEW AGENT; Plan Mode orchestration remains unchanged.

## Later

- Persistent historical run browser, provider-supported child steering, nested
  orchestrators, per-agent model/cost controls, and cross-device workers.

## Slice 6 — Persistent terminals and close lifecycle (V1)

Goal: every rendered Agent is a persistent OpenClaw session the owner can enter
and continue controlling, then close independently.

- Replace rendered ephemeral spawns with `visible:true` persistent sessions.
- Persist and validate the receipt's exact `sessionUrl`; render ENTER TERMINAL
  on every accepted child.
- Replace active-only STOP with always-present CLOSE. Resolve the durable
  session generation and archive it through OpenClaw before hiding the card.
- Reconcile results from the task ledger and bounded session history without
  blocking the WebSocket or voice loop.
- Verify same-session navigation, follow-up control, running/terminal close,
  sibling isolation, desktop/390 px layout, and packaged-app behavior.

Rollback: disable the board or revert Slice 6; sequential Plan Mode remains.
