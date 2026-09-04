# MERRICK Architecture

## Purpose

MERRICK is a transparent macOS voice assistant. It accepts local speech, streams a conversational or research answer, presents a point-cloud desktop UI, and performs only host-validated desktop operations. It uses a locally managed OpenClaw Gateway and the selected model provider; it is not a general-purpose remote-control shell.

## Scope

Included:

- Voice turns, interruption, streamed text and TTS.
- Public research, source display, bounded page reading and synthesis.
- User-authorized workspace documents, memory and meeting/organizer data.
- Validated macOS actions, screen inspection and native permissions.

Not included:

- Arbitrary shell/process execution.
- Unbounded filesystem access or unattended deletion.
- A promise that browser pages or third-party model tools are always available.

## Current component map

| Component | Responsibility | Implementation | Depends on |
|---|---|---|---|
| Native host | macOS lifecycle, permissions, speech, native actions and window placement | desktop/MerrickApp.swift | Web UI bridge, local backend |
| Desktop UI | Point-cloud HUD, settings, WebSocket rendering, audio queue and native bridge messages | web/app.js, web/index.html, web/style.css | WebSocket event schema |
| Session orchestrator | Turn lifecycle, routing, output streaming, cancellation and host-side policy composition | server/main.py:Session | Domain modules, gateway facade, WebSocket |
| Model/gateway facade | Isolated OpenClaw lifecycle, model streaming, plan validation and signed public-page capabilities | server/openclaw_client.py | Local OpenClaw Gateway |
| Local domain services | Document extraction, memory, organizer, voice identity, TTS and weather | server/library.py, server/local_memory.py, server/organizer.py, server/voice_identity.py, server/tts.py, server/weather.py | Local storage or bounded external APIs |
| Safe-tool plugin | Capability-checked public-page operations available to OpenClaw | openclaw/plugins/jarvis-safe-tools | OpenClaw plugin runtime |
| Runtime configuration | Provider selection, OpenClaw agent policy and build/package lifecycle | openclaw/openclaw.template.json5, scripts | macOS Application Support |

## Representative flow: public research

1. desktop/MerrickApp.swift produces local speech results; web/app.js sends a stable transcript over the local WebSocket.
2. server/main.py:Session.handle_message creates one turn and calls Session.run_query with action detection enabled.
3. simple_browser_search_action, direct_public_analysis_query, or the bounded action planner classifies the request. The host, not the model, compiles and validates the public query.
4. Session.execute_action_plan requests the native visible browser search; Session.deep_research_last_search finds source metadata, emits source cards, opens bounded research panels, and optionally reads source pages.
5. Session.run_query with agent_id researcher and research_context supplies bounded untrusted evidence to the tool-free researcher. Its final delta stream becomes the single assistant answer and TTS input.
6. web/app.js renders the answer and source cards. The native host owns any separate research windows.

## Boundaries and invariants

- Native authority: only desktop/MerrickApp.swift performs macOS actions. Python emits validated action requests; JavaScript and Swift both validate bridge payloads before execution.
- Model authority: server/openclaw_client.py treats model action output as an untrusted proposal. It binds action targets and meaningful query words to the current utterance before execution.
- Public web: search cards and page contents are untrusted. Page reads use literal URLs and short-lived capabilities; source text cannot grant desktop, memory or file authority.
- Private data: server/library.py confines document access to the MERRICK workspace. server/voice_identity.py gates private-memory access. Screen capture is one-shot, read-only visual input.
- Turn invariant: a completed user turn produces at most one final assistant answer. Progress events and source cards must never be emitted as answer deltas or sent to the final-answer TTS queue.
- Cancellation invariant: a newer stable transcript or explicit interrupt invalidates prior text, audio and native-action work by turn number/request ID.

## Current architecture risks

| Finding | Evidence | Consequence |
|---|---|---|
| Session orchestration and policy are concentrated in one module | server/main.py is about 6,800 lines and contains routing, research, voice, memory, TTS and transport code | Changes can accidentally cross a boundary, as the research-overview duplicate-answer regression did. |
| UI event semantics are implicit dictionaries | Python, JavaScript and Swift each construct or interpret string event types | A progress event can be mistaken for a conversational delta without a shared contract. |
| Some tests import the process-global gateway | tests/test_session_action_execution.py imports openclaw_gateway | A poorly mocked test can start or disturb a live local runtime. |
| Platform details are mixed into application flow | Session directly waits for screen/native-action WebSocket responses | Future Windows/Linux hosts would require changes across routing code rather than one adapter. |

## Target direction (proposed; not yet implemented)

Use a modular monolith with stable in-process ports, not microservices and not a rewrite. The Python backend remains one process, but its dependencies become directional:

Desktop host, web UI, OpenClaw and storage adapters → application workflows → domain policies and typed event contracts.

- Domain: pure turn, research, action and output-state rules; no FastAPI, WebSocket, macOS or OpenClaw imports.
- Application: workflows that coordinate domain policies through ports.
- Adapters: FastAPI/WebSocket transport, OpenClaw, macOS bridge, storage, TTS and HTTP implementations.
- Contracts: versioned typed messages shared by backend, UI and native host.

This keeps macOS behaviour intact while making a future host implement only the native bridge and speech/screen adapters. It does not require moving to microservices or changing the user-facing protocol all at once.

## Where to make changes today

| Change | Primary location | Also verify |
|---|---|---|
| Turn routing or research lifecycle | server/main.py:Session.run_query and Session.deep_research_last_search | tests/test_session_action_execution.py and web/app.js |
| Action schema/validation | server/openclaw_client.py | Safe-tool plugin tests, desktop/MerrickApp.swift and web/app.js |
| Native permissions/actions | desktop/MerrickApp.swift | tests/test_desktop_lifecycle.py and bridge validation in web/app.js |
| Display/audio streaming | web/app.js, server/tts.py and server/main.py | tests/test_tts.py and turn-interrupt tests |
| Memory/organizer behaviour | server/local_memory.py and server/organizer.py | Matching unit tests |
| Gateway policy or provider runtime | openclaw/openclaw.template.json5 and scripts | tests/test_gateway_identity.py and packaging build |

## Verification baseline

Use the isolated test suite and avoid any test that can manage the currently running Gateway unless its gateway facade is explicitly injected or mocked.

- PYTHONPATH=server ./.venv/bin/python -m unittest discover -s tests -v
- pnpm --filter openclaw-plugin-jarvis-safe-tools test
- ./scripts/build-macos-app.sh

