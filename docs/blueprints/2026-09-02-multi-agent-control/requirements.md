# Requirements

## Functional requirements

- FR1: A parallel Plan Mode approach launches one real, visible OpenClaw child
  session per independent work step and records every accepted `runId`, session
  key, and Control UI URL.
- FR2: A launch rejection fails that child and the overall run; it must never be
  rendered as completed.
- FR3: MERRICK reconciles the durable task ledger asynchronously while the UI
  remains responsive, then reads the visible session result and maps it to its
  plan step.
- FR4: The main MERRICK agent receives the bounded child outputs and produces one
  final synthesis after all children are terminal.
- FR5: The Agent Board shows aggregate progress and child label, status, elapsed
  time, result/error, and session identity.
- FR6: Users can open/close the board, refresh it, inspect completed children,
  and cancel an active run.
- FR7: Sequential plans continue to use the existing runner.
- FR8: Planner output describes actual work units and declares `sequential` or
  `parallel`; it must not create fake spawn/wait/merge work steps.
- FR9: Plan and Organizer status reflect accepted/terminal OpenClaw state only.
- FR10: Restart/reconnect restores visible task state from the OpenClaw ledger.
- FR11: English and Chinese labels remain usable without clipping.
- FR12: The owner can launch a manual persistent agent when no run is active.
- FR13: The owner can append a persistent agent to an active run while the run remains
  below the eight-child admission cap; final synthesis waits for that child.
- FR14: Every child card always exposes CLOSE. Closing one child archives that
  exact OpenClaw session (and therefore cancels its active/queued work) without
  changing siblings or deleting MERRICK evidence.
- FR15: Every accepted child card exposes ENTER TERMINAL. It opens the receipt's
  validated `sessionUrl` route using OpenClaw's short-lived native bootstrap
  handoff on the currently owned loopback Gateway, where the owner can inspect
  history and continue issuing instructions to the same persistent session
  after an app restart without manually copying a token.
- FR16: A missing `sessionUrl` produces an explicit unavailable state rather
  than fabricating a dashboard route.

## Non-functional requirements

- NFR1: Starting the board or refreshing status performs no network search and
  creates no new work.
- NFR2: First board update appears within 250 ms of an accepted spawn receipt.
- NFR3: A run of up to eight children remains usable at narrow desktop widths.
- NFR4: All list regions scroll internally; buttons retain stable dimensions.
- NFR5: Child task text and results are treated as untrusted data and rendered
  with `textContent`, never HTML.
- NFR6: No Gateway token, tool arguments, hidden reasoning, or raw transcript is
  exposed to the browser.
- NFR7: Cancellation and duplicate-run requests are idempotent.
- NFR8: Existing conversation, voice, Organizer, and sequential Plan Mode tests
  remain green.
- NFR9: Manual task input is capped at 4,000 characters and is never echoed in
  board snapshots; launch, open, and close commands are owner-session scoped.
- NFR10: Only loopback HTTP(S) Control UI URLs returned by OpenClaw may cross
  the native open-URL boundary.

## Implicit requirements checked

- Pagination: not needed for the live board; the bounded view holds one selected
  plan with at most eight children. Historical paging remains OpenClaw-owned.
- Error/empty/loading states: required.
- Notifications: existing voice/action progress is reused; no new email channel.
- Mobile: not a product target, but the panel must work at a 390 px test width.
- Admin panel: Agent Board is the bounded owner control surface; OpenClaw
  Control UI remains the cross-session operator surface.
- Uploads: not in scope.
- Audit: OpenClaw task/run identifiers and local plan transition traces provide
  correlation without duplicating raw task content.
- Soft delete: CLOSE archives the OpenClaw session and hides the card while the
  MERRICK run retains a tombstone; OpenClaw can restore the session later.
- Audit: child launch and stop retain immutable OpenClaw run/task identifiers.

## Constraints and assumptions

- Use the installed OpenClaw runtime and authenticated loopback RPC bridge.
- Visible sessions require `sessions_spawn` and Control UI availability.
- Children are isolated, flat leaves; nested swarms are outside this slice.
- Manual children join only an active `starting`/`running` run; terminal or
  synthesizing runs are immutable and a manual launch starts a new run.
- Child outputs are bounded before synthesis and UI delivery.
- Existing user changes in the dirty worktree must be preserved.

## Dependencies

- OpenClaw `sessions_spawn`, `sessions_list`, `sessions_history`, `tasks.list`,
  and `sessions.patch`.
- MERRICK `OpenClawGatewayRPC`, `PlanModeCoordinator`, Organizer, and HUD WebSocket.

## Resolved decisions

- OpenClaw is authoritative for execution state; MERRICK does not maintain a
  competing child-process registry.
- Parallel execution is explicit plan metadata, not inferred from step wording.
- User-followable work uses `visible:true` persistent sessions. Hidden
  collectors remain appropriate only for internal work that is never rendered
  as a user-controllable Agent card.
