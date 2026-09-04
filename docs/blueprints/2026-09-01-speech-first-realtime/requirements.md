# Requirements

## Functional requirements

| ID | Requirement | Acceptance condition |
|---|---|---|
| FR-001 | Put voice feedback ahead of model/planner latency for every complete spoken turn that needs a response. | The backend emits a cached, local cue before turn-understanding, prior-turn cancellation wait, model dispatch and action planning. |
| FR-002 | Preserve action capability and concurrency. | The cue changes neither `run_query` routing nor OpenClaw request arguments; action/research work starts without waiting for cue playback. |
| FR-003 | Keep acknowledgements semantically honest. | Conversation cues do not assert research/action success; action/research cues only say that work is starting. |
| FR-004 | Keep true model text streaming. | First answer clause enters incremental TTS immediately after its natural punctuation boundary; no whole-answer wait is introduced. |
| FR-005 | Measure the entire foreground path. | Structured timing marks exist for input receipt, cue availability, cue playback start, model first delta, first answer clause queued and first answer audio ready. |
| FR-006 | Preserve interruption. | A new stable transcript sends `audio_cancelled` with a higher turn and cannot play an old cue or answer. |

## Non-functional requirements

| ID | Target |
|---|---|
| NFR-001 | Cached cue becomes available in <50 ms and begins device playback within 250 ms on a warm WebKit audio path. |
| NFR-002 | Cue dispatch adds no awaited network/model/TTS work before `run_query` starts. |
| NFR-003 | First substantive answer audio is targeted below 1.5 s after model first delta when local incremental synthesis is active. |
| NFR-004 | No increased audio clipping, duplicate responses or self-interruptions. |

## Constraints and assumptions

- The existing AppKit host, WebSocket and `web/app.js` audio queue remain the
  delivery path; no second audio process or IPC hop is added.
- The existing OpenClaw Gateway remains app-owned and warm. No new provider or
  model is selected here.
- Local cached assets are the only foreground cue source. If one is missing,
  the response must continue normally rather than blocking or synthesising one
  on the critical path.
- Existing user-selected language/address behaviour is preserved.

## Dependencies

- `server/main.py`: turn lifecycle and timing marks.
- `server/tts.py`: cached cue lookup and natural-boundary chunking.
- `web/app.js`: existing serialized playback and playback-start event.
- `tests/test_session_action_execution.py` and `tests/test_tts.py`.

## Resolved design choices

- Use a short neutral acknowledgement for conversation turns rather than a
  fake answer. This makes speech feel immediate without inventing content.
- Do not wait for the acknowledgement to finish before dispatching OpenClaw.
- Do not reduce first-clause quality by cutting words or punctuation-free text.
