# Internal Contracts

## Phase 3 — Store contract

No new network endpoint is required. These are in-process application/storage
contracts.

### `record_preference_candidate`

```python
record_preference_candidate(
    preference_key: str,
    value: str,
    *,
    source_episode_id: int | None = None,
    confidence: float = 0.55,
) -> str
```

Returns `candidate` or `proposed`. Repeated exact canonical evidence increments
`evidence_count`; the store may promote to `proposed` at the configured
threshold. It never activates a preference.

Errors: invalid key/value returns no row; SQLite errors are handled at the host
boundary and do not block conversation.

### `activate_preference`

```python
activate_preference(
    preference_key: str,
    value: str,
    *,
    revision_id: str,
    confidence: float = 1.0,
) -> None
```

Transactionally supersedes prior lifecycle rows for the key and upserts the
new active value. The active JSON card is still written by host policy.

### `forget_preference`

```python
forget_preference(preference_key: str) -> None
```

Deletes lifecycle evidence for the key. The host separately records a revoked
materialized card so the old value cannot reappear through legacy fallback.

### `preference_candidates`

```python
preference_candidates(*, limit: int = 6) -> list[str]
```

Compatibility read for internal review only. Ordinary preference answers must
not call it.

## Serving contract

### `active_preference_context(language)`

- Input: selected conversation language.
- Output: at most eight current values and 700 characters.
- Excludes revoked, superseded, candidate and proposed values.
- Contains no change history or narration instructions.

### `recall_long_term_context(user_text)`

- For an ordinary history question, returns bounded episode/fact context.
- For a current-preference question, returns active values only.
- Must not append candidate tendencies or earlier preference episodes to a
  current-preference answer.

## Acknowledgement contract

When the current turn explicitly changes a preference, model instructions must
require a concise, forward-looking acknowledgement. They forbid:

- “You used to prefer …”
- “You like X rather than Y …”
- a list of stored fields
- mentioning memory levels, cards or internal storage

The preferred effect is silent behavioural adaptation; acknowledgement is
limited to the directly requested result.
