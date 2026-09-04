# Data Model

## Phase 3 — Existing entities

### Episode — Level 1

**Table:** `episodes`

Completed owner conversation evidence. Existing schema remains authoritative
for conversational recall.

### Observation

**Table:** `observations`

Existing conservative extracted evidence. Existing rows remain compatible and
may seed Level 2 candidates later.

## Entity: PreferenceLifecycle

**Table:** `preference_lifecycle`
**Description:** Reviewable lifecycle state for adaptive preferences. It is an
audit/governance record, not the prompt-serving source.

### Fields

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | INTEGER | PK, auto increment | Local identifier |
| preference_key | TEXT | NOT NULL, max 96 | Stable host-owned category |
| value_hash | TEXT | NOT NULL, 64 hex | Deduplication without indexing raw text |
| value | TEXT | NOT NULL, max 600 | Candidate/proposed/active value |
| stage | TEXT | NOT NULL | `candidate`, `proposed`, `active`, `superseded` |
| confidence | REAL | NOT NULL, 0–1 | Evidence confidence |
| evidence_count | INTEGER | NOT NULL, >=1 | Number of supporting observations |
| first_observed_at | TEXT | NOT NULL, ISO-8601 UTC | First evidence |
| updated_at | TEXT | NOT NULL, ISO-8601 UTC | Last transition/evidence |
| source_episode_id | INTEGER | nullable FK episodes | Most recent supporting episode |
| active_revision_id | TEXT | nullable, max 48 | Card revision that activated the value |

### Relationships

- A lifecycle row may reference one latest supporting episode.
- One preference key may have many historical lifecycle rows.
- At most one row per key may be `active`.

### Indexes

- Unique `(preference_key, value_hash)` for evidence aggregation.
- `(preference_key, stage, updated_at DESC)` for latest-state and proposal reads.
- `(stage, updated_at DESC)` for a future review queue.

### Business rules

- Explicit owner directives may insert directly at `active`.
- Activating one row transactionally changes other active/proposed rows for the
  same key to `superseded`.
- Candidate/proposed rows never enter ordinary prompts.
- A forget operation deletes candidate/proposed/superseded lifecycle rows for
  the key after the current card is revoked.
- Schema creation is `CREATE TABLE/INDEX IF NOT EXISTS`; no destructive
  migration is required.

## Materialized ActivePreference

**File:** `jarvis-memory-cards.json`

The existing per-key card remains the serving authority during this increment.
Only `status=active` values enter prompts. `revision_id` links the active card
to the lifecycle audit.

## Retention

- Episodes follow the existing private-memory retention policy.
- Superseded lifecycle rows are retained for owner-requested history unless a
  forget request removes the key.
- OpenClaw receives only the materialized active projection and retains no
  lifecycle rows.
