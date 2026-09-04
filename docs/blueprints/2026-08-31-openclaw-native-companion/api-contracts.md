# API and event contracts

The browser-facing surface remains the authenticated MERRICK loopback
WebSocket. The Python-to-Node bridge uses newline-delimited JSON over inherited
stdio. The Node bridge alone speaks the OpenClaw Gateway protocol.

## Common envelope

```json
{
  "v": 1,
  "type": "openclaw.run.started",
  "requestId": "uuid",
  "sessionKey": "opaque",
  "runId": "opaque",
  "at": "2026-08-31T12:00:00.000Z",
  "data": {}
}
```

All unknown fields are ignored only when `v` is supported. Unknown versions,
invalid sizes or invalid identifiers fail closed with a typed error.

## Command: `openclaw.session.send`

Purpose: send one user-authored turn to the bound OpenClaw session.

```json
{
  "type": "openclaw.session.send",
  "requestId": "uuid",
  "conversationId": "jarvis-main",
  "text": "Please inspect this repository and fix the failing tests.",
  "attachments": [],
  "permissionMode": "auto"
}
```

Validation: text 1-100,000 UTF-8 characters; attachment count/size/MIME are
bounded; `permissionMode` must be an OpenClaw-advertised enum. Repeating the
same `requestId` returns the original run.

## Command: `openclaw.run.cancel`

```json
{
  "type": "openclaw.run.cancel",
  "requestId": "uuid",
  "runId": "run-id",
  "reason": "user_interrupt"
}
```

Only an active run belonging to the authenticated local session may be
cancelled. Cancellation is idempotent.

## Command: `openclaw.dashboard.open`

```json
{
  "type": "openclaw.dashboard.open",
  "requestId": "uuid",
  "sessionKey": "optional-session-key"
}
```

Response contains only `{ "opened": true }` or a typed error. The short-lived
browser URL is consumed inside the Swift host and is never returned to web
JavaScript or written to logs.

## Command: `openclaw.permission.set`

```json
{
  "type": "openclaw.permission.set",
  "requestId": "uuid",
  "sessionKey": "opaque",
  "mode": "full"
}
```

The Gateway validates available modes and operator scope. MERRICK mirrors
the result but does not synthesize its own policy.

## Command: `openclaw.interaction.resolve`

```json
{
  "type": "openclaw.interaction.resolve",
  "requestId": "uuid",
  "interactionId": "opaque",
  "decision": "allow_once",
  "answer": null
}
```

Valid decisions depend on the advertised interaction schema. A stale,
cancelled, modified or already resolved interaction returns `409` semantics
through the WebSocket error envelope.

## Event: `openclaw.run.progress`

```json
{
  "v": 1,
  "type": "openclaw.run.progress",
  "requestId": "uuid",
  "sessionKey": "opaque",
  "runId": "opaque",
  "at": "2026-08-31T12:00:01.000Z",
  "data": {
    "phase": "tool",
    "headline": "Inspecting the test failures",
    "agentCount": 2,
    "needsInput": false
  }
}
```

Progress is bounded presentation text and is never appended to final answer or
spoken as final TTS.

## Event: `openclaw.interaction.requested`

```json
{
  "v": 1,
  "type": "openclaw.interaction.requested",
  "requestId": "uuid",
  "sessionKey": "opaque",
  "runId": "opaque",
  "at": "2026-08-31T12:00:02.000Z",
  "data": {
    "interactionId": "opaque",
    "kind": "exec_approval",
    "title": "Run repository tests?",
    "summary": "Run the test command in the selected workspace.",
    "choices": ["allow_once", "allow_always", "deny"]
  }
}
```

The event never contains tokens, environment secret values or an unbounded raw
command transcript.

## Event: `openclaw.run.completed`

```json
{
  "v": 1,
  "type": "openclaw.run.completed",
  "requestId": "uuid",
  "sessionKey": "opaque",
  "runId": "opaque",
  "at": "2026-08-31T12:00:10.000Z",
  "data": {
    "messageId": "opaque",
    "text": "The tests now pass and the changed files are ready for review."
  }
}
```

Only this event feeds the final answer/TTS path. Duplicate terminal events are
deduplicated by `runId` and `messageId`.

## Bridge operations

| Operation | Direction | Required Gateway scope |
|---|---|---|
| `connect` | Python -> bridge | bootstrap then paired device |
| `sessions.subscribe` | Python -> bridge | `operator.read` |
| `chat.send` | Python -> bridge | `operator.write` |
| `chat.history` | Python -> bridge | `operator.read` |
| `exec.approval.list/resolve` | Python -> bridge | `operator.approvals` |
| question list/resolve | Python -> bridge | `operator.questions` |
| run cancellation | Python -> bridge | `operator.write` |

## Pagination and rate bounds

- Session page default 60, maximum 100.
- History page default 50, maximum 100; use opaque anchors/cursors.
- At most one active send per session from the voice surface.
- Approval/question resolution limited to 10 attempts per minute per local
  client to contain broken UI loops.
- Dashboard handoffs limited to 5 per minute and never retried automatically.
