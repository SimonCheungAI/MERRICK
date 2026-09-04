# API and Tool Contracts

## Contract rules

- Local API prefix: `/api/v1`. The native bridge token is required and accepted only from loopback/origin-validated clients.
- Every mutation requires `Idempotency-Key`; mutable resources require `If-Match: <revision>`.
- Responses use `{ "data": ..., "meta": ... }`; failures use the error envelope defined in [errors.md](errors.md).
- Cursor values are opaque. Default page size is 25, maximum 100.
- Provider secrets, OAuth codes after exchange, raw payment values and capability tokens never appear in response bodies.
- JSON fields use `snake_case`; resource URLs use plural kebab-free nouns; actions use explicit subresources such as `/decision` or `/prepare-booking`.
- Rate limits: OAuth/auth starts are limited to 5 attempts per 15 minutes per owner/provider; planning to 30/minute; expensive search to 6/minute/provider; provider `Retry-After` always wins.

## Connections and permissions

| Method and path | Purpose | Request | Success |
|---|---|---|---|
| `GET /api/v1/connections` | List account connections | `kind?`, `status?`, `cursor?`, `limit?` | `200` connection summaries |
| `POST /api/v1/connections/oauth/start` | Begin PKCE connection | `{provider, account_kind, requested_capabilities[]}` | `201 {connection_id, authorization_url, expires_at}` |
| `POST /api/v1/connections/oauth/complete` | Exchange loopback result | `{connection_id, state, code}` | `200` redacted active connection |
| `POST /api/v1/connections/{id}/reauthorize` | Add/refresh narrowly selected scopes | `{requested_capabilities[]}` | `202` new authorization session |
| `DELETE /api/v1/connections/{id}` | Revoke provider and local grant | `{confirmed:true}` | `202 {status:"revoking"}` |
| `GET /api/v1/capability-grants` | View effective grants | filters + cursor | `200` grants |
| `PATCH /api/v1/capability-grants/{id}` | Set `disabled`, `ask` or standing rule | `{mode,constraints,revision}` | `200` updated grant |

`oauth/start` validates provider/scope mappings server-side. The client never supplies raw scope strings or redirect URIs.

## Capability catalog and connector bindings

| Method and path | Purpose | Request | Success |
|---|---|---|---|
| `GET /api/v1/capabilities/effective` | Read the last active safe snapshot | `kind?`, `intent?`, `readiness?`, `cursor?`, `limit?` | `200` redacted descriptors + snapshot generation |
| `POST /api/v1/capabilities/refresh` | Start read-only background discovery | empty body + idempotency key | `202` discovery workflow; current snapshot remains active |
| `GET /api/v1/capabilities/diagnostics` | Explain missing dependencies, auth and quarantines | source/intent filters | `200` bounded actionable findings |
| `GET /api/v1/connector-bindings` | List canonical intent mappings | intent/status/cursor | `200` reviewed mappings and effective health |
| `PATCH /api/v1/connector-bindings/{id}` | Enable, disable or reprioritize an already reviewed mapping | `{status, priority, constraints, revision}` | `200` updated binding; cannot increase risk or scope |
| `POST /api/v1/connector-bindings/{id}/revalidate` | Re-run compatibility/health checks | `{revision}` | `202` validation workflow |

These endpoints never accept a package URL, shell command, credential, raw
OAuth scope, arbitrary tool name or arbitrary schema. Plugin install/update/
remove and account connection use separate visible owner workflows. A refresh
cannot activate an unreviewed descriptor.

## Operations, approvals and audit

| Method and path | Purpose | Request | Success |
|---|---|---|---|
| `POST /api/v1/operations/plan` | Validate a proposed typed operation | `{kind, targets, parameters, source_turn_id}` | `201` plan/risk/preview or clarification |
| `GET /api/v1/operations/{id}` | Inspect status and receipt | path ID | `200` operation |
| `POST /api/v1/operations/{id}/cancel` | Cancel before irreversible effect | `{revision}` | `202` cancelled/cancelling |
| `GET /api/v1/approvals` | Paginated pending/history view | `status?`, `cursor?` | `200` approval summaries |
| `POST /api/v1/approvals/{id}/decision` | Decide exact preview | `{decision, preview_hash, biometric_assertion?}` | `200` operation state; capability token remains server-side |
| `GET /api/v1/audit-events` | Search local audit | time/type/resource/correlation/cursor filters | `200` redacted append-only events |

