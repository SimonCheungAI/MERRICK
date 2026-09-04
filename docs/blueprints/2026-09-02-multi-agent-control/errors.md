# Error taxonomy

| Code | Meaning | UI behavior | Plan behavior |
|---|---|---|---|
| `MULTI_AGENT_DISABLED` | Feature switch is off | hide board | use sequential runner |
| `RUN_STALE` | Client referenced another run | non-destructive notice | unchanged |
| `SPAWN_REJECTED` | OpenClaw rejected a child | child failed with reason | stop/cancel accepted siblings |
| `SPAWN_RECEIPT_INVALID` | Accepted response lacks ids | child failed | fail run |
| `RECONCILE_FAILED` | task/session reconciliation failed | retryable run error | keep real child states |
| `CHILD_FAILED` | Child terminal failure | failed card | aggregate partial/failed |
| `CHILD_TIMED_OUT` | Child exceeded timeout | timed-out card | aggregate partial/failed |
| `SYNTHESIS_FAILED` | Children finished but main summary failed | results remain inspectable | failed, never succeeded |
| `CANCEL_FAILED` | One or more active tasks could not cancel | show exact remaining count | running/partial |
| `GATEWAY_UNAVAILABLE` | OpenClaw RPC unavailable | actionable reconnect state | failed/blocked |
| `CHILD_STALE` | Child id is absent or already terminal | non-destructive notice | unchanged |
| `AGENT_INPUT_INVALID` | Missing/oversized label or task | keep launch form open | unchanged |
| `RUN_CAPACITY` | Active run already owns eight children | disable new action | unchanged |
| `TERMINAL_UNAVAILABLE` | accepted spawn omitted Control UI URL | disable terminal control | execution continues |
| `ARCHIVE_FAILED` | exact session archive did not commit | keep card visible with error | unchanged |
| `SESSION_GENERATION_STALE` | session key now names another generation | refresh; never close replacement | unchanged |

Errors are bounded and sanitized. No stack trace, token, hidden prompt, or raw
tool arguments cross the browser boundary.
