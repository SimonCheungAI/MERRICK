# Error behaviour

| Condition | User-visible state | Recovery | Normal conversation impact |
|---|---|---|---|
| Planning provider unavailable | `PLAN_UNAVAILABLE` with retry control | Retry plan generation; retain typed goal | None |
| Automatic router unavailable or malformed | No Plan Mode error; continue the original direct turn | Retry via manual Plan Mode if wanted | None; it preserves the original response/action route |
| Planner emits malformed structure | `PLAN_INVALID` with retry control | Discard draft, ask planner again | None |
| Stale plan/approach selection | `PLAN_STALE` | Refresh current panel snapshot | None |
| Step execution fails | Step `failed` plus its concise error | Edit/re-plan or start a new plan | Existing answer routing remains available |
| Gateway restart during run | Step `blocked` until Task Flow status resolves | Refresh/retry/resume in later slice | No stuck speaking/listening state |
| User cancels | Plan `cancelled` | New plan or ordinary command | No later plan step begins |

Plan errors are never translated into a generic connection-stalled assistant
answer. They remain scoped to the Plan Mode panel and system log.
