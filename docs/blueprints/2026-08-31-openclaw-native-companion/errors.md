# Error taxonomy

## Envelope

```json
{
  "type": "openclaw.error",
  "requestId": "uuid",
  "code": "OPENCLAW_PROTOCOL_MISMATCH",
  "message": "OpenClaw and MERRICK need to be upgraded together.",
  "retryable": false,
  "action": "repair_runtime"
}
```

## Codes

| Code | Meaning | Retry | User action |
|---|---|---:|---|
| `OPENCLAW_NOT_READY` | Gateway is starting or recovering | Yes | Wait; automatic bounded reconnect |
| `OPENCLAW_PROTOCOL_MISMATCH` | Client/Gateway wire versions differ | No | Repair or roll back the bundled runtime |
| `OPENCLAW_PAIRING_REQUIRED` | Companion device needs approval | No automatic send | Show the exact pairing request |
| `OPENCLAW_SCOPE_REQUIRED` | Device lacks approval/question/write scope | No | Approve requested scope in Control UI |
| `OPENCLAW_SESSION_UNAVAILABLE` | Bound session no longer resolves | Conditional | Relink or start a new session |
| `OPENCLAW_RUN_CONFLICT` | Same session already owns an incompatible active run | Yes after state refresh | Wait, cancel or queue |
| `OPENCLAW_INTERACTION_STALE` | Approval/question already changed | No | Refresh pending interactions |
| `OPENCLAW_PERMISSION_DENIED` | OpenClaw denied the requested operation | No | Change session mode or approve through OpenClaw if supported |
| `OPENCLAW_DASHBOARD_HANDOFF_FAILED` | Single-use dashboard URL could not be issued/opened | Yes on user click | Retry dashboard open |
| `OPENCLAW_MIGRATION_FAILED` | Upgrade validation failed | No | Automatic rollback to prior verified runtime |
| `OPENCLAW_BRIDGE_EXITED` | Official client bridge stopped | Yes | Supervisor restarts with circuit breaker |
| `OPENCLAW_PROVIDER_FAILED` | Selected provider failed the run | Depends on normalized provider code | Preserve connection and show exact recovery |

## Handling rules

1. Transport failures never clear provider credentials or session bindings.
2. Reconnectable failures preserve the current turn and show visible progress.
3. Authentication, scope and protocol failures never loop silently.
4. An ambiguous externally effectful operation is reconciled through OpenClaw
   state before retry; MERRICK never blindly repeats it.
5. Logs include code, run/session correlation and component, but redact token,
   bootstrap URL, secret values and private content.
6. The fallback path is allowed only before native mode reaches GA and never
   after OpenClaw reports that an effect may already have occurred.
