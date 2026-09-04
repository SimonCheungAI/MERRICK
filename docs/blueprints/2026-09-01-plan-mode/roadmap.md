# Incremental roadmap

## Slice 1 — Auto-draft, work projection and in-session execution (this change)

User-visible outcome: speak or type a multi-step task, receive an automatic
reviewable plan when OpenClaw judges it useful, then select, revise, or execute
it. Selected steps appear in Assistant work management and remain in-session
rather than restart-durable.

- Add pure Plan Mode domain types/parser and tests.
- Add typed websocket events, a small adapter seam and ordered step runner.
- Add an independent responsive panel and event dispatch.
- Add the direct-or-plan OpenClaw router and selected-plan Organizer projection.
- Rollback: hide via `PLAN_MODE_ENABLED=false` or revert this slice.

## Slice 2 — Durable Task Flow execution

User-visible outcome: an active approach survives gateway restart with durable
step status, revision tracking and cancellation.

- Replace the compatibility runner with an OpenClaw managed Task Flow
  controller adapter while retaining the same configured main-session
  capabilities.
- Add cancellation/restart/revision-conflict coverage.
- Rollback: disable execution controls but retain draft inspection.

## Slice 3 — Resume and edit

User-visible outcome: reopen recent Plan Mode runs, retry/re-plan a failed
step, and edit a goal without losing the earlier audit trail.

- Expose Task Flow lookup and re-plan derived draft/history.
- No changes to normal turn loop.

## Release gates

- Unit and integration tests pass without a live gateway.
- Existing action and voice test suites remain green.
- Native macOS build verifies.
- Desktop visual review confirms expanded/closed panel behaviour.
