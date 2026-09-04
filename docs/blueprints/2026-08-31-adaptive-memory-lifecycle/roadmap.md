# Roadmap

## Phase 4 — Thin vertical slices

### Slice 1 — Latest-only answers (MVP, 2–3 hours)

Goal: current-preference questions and normal prompts contain only active
values, with no candidate or historical preference narration.

- Add failing regressions for old preference/candidate leakage.
- Filter preference recall to the active materialized view.
- Add a concise forward-only instruction for explicit preference changes.

Deliverable: changing a response-style preference affects future behaviour;
asking for current preferences cannot surface the superseded value.

Testing: focused `test_long_term_memory.py` and prompt-construction session test.

Rollback: git revert; no schema change in this slice.

### Slice 2 — Four-level lifecycle persistence (V1, 3–4 hours)

Goal: episodes, candidates, proposals and active preferences have durable local
representation without changing the serving source.

- Add the idempotent `preference_lifecycle` table and indexes.
- Add candidate aggregation/proposal threshold contract.
- Link explicit active/revoke operations to lifecycle rows.
- Remove lifecycle evidence on explicit forget.

Deliverable: a temporary SQLite integration test demonstrates L1–L4 state and
one-active-value-per-key supersession.

Testing: real temporary SQLite store tests plus existing migration tests.

Rollback: code revert; additive table may remain unused.

### Slice 3 — Proposal review experience (V2, later)

Goal: the owner can review Level 3 proposals without unsolicited or mechanical
conversation interruptions.

- Add owner-only memory-review UI or an explicit “review memory proposals” flow.
- Confirm/reject proposals with exact key/value preview.
- Paginate history and support per-key forget.

Deliverable: one candidate can be reviewed, activated or rejected without
exposing unrelated history.

Testing: UI/API integration and owner-gate tests.

Rollback: feature flag off; core latest-only serving remains.

## Sequence

Slices 1 and 2 form the current implementation. Slice 3 remains deliberately
separate because the user requested natural adaptation, not unsolicited
preference announcements.
