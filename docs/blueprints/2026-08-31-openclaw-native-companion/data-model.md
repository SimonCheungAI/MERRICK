# Data model

OpenClaw remains the system of record for agents, sessions, messages, runs,
tasks, plugins, automations and approvals. MERRICK stores only companion
bindings and reconnect projections.

## Entity: RuntimeMigration

**Table:** `openclaw_runtime_migrations`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | UUID |
| from_version | TEXT | NOT NULL | Exact previous package version |
| to_version | TEXT | NOT NULL | Exact target package version |
| state | TEXT | NOT NULL, CHECK | `prepared`, `backed_up`, `migrated`, `verified`, `rolled_back`, `failed` |
| backup_path | TEXT | NULL | App-owned staging path, never a broad home path |
| config_hash_before | TEXT | NOT NULL | SHA-256 |
| config_hash_after | TEXT | NULL | SHA-256 |
| diagnostic_code | TEXT | NULL | Redacted failure classification |
| started_at | TEXT | NOT NULL | UTC ISO-8601 |
| finished_at | TEXT | NULL | UTC ISO-8601 |

Indexes: `(to_version, state)`, `started_at DESC`.

Rules: only one non-terminal migration may exist; rollback never deletes the
verified backup; secrets are excluded from hashes and diagnostics.

## Entity: GatewayDeviceBinding

**Table:** `openclaw_gateway_devices`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | Local binding UUID |
| gateway_fingerprint | TEXT | UNIQUE, NOT NULL | Endpoint plus Gateway identity hash |
| device_id | TEXT | UNIQUE, NOT NULL | OpenClaw-issued device ID |
| secret_ref | TEXT | NOT NULL | Opaque reference to device token |
| scopes_json | TEXT | NOT NULL | Validated array of approved scopes |
| protocol_version | INTEGER | NOT NULL | Exact negotiated wire version |
| state | TEXT | NOT NULL, CHECK | `pairing`, `ready`, `revoked`, `mismatch` |
| created_at | TEXT | NOT NULL | UTC ISO-8601 |
| last_connected_at | TEXT | NULL | UTC ISO-8601 |

Indexes: `state`, `last_connected_at DESC`.

Rules: token values are never stored in SQLite; scope upgrades require a new
OpenClaw pairing decision.

## Entity: SessionBinding

**Table:** `openclaw_session_bindings`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | UUID |
| jarvis_conversation_id | TEXT | UNIQUE, NOT NULL | Stable local conversation identity |
| gateway_fingerprint | TEXT | NOT NULL, FK | Gateway device binding |
| session_key | TEXT | UNIQUE, NOT NULL | OpenClaw session key |
| agent_id | TEXT | NOT NULL | Default `main` |
| workspace_path | TEXT | NULL | OpenClaw-owned workspace projection |
| permission_mode | TEXT | NOT NULL | OpenClaw mode snapshot, not authority |
| state | TEXT | NOT NULL, CHECK | `active`, `archived`, `unavailable` |
| last_event_cursor | TEXT | NULL | Reconnect cursor |
| created_at | TEXT | NOT NULL | UTC ISO-8601 |
| updated_at | TEXT | NOT NULL | UTC ISO-8601 |

Indexes: `(gateway_fingerprint, updated_at DESC)`, `(agent_id, state)`.

Rules: the Gateway owns session existence and permissions; this row is deleted
only after an explicit unlink or confirmed remote deletion.

## Entity: RunProjection

**Table:** `openclaw_run_projections`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| run_id | TEXT | PK | OpenClaw run ID |
| session_binding_id | TEXT | NOT NULL, FK | Owning companion binding |
| client_request_id | TEXT | UNIQUE, NOT NULL | Idempotency/reconnect key |
| turn_number | INTEGER | NOT NULL | MERRICK cancellation boundary |
| status | TEXT | NOT NULL, CHECK | `queued`, `running`, `waiting_question`, `waiting_approval`, `completed`, `failed`, `cancelled` |
| headline | TEXT | NULL | Redacted bounded progress text |
| final_message_id | TEXT | NULL | OpenClaw message anchor |
| error_code | TEXT | NULL | Stable taxonomy only |
| started_at | TEXT | NOT NULL | UTC ISO-8601 |
| finished_at | TEXT | NULL | UTC ISO-8601 |

Indexes: `(session_binding_id, started_at DESC)`, `(status, started_at)`.

Rules: one `client_request_id` can create at most one run; terminal states are
immutable except a late event may enrich the final message anchor.

## Entity: PendingInteractionProjection

**Table:** `openclaw_pending_interactions`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| interaction_id | TEXT | PK | OpenClaw question or approval ID |
| run_id | TEXT | NOT NULL, FK | Associated run |
| kind | TEXT | NOT NULL, CHECK | `question`, `exec_approval`, `plugin_approval` |
| summary_json | TEXT | NOT NULL | Schema-validated redacted display model |
| state | TEXT | NOT NULL, CHECK | `pending`, `resolved`, `expired`, `cancelled` |
| requested_at | TEXT | NOT NULL | UTC ISO-8601 |
| expires_at | TEXT | NULL | UTC ISO-8601 |
| resolved_at | TEXT | NULL | UTC ISO-8601 |

Indexes: `(state, requested_at)`, `run_id`.

Rules: the row carries no reusable authority; resolution is always sent to the
Gateway using the original ID and authenticated client scope.

## Entity: EventCursor

**Table:** `openclaw_event_cursors`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| stream_key | TEXT | PK | Gateway/session subscription identity |
| cursor | TEXT | NOT NULL | Opaque OpenClaw cursor |
| observed_at | TEXT | NOT NULL | UTC ISO-8601 |

Rules: cursors are updated transactionally with the projection they produced;
an unknown cursor triggers bounded history reconciliation rather than reset.

## Retention

- Terminal run projections: 30 days by default, configurable.
- Resolved interaction projections: 7 days.
- Device/session bindings: until unlink/revocation.
- Runtime migration records and verified backup metadata: retain the last three
  successful versions.
- Full transcript, tool output and plugin state remain in OpenClaw's own state.
