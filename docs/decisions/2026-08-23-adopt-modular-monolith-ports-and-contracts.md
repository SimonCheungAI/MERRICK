---
status: accepted
date: 2026-08-23
decision-makers: Project owner
consulted: Codex
informed: Future MERRICK maintainers and coding agents
---

# ADR-0001: Adopt a Modular Monolith with Ports and Typed Desktop Contracts

## Context and Problem Statement

How should MERRICK become easier to maintain and eventually portable to another desktop operating system without destabilising its current macOS voice, research, memory, and desktop-control behaviour?

The current product is a capable macOS application with a Swift host, a browser-based HUD, a FastAPI local backend, and an isolated OpenClaw Gateway. The principal session implementation in server/main.py coordinates voice transcripts, turn cancellation, research, model streaming, TTS, memory, screen capture, native action requests and WebSocket output. It is about 6,800 lines long.

This concentration makes cross-cutting regressions likely. The August 2026 research regression demonstrated this: source-progress text was emitted as an assistant answer delta and placed on the TTS queue, so one research request appeared to answer twice. The bug was small, but its cause crossed research, output and presentation boundaries.

The product must retain its existing macOS safety model: only the native host performs desktop actions; model output is an untrusted proposal; public web content is untrusted; private memory, documents and screen input retain their current gates. A future platform host must not require application workflows to embed macOS-specific bridge details.

## Decision Drivers

- Preserve current user-facing behaviour while reducing regression risk.
- Keep voice and action latency low; do not add service-to-service network hops.
- Make output, interruption and research behaviour testable without a live OpenClaw Gateway.
- Permit a future Windows or Linux host without weakening the existing authority boundaries.
- Keep changes reversible and small enough to validate in the running desktop app.

## Considered Options

- Keep extending the current Session-centric architecture.
- Rewrite the application around a new architecture before further feature work.
- Split MERRICK into independently deployed microservices.
- Incrementally adopt a modular monolith with ports and typed desktop contracts.

## Decision Outcome

Chosen option: "Incrementally adopt a modular monolith with ports and typed desktop contracts", because it preserves the proven local single-process latency and safety model while creating explicit seams for testing and future platform hosts.

The backend remains one local Python process. Dependencies point inward:

- Domain policies define turn, research, action and output rules without FastAPI, WebSocket, macOS or OpenClaw imports.
- Application workflows coordinate those policies through narrow ports.
- Adapters implement WebSocket transport, OpenClaw, the macOS bridge, storage, TTS, HTTP and local speech/screen integration.
- Contracts define versioned typed messages shared across backend, web UI and native host.

## Consequences

- Good, because a research progress event cannot become an answer by convention alone; its category is explicit and testable.
- Good, because external integrations can be replaced with fakes in unit tests, removing the need for unit tests to manage a real local Gateway.
- Good, because a future platform needs to implement host ports rather than duplicate research or turn logic.
- Bad, because there is short-term duplication while each old Session path delegates to an extracted workflow.
- Bad, because every boundary extraction must maintain backward-compatible WebSocket fields until all clients migrate.
- Neutral, because this decision does not add a provider, database, plugin, background service or second desktop platform.

## Implementation Plan

- **Affected paths**:
  - Current orchestration: server/main.py.
  - Gateway adapter: server/openclaw_client.py.
  - Existing local services: server/library.py, server/local_memory.py, server/organizer.py, server/voice_identity.py, server/tts.py and server/weather.py.
  - Current UI/native adapters: web/app.js and desktop/MerrickApp.swift.
  - Tests: tests/test_session_action_execution.py, tests/test_openclaw_client.py, tests/test_tts.py, tests/test_voice_turn_runtime.py and tests/test_desktop_lifecycle.py.
  - Architecture map and slice order: docs/architecture.md and docs/refactor-roadmap.md.

- **Dependencies**: Add no network dependency for the initial slices. Use standard-library dataclasses, TypedDicts or equivalent existing Python facilities for contracts. A validation library requires a separate ADR before introduction.

- **Patterns to follow**:
  - Retain Session as a compatibility entry point while extracted workflows are introduced behind stable delegates.
  - Use injected ports/fakes at OpenClaw, native-host, search/page-reader and output boundaries.
  - Preserve the current turn number and request ID stale-event guards.
  - Keep current JSON field names at the WebSocket boundary until a versioned contract migration is complete.
  - Add a regression test before changing any behaviour that previously failed in a user-visible way.

- **Patterns to avoid**:
  - Do not split into microservices, add IPC hops, or create a second Gateway.
  - Do not expose a model directly to native actions, filesystem paths, secrets or arbitrary page content.
  - Do not let unit tests call ensure_ready, start, stop or restart the process-global live gateway.
  - Do not mix progress, source-card and final-answer events, or place non-answer events in the final-answer TTS queue.
  - Do not rewrite the Swift host, web UI or Session class in one branch.

- **Configuration**: No new environment variable or feature flag is required for Slice 0. Later extracted workflows use local compatibility flags only while the old delegate remains available; remove a flag after its replacement is the default and verified.

- **Migration steps**:
  1. Characterize and protect output lifecycle semantics.
  2. Introduce typed event contracts with compatibility serialization.
  3. Extract public research into an application workflow with injected ports.
  4. Extract turn/output coordination.
  5. Introduce host ports and prove them with fake adapters before targeting another platform.

### Verification

- [ ] docs/architecture.md names every current top-level component, authority boundary and representative research flow with existing paths.
- [ ] A research-source progress event emits neither assistant_delta nor final-answer TTS input.
- [ ] The duplicate-answer regression test runs without network access or a live OpenClaw Gateway.
- [ ] Each new workflow has injected ports and an explicit compatibility delegate from Session until migration completes.
- [ ] No extracted domain/application module imports FastAPI, WebSocket transport, desktop/MerrickApp.swift bridge names or OpenClaw implementation code.
- [ ] The WebSocket boundary validates typed events while accepting current field names during migration.
- [ ] Existing unit tests do not start, stop or restart the user's active gateway.
- [ ] The macOS build succeeds after each slice.
- [ ] Every slice documents its rollback as git revert or a local compatibility-flag disablement.

## Pros and Cons of the Options

### Keep extending the Session-centric architecture

- Good, because it has no immediate extraction cost.
- Bad, because new behaviour keeps accumulating in the same cross-cutting module.
- Bad, because tests must understand transport, policy and workflow internals at once.

### Rewrite before further feature work

- Good, because a new architecture can be aesthetically clean.
- Bad, because voice, interruption, TTS and native permissions have many existing edge cases.
- Bad, because a rewrite removes the current safe fallback and delays user-facing reliability work.

### Split into microservices

- Good, because process boundaries are explicit.
- Bad, because local voice latency and failure modes become worse.
- Bad, because it adds deployment, observability and versioning overhead without a demonstrated scale need.

### Incremental modular monolith with ports and typed contracts

- Good, because it creates explicit seams while retaining a low-latency local process.
- Good, because it supports fakes, characterization tests and later host portability.
- Bad, because migration temporarily has compatibility code and requires discipline.

## More Information

The implementation order and rollback strategy are maintained in docs/refactor-roadmap.md. Revisit this decision if MERRICK must support a second host platform, if a current local process becomes a measured latency or reliability bottleneck, or if a new contract requires a non-standard dependency.
