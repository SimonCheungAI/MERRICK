# Error taxonomy

| Code / trace | Meaning | User effect | Recovery |
|---|---|---|---|
| `tts.fast_ack_unavailable` | Cached cue asset cannot be read | No cue; normal response continues | Package/asset diagnostic only. |
| `tts.fast_ack_stale` | Cue belongs to an invalidated turn | No old audio plays | Normal higher-turn cancellation. |
| `tts.queue_timeout` | Substantive TTS queue did not drain in its bound | Existing response finalisation continues | Existing bounded queue cleanup. |
| `latency.*` | Measurement mark | None | Inspect exact phase timing without changing routing. |

Rules:

1. Cue failure never becomes “connection stalled”, never retries OpenClaw and
   never blocks a substantive answer.
2. Model/provider failures retain their existing normalized errors.
3. A cue must never make a failed or pending action sound complete.
