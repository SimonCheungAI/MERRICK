# Architecture

## Pattern

Retain a **modular monolith with supervised runtime adapters**. OpenClaw is a
replaceable app-owned child runtime, not a Python library. The integration uses
the official Gateway wire contract outside OpenClaw and the supported Plugin
SDK inside OpenClaw.

Microservices are rejected because this is a single-owner local application.
Directly reimplementing the Gateway protocol in Python is rejected because it
would duplicate device pairing, reconnect and protocol-version behavior. A
browser-only integration is rejected because voice turns must continue while
Control UI is closed.

## Component diagram

```text
Microphone / text / macOS events
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│ MERRICK native companion                                   │
│ Swift lifecycle + Web HUD + Python voice/session coordinator     │
│ acknowledgement · speech/TTS · native notifications · rendering │
└───────────────┬───────────────────────────┬──────────────────────┘
                │ typed stdio               │ short-lived dashboard handoff
                ▼                           ▼
┌──────────────────────────────┐     ┌─────────────────────────────┐
│ Official Gateway client      │     │ OpenClaw Control UI         │
│ supervised Node bridge       │     │ chat · code · tasks ·       │
│ protocol v4 · device auth ·  │     │ plugins · approvals ·       │
│ reconnect · subscriptions    │     │ browser · dashboards        │
└──────────────┬───────────────┘     └──────────────┬──────────────┘
               │ authenticated WS/RPC               │ authenticated WS/RPC
               └─────────────────┬───────────────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│ OpenClaw Gateway 2026.8.1                                       │
│ sessions · agents · tools · plugins · skills · browser · code    │
│ automations · questions · approvals · subagents · memory         │
│                                                                  │
│ bundled jarvis-companion plugin                                  │
│ session projection · MERRICK commands · UI tab · lifecycle hooks  │
└──────────────────────┬───────────────────────────────────────────┘
                       ▼
             Local host / providers / nodes
```

## Responsibility boundaries

| Component | Owns | Does not own |
|---|---|---|
| OpenClaw Gateway | Agent runs, tools, code, subagents, plugins, browser, automations, memory, permissions and approvals | Microphone capture, Steadfast voice, macOS app lifecycle |
| Gateway client bridge | Protocol validation, device pairing, reconnect, event subscription, run dispatch and cancellation | Tool-policy decisions or model prompts |
| `jarvis-companion` plugin | OpenClaw-native session metadata, commands, Control UI contribution and cleanup hooks | Shared gateway tokens, arbitrary native process control |
| Python coordinator | Voice turn state, immediate acknowledgement, mapping a turn to one run, TTS and UI projection | Filtering OpenClaw's tool catalog or validating a second action plan |
| Swift host | App/windows, permissions, safe dashboard launch, process supervision and notifications | Deciding which OpenClaw tool may execute |
| Web HUD | Rendering run/approval/question state and collecting explicit user choices | Granting authority from client-supplied fields |

## Key flow A — voice command to an OpenClaw run

1. The final transcript atomically changes the MERRICK turn to
   `processing`; a cached Steadfast acknowledgement begins immediately.
2. The Python coordinator resolves or creates the bound OpenClaw session. It
   does not classify the utterance into a local capability list.
3. The supervised Gateway client sends `chat.send` with the stable session key
   and client request ID. The Gateway owns agent/tool selection.
4. Run events update the HUD. Tool calls, coding work and subagents remain
   visible as OpenClaw state rather than silent MERRICK background work.
5. If OpenClaw emits a question or approval request, both Control UI and the
   MERRICK projection can answer it. Resolution uses the original ID and
   OpenClaw-required scope.
6. One terminal run becomes the single final response and TTS stream. A newer
   turn cancels or supersedes the previous run according to the user's intent.

## Key flow B — open the advanced OpenClaw workspace

1. A button or explicit bilingual command requests `dashboard.open` from the
   native host.
