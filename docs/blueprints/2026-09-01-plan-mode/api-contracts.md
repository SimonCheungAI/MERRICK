# WebSocket contracts

All Plan Mode messages are JSON objects with `type` and use the current socket.
Existing messages and fields remain unchanged.

## Client to server

```json
{"type":"plan_mode_create","goal":"Research agentic AI and prepare a comparison"}
{"type":"plan_mode_select","plan_id":"uuid","approach_id":"research-first"}
{"type":"plan_mode_run","plan_id":"uuid","mode":"next"}
{"type":"plan_mode_run","plan_id":"uuid","mode":"all"}
{"type":"plan_mode_cancel","plan_id":"uuid"}
{"type":"plan_mode_dismiss"}
```

## Server to client

```json
{"type":"plan_mode_state","status":"planning|ready|running|succeeded|failed|cancelled|blocked","plan":{},"origin":"manual|auto"}
{"type":"plan_mode_step","plan_id":"uuid","step_id":"sources","status":"running","result":""}
{"type":"plan_mode_error","code":"PLAN_UNAVAILABLE","text":"Plan Mode is not available."}
```

`plan` is a serialization of `PlanDraft`. Result text is presentation data only;
it never appears as `assistant_delta`.

An automatic routing decision is server-internal and deliberately does not
add a second client request. A `plan` outcome uses the existing state event;
its `origin` lets the panel explain why it opened.

## Compatibility

- Client ignores unknown Plan Mode fields.
- Server validates IDs against the current session draft and returns a
  `plan_mode_error` for stale messages without changing state.
- `plan_mode_dismiss` is UI cleanup only: it does not cancel a live plan.
