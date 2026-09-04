# Data Model

## Storage rules

- SQLite at `PluginVault/registry.sqlite` is the source of truth. Enable foreign
  keys, WAL, `busy_timeout`, integrity checks and numbered migrations.
- IDs are opaque prefixed UUIDs. All timestamps are ISO-8601 UTC.
- Mutable rows carry an integer `revision` for optimistic concurrency.
- Plugin source and build output are immutable filesystem objects addressed by
  SHA-256; SQLite stores paths relative to `PluginVault`, never arbitrary or
  absolute plugin-controlled paths.
- Secrets, bridge tokens, signing private keys and macOS authorization material
  are Keychain values referenced by opaque handles and are never database fields.
- JSON columns accept only versioned host schemas and canonical serialization.

## Identity and source entities

### `plugin_origins`

Identifies where a plugin lineage came from independently of its declared
OpenClaw plugin ID.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `origin-*` |
| kind | TEXT | NOT NULL, CHECK | `generated`, `imported`, `bundled`, `native_local` |
| publisher_name | TEXT | NULL, max 120 | Display only, never trust |
| publisher_key_id | TEXT | NULL | Public-key fingerprint only |
| source_uri | TEXT | NULL, max 500 | Redacted provenance, never fetched automatically |
| trust_state | TEXT | NOT NULL | `core`, `local_owner`, `verified`, `unverified`, `blocked` |
| created_at | TEXT | NOT NULL | UTC |
| updated_at | TEXT | NOT NULL | UTC |

Indexes: `(kind, trust_state)`, unique non-null `publisher_key_id` where desired.

### `plugin_projects`

A mutable owner workspace that produces immutable revisions.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `project-*` |
| origin_id | TEXT | FK plugin_origins, NOT NULL | Stable lineage |
| slug | TEXT | NOT NULL, normalized | Owner-facing stable slug |
| display_name | TEXT | NOT NULL, max 120 | |
| description | TEXT | NOT NULL, max 1000 | |
| requested_capability | TEXT | NOT NULL, max 4000 | Owner request, not an authorization |
| target_profile | TEXT | NOT NULL | `sandboxed_harness` or `native_full_trust` |
| status | TEXT | NOT NULL | `draft`, `busy`, `ready`, `trashed` |
| worktree_relpath | TEXT | NOT NULL UNIQUE | Host-created relative path |
| head_revision_id | TEXT | NULL | FK added after revisions exist |
| revision | INTEGER | NOT NULL DEFAULT 1 | Optimistic concurrency |
| created_at | TEXT | NOT NULL | |
| updated_at | TEXT | NOT NULL | |
| trashed_at | TEXT | NULL | Soft delete |

Unique `(origin_id, slug)`. Index `(status, updated_at DESC)`.

### `plugin_revisions`

An immutable normalized source and artifact revision.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `pluginrev-*` |
| project_id | TEXT | FK plugin_projects, NULL | NULL for retained imported-only lineage |
| origin_id | TEXT | FK plugin_origins, NOT NULL | |
| parent_revision_id | TEXT | FK self, NULL | Revision ancestry |
| declared_plugin_id | TEXT | NOT NULL, max 81 | OpenClaw-facing ID |
| version | TEXT | NOT NULL, SemVer | Package revision version |
| target_profile | TEXT | NOT NULL | Immutable execution profile |
| source_hash | TEXT | NOT NULL | SHA-256 canonical source tree |
| artifact_hash | TEXT | NULL | Present after successful build |
| manifest_hash | TEXT | NOT NULL | Canonical metadata hash |
| source_relpath | TEXT | NOT NULL UNIQUE | Read-only directory |
| artifact_relpath | TEXT | NULL UNIQUE | Read-only directory |
| harness_api_range | TEXT | NOT NULL | Supported Harness ABI |
| openclaw_range | TEXT | NOT NULL | Supported OpenClaw versions |
| node_range | TEXT | NOT NULL | Supported Node runtime |
| state | TEXT | NOT NULL | `drafted`, `built`, `verified`, `rejected`, `quarantined` |
| provenance_json | TEXT | NOT NULL | Agent/model/tool/build identities, no prompts/secrets |
| created_at | TEXT | NOT NULL | |

