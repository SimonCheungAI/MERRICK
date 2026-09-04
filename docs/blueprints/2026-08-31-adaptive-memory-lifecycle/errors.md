# Error Strategy

## Phase 3 — Taxonomy

| Code | Condition | Safe behaviour |
|---|---|---|
| `MEMORY_LIFECYCLE_DB_UNAVAILABLE` | SQLite cannot open/write lifecycle table | Keep last valid active card; continue conversation |
| `MEMORY_LIFECYCLE_INVALID_KEY` | Key fails host validation | Ignore lifecycle mutation; do not broaden to a generic key |
| `MEMORY_LIFECYCLE_INVALID_VALUE` | Empty, oversized or sensitive value | Reject candidate/activation |
| `MEMORY_LIFECYCLE_MIGRATION_FAILED` | Additive table/index creation fails | Existing memory store remains usable |
| `MEMORY_ACTIVE_PROJECTION_FAILED` | Card/snapshot update fails | Do not update OpenClaw wiki; retain previous projection |
| `MEMORY_FORGET_PARTIAL` | Card revocation succeeds but lifecycle cleanup fails | Card stays revoked; retry cleanup later without serving old value |

## Logging

- Log error code, preference key, stage and exception class.
- Never log preference value, raw episode text, voice data or wiki body.
- OpenClaw sync failure remains non-fatal and cannot roll back local authority.

## Recovery

- Table creation is retried on the next store connection.
- Existing cards are sufficient to reconstruct active lifecycle rows if needed.
- A corrupt lifecycle row is ignored rather than exposed to the prompt.
- Rollback is `git revert`; additive unused tables may remain harmlessly.
