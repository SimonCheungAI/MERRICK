# Architecture

## Pattern

This is an incremental **modular-monolith foreground-lane extraction**. The
foreground lane is a presentation concern; the execution lane remains the
existing OpenClaw/model workflow. They meet only at a `turn` identifier and
the existing serialized audio queue.

```text
stable speech endpoint
        |
        +--> foreground voice lane (local cached cue) --> WebSocket --> HUD queue --> speakers
        |          |                                      ^                         |
        |          +--> timing: cue_ready / cue_play_started              barge-in/AEC
        |
        +--> execution lane (parallel, non-blocking) --> OpenClaw/model --> answer deltas
                                                   |                         |
                                                   +--> natural-clause TTS --+
```

## Responsibility boundaries

| Component | Owns | Does not own |
|---|---|---|
| `Session.handle_message` | Allocate turn, cancel stale audio, select presentation cue, start sidecar and query task | Action permission or action result claims |
| `Session.run_query` | Existing dialogue, research/action routing and model streaming | Waiting for acknowledgement playback |
| `tts.py` | Read pre-generated approved cue assets and split substantive answer at natural boundaries | Intent/action routing |
| `web/app.js` | One ordered audio queue, audio start/stop feedback and barge-in bridge | Model dispatch or execution decisions |
| OpenClaw | Model/tool planning and action execution | Audio timing and speaker state |

## Key flow A — ordinary dialogue

1. Local speech reaches a stable endpoint and the session allocates a new turn.
2. The coordinator sends a neutral cached cue to the active audio queue.
3. In the same event-loop turn it starts contextual understanding and
   `run_query`; neither awaits speaker playback.
4. The first model natural clause is queued for incremental TTS. Later clauses
   continue streaming in order.
5. A higher-numbered turn invalidates any unfinished cue or response audio.

## Key flow B — action or research

1. The session emits an existing truthful action/research cue.
2. It immediately begins the unchanged action/research route and sends visual
   progress independently of final-answer text.
3. OpenClaw/native work runs while the cue plays. Its verified result or model
   answer enters the normal substantive response stream.
4. Neither the cue nor a progress event is interpreted as an execution result.

## Performance approach

- Cached cues avoid model, network and synthesiser startup on the first-audio
  path.
- OpenClaw/Gateway prewarm continues while the user speaks.
- A single audio queue avoids overlapping clips and preserves AEC reference
  semantics.
- Natural punctuation remains the release condition for substantive content;
  latency is reduced through the cue, not through destructive clause cutting.

## Security and reliability

- Cue classification is presentation-only and cannot grant new access.
- The `turn` number remains the stale-event/cancellation authority across
  backend, browser and native host.
- Cue assets contain no user content, credential or action result.
- Missing/corrupt assets fail open to the existing stream; they are logged as
  a diagnosis, not surfaced as a connection error.
