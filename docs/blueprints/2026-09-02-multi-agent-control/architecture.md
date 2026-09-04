# Architecture

## Pattern

Extend the existing modular monolith with an event-driven compatibility module.
OpenClaw remains the execution kernel and durable task ledger; MERRICK owns plan
selection, aggregation, and presentation.

```text
User request
  -> tool-free plan router
  -> PlanDraft(execution_mode)
  -> user selects + RUN ALL
  -> MultiAgentRunController
       -> Gateway RPC tools.invoke(sessions_spawn, visible=true) x N
       -> spawn receipts {runId, childSessionKey, sessionUrl}
       -> multi_agent_state -> Agent Board
       -> Gateway tasks.list reconciliation, bounded async loop
       -> sessions_history result recovery
       -> PlanModeCoordinator + Organizer status
       -> one main-agent synthesis turn
  -> final answer + terminal Agent Board

Gateway task events/tasks.list
  -> reconciliation snapshot -> same Agent Board after reconnect

Agent Board NEW AGENT
  -> validated owner WebSocket command
  -> create manual run or append child to active run
  -> same persistent-session/task-ledger truth path

Agent card ENTER TERMINAL
  -> request short-lived Control UI bootstrap URL from owned Gateway
  -> combine its authenticated origin/fragment with receipt-provided chat route
  -> owner continues controlling the same OpenClaw session

Agent card CLOSE
  -> run + child ownership validation
  -> sessions_list(session key) -> durable sessionId
  -> sessions.patch(archived=true, expectedSessionId)
  -> hidden archived card; siblings continue
```

## Responsibility boundaries

| Component | Owns | Does not own |
|---|---|---|
| `multi_agent.py` | Run/child state, receipt parsing, ledger reconciliation, exact-session archive, UI-safe serialization | Model planning, DOM, OpenClaw internals |
| `OpenClawGateway` adapter | Authenticated RPC methods and response normalization | Plan semantics or UI state |
| `PlanModeCoordinator` | Plan metadata and status transitions | Guessing child completion |
| OpenClaw | Child admission, scheduling, execution, durable task state and result delivery | MERRICK visual layout |
| `Session` | Lifecycle wiring, event delivery, final synthesis | Duplicate task registry |
| `agent-board.js` | Accessible rendering and user commands | Execution authority or HTML interpretation |

## Key flows

### Parallel run

1. Validate selected plan, cap children at eight, and create one local run id.
2. Submit visible spawns into the MERRICK Agents sidebar group and emit a child
   update after every accepted receipt.
3. If any launch is rejected, retain accepted children, cancel them, and mark
   the run failed with the real rejection.
4. Reconcile accepted run ids against `tasks.list`; on success, read the bounded
   last assistant reply through `sessions_history`. Each task maps to exactly
   one plan step.
5. After all children are terminal, synthesize bounded outputs once. A failed
   child remains visibly failed even if the synthesis can explain partial work.
6. The wait set is recomputed from live child state so an owner-added session
   joins the same completion barrier before synthesis.

### Manual launch, terminal entry, and per-agent close

1. `multi_agent_spawn` validates the optional current run id, label, and task.
2. If a run is active, append one child and emit `queued` before Gateway work;
   otherwise create a new one-child manual run in a background task.
3. ENTER TERMINAL preserves only the stored receipt URL's validated `/chat/`
   route. After a Gateway restart, native code rebases that route onto the
   short-lived authenticated Control UI URL produced by OpenClaw for the
   current owner-file loopback origin; no token enters WebKit and no session
   key is interpolated into a guessed route.
4. CLOSE resolves the exact session row, supplies its durable `sessionId` as
   `expectedSessionId`, and archives it. The card is hidden only after commit.
5. An archive race never overwrites a locally terminal/closed state, and no
   sibling is selected by label or list position.

### Reconnect and cancellation

1. On socket connect, the current in-memory board snapshot is sent immediately.
2. If the server restarted, `tasks.list` reconciles known OpenClaw identifiers.
3. Whole-run cancel closes each active OpenClaw session through the same exact
   lifecycle contract; terminal children remain inspectable until closed.

## Security and scaling

- The RPC bridge is loopback-only and already authenticated as the local owner.
- Browser events carry opaque run/session ids, OpenClaw-returned loopback URLs,
  and bounded visible output only.
- Inputs are validated server-side; all UI text uses DOM `textContent`.
- Manual task text crosses only the authenticated local WebSocket and is not
  serialized back to the browser or persisted in the presentation snapshot.
- Concurrency is capped in MERRICK and by OpenClaw subagent admission.
- Long work stays asynchronous; no HTTP or WebSocket handler blocks.
- Horizontal scaling is intentionally out of scope for this single-user local
  desktop product; OpenClaw's durable ledger provides restart reconciliation.

## Rollback

`JARVIS_MULTI_AGENT_ENABLED=false` restores the existing sequential runner and
hides the Agent Board. No new MERRICK database migration is required.
