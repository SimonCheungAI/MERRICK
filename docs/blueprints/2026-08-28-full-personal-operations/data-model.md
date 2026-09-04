# Data Model

## Phase 3 — Storage rules

- SQLite remains the local source of truth for workflow and organizer state. Enable foreign keys, WAL and schema migrations.
- All timestamps are ISO-8601 UTC; user-facing recurrence keeps an IANA `timezone`.
- IDs are opaque prefixed UUIDs. External provider IDs never become local authorization tokens.
- OAuth tokens, API keys, payment data and sensitive traveller identity fields are not database columns. Tables contain Keychain `secret_ref` values only.
- Mutable rows carry `revision`; every governed write uses optimistic concurrency and an idempotency key.

## Core identity and connection entities

### `owner_profiles`

One local owner profile.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | Stable `owner-*` ID |
| locale | TEXT | NOT NULL | `en-GB` or `zh-CN` initially |
| timezone | TEXT | NOT NULL | IANA name |
| default_currency | TEXT | NOT NULL | ISO-4217 |
| created_at | TEXT | NOT NULL | UTC |
| updated_at | TEXT | NOT NULL | UTC |

### `capability_snapshots`

One immutable, redacted observation of the effective OpenClaw capability
surface. Discovery failure never overwrites the last active safe snapshot.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `caps-*` |
| owner_id | TEXT | FK owner_profiles, NOT NULL | |
| runtime_name | TEXT | NOT NULL | `openclaw` |
| runtime_version | TEXT | NOT NULL | Pinned observed version |
| generation | INTEGER | NOT NULL | Monotonic per owner/runtime |
| status | TEXT | NOT NULL | `building`, `active`, `superseded`, `failed` |
| content_hash | TEXT | NOT NULL | SHA-256 of canonical redacted descriptors |
| counts_json | TEXT | NOT NULL | Bounded plugin/skill/tool/source totals |
| error_code | TEXT | NULL | Redacted discovery error |
| created_at | TEXT | NOT NULL | UTC |
| activated_at | TEXT | NULL | UTC |

Unique `(owner_id, runtime_name, generation)` and unique active snapshot per
owner/runtime. Index `(owner_id, status, generation DESC)`.

### `capability_descriptors`

Observed operations belonging to an immutable snapshot. These rows are catalog
evidence, not authorization.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `cap-*` |
| snapshot_id | TEXT | FK capability_snapshots ON DELETE CASCADE | |
| source_kind | TEXT | NOT NULL | `plugin`, `skill`, `mcp`, `codex_dynamic`, `local` |
| source_id | TEXT | NOT NULL | Bounded source/package ID |
| source_version | TEXT | NULL | Observed version only |
| operation_id | TEXT | NOT NULL | Source-native tool/operation ID |
| canonical_intent | TEXT | NULL | NULL until reviewed/mapped |
| schema_hash | TEXT | NOT NULL | Canonical input/output contract hash |
| effect_class | TEXT | NOT NULL | `read`, `local_write`, `external_write`, `destructive`, `financial` |
| max_risk | TEXT | CHECK R0–R3 | Conservative host classification |
| trust_state | TEXT | NOT NULL | `core`, `reviewed`, `unreviewed`, `quarantined` |
| readiness | TEXT | NOT NULL | `ready`, `disabled`, `dependency_missing`, `auth_required`, `incompatible`, `unhealthy` |
| requirements_json | TEXT | NOT NULL | Bounded bins/config/OS requirements; no secret values |
| auth_requirements_json | TEXT | NOT NULL | Canonical capabilities/scopes, never tokens |
| metadata_json | TEXT | NOT NULL | Redacted labels, origin and health summary |
| observed_at | TEXT | NOT NULL | UTC |

Unique `(snapshot_id, source_kind, source_id, operation_id)`. Index
`(snapshot_id, canonical_intent, readiness)`.

### `connector_bindings`

