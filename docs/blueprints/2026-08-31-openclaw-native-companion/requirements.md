# Requirements

## Explicit functional requirements

| ID | Requirement | Acceptance condition |
|---|---|---|
| FR-001 | Upgrade both `openclaw` and `@openclaw/codex` to `2026.8.1`. | Lockfile, packaged runtime and reported CLI versions agree. |
| FR-002 | Migrate legacy `codex/*` and `openai-codex/*` routes to `openai/*`. | A copied state directory passes `openclaw doctor --fix`, config validation and provider probes without losing the selected account. |
| FR-003 | Remove the MERRICK-owned tool/capability allowlist from the main execution path. | A tool that is enabled and permitted by OpenClaw is not denied by a second MERRICK catalog or action schema. |
| FR-004 | Make OpenClaw the default execution kernel for ordinary conversation and actionable requests. | Every accepted voice/text turn is represented by an OpenClaw session/run unless the native-path kill switch is off. |
| FR-005 | Preserve the complete OpenClaw tool profile. | Coding, filesystem, browser, skills, plugins, MCP, automations, sessions and subagent surfaces remain discoverable according to OpenClaw's resolved session policy. |
| FR-006 | Expose OpenClaw coding and multi-agent work. | The user can start coding work, observe progress/questions and receive the final result through MERRICK or Control UI. |
| FR-007 | Open the OpenClaw Control UI safely. | A visible MERRICK button and bilingual voice intent call `openclaw dashboard --json` and open its short-lived `browserUrl`; the shared token never enters a URL or app log. |
| FR-008 | Reuse the same session in both products. | Opening Control UI from a MERRICK turn selects or links to its OpenClaw session instead of creating unrelated context. |
| FR-009 | Project OpenClaw progress into MERRICK | The HUD shows queued, processing, tool, waiting-for-input, waiting-for-approval, completed, cancelled and failed states. |
| FR-010 | Resolve OpenClaw approvals and questions from MERRICK | Pending items are backfilled after reconnect and can be approved, denied, skipped or answered through typed controls. |
| FR-011 | Package MERRICK integration as an OpenClaw plugin. | A bundled `jarvis-companion` plugin registers session metadata, commands, UI contribution and lifecycle cleanup through supported Plugin SDK entry points. |
| FR-012 | Retire legacy planner/safe-tool gating only after parity. | Legacy action-planner branches are unreachable in native mode and removable after two verified releases; specific Merrick tools may remain as capabilities, never as a global gate. |

## Implicit requirements

| ID | Requirement |
|---|---|
| IR-001 | Session and run lists are paginated and merged by stable OpenClaw keys. |
| IR-002 | Reconnect restores subscriptions, history cursor, questions and approvals without duplicating a run. |
| IR-003 | OpenClaw device identity and device token are stored outside prompts and logs using an app-owned secret reference. |
| IR-004 | The user can select OpenClaw permission mode per session; `auto` is the initial default and `full` is an explicit owner selection. |
| IR-005 | Plugin installation, enablement and trust remain OpenClaw-native operations visible in Control UI. |
| IR-006 | File attachments retain content/type/size validation at the transport boundary even when all tools are exposed. |
| IR-007 | App shutdown cancels active runs only when the user requests cancellation; it always closes app-owned client/bridge processes. |
| IR-008 | Uninstall removes app-owned runtime/state according to the existing uninstall choice and never deletes an unrelated OpenClaw installation. |
| IR-009 | Audit events are redacted projections; command output, secrets and private content are not duplicated into a second long-lived MERRICK audit database. |
| IR-010 | Both Chinese and English UI/voice commands support OpenClaw workspace, permission, approval and session actions. |

## Non-functional requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-001 | Immediate feedback | Processing state in <50 ms and cached spoken acknowledgement target <200 ms. |
| NFR-002 | Run start | Gateway dispatch begins within 500 ms after final transcript on a warm runtime, excluding model latency. |
| NFR-003 | Reconnect | First retry within 250 ms; bounded exponential backoff; state restored within 5 s after Gateway recovery. |
| NFR-004 | Reliability | No duplicate externally visible run after retry or reconnect. |
| NFR-005 | Lifecycle | App quit leaves zero app-owned `openclaw-gateway` or bridge processes within 5 s. |
| NFR-006 | Compatibility | Gateway client and protocol packages are pinned to the exact OpenClaw release train. |
| NFR-007 | Accessibility | Controls remain keyboard accessible, localized and responsive without clipping. |
| NFR-008 | Observability | Structured lifecycle logs contain run/session IDs and error codes but no bearer/device tokens or raw secret values. |

## Constraints

- macOS remains the first native host.
- The Gateway binds to `127.0.0.1` unless the user separately configures an
  OpenClaw-supported remote access mode.
- The app continues to ship its own pinned Node and OpenClaw runtime.
- The Python/FastAPI voice backend and Swift host are retained; this is not a
  language rewrite.
- OpenClaw's native permission and approval rules are authoritative even when
  they deny a requested operation.
- Browser authentication uses OpenClaw's device pairing/bootstrap flow, not a
  token injected into page JavaScript.

## Dependency map

- `openclaw@2026.8.1`
- `@openclaw/codex@2026.8.1`
- matching `@openclaw/gateway-client` and `@openclaw/gateway-protocol`
- existing Swift host, web HUD, FastAPI backend and bundled Node runtime
- new bundled `jarvis-companion` plugin
- existing runtime contract generator extended with Gateway protocol and
  feature-flag fields

## Resolved conflicts

### Full capability versus safety

“No MERRICK allowlist” means MERRICK no longer suppresses tools or
re-validates OpenClaw plans through a smaller action schema. It does not mean
“ignore OpenClaw permission decisions.” OpenClaw's session mode, device scope,
plugin trust, exec approval and operator approval surfaces remain intact.

### Normal conversation versus accidental execution

All turns go to OpenClaw, but tool use is controlled by OpenClaw's model/tool
policy and session permission mode. MERRICK may provide conversational
guidance (“do not act unless the user asks”), but that guidance is not a hidden
host-side whitelist.

## Open questions deferred without blocking V1

- Whether a later release embeds Control UI in a signed native window instead
  of opening the default browser.
- Whether experimental Swarm should be enabled globally or selected per
  session after its release stability is proven.
- Which remote channels should be surfaced in the MERRICK settings UI;
  Control UI already provides the complete management surface.
