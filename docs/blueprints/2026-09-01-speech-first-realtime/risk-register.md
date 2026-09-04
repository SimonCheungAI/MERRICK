# Risk register

| ID | Risk | Mitigation | Owner |
|---|---|---|---|
| R-001 | A cue falsely suggests an action finished | Use neutral “I’m on it” wording only; keep results on existing verified path. | M1 |
| R-002 | Cue overlaps final answer | Preserve one serial queue and `fast_ack_turn` duplicate guard. | M1 |
| R-003 | A cue is played after interruption | Reuse the existing higher-turn `audio_cancelled` boundary. | M1 |
| R-004 | Lower TTS chunk threshold clips speech | Do not lower it; use cached cue for latency. | M1 |
| R-005 | Extra classifier affects execution | Keep cue selection local/presentation-only; tests assert unchanged `run_query` inputs. | M1 |
| R-006 | Optimisation hides a model stall | Add separate cue/model/TTS/playback timing marks. | M2 |
