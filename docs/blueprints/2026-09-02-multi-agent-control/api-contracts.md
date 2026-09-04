# WebSocket and Gateway contracts

## Client to server

```json
{"type":"multi_agent_refresh","run_id":"uuid"}
{"type":"multi_agent_cancel","run_id":"uuid"}
{"type":"multi_agent_spawn","run_id":"uuid-or-empty","label":"Security review","task":"Review the authentication path."}
{"type":"multi_agent_close_child","run_id":"uuid","child_id":"uuid"}
{"type":"multi_agent_dismiss","run_id":"uuid"}
```

IDs must match the current session run. Unknown or stale identifiers return a
`multi_agent_error` without changing execution.

`multi_agent_spawn` accepts a 1..120 character label and 1..4,000 character
task. `run_id` is required when joining an active run and omitted when starting
a new manual run. A current run at eight children returns `RUN_CAPACITY`.

## Server to client

```json
{
  "type": "multi_agent_state",
  "run": {
    "id": "uuid",
    "plan_id": "uuid",
    "goal": "Review the release",
    "status": "running",
    "progress": {"completed": 1, "total": 3},
    "children": [
      {
        "id": "security",
        "label": "Security review",
        "status": "succeeded",
        "run_id": "opaque",
        "session_key": "opaque",
        "session_url": "http://127.0.0.1:18789/...",
        "can_open": true,
        "closed": false,
        "elapsed_ms": 4200,
        "result": "Bounded visible result",
        "error": ""
      }
    ],
    "summary": "",
    "error": ""
  }
}
```

```json
{"type":"multi_agent_error","code":"RUN_STALE","text":"That agent run is no longer active."}
```

Additional control errors use the same shape with `CHILD_STALE`,
`AGENT_INPUT_INVALID`, `RUN_CAPACITY`, `TERMINAL_UNAVAILABLE`, or
`ARCHIVE_FAILED`.

## Internal OpenClaw RPC

- `tools.invoke` / `sessions_spawn`: `visible=true`, `group=MERRICK Agents`,
  stable `taskName`, `context=isolated`, bounded timeout; `collect`, `thinking`,
  thread/session mode, and swarm-only fields are omitted.
- `tasks.list`: reconcile visible state by requester session.
- `tools.invoke` / `sessions_list`: resolve the exact visible session generation.
- `tools.invoke` / `sessions_history`: recover the bounded last assistant result.
- `tools.invoke` / `sessions`: archive with `sessionKey`, `archived=true`, and
  the observed `expectedSessionId`.

The adapter accepts only RPC `ok=true` plus a tool-level successful payload.
Textual tool results are parsed as JSON and rejected if required identifiers
are absent.