Approval decisions fail if expired, already consumed, preview hash changed, connection/grant changed or provider price/version is stale.

## Mail

| Method and path | Risk | Request | Success |
|---|---:|---|---|
| `GET /api/v1/mail/threads` | R0 | `connection_id`, query/label/unread/cursor/limit | `200` minimal thread cards |
| `GET /api/v1/mail/threads/{id}` | R0 | `include_body=false` by default | `200` bounded thread; attachments are metadata only |
| `POST /api/v1/mail/actions/classify` | R0/R1 | `{thread_ids[], labels[], archive?, create_followups?}` | `201` operation plan |
| `POST /api/v1/mail/drafts` | R1 | `{connection_id, thread_id?, to[], cc[], subject, body, attachment_refs[]}` | `201` encrypted local/provider draft |
| `PATCH /api/v1/mail/drafts/{id}` | R1 | exact fields + revision | `200` updated preview hash |
| `POST /api/v1/mail/drafts/{id}/send` | R2 | `{revision, preview_hash}` | `202` approval required or executing under valid rule |
| `DELETE /api/v1/mail/drafts/{id}` | R1 | revision | `204` soft-discarded |

Recipient addresses are normalized and resolved server-side. Attachments must be bounded Workspace staging references, never arbitrary paths.

## Calendar

| Method and path | Risk | Request | Success |
|---|---:|---|---|
| `GET /api/v1/calendar/events` | R0 | connections, start/end, timezone, cursor | `200` merged events |
| `POST /api/v1/calendar/freebusy` | R0 | connections, participants, range, duration | `200` candidate slots |
| `POST /api/v1/calendar/proposals` | R1 | title/time/timezone/calendar/attendees/location/notes | `201` proposal + conflict analysis |
| `POST /api/v1/calendar/proposals/{id}/commit` | R1/R2 | revision + preview hash | `202` approval/execution |
| `PATCH /api/v1/calendar/events/{id}` | R2 | provider etag + exact patch | `202` governed operation |
| `DELETE /api/v1/calendar/events/{id}` | R2/R3 | provider etag + cancellation notice preview | `202` governed operation |

Invitations, attendee changes and cancellations are R2; permanent calendar deletion and cascading cancellation penalties are R3.

## Work and documents

| Method and path | Purpose |
|---|---|
| `GET/POST /api/v1/projects` | Paginated list/create using existing organizer service |
| `PATCH/DELETE /api/v1/projects/{id}` | Revise/soft archive with revision |
| `GET/POST /api/v1/tasks` | Filtered list/create with recurrence, tags and external links |
| `PATCH/DELETE /api/v1/tasks/{id}` | Update/complete/soft delete |
| `POST /api/v1/tasks/{id}/sync` | Link or reconcile with selected task provider |
| `GET /api/v1/documents` | List bounded Workspace artifacts with cursor |
| `POST /api/v1/documents/jobs` | Create/revise/report/convert through typed artifact job |
| `GET /api/v1/documents/jobs/{id}` | Progress and output resource link |

## Travel

| Method and path | Risk | Request | Success |
|---|---:|---|---|
| `POST /api/v1/travel/plans` | R1 | validated trip constraints and Keychain traveller profile refs | `201` travel plan |
| `PATCH /api/v1/travel/plans/{id}` | R1 | constraints + revision | `200` revised plan; invalidates stale options |
| `POST /api/v1/travel/plans/{id}/search` | R0 | `{kinds:[flight,hotel], providers?}` | `202` workflow ID |
| `GET /api/v1/travel/plans/{id}/options` | R0 | kind/sort/filter/cursor | `200` normalized options |
| `POST /api/v1/travel/plans/{id}/select` | R1 | `{option_id, revision}` | `200` selected + refresh required flag |
| `POST /api/v1/travel/plans/{id}/prepare-booking` | R2 | option/plan revision | `202` refreshed quote and exact disclosure preview |
| `POST /api/v1/travel/reservations/{id}/handoff` | R3 | preview hash | `200 {handoff_url/window_id, expires_at}` after native approval |
| `POST /api/v1/travel/reservations/{id}/reconcile` | R0 | provider callback/explicit user result | `200` confirmed/unknown/failed |
| `POST /api/v1/travel/reservations/{id}/cancel-plan` | R3 | `{reason}` | `201` penalty preview only; no cancellation yet |

