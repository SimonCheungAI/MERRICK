# MERRICK Incremental Refactor Roadmap

Status: Proposed

This roadmap preserves the current macOS application while making future changes smaller, testable and portable. Every slice keeps the existing route as a safe fallback; no slice introduces a new provider, model, plugin or platform.

## Slice 0 — Characterize output lifecycle

User value: research returns one final spoken and rendered answer.

- Add a regression test for source-card/progress events followed by a model answer; assert only the final answer uses assistant_delta and TTS.
- Centralize the distinction between progress, source, answer and terminal event categories in a small backend module.
- Keep existing WebSocket strings during this slice; use a compatibility mapper at the boundary.

Done when: the duplicate-answer case is reproducible in a unit test and the test passes without a live Gateway.

Rollback: git revert. No persisted state changes.

## Slice 1 — Define typed desktop contracts

User value: fewer stale/duplicate messages across display, audio and native actions.

- Introduce typed Python message models for backend-to-UI events and UI-to-backend commands.
- Define explicit event classes: TurnStarted, Progress, ResearchSources, AnswerDelta, AnswerCompleted, Audio and NativeActionRequest.
- Validate every event at the FastAPI/WebSocket boundary and retain current JSON field names for compatibility.
- Add contract fixtures consumed by both Python and JavaScript tests.

Done when: invalid events fail before changing session state, and every emitted event has one declared category.

Rollback: disable typed validation with one local compatibility flag and retain the current serializer.

## Slice 2 — Extract research workflow

User value: searches open sources quickly and always yield one synthesis, even when a reader blocks or OpenClaw hosted search is unavailable.

- Move source selection, reading fallback and research-context construction out of Session into a research application workflow with injected ports for search, page reading, source presentation and synthesis.
- Keep Session.deep_research_last_search as a thin compatibility delegate.
- Use fake search/page-reader ports for unit tests; add one integration test with the local metadata-search fallback only.

Done when: no research business rule imports FastAPI, WebSocket or macOS code.

Rollback: route the delegate back to the existing implementation.

## Slice 3 — Extract turn and output coordination

User value: interruption, voice streaming and TTS remain responsive while independent features can be changed safely.

- Create a turn coordinator that owns turn IDs, cancellation and one-final-answer semantics.
- Move output/TTS buffering behind an output port; keep tts.py as the first adapter.
- Make research, chat, screen and local-document workflows return typed output events rather than write to the WebSocket directly.

Done when: all output paths have characterization tests for completion, cancellation and stale-event rejection.

Rollback: use the existing Session output path behind a feature flag.

## Slice 4 — Introduce host ports for portability

User value: the same assistant workflows can later run on another desktop host without weakening macOS safety checks.

- Define ports for speech input, native action execution, frontmost-window capture, local notifications and research-panel presentation.
- Make the current WebSocket/native Swift bridge the macOS implementation.
- Do not add another platform in this slice; prove portability with fakes and contract tests first.

Done when: application workflows refer only to port interfaces, not to MerrickApp.swift, JavaScript bridge names or macOS-only payload details.

Rollback: retain the current macOS adapter and remove unused port wiring.

## Slice discipline

- One slice is at most 400 changed implementation lines and includes its tests and documentation update.
- No slice can call, stop or start a real user Gateway from a unit test.
- Existing behaviour remains the default until its replacement has passing characterization and integration tests.
- Each merged slice receives an ADR reference when it changes a durable boundary or contract.