Reviewed application policy that binds a canonical intent to one observed
source operation. It survives catalog refresh but executes only while its
version/schema constraints still match.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `binding-*` |
| owner_id | TEXT | FK owner_profiles, NOT NULL | |
| canonical_intent | TEXT | NOT NULL | e.g. `mail.search` |
| source_kind | TEXT | NOT NULL | |
| source_id | TEXT | NOT NULL | |
| operation_id | TEXT | NOT NULL | |
| compatible_version_json | TEXT | NOT NULL | Exact/range compatibility policy |
| approved_schema_hash | TEXT | NOT NULL | Drift fails closed |
| max_risk | TEXT | CHECK R0–R3 | May only narrow descriptor risk |
| priority | INTEGER | NOT NULL DEFAULT 100 | Lower value preferred |
| status | TEXT | NOT NULL | `disabled`, `active`, `quarantined` |
| constraints_json | TEXT | NOT NULL | Accounts, resources, result and timeout bounds |
| reviewed_at | TEXT | NOT NULL | |
| revision | INTEGER | NOT NULL DEFAULT 1 | |
| updated_at | TEXT | NOT NULL | |

Unique active binding `(owner_id, canonical_intent, source_kind, source_id,
operation_id)`. Index `(owner_id, canonical_intent, status, priority)`.

### `connected_accounts`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `connection-*` |
| owner_id | TEXT | FK owner_profiles, NOT NULL | Ownership check on every use |
| provider | TEXT | NOT NULL | `google`, `microsoft`, `todoist`, etc. |
| account_kind | TEXT | NOT NULL | `mail`, `calendar`, `tasks`, `travel` |
| display_name | TEXT | NOT NULL | Safe user-facing label |
| principal_hint | TEXT | NULL | Redacted account hint, never an auth identity source |
| secret_ref | TEXT | NOT NULL | Keychain reference |
| status | TEXT | NOT NULL | `connecting`, `active`, `reauth_required`, `revoked`, `error` |
| granted_scopes_json | TEXT | NOT NULL | Canonical scope list |
| provider_tenant | TEXT | NULL | Tenant/domain hint |
| last_sync_at | TEXT | NULL | UTC |
| last_error_code | TEXT | NULL | Stable redacted error |
| revision | INTEGER | NOT NULL DEFAULT 1 | Optimistic concurrency |
| created_at | TEXT | NOT NULL | UTC |
| updated_at | TEXT | NOT NULL | UTC |

Indexes: `(owner_id, status)`, unique `(owner_id, provider, account_kind, principal_hint)` where principal hint exists.

### `capability_grants`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `grant-*` |
| owner_id | TEXT | FK, NOT NULL | |
| connection_id | TEXT | FK connected_accounts, NULL | NULL for local capabilities |
| capability | TEXT | NOT NULL | e.g. `mail.read`, `mail.send`, `calendar.events.write` |
| risk_level | TEXT | CHECK R0–R3 | Maximum intrinsic risk |
| mode | TEXT | NOT NULL | `disabled`, `ask`, `standing_rule` |
| constraints_json | TEXT | NOT NULL | Accounts, recipients, calendars, cost/time bounds |
| expires_at | TEXT | NULL | Optional temporary grant |
| revoked_at | TEXT | NULL | |
| revision | INTEGER | NOT NULL DEFAULT 1 | |
| created_at | TEXT | NOT NULL | |
| updated_at | TEXT | NOT NULL | |

Unique active grant: `(owner_id, connection_id, capability)`.

### `sync_cursors`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| connection_id | TEXT | PK/FK | |
| cursor_type | TEXT | NOT NULL | `history_id`, `delta_link`, `page_token` |
| cursor_ciphertext | BLOB | NOT NULL | Encrypted when provider treats it as sensitive |
| watermark_at | TEXT | NULL | Last provider timestamp |
| updated_at | TEXT | NOT NULL | |

## Workflow, authorization and audit entities

### `workflows`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `workflow-*` |
| owner_id | TEXT | FK, NOT NULL | |
| kind | TEXT | NOT NULL | `mail_triage`, `calendar_change`, `travel_booking`, etc. |
| source | TEXT | NOT NULL | `voice`, `text`, `automation`, `webhook` |
| source_turn_id | TEXT | NULL | Conversation correlation |
| status | TEXT | NOT NULL | `planned`, `running`, `waiting`, `succeeded`, `failed`, `cancelled` |
| current_step | INTEGER | NOT NULL DEFAULT 0 | |
| input_json | TEXT | NOT NULL | Validated, minimized request |
| result_json | TEXT | NULL | Redacted result/receipt references |
| error_code | TEXT | NULL | |
| created_at | TEXT | NOT NULL | |
| updated_at | TEXT | NOT NULL | |
| completed_at | TEXT | NULL | |

