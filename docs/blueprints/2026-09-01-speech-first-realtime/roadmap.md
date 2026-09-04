# Roadmap

## Milestone 1 — Foreground cue parity (working slice)

Goal: every complete conversational turn receives the same immediate local
voice acknowledgement already available to action/research turns.

- [ ] Add approved neutral conversation cue assets in English and Chinese.
- [ ] Extend the presentation-only cue classifier to select conversation.
- [ ] Add timing mark that distinguishes cue availability from substantive TTS.
- [ ] Add red/green unit tests for neutral cue selection and dispatch ordering.

Deliverable: simple chat starts speaking immediately while OpenClaw streams in
parallel. Rollback: `JARVIS_FAST_VOICE_FLOW=0`.

## Milestone 2 — Measurement and regression proof

Goal: prove the perceived speed improvement without destabilising action,
audio or interruption.

- [ ] Verify logs contain one ordered timing trace per exercised turn.
- [ ] Exercise normal dialogue, research, desktop action and barge-in paths.
- [ ] Confirm no cue is duplicated by action progress or a final answer.
- [ ] Run focused Python tests and macOS package build; inspect a live launch.

Deliverable: measured voice-first behaviour and a documented rollback.
