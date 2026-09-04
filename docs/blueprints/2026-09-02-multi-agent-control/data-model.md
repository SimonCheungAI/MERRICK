# Data model

## Plan changes

```text
PlanApproach
  execution_mode: sequential | parallel (default sequential)
```

## MultiAgentRun

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID string | required | MERRICK correlation id |
| plan_id | UUID string | required | selected plan |
| group_id | string | required, <=160 chars | MERRICK correlation group |
| goal | string | required, <=4000 chars | display/synthesis goal |
| status | enum | queued/running/synthesizing/succeeded/partial/failed/cancelled | aggregate truth |
| created_at | ISO-8601 UTC | required | consistent timestamp |
| updated_at | ISO-8601 UTC | required | latest transition |
| children | tuple | 1..8 | selected work units |
| summary | string | <=12000 chars | final visible synthesis |
| error | string | <=1000 chars | actionable aggregate failure |

## MultiAgentChild

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | string | unique within run | plan step id |
| label | string | required, <=120 chars | user-facing work label |
| task | string | required, <=8000 chars | delegated brief, server-only |
| status | enum | queued/starting/running/cancelling/succeeded/failed/timed_out/cancelled | OpenClaw-derived |
| run_id | string or null | immutable after receipt | OpenClaw child run |
| child_session_key | string or null | immutable after receipt | OpenClaw child session |
| session_url | string or null | immutable after receipt | exact loopback Control UI URL |
| session_id | string or null | immutable when resolved | lifecycle generation guard |
| task_id | string or null | immutable when known | task ledger id |
| closed | bool | default false | hide card after archive commit |
| started_at | ISO-8601 UTC or null | optional | accepted start |
| ended_at | ISO-8601 UTC or null | optional | terminal time |
| result | string | <=8000 chars | bounded child output |
| error | string | <=1000 chars | bounded failure |

## Invariants

- `succeeded` requires an accepted receipt and a successful task-ledger result.
- Every `run_id` belongs to exactly one child.
- Aggregate success requires all children succeeded and synthesis completed.
- Aggregate partial requires at least one successful and one unsuccessful child.
- Cancellation never rewrites a previously terminal child.
- Planner text cannot directly set execution status.
- Child count never exceeds eight, including owner-added children.
- `instruction` remains process-private and is omitted from persisted/browser
  snapshots; restored runs cannot silently retry a missing instruction.
- Dynamic children belong to the current run id and OpenClaw sidebar group.
- `closed=true` requires a committed archive; a UI click alone cannot hide it.
- Browser-openable URLs must be exact receipt values on a loopback HTTP origin.

No additional SQLite table is introduced in this slice; OpenClaw's task ledger
is the durable store and the plan/board snapshot is a bounded presentation model.