Indexes: `(owner_id, status, updated_at DESC)`, `(kind, created_at DESC)`.

### `workflow_steps`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `step-*` |
| workflow_id | TEXT | FK workflows ON DELETE CASCADE | |
| position | INTEGER | NOT NULL | Unique per workflow |
| kind | TEXT | NOT NULL | Typed operation name |
| state | TEXT | NOT NULL | `pending`, `running`, `waiting_approval`, `waiting_user`, `succeeded`, `failed`, `skipped` |
| input_json | TEXT | NOT NULL | Host-validated input |
| output_json | TEXT | NULL | Redacted output |
| retry_count | INTEGER | NOT NULL DEFAULT 0 | |
| next_attempt_at | TEXT | NULL | |
| started_at | TEXT | NULL | |
| completed_at | TEXT | NULL | |

Unique `(workflow_id, position)`; index `(state, next_attempt_at)`.

### `operation_requests`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `operation-*` |
| workflow_id | TEXT | FK, NOT NULL | |
| step_id | TEXT | FK, NOT NULL | |
| owner_id | TEXT | FK, NOT NULL | |
| connection_id | TEXT | FK, NULL | |
| capability | TEXT | NOT NULL | |
| risk_level | TEXT | CHECK R0–R3 | Host-computed |
| target_json | TEXT | NOT NULL | Opaque resource IDs and destinations |
| effect_json | TEXT | NOT NULL | Exact proposed mutation/disclosure/cost |
| preview_hash | TEXT | NOT NULL | SHA-256 of canonical preview |
| idempotency_key | TEXT | NOT NULL UNIQUE | Stable across safe retries |
| status | TEXT | NOT NULL | State machine below |
| expires_at | TEXT | NOT NULL | Intent freshness bound |
| revision | INTEGER | NOT NULL DEFAULT 1 | |
| created_at | TEXT | NOT NULL | |
| updated_at | TEXT | NOT NULL | |

Operation state machine:

```text
proposed → awaiting_approval → authorized → executing → succeeded
    │              │              │             ├→ failed → reconciling → succeeded|failed
    │              │              │             └→ compensating → compensated|failed
    └→ rejected    └→ expired     └→ cancelled
```

### `approval_requests`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `approval-*` |
| operation_id | TEXT | FK UNIQUE, NOT NULL | One active approval per immutable operation |
| preview_hash | TEXT | NOT NULL | Must match operation at decision time |
| reason | TEXT | NOT NULL | User-readable risk explanation |
| decision | TEXT | NOT NULL | `pending`, `approved_once`, `denied`, `expired` |
| decision_method | TEXT | NULL | `native_click`, `biometric`, `handoff` |
| capability_token_hash | TEXT | NULL UNIQUE | Single-use token hash only |
| decided_at | TEXT | NULL | |
| expires_at | TEXT | NOT NULL | |
| created_at | TEXT | NOT NULL | |

### `execution_attempts`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `attempt-*` |
| operation_id | TEXT | FK, NOT NULL | |
| attempt_no | INTEGER | NOT NULL | |
| connector | TEXT | NOT NULL | |
| request_fingerprint | TEXT | NOT NULL | No secret/body |
| provider_request_id | TEXT | NULL | |
| provider_resource_id | TEXT | NULL | |
| outcome | TEXT | NOT NULL | `started`, `succeeded`, `transient_failure`, `permanent_failure`, `unknown` |
| error_code | TEXT | NULL | |
| started_at | TEXT | NOT NULL | |
| completed_at | TEXT | NULL | |

Unique `(operation_id, attempt_no)`, index `(provider_request_id)`.

### `audit_events`

Append-only; updates and deletes forbidden by application API.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| sequence | INTEGER | PK AUTOINCREMENT | Local total order |
| id | TEXT | UNIQUE, NOT NULL | `audit-*` |
| owner_id | TEXT | FK, NOT NULL | |
| correlation_id | TEXT | NOT NULL | Turn/workflow/operation |
| event_type | TEXT | NOT NULL | |
| actor | TEXT | NOT NULL | `owner`, `jarvis`, `automation`, `connector` |
| resource_type | TEXT | NOT NULL | |
| resource_id | TEXT | NULL | |
| metadata_json | TEXT | NOT NULL | Redacted allowlisted fields |
| previous_hash | TEXT | NULL | Tamper-evident chain |
| event_hash | TEXT | NOT NULL UNIQUE | |
| created_at | TEXT | NOT NULL | |