Unique `(origin_id, declared_plugin_id, version, source_hash)`. Index
`(declared_plugin_id, state, created_at DESC)`. Rows are never updated except a
monotonic state transition and artifact attachment within one build transaction;
source content is never changed.

### `permission_declarations`

Host-normalized capabilities observed or declared by one immutable revision.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `permdecl-*` |
| plugin_revision_id | TEXT | FK plugin_revisions ON DELETE CASCADE | |
| capability_kind | TEXT | NOT NULL | `filesystem`, `network`, `process`, `application`, `data`, `secret`, `effect`, `runtime` |
| resource_pattern | TEXT | NOT NULL, host-normalized | Never regex supplied directly to an executor |
| access_modes_json | TEXT | NOT NULL | Enum list |
| rationale | TEXT | NOT NULL, max 500 | Untrusted display text |
| source | TEXT | NOT NULL | `declared`, `static_analysis`, `preview_observed` |
| risk_level | TEXT | NOT NULL | `R0`–`R3` or `FULL` |
| declaration_hash | TEXT | NOT NULL | Canonical row hash |

Unique `(plugin_revision_id, capability_kind, resource_pattern, source)`; index
`(plugin_revision_id, risk_level)`.

## Workflow and evidence entities

### `harness_jobs`

Durable author/build/test/preview/import/export/install/migration work.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `hjob-*` |
| project_id | TEXT | FK plugin_projects, NULL | |
| plugin_revision_id | TEXT | FK plugin_revisions, NULL | |
| kind | TEXT | NOT NULL | `author`, `build`, `test`, `preview`, `import`, `export`, `activate`, `rollback`, `migrate` |
| source | TEXT | NOT NULL | `voice`, `text`, `ui`, `startup` |
| status | TEXT | NOT NULL | State machine below |
| current_step | TEXT | NULL | Stable step ID |
| progress | INTEGER | NOT NULL DEFAULT 0, CHECK 0–100 | Informational only |
| requested_input_json | TEXT | NOT NULL | Validated minimized input |
| result_json | TEXT | NULL | IDs/hashes and safe summaries |
| error_code | TEXT | NULL | Stable taxonomy |
| correlation_id | TEXT | NOT NULL UNIQUE | |
| cancellation_requested_at | TEXT | NULL | |
| lease_owner | TEXT | NULL | Process identity |
| lease_expires_at | TEXT | NULL | Crash recovery |
| created_at | TEXT | NOT NULL | |
| started_at | TEXT | NULL | |
| updated_at | TEXT | NOT NULL | |
| completed_at | TEXT | NULL | |

Indexes: `(status, updated_at)`, `(project_id, created_at DESC)`,
`(plugin_revision_id, created_at DESC)`.

```text
queued → running → waiting_owner → running → succeeded
   │        ├→ cancelling → cancelled
   │        ├→ failed
   │        └→ interrupted → queued|failed
   └→ cancelled
```

### `harness_job_steps`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `hstep-*` |
| job_id | TEXT | FK harness_jobs ON DELETE CASCADE | |
| position | INTEGER | NOT NULL | Unique per job |
| kind | TEXT | NOT NULL | e.g. `static_scan`, `gateway_smoke` |
| status | TEXT | NOT NULL | `pending`, `running`, `passed`, `failed`, `skipped`, `cancelled` |
| input_hash | TEXT | NOT NULL | Reproducibility |
| output_summary_json | TEXT | NULL | Bounded/redacted |
| log_relpath | TEXT | NULL | Bounded evidence file |
| started_at | TEXT | NULL | |
| completed_at | TEXT | NULL | |

Unique `(job_id, position)`, index `(job_id, status)`.

### `evidence_runs`

