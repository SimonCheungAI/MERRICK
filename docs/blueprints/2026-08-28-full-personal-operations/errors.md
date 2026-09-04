# Error and Recovery Contract

## Error envelope

```json
{
  "error": {
    "code": "APPROVAL_EXPIRED",
    "message": "The approval expired. Review the updated preview before continuing.",
    "retryable": false,
    "correlation_id": "workflow-…",
    "recovery": ["refresh_preview"]
  }
}
```

Messages are safe for the owner; provider payloads, stack traces, tokens and PII remain in redacted diagnostic logs only.

## Taxonomy

| Family | Example codes | HTTP | Behaviour |
|---|---|---:|---|
| Validation | `INVALID_INPUT`, `AMBIGUOUS_TARGET`, `TIMEZONE_REQUIRED` | 400 | Ask for one missing/ambiguous fact |
| Authentication | `CONNECTION_REQUIRED`, `TOKEN_EXPIRED`, `REAUTH_REQUIRED` | 401/428 | Pause only affected workflow; preserve draft |
| Authorization | `CAPABILITY_DISABLED`, `SCOPE_MISSING`, `APPROVAL_REQUIRED`, `APPROVAL_EXPIRED` | 403/409 | Never auto-broaden scope; open exact settings/approval |
| Capability catalog | `CAPABILITY_DISCOVERY_FAILED`, `CATALOG_STALE`, `DEPENDENCY_MISSING`, `CONNECTOR_NOT_CONNECTED` | 409/503 | Keep last safe snapshot; diagnose only affected source |
| Compatibility | `PLUGIN_UNREVIEWED`, `SCHEMA_INCOMPATIBLE`, `PLUGIN_QUARANTINED`, `CONNECTOR_UNHEALTHY` | 409/422 | Do not coerce or silently fall back; review/revalidate mapping |
| Ownership | `RESOURCE_NOT_OWNED`, `CONNECTION_MISMATCH` | 403 | Fail closed and security-audit |
| Not found | `RESOURCE_NOT_FOUND`, `PROVIDER_OBJECT_GONE` | 404/410 | Reconcile/tombstone; do not recreate silently |
| Conflict | `REVISION_CONFLICT`, `PROVIDER_ETAG_CONFLICT`, `DUPLICATE_EFFECT` | 409 | Refresh and show differences |
| Provider transient | `RATE_LIMITED`, `PROVIDER_UNAVAILABLE`, `NETWORK_TIMEOUT` | 429/503/504 | Bounded backoff for reads and known-safe writes |
| Provider permanent | `PROVIDER_REJECTED`, `INVALID_RECIPIENT`, `OFFER_EXPIRED` | 422 | Return to edit/search; no blind retry |
| Unknown outcome | `SEND_OUTCOME_UNKNOWN`, `BOOKING_OUTCOME_UNKNOWN` | 202/409 | Reconcile by idempotency/provider lookup; never create another effect |
| Browser | `BROWSER_UNAVAILABLE`, `SELECTOR_STALE`, `CAPTCHA_REQUIRED`, `USER_HANDOFF_REQUIRED` | 409/428 | Pause with visible handoff and retained state |
| Security | `PROMPT_INJECTION_BLOCKED`, `SSRF_BLOCKED`, `DATA_DISCLOSURE_BLOCKED` | 403 | Stop step, audit and explain without echoing malicious content |
| Local runtime | `DATABASE_BUSY`, `MIGRATION_FAILED`, `GATEWAY_UNAVAILABLE` | 503 | Preserve local state; unrelated modules remain available |
| Internal | `INTERNAL_ERROR` | 500 | Correlation ID, redacted log, no provider retry assumption |

## Retry policy

| Operation | Automatic retry | Limit | Notes |
|---|---|---:|---|
| Read/search/free-busy | Yes | 3 with jitter | Respect `Retry-After` |
| Cursor synchronization | Yes | 5 over 30 min | Cursor invalidation triggers bounded full resync |
| Local transaction before external call | Yes | 3 | SQLite busy only |
| Label/archive/task sync | Yes with idempotency | 3 | Reconcile external version first |
| Mail send | Only after provider confirms no effect | 1 retry | Unknown outcome goes to reconciliation |
| Calendar invite/update | Only after resource lookup | 1 retry | Use provider event ID/etag |
| Booking/cancellation/payment | No blind retry | 0 | Provider lookup/webhook or human support flow |
| Browser action | Selector refresh once | 1 | Never repeat final submit |

## Circuit breakers

- Per connection/provider: open after five transient failures in five minutes; half-open after provider `Retry-After` or five minutes.
- Browser adapter: open after three structural failures for one site version; require explicit retry/update.
- Model planner: fall back to local organizer/read-only dashboard, never to unrestricted execution.
- Notification failure never fails the underlying operation; it creates a visible dashboard warning.
- Capability discovery has its own circuit breaker after three failures in ten minutes and serves the last active snapshot; it never restarts the Gateway from the voice response path.

## Cancellation and compensation

- Pending/planning steps cancel immediately.
- Executing writes cancel only when the provider supports cancellation and the effect has not committed.
- Local tasks, labels and draft changes use inverse operations or soft delete.
- Sent messages are not recalled unless the provider exposes a verified recall contract; follow-up is a separate operation.
- Calendar changes retain the previous event snapshot for a proposed revert.
- Travel cancellation is never called “undo”; it is a new R3 workflow showing penalties and refund terms.

## Restart recovery

1. Mark stale `running` steps as `reconciling`, never `pending`.
2. Verify connection/grant/approval validity and provider resource/version.
3. Resume read-only or locally reversible steps automatically.
4. Return R2/R3 operations to preview when intent or price freshness expired.
5. Emit one user-visible completion/failure, deduplicated by workflow event ID.