No endpoint accepts raw card number, CVV, passport number or provider password.

## Automation and notifications

| Method and path | Purpose |
|---|---|
| `GET/POST /api/v1/standing-rules` | List/create disabled-by-default bounded rules |
| `PATCH/DELETE /api/v1/standing-rules/{id}` | Revise/pause/soft-delete |
| `GET /api/v1/workflows` | Paginated workflow/run history |
| `GET /api/v1/workflows/{id}` | Steps, progress, approvals and receipts |
| `POST /api/v1/workflows/{id}/retry` | Retry only safe/reconciled failed step |
| `GET/PATCH /api/v1/notification-settings` | Per-kind local notification preferences |

## WebSocket events

All messages include `schema_version`, `event_id`, `correlation_id`, `occurred_at` and `payload`.

| Event | Direction | Payload purpose |
|---|---|---|
| `connection.snapshot` | server→HUD | Redacted status/scopes/errors |
| `operation.planned` | server→HUD | Typed steps, risk and preview |
| `approval.required` | server→HUD | Exact effect, disclosure, cost, expiry |
| `approval.decided` | both | Decision acknowledgement; never a raw capability token |
| `workflow.progress` | server→HUD | Current step and safe status copy |
| `workflow.completed` | server→HUD | Receipt and follow-up proposals |
| `workflow.failed` | server→HUD | Stable error and recovery actions |
| `sync.status` | server→HUD | Provider sync/cursor health |
| `notification.action` | native→server | Open/dismiss/snooze bounded action |
| `capability.snapshot` | server→HUD | New active generation, counts and stale/degraded state |
| `capability.quarantined` | server→HUD | Source/operation and safe compatibility reason |

## OpenClaw tool surface

The conversational model receives typed tools, not provider SDKs. Every tool returns a plan/result envelope and validates host-issued IDs.

| Tool | Risk ceiling | Important arguments |
|---|---:|---|
| `jarvis_connections_list` | R0 | `kind?`, `status?` |
| `jarvis_mail_search` | R0 | `connection_id`, bounded query, cursor |
| `jarvis_mail_read` | R0 | host-issued `thread_id`, body policy |
| `jarvis_mail_draft` | R1 | exact recipients/content/attachment refs |
| `jarvis_mail_send_request` | R2 | `draft_id`, `preview_hash`; cannot directly send |
| `jarvis_calendar_list` | R0 | range, calendars, timezone |
| `jarvis_calendar_freebusy` | R0 | participant IDs, range, duration |
| `jarvis_calendar_propose` | R1 | exact event draft |
| `jarvis_calendar_commit_request` | R2 | proposal ID/hash; cannot bypass policy |
| `jarvis_tasks_query` | R0 | filters/cursor |
| `jarvis_tasks_mutate` | R1/R2 | typed create/update/complete only |
| `jarvis_travel_search` | R0 | travel plan ID and search kinds |
| `jarvis_travel_select` | R1 | plan/option IDs |
| `jarvis_travel_prepare_handoff` | R3 | returns preview, never completes payment |
| `jarvis_workflow_status` | R0 | workflow ID |
| `jarvis_approval_status` | R0 | operation ID; model cannot decide |

Tool invariants:

1. No raw access token, arbitrary shell, arbitrary URL, AppleScript, filesystem path or payment field.
2. Read tools cannot call write tools indirectly.
3. Untrusted-content agents receive read-only subsets.
4. A tool cannot broaden OAuth scopes or create standing rules.
5. Model output is a proposal; only the application API can issue an execution attempt.
6. There is no generic `jarvis_call_plugin` tool. The model can call only canonical app-owned tools whose connector mapping is resolved and revalidated by the host.
7. Tool, plugin, skill and MCP descriptions are untrusted catalog metadata and cannot select an account, raise a risk ceiling or authorize another capability.
8. A connector schema/version change disables only the affected binding until revalidation; it never falls through to a lower-trust write connector.