Immutable result of a verification pipeline.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `evidence-*` |
| plugin_revision_id | TEXT | FK plugin_revisions, NOT NULL | |
| job_id | TEXT | FK harness_jobs, NOT NULL | |
| result | TEXT | NOT NULL | `pass`, `fail`, `warning` |
| build_hash | TEXT | NOT NULL | Exact tested artifact |
| permission_set_hash | TEXT | NOT NULL | Exact evaluated declaration |
| tool_schema_hash | TEXT | NOT NULL | Registered tool contracts |
| checks_json | TEXT | NOT NULL | Versions and pass/fail summaries |
| evidence_relpath | TEXT | NOT NULL UNIQUE | Immutable bounded bundle |
| expires_at | TEXT | NULL | Optional revalidation horizon |
| created_at | TEXT | NOT NULL | |

Index `(plugin_revision_id, created_at DESC)`.

## Authorization and runtime entities

### `permission_grants`

One host decision bound to a revision and declaration set. Imported packages
cannot create these rows.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `pgrant-*` |
| plugin_revision_id | TEXT | FK plugin_revisions, NOT NULL | Exact immutable code |
| declaration_set_hash | TEXT | NOT NULL | Invalidated by permission drift |
| mode | TEXT | NOT NULL | `once`, `session`, `while_enabled`, `persistent`, `full_access` |
| effective_scope_json | TEXT | NOT NULL | Host-normalized scope |
| decision | TEXT | NOT NULL | `active`, `denied`, `revoked`, `expired` |
| owner_assertion_hash | TEXT | NOT NULL | No biometric material |
| approved_via | TEXT | NOT NULL | `native_click`, `native_biometric` |
| granted_at | TEXT | NOT NULL | |
| expires_at | TEXT | NULL | Required for once/session |
| revoked_at | TEXT | NULL | |
| revision | INTEGER | NOT NULL DEFAULT 1 | |

Only one active `while_enabled`, `persistent` or `full_access` grant per plugin
revision. Index `(plugin_revision_id, decision, expires_at)`.

### `plugin_installations`

Represents one retained revision's installation and production lifecycle.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `install-*` |
| plugin_revision_id | TEXT | FK plugin_revisions, UNIQUE, NOT NULL | |
| installation_state | TEXT | NOT NULL | `staged`, `installed`, `enabled`, `disabled`, `quarantined`, `trashed` |
| compatibility_state | TEXT | NOT NULL | `unknown`, `compatible`, `incompatible`, `needs_retest` |
| health_state | TEXT | NOT NULL | `unknown`, `healthy`, `degraded`, `unhealthy` |
| active_grant_id | TEXT | FK permission_grants, NULL | |
| installed_at | TEXT | NULL | |
| enabled_at | TEXT | NULL | |
| last_health_at | TEXT | NULL | |
| quarantine_code | TEXT | NULL | Stable reason |
| revision | INTEGER | NOT NULL DEFAULT 1 | |
| updated_at | TEXT | NOT NULL | |

Indexes: `(installation_state, updated_at DESC)`,
`(compatibility_state, health_state)`.

### `runtime_instances`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `runtime-*` |
| installation_id | TEXT | FK plugin_installations, NOT NULL | |
| active_set_generation | INTEGER | NOT NULL | Exact config generation |
| process_id | INTEGER | NULL | Same-user diagnostic only |
| socket_relpath | TEXT | NOT NULL UNIQUE | Under `runtime/` |
| state | TEXT | NOT NULL | `starting`, `healthy`, `stopping`, `stopped`, `crashed` |
| started_at | TEXT | NOT NULL | |
| heartbeat_at | TEXT | NULL | |
| stopped_at | TEXT | NULL | |
| exit_code | INTEGER | NULL | |

Only one live runtime per installation. Process IDs never authorize RPC.

### `active_sets` and `active_set_members`