2. The host invokes the pinned CLI as `openclaw dashboard --json` with the
   app-owned state/config environment.
3. The CLI returns a short-lived, single-use `browserUrl`; logs retain only the
   success state and expiry, never the URL or token.
4. macOS opens the URL in the user's chosen browser. OpenClaw exchanges it for
   a device credential and removes the bootstrap from the address bar.
5. The requested MERRICK session is selected after authentication through
   a normal session navigation action, not by putting a durable credential in
   a URL.

## Tool and permission architecture

- Global OpenClaw tool profile is `full`.
- The MERRICK main execution agent has no local `allow`/`deny` overlay.
- The explicit `plugins.allow` list is removed; installed plugins still require
  OpenClaw enablement, trust/capability review and any manifest consent.
- Default session permission mode is OpenClaw `auto`; the user may choose
  guarded/read-only/full in OpenClaw or the mirrored MERRICK control.
- MERRICK never changes a denied call into an allowed call. It only shows
  the OpenClaw decision and the supported next action.
- Existing `jarvis-safe-tools` may survive temporarily for literal public-page
  helpers, but native mode never depends on it to expose the rest of OpenClaw.

## Process lifecycle

- Swift supervises the Python backend.
- Python supervises the official Gateway-client bridge and the Gateway through
  explicit PIDs and executable fingerprints.
- Gateway starts with `OPENCLAW_SUPERVISOR_MODE=external`,
  `OPENCLAW_NO_RESPAWN=1` and the existing loopback configuration.
- Child stdout/stderr are consumed immediately and redacted.
- Shutdown closes client subscriptions, requests Gateway shutdown, waits a
  bounded interval, then terminates only fingerprint-matching app-owned PIDs.
- OpenClaw's self-update is disabled in embedded mode; MERRICK upgrades
  the pinned runtime transactionally.

## Scalability and performance

- Optimize for one owner with many sessions, plugins and provider accounts.
- OpenClaw owns durable run/session state; MERRICK stores only bindings and
  cursors required for UX and reconnect.
- Subscribe to `sessions.changed`, run, question and approval events instead of
  polling. Paginate history and session lists using Gateway cursors/offsets.
- Serialize mutations per session; permit bounded parallel sessions/subagents
  as OpenClaw allows.
- Cache only redacted session summaries and UI projections. Do not duplicate
  complete transcripts or command output solely for the companion view.
- A future remote Gateway changes the adapter endpoint and device pairing, not
  voice/application domain code.

## Security architecture

- Gateway and companion bridge bind to loopback by default.
- Official device identity uses Ed25519 pairing and least-required scopes:
  `operator.read`, `operator.write`, `operator.approvals` and
  `operator.questions`. Administrative settings stay in Control UI.
- The shared bootstrap secret and device token live behind opaque secret refs;
  neither enters model context, WebSocket UI payloads or logs.
- Dashboard launch uses OpenClaw's single-use browser handoff.
- All companion messages are schema-validated and size-bounded.
- OpenClaw remains authoritative for exec modes, approval binding, plugin
  trust, workspace restrictions and external effects.
- CSP, origin checks and loopback WebSocket authentication remain enabled for
  the MERRICK HUD.

## Target folder ownership

```text
server/openclaw_native/             Python application port and projections
  client.py                         supervised bridge facade
  sessions.py                       turn/session binding workflow
  events.py                         typed OpenClaw event projection
  models.py                         binding/run/approval models
openclaw/gateway-client-bridge/     official TypeScript Gateway client process
openclaw/plugins/jarvis-companion/  supported OpenClaw Plugin SDK integration
desktop/openclaw/                   dashboard launch and native windows
web/openclaw/                       session/progress/approval components
tests/openclaw_native/              contract, reconnect and lifecycle tests
```

Dependencies point inward: OpenClaw/Swift/Node/WebSocket adapters depend on the
Python application port; the application port knows no CLI paths or UI code.
