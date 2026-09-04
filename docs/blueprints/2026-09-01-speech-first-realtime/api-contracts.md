# API and event contracts

The local authenticated WebSocket remains the contract boundary. No external
HTTP endpoint or OpenClaw protocol change is needed.

## Event: foreground cue

Existing `audio` event, with one additive presentation field:

```json
{
  "type": "audio",
  "seq": 12,
  "turn": 41,
  "mime": "audio/wav",
  "data": "base64...",
  "role": "acknowledgement"
}
```

Rules:

- `role: acknowledgement` is presentation metadata only.
- The browser orders `seq`; it discards stale audio by `turn` through the
  existing `audio_cancelled` path.
- Existing clients may ignore `role` and still play the audio safely.

## Event: timing feedback

The existing client event remains bounded and has no sensitive payload:

```json
{
  "type": "client_event",
  "event": "audio_play_started",
  "detail": "remaining=0 ready=4"
}
```

The backend records this as `latency.audio_play_started`. An acknowledgement
will additionally be marked as `latency.foreground_cue_ready`; normal answer
audio remains `latency.tts_audio_ready`.

## Compatibility

No event is removed or renamed. The audio and cancellation contract remains
backward compatible with the existing native HUD.
