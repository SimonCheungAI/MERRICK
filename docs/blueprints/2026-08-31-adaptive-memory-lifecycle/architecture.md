# Architecture

## Phase 2 — Pattern and rationale

Extend the accepted modular monolith. `server/local_memory.py` owns lifecycle
persistence and query filtering; `server/main.py` owns owner-gated preference
commands and prompt projection; OpenClaw receives only a derived active-state
wiki page.

No microservice, message broker, ORM or cloud memory provider is justified for
single-owner, personal-scale state.

## Component view

```text
verified owner turn
       |
       v
Session / host policy ------------------------------+
       |                                             |
       | completed turn                              | explicit set/forget
       v                                             v
LocalMemoryStore                              memory-card revision
  episodes (L1)                                     |
  observations (existing)                           |
  preference_lifecycle (L2/L3/L4 audit) <------------+
       |                                             |
       +------------------+--------------------------+
                          v
                 latest active projection
                    |              |
                    v              v
             conversation prompt   OpenClaw wiki synthesis
             (current only)        (current only)
```

## Ownership

| Component | Owns | Must not own |
|---|---|---|
| `LocalMemoryStore` | SQLite schema, lifecycle rows, latest-only filtering | Voice authority, model phrasing, OpenClaw calls |
| `server.main` memory policy | Preference keys, explicit confirmation/revocation, prompt projection | Raw SQL, OpenClaw memory authority |
| Materialized card file | Current active/revoked state for compatibility | Candidate evidence or change narration |
| OpenClaw memory-writer | Transcript/wiki indexing of bounded projections | Activation, supersession or owner authorization |

## Flow A — Explicit preference revision

1. The verified owner says a directive such as “from now on, explain technical
   questions in detail.”
2. Host policy maps it to one stable preference key.
3. The active card is atomically replaced.
4. The lifecycle store marks older rows for that key non-serving and records
   the new Level 4 active revision.
5. The preference snapshot and OpenClaw projection contain only the new value.
6. The reply acknowledges the future behaviour concisely; it does not contrast
   the old and new values.

## Flow B — Ordinary preference recall

1. The verified owner asks for current preferences.
2. The host reads active cards, not raw history.
3. Local episode search may still run for unrelated facts, but preference
   questions suppress episode snippets and unconfirmed candidates.
4. The model receives a compact current-state list only.
5. Superseded values cannot re-enter through OpenClaw because its wiki is a
   projection of the same current cards.

## Scalability and performance

- Personal-scale rows remain in one SQLite file.
- Index `(preference_key, stage, updated_at)` supports current/proposal reads.
- Writes run off the streamed voice path as today.
- Serving uses the already materialized card file, so lifecycle history size
  does not increase prompt latency.
- A future multi-host product can move the store behind a port without changing
  lifecycle semantics; no horizontal scaling is required today.

## Security and privacy

- Only the verified owner path may mutate or retrieve private preferences.
- SQL parameters are bound; keys and values remain length-limited.
- Raw conversation evidence never enters the active projection automatically.
- Sensitive tokens continue to be rejected by preference parsing.
- OpenClaw receives no lifecycle history, candidate evidence or private DB path.
- Normal logs contain keys/stages/counts, never preference values.

## Technology choices

| Layer | Choice | Rationale |
|---|---|---|
| Runtime | Existing Python/FastAPI process | No new deployment or IPC |
| Persistence | Standard-library `sqlite3` | Existing private store, transactional additive migration |
| Current projection | Existing JSON cards + Markdown snapshot | Backward compatible and deterministic |
| Tests | `unittest` + temporary SQLite | Real store semantics without live user state |
| OpenClaw | Existing memory-writer adapter | Bounded derived projection only |
