# Data model

No persistent database entity is required. The feature uses existing
process-local `Session` turn state and the WebSocket audio event schema.

## Entity: ForegroundVoiceTurn

**Storage:** process-local fields on `Session`; lifetime is one active turn.

| Field | Type | Constraint | Meaning |
|---|---|---|---|
| `turn` | integer | monotonically increasing | Stale-event boundary shared by text/audio/action work. |
| `cueKind` | enum/null | `conversation`, `action`, `research`, null | Presentation-only choice. |
| `fast_ack_turn` | integer | equals `turn` at most once | Prevents duplicate cue/progress speech. |
| `latency_marks` | set[string] | one mark per phase | Measurement-only, never persisted. |
| `audio_seq` | integer | increasing per emitted clip | Establishes queue ordering in the HUD. |

## Event retention

Timing marks are structured local logs associated with a turn number. They do
not store raw audio, full transcript, secrets or provider payloads. Existing
logs/retention policy applies.
