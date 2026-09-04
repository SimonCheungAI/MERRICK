# Validation

## Architecture blueprint validation

| Category | Result | Evidence |
|---|---|---|
| Requirements | PASS | Functional/non-functional requirements and explicit Slice 1 boundary are documented. |
| Architecture | PASS | Components, dependency direction, compatibility delegate and rollback are explicit. |
| Data | PASS | Draft, approach, step and run state plus transitions are defined. |
| Contracts | PASS | New request/event schemas, validation and compatibility behaviour are defined. |
| Errors and risks | PASS | Recovery states are scoped to the Plan panel and include no new action limits. |
| Roadmap | PASS WITH WARNINGS | Slice 1 is independent; managed Task Flow execution stays a later vertical slice because it requires a plugin controller. |

## Slice 1 verification checklist

- [ ] Parser accepts valid one-to-three approach output and rejects malformed output without retaining a partial draft.
- [ ] Selecting an approach changes only Plan Mode state.
- [ ] An eligible task with a `direct` decision reaches the unchanged direct route; a `plan` decision opens the panel and does not execute tools.
- [ ] Selecting an approach creates matching Organizer work records exactly once; a succeeded step completes its matching record.
- [ ] Creating/selecting/dismissing a plan emits no `assistant_delta`, `audio`, native action or tool request.
- [ ] Unknown or stale request cannot overwrite the current draft.
- [ ] Existing session action tests remain green.
- [ ] `node --check web/app.js` and `node --check web/plan-mode.js` pass.
- [ ] Expanded desktop screenshot shows panel without covering the point cloud, mic control or Display.
- [ ] macOS release verifier passes after the slice is built.

## Slice 2 gates

- [ ] Task Flow controller creates a managed flow with goal, controller id and expected revision handling.
- [ ] Run next starts exactly one pending step; Run all stops after failure/block/cancel.
- [ ] Task Flow cancellation is requested and its resulting status is accurately displayed.
- [ ] A gateway restart can be inspected and does not wedge the normal HUD.