`active_sets` stores transactional production generations.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| generation | INTEGER | PK, AUTOINCREMENT | Monotonic |
| state | TEXT | NOT NULL | `candidate`, `active`, `failed`, `superseded`, `rolled_back` |
| config_hash | TEXT | NOT NULL | Projected OpenClaw config |
| gateway_version | TEXT | NOT NULL | |
| harness_api_version | TEXT | NOT NULL | |
| previous_generation | INTEGER | FK self, NULL | Rollback parent |
| health_receipt_json | TEXT | NULL | Redacted |
| created_at | TEXT | NOT NULL | |
| activated_at | TEXT | NULL | |

`active_set_members` fields: `generation` FK, `installation_id` FK,
`plugin_revision_id` FK, `grant_id` FK, `public_plugin_id`, `artifact_hash`,
`tool_schema_hash`; primary key `(generation, installation_id)`, unique
`(generation, public_plugin_id)` to prevent OpenClaw ID collision.

At most one `active_sets.state='active'`. A member's hashes must equal its
revision/evidence/grant records before projection.

## Package, migration and audit entities

### `package_records`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id | TEXT | PK | `package-*` |
| direction | TEXT | NOT NULL | `import`, `export` |
| plugin_revision_id | TEXT | FK plugin_revisions, NULL until accepted | |
| archive_hash | TEXT | NOT NULL UNIQUE | SHA-256 original bytes |
| archive_relpath | TEXT | NOT NULL UNIQUE | Intake/export location |
| schema_version | INTEGER | NOT NULL | `.jarvis-plugin` schema |
| signature_state | TEXT | NOT NULL | `absent`, `valid`, `invalid`, `unknown_key` |
| signer_key_id | TEXT | NULL | |
| inspection_state | TEXT | NOT NULL | `pending`, `accepted`, `rejected`, `quarantined` |
| inspection_json | TEXT | NOT NULL | Counts, sizes, compatibility, stable warnings |
| created_at | TEXT | NOT NULL | |
| expires_at | TEXT | NULL | Intake cleanup |

Index `(direction, inspection_state, created_at DESC)`.

### `schema_migrations`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| version | INTEGER | PK | Forward-only version |
| app_version | TEXT | NOT NULL | Initiating release |
| checksum | TEXT | NOT NULL | Migration source checksum |
| state | TEXT | NOT NULL | `running`, `applied`, `failed` |
| backup_relpath | TEXT | NOT NULL | Snapshot created before change |
| started_at | TEXT | NOT NULL | |
| completed_at | TEXT | NULL | |
| error_code | TEXT | NULL | Redacted |

### `audit_events`

Append-only; application APIs expose no update or delete operation.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| sequence | INTEGER | PK, AUTOINCREMENT | Stable ordering |
| id | TEXT | UNIQUE, NOT NULL | `audit-*` |
| occurred_at | TEXT | NOT NULL | UTC |
| actor | TEXT | NOT NULL | `owner`, `agent`, `host`, `plugin`, `system` |
| action | TEXT | NOT NULL | Stable event code |
| resource_kind | TEXT | NOT NULL | |
| resource_id | TEXT | NULL | Opaque local ID |
| correlation_id | TEXT | NOT NULL | Job/activation flow |
| decision | TEXT | NULL | Safe outcome |
| details_json | TEXT | NOT NULL | Allowlisted redacted metadata |
| previous_hash | TEXT | NULL | Tamper-evident local chain |
| event_hash | TEXT | NOT NULL UNIQUE | Canonical event hash |

Indexes: `(occurred_at DESC)`, `(resource_kind, resource_id, sequence DESC)`,
`(correlation_id, sequence)`.

## Retention and deletion

- Worktrees may be compacted after an immutable revision and export exist;
  immutable revisions used by an installation, active set or package record
  cannot be deleted.
- Trash retains recoverable plugin content for 30 days by default. Permanent
  deletion requires no active references, an owner assertion and a tombstone
  audit event.
- Job logs and detailed evidence default to 90 days; evidence referenced by the
  active revision is retained while active. Redacted audit metadata is retained
  until the owner uses a future whole-vault privacy reset.
- Pre-migration backups retain the last three successful schema generations and
  the most recent failed migration snapshot, subject to available disk space.
