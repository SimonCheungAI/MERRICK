# Validation

## 25-point architecture check

| Check | Result | Resolution |
|---|---|---|
| S1 indexes | PASS | OpenClaw owns indexed task ledger; no new table |
| S2 N+1 | PASS | batch `agents_wait` and bounded task list |
| S3 cache | PASS | current run snapshot caches live board |
| S4 stateless tier | WARNING | local desktop session state; ledger reconciles restart in Slice 3 |
| S5 horizontal scale | N/A | single-user local product |
| S6 async work | PASS | controller runs in asyncio task |
| SEC1 auth | PASS | authenticated native WebSocket and loopback RPC |
| SEC2 authorization | PASS | current session run-id ownership checks |
| SEC3 validation | PASS | bounded enums, run/child ids, counts and manual task text |
| SEC4 sensitive data | PASS | no secrets/raw prompts sent to UI |
| SEC5 secrets | PASS | existing app-owned Gateway token path |
| SEC6 auth rate limit | N/A | no new login endpoint |
| M1 structure | PASS | dedicated server/UI modules |
| M2 separation | PASS | controller, adapter, state, renderer boundaries |
| M3 circular deps | PASS | controller depends on adapter; Session wires both |
| M4 config | PASS | environment switch and OpenClaw Swarm settings |
| M5 logging | PASS | correlated run/child trace events |
| M6 actionable errors | PASS | stable taxonomy and bounded detail |
| P1 latency | PASS | 250 ms receipt-to-board target |
| P2 pooling | N/A | no new DB connection |
| P3 pagination | N/A | bounded one-run board, max eight |
| P4 assets | PASS | bundled static JS/CSS |
| C1 naming | PASS | snake_case Python, camelCase DOM internals, existing WS convention |
| C2 error shape | PASS | `multi_agent_error` contract |
| C3 timestamps | PASS | UTC ISO-8601 |

Verdict: PASS WITH WARNINGS. The single warning is explicitly assigned to
Slice 3 restart reconciliation and does not block the first working vertical
slice. Implementation may begin.

Control-extension gate: PASS. Per-child cancellation uses immutable OpenClaw
identifiers, owner input is bounded and non-persistent, dynamic joins are capped
and included in the live completion barrier, and unsupported pause/resume/
steering is explicitly absent. Implementation may begin.

Persistent-session extension gate: PASS. `visible:true` is an installed-runtime
capability, terminal navigation uses only the returned loopback `sessionUrl`,
and close uses `sessionKey + expectedSessionId` so a stale card cannot archive a
replacement. Ledger/history polling is asynchronous and bounded. No schema or
secret-storage change is required. Implementation may begin.

## Release gates

- [x] Exactly N accepted receipts create exactly N board children.
- [x] No receipt means no succeeded step.
- [x] Parallel child start times overlap in a live dynamic-add test.
- [x] A failed child produces partial/failed aggregate state.
- [x] Cancel targets active children and retains terminal evidence.
- [x] Planner emits work units, never spawn/wait/merge meta-steps.
- [x] Previous local-document misroute reproducer passes.
- [x] Existing Python and JavaScript suites pass (528 tests).
- [x] Desktop and 390 px screenshots have no clipping or overflow.
- [x] Installed app hash matches the verified source build.
- [x] Stopping one child leaves every sibling running or terminal unchanged.
- [x] A dynamically added child delays synthesis until its terminal result.
- [x] Manual task input never appears in a server-to-browser snapshot.
- [x] NEW AGENT and per-agent controls remain usable at desktop and 390 px widths.
- [x] Every accepted child exposes its exact OpenClaw terminal URL.
- [x] A follow-up entered from that terminal continues the same session.
- [x] CLOSE is present for running and terminal cards and archives only its target.
- [x] Desktop and 390 px screenshots keep both controls visible without overflow.
