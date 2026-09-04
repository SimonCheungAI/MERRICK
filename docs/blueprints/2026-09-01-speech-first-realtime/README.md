# Speech-first realtime voice flow

## Decision

- Complexity: **Moderate**
- Verdict: **PROCEED**
- Pattern: retain the local modular monolith and add a small, typed foreground
  voice lane. OpenClaw remains the single execution authority and continues in
  parallel with, never behind, the foreground lane.
- Estimated delivery: two small, independently shippable slices (1-2 days).

## Outcome

Every completed voice turn has a prompt, truthful audible acknowledgement when
there is likely model or tool wait. The acknowledgement is pre-generated local
audio, so it does not wait for model tokens or TTS synthesis. The normal model
answer remains the only substantive answer and still streams to TTS as natural
clauses arrive. Actions, research and model planning continue on their current
OpenClaw path concurrently.

## Package

1. `requirements.md`
2. `architecture.md`
3. `data-model.md`
4. `api-contracts.md`
5. `errors.md`
6. `risk-register.md`
7. `roadmap.md`
8. `validation.md`

## Architectural invariants

1. A cue is a truthful acknowledgement, never a claim that an action finished.
2. A cue never changes model/tool routing, permissions, session identity or
   cancellation authority.
3. A turn retains one spoken substantive answer; progress events never become
   answer text.
4. A newer turn invalidates old cue, streamed audio and model text by turn ID.
5. The foreground audio queue stays serialized and preserves the existing
   barge-in/AEC semantics.

Implementation status: architecture validation **PASS WITH WARNINGS**.
Implementation may begin.
