# Risk Register

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---:|---:|---|
| R-01 | Old preference returns through episode retrieval | High | High | Current-preference questions bypass raw episode/candidate output |
| R-02 | Incidental statement silently changes behaviour | Medium | High | Candidates/proposals never serve without owner confirmation |
| R-03 | Explicit correction leaves two active values | Medium | High | Transactionally supersede by stable preference key |
| R-04 | Forget revokes card but leaves retrievable evidence | Medium | High | Exclude preference history by default and delete lifecycle rows on forget |
| R-05 | Model mechanically narrates preference storage | Medium | Medium | Prompt contract requires silent adaptation or short forward acknowledgement |
| R-06 | Migration damages existing private memory | Low | Critical | Additive idempotent schema only; temporary-DB integration tests |
| R-07 | OpenClaw wiki becomes a second authority | Low | High | One-way projection from active cards; no reverse activation path |
| R-08 | Lifecycle values leak into logs | Low | High | Log keys/counts only; tests inspect prompt and projection boundaries |
| R-09 | Dirty worktree changes are overwritten | Medium | High | Patch only targeted functions/files; inspect diff before handoff |
| R-10 | Candidate accumulation becomes noisy | Medium | Medium | Stable keys, bounded values, review-only serving and future retention policy |

## Rollback

- **L1:** revert code/tests/docs; additive SQLite table is ignored by old code.
- **L2:** if activation bookkeeping fails, existing card projection remains the
  serving fallback.
- No destructive data migration or remote state change is required.