Indexes: `(owner_id, sequence DESC)`, `(correlation_id, sequence)`.

### `standing_rules`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `rule-*` |
| owner_id | TEXT | FK, NOT NULL | |
| name | TEXT | NOT NULL | |
| trigger_kind | TEXT | NOT NULL | `schedule`, `event`, `manual` |
| trigger_json | TEXT | NOT NULL | Bounded schedule/event filter |
| capabilities_json | TEXT | NOT NULL | Explicit allowlist |
| constraints_json | TEXT | NOT NULL | Accounts, senders, recipients, calendars, max count/cost |
| enabled | INTEGER | NOT NULL DEFAULT 0 | |
| last_run_at | TEXT | NULL | |
| revision | INTEGER | NOT NULL DEFAULT 1 | |
| created_at | TEXT | NOT NULL | |
| updated_at | TEXT | NOT NULL | |

R3 capabilities are rejected from standing rules in V1.

## Domain cache and artifact entities

### `external_object_links`

Maps local organizer objects to provider objects without making external IDs authoritative.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | |
| connection_id | TEXT | FK, NOT NULL | |
| local_type | TEXT | NOT NULL | `task`, `meeting`, `reservation`, etc. |
| local_id | TEXT | NOT NULL | |
| provider_type | TEXT | NOT NULL | |
| provider_id | TEXT | NOT NULL | |
| provider_etag | TEXT | NULL | Conflict detection |
| last_synced_at | TEXT | NOT NULL | |
| tombstoned_at | TEXT | NULL | |

Unique `(connection_id, provider_type, provider_id)` and `(connection_id, local_type, local_id)`.

### `mail_items`

Minimal cache; full bodies are fetched on demand.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | Local ID |
| connection_id | TEXT | FK, NOT NULL | |
| provider_message_id | TEXT | NOT NULL | |
| provider_thread_id | TEXT | NOT NULL | |
| subject | TEXT | NOT NULL | May be locally encrypted by retention setting |
| sender_hint | TEXT | NOT NULL | Redacted/display value |
| received_at | TEXT | NOT NULL | |
| labels_json | TEXT | NOT NULL | |
| flags_json | TEXT | NOT NULL | unread/important/attachment |
| summary_ciphertext | BLOB | NULL | Optional local summary |
| classification_json | TEXT | NOT NULL | Priority/action-needed with evidence IDs |
| expires_at | TEXT | NULL | Cache retention |
| updated_at | TEXT | NOT NULL | |

Unique `(connection_id, provider_message_id)`; indexes `(connection_id, received_at DESC)` and `(connection_id, provider_thread_id)`.

### `mail_drafts`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | |
| connection_id | TEXT | FK, NOT NULL | |
| in_reply_to_mail_id | TEXT | FK mail_items, NULL | |
| recipients_ciphertext | BLOB | NOT NULL | Encrypted |
| subject_ciphertext | BLOB | NOT NULL | Encrypted |
| body_ciphertext | BLOB | NOT NULL | Encrypted |
| attachment_refs_json | TEXT | NOT NULL | Bounded staging refs |
| preview_hash | TEXT | NOT NULL | |
| status | TEXT | NOT NULL | `draft`, `awaiting_approval`, `sent`, `discarded` |
| provider_draft_id | TEXT | NULL | |
| provider_message_id | TEXT | NULL | |
| revision | INTEGER | NOT NULL DEFAULT 1 | |
| created_at | TEXT | NOT NULL | |
| updated_at | TEXT | NOT NULL | |

### `travel_plans`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `travel-*` |
| owner_id | TEXT | FK, NOT NULL | |
| title | TEXT | NOT NULL | |
| status | TEXT | NOT NULL | `draft`, `searching`, `comparing`, `selected`, `awaiting_handoff`, `booked`, `cancelled` |
| origin_json | TEXT | NOT NULL | Validated locations |
| destinations_json | TEXT | NOT NULL | |
| start_date | TEXT | NOT NULL | Local date |
| end_date | TEXT | NOT NULL | Local date |
| traveller_profile_refs_json | TEXT | NOT NULL | Keychain refs only |
| preferences_json | TEXT | NOT NULL | Cabin, room, loyalty, accessibility |
| budget_json | TEXT | NOT NULL | Amount/currency bounds |
| selected_option_id | TEXT | NULL | FK travel_options after creation |
| revision | INTEGER | NOT NULL DEFAULT 1 | |
| created_at | TEXT | NOT NULL | |
| updated_at | TEXT | NOT NULL | |

### `travel_options`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | |
| travel_plan_id | TEXT | FK ON DELETE CASCADE | |
| kind | TEXT | NOT NULL | `flight`, `hotel`, `bundle` |
| provider | TEXT | NOT NULL | |
| provider_offer_id | TEXT | NOT NULL | |
| offer_expires_at | TEXT | NULL | |
| itinerary_json | TEXT | NOT NULL | Normalized segments/property |
| total_amount_minor | INTEGER | NOT NULL | Integer money |
| currency | TEXT | NOT NULL | ISO-4217 |
| terms_json | TEXT | NOT NULL | Refund/cancel/baggage/tax |
| ranking_json | TEXT | NOT NULL | Score plus reasons, never authority |
| raw_receipt_ref | TEXT | NULL | Encrypted bounded blob ref |
| refreshed_at | TEXT | NOT NULL | |

Indexes: `(travel_plan_id, kind, total_amount_minor)`; unique `(provider, provider_offer_id, travel_plan_id)`.

### `reservations`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | |
| travel_plan_id | TEXT | FK, NOT NULL | |
| provider | TEXT | NOT NULL | |
| provider_reservation_id | TEXT | NULL | NULL while outcome unknown |
| status | TEXT | NOT NULL | `pending`, `confirmed`, `unknown`, `cancelled`, `failed` |
| amount_minor | INTEGER | NOT NULL | |
| currency | TEXT | NOT NULL | |
| confirmation_ciphertext | BLOB | NULL | Encrypted confirmation details |
| terms_ciphertext | BLOB | NULL | Encrypted cancellation terms |
| booked_at | TEXT | NULL | |
| reconciled_at | TEXT | NULL | |
| created_at | TEXT | NOT NULL | |
| updated_at | TEXT | NOT NULL | |

Unique `(provider, provider_reservation_id)` when non-null.

### `notification_deliveries`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | |
| owner_id | TEXT | FK, NOT NULL | |
| source_type | TEXT | NOT NULL | workflow/approval/reminder |
| source_id | TEXT | NOT NULL | |
| channel | TEXT | NOT NULL | `macos`, optional configured channel |
| scheduled_at | TEXT | NOT NULL | |
| delivered_at | TEXT | NULL | |
| status | TEXT | NOT NULL | `pending`, `delivered`, `failed`, `dismissed` |
| error_code | TEXT | NULL | |

Unique `(source_type, source_id, channel, scheduled_at)`.

## Existing organizer migrations

- Add `owner_id`, `revision`, `archived_at` and optional `external_sync_state` to projects/tasks/reminders.
- Add task recurrence, dependencies, tags, assignee and `source_connection_id` without changing existing IDs.
- Keep meeting transcripts local; store only external meeting/event links in `external_object_links`.
- Keep briefing and intelligence edition tables; add source account filters and workflow provenance.
- All destructive migrations use copy-verify-swap and retain a timestamped recoverable backup.

## Query and index checklist

- `approval_requests(decision, expires_at)`, `operation_requests(owner_id, status, updated_at DESC)` for approval queues.
- `workflow_steps(workflow_id, position)` and `(state, next_attempt_at)` for run display and worker claims.
- `standing_rules(owner_id, enabled, trigger_kind)` for scheduler evaluation.
- `notification_deliveries(status, scheduled_at)` for notification dispatch.
- `mail_items(connection_id, received_at DESC)`, `(connection_id, provider_thread_id)` for inbox/thread reads.
- `travel_options(travel_plan_id, kind, total_amount_minor)` for comparisons.
- `audit_events(owner_id, sequence DESC)` and `(correlation_id, sequence)` for activity and receipts.
- `capability_snapshots(owner_id, status, generation DESC)` and `capability_descriptors(snapshot_id, canonical_intent, readiness)` for the effective catalog.
- `connector_bindings(owner_id, canonical_intent, status, priority)` for bounded connector resolution without scanning raw manifests.

Dashboard repositories return pre-joined projections and batch-load referenced IDs. Connector interfaces accept batches and cursors; code must not issue one provider call per cached row.
