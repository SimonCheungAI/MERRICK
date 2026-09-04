# API Contracts

## Common rules

- Base path: `/api/v1/harness`; WebSocket events use `schema_version: 1`.
- The loopback bridge requires the existing per-launch session secret and exact
  trusted origin. Every resource lookup also verifies the local owner scope.
- Mutation requests require `Idempotency-Key`; edits require `If-Match` with the
  current entity revision. Expensive operations return `202` with a durable job.
- Persistent permission, Full Access, activation, rollback and permanent delete
  additionally require a short-lived `owner_assertion` minted by the native
  host for the exact action/resource/hash. The Web HUD cannot mint assertions.
- JSON request bodies default to 256 KiB maximum. Plugin archives use a separate
  streaming upload endpoint with a 50 MiB compressed limit.
- All inputs are server-validated against versioned Pydantic/JSON Schema. JSON
  fields use `snake_case`, resource paths use plural REST nouns and timestamps
  are UTC ISO-8601. Plugin-provided strings are always escaped on output.
- List responses use `{items, next_cursor}` and default `limit=50`, maximum 100.
- Per owner session, ordinary reads are limited to 120 requests/minute, mutations
  to 30/minute, job creation to 10/minute and package upload/owner-assertion
  verification to 5/minute. Expensive job concurrency is separately capped.
  Failed/expired assertion attempts use progressive local backoff and audit.
- No API accepts a source checkout path, OpenClaw config path, shell command,
  environment map, secret value or arbitrary export include path.

## Common envelopes

```json
{
  "data": {},
  "meta": {"schema_version": 1, "correlation_id": "corr-…"}
}
```

```json
{
  "error": {
    "code": "PERMISSION_EXPANSION_REQUIRES_APPROVAL",
    "message": "Review the expanded permission scope before continuing.",
    "retryable": false,
    "correlation_id": "corr-…",
    "recovery": ["open_permission_sheet"]
  }
}
```

## Projects and revisions

### `POST /api/v1/harness/projects`

Creates a Harness workspace. Auth: verified local owner session. Body:

```json
{
  "display_name": "Meeting follow-ups",
  "requested_capability": "Turn selected meeting notes into task drafts",
  "target_profile": "sandboxed_harness",
  "source": "text"
}
```

`target_profile` defaults to `sandboxed_harness`; selecting
`native_full_trust` records intent but does not authorize activation. Success
`201`: project summary, worktree status and revision number.

### Project endpoints

| Method and path | Purpose | Success |
|---|---|---|
| `GET /api/v1/harness/projects` | Search/filter projects by `status`, `query`, `cursor`, `limit` | `200` summaries |
| `GET /api/v1/harness/projects/{id}` | Project, head revision, recent jobs/evidence | `200` detail |
| `PATCH /api/v1/harness/projects/{id}` | Rename/describe using `If-Match` | `200` revised project |
| `DELETE /api/v1/harness/projects/{id}` | Soft-delete an idle project | `202` trash job |
| `POST /api/v1/harness/projects/{id}/restore` | Restore recoverable project | `200` project |
| `POST /api/v1/harness/projects/{id}/revisions` | Snapshot current worktree into immutable revision | `201` revision |
| `GET /api/v1/harness/revisions/{id}` | Manifest, hashes, compatibility, permissions, evidence | `200` detail |
| `GET /api/v1/harness/revisions/{id}/diff` | Bounded diff against parent or `base_revision_id` | `200` structured/text diff |

The diff endpoint truncates by lines/bytes and exposes a download ticket for a
larger local artifact. It never renders untrusted HTML from source or README.

## Authoring and verification jobs

### `POST /api/v1/harness/jobs`

Creates one durable operation. Auth: owner session; the model-facing adapter may
call only `author`, `build`, `test` and `preview`, never activation or grants.

```json
{
  "kind": "author",
  "project_id": "project-…",
  "plugin_revision_id": null,
  "instruction": "Add a read-only Linear issue lookup tool",
  "limits": {"wall_seconds": 900, "max_iterations": 12}
}
```

`instruction` is allowed only for `author` and is stored in the mutable project,
not audit metadata or export provenance. Host policy clamps all limits. Success
`202`: `{job_id, status:"queued"}`.

| Method and path | Purpose | Success |
|---|---|---|
| `GET /api/v1/harness/jobs` | Filter by kind/status/project with cursor | `200` jobs |
| `GET /api/v1/harness/jobs/{id}` | State, progress, steps, safe result | `200` job |
| `POST /api/v1/harness/jobs/{id}/cancel` | Idempotently request cancellation | `202` cancelling/cancelled |
| `POST /api/v1/harness/jobs/{id}/resume` | Resume an interrupted resumable job | `202` queued |
| `GET /api/v1/harness/revisions/{id}/evidence` | Paginated immutable evidence summaries | `200` evidence |
| `GET /api/v1/harness/evidence/{id}` | Checks, hashes, observed permissions | `200` detail |

An `activate` job can only be created through the approval decision endpoint;
clients cannot submit `kind:"activate"` here.

## Permission preview and decisions

### `POST /api/v1/harness/revisions/{id}/permission-preview`

Computes, but does not grant, the effective scope. Body:

```json
{
  "requested_mode": "while_enabled",
  "scope_edits": {
    "filesystem": [{"root_ref": "workspace_documents", "modes": ["read"]}],
    "network": [{"host": "api.linear.app", "methods": ["POST"]}]
  }
}
```

Success `200`: exact revision/declaration hashes, normalized scope, R0–R3/FULL
risk, declared-versus-observed differences, OS permission gaps, incompatible
requests and a `preview_hash`. Client edits may only narrow declared scope.

### `POST /api/v1/harness/revisions/{id}/permission-decision`

Trusted-host-only decision for the exact preview.

```json
{
  "decision": "approve",
  "mode": "full_access",
  "preview_hash": "sha256:…",
  "owner_assertion": "opaque-native-assertion"
}
```

Success `201`: grant metadata without reusable authorization material. Fails if
the revision, declaration set, preview, owner session, OS permission state or
assertion changed/expired. `deny` requires no privileged assertion but remains
audited. Voice and model tools can request a permission sheet but cannot submit
this endpoint.

### Grant endpoints

| Method and path | Purpose | Success |
|---|---|---|
| `GET /api/v1/harness/grants` | Paginated active/history projection | `200` redacted grants |
| `GET /api/v1/harness/grants/{id}` | Effective normalized scope | `200` detail |
| `POST /api/v1/harness/grants/{id}/revoke` | Immediate broker revocation; owner assertion for persistent/FULL | `200` revoked + runtime effect |

Scope expansion always creates a new preview and grant; a grant row is never
edited to broaden authority.

## Installation, activation and recovery

### `POST /api/v1/harness/revisions/{id}/activate`

Auth: trusted owner assertion. Body:

```json
{
  "grant_id": "pgrant-…",
  "evidence_id": "evidence-…",
  "expected_active_generation": 12,
  "owner_assertion": "opaque-native-assertion"
}
```

The server verifies that evidence and grant hashes match the exact artifact,
creates a candidate active set and returns `202 {job_id, candidate_generation}`.
The job stages, projects, validates, refreshes/restarts, health-checks and commits
or rolls back as one lifecycle transaction.

| Method and path | Purpose | Success |
|---|---|---|
| `GET /api/v1/harness/library` | Installed/generated/imported/core inventory; source/status/query/cursor filters | `200` summaries |
| `GET /api/v1/harness/installations/{id}` | Revision, grants, health and rollback options | `200` detail |
| `POST /api/v1/harness/installations/{id}/disable` | Stop worker/remove tools, retain code/grants according to policy | `202` lifecycle job |
| `POST /api/v1/harness/installations/{id}/enable` | Revalidate current revision/grant before enable | `202` lifecycle job |
| `POST /api/v1/harness/installations/{id}/rollback` | Activate selected prior compatible revision and its valid grant | `202` rollback job |
| `DELETE /api/v1/harness/installations/{id}` | Soft-uninstall to trash | `202` lifecycle job |
| `POST /api/v1/harness/installations/{id}/permanent-delete` | Delete unreferenced trashed content with owner assertion | `202` delete job |
| `GET /api/v1/harness/runtime/health` | Gateway/bridge/worker/active generation status | `200` health |
| `POST /api/v1/harness/runtime/safe-mode` | Disable all user plugins for next/current boot | `202` recovery job |
| `GET /api/v1/harness/active-sets` | Active/failed/rollback generations | `200` bounded history |

Rollback never restores an expired or broader grant. If no valid historical
grant exists, it stops at `waiting_owner` with a permission preview.

## Export

### `POST /api/v1/harness/revisions/{id}/exports`

Body: `{include_evidence: true, sign_with_local_identity: false}`. The include
set is fixed by server schema. Success `202`: export job. Export always excludes
grants, secrets, prompts, raw logs, absolute paths, caches and dependencies.

| Method and path | Purpose | Success |
|---|---|---|
| `GET /api/v1/harness/exports/{package_id}` | Package hash/signature/size/job status | `200` metadata |
| `POST /api/v1/harness/exports/{package_id}/download-ticket` | Mint one-use, 60-second ticket | `201` ticket |
| `GET /api/v1/harness/download/{ticket}` | Stream exact immutable archive | `200 application/vnd.jarvis.plugin+zip` |

Download tickets are bound to package hash, current owner session and one use.

## Import/upload

### `POST /api/v1/harness/imports`

Streams one archive with content type `application/vnd.jarvis.plugin+zip` to a
randomized intake file. `Content-Length` is required and limited to 50 MiB; the
server also enforces streaming bytes and hashes the raw archive. Filenames are
display metadata only. Success `202`: inspection job and package ID.

| Method and path | Purpose | Success |
|---|---|---|
| `GET /api/v1/harness/imports/{package_id}` | Inspection status, metadata, compatibility, signature, permission summary | `200` detail |
| `GET /api/v1/harness/imports/{package_id}/files` | Paginated canonical file inventory, no extraction execution | `200` entries |
| `POST /api/v1/harness/imports/{package_id}/accept` | Copy accepted source into immutable vault revision | `201` revision/project |
| `DELETE /api/v1/harness/imports/{package_id}` | Delete pending/rejected intake file | `204` |

`accept` does not build, grant or activate. Invalid signatures, hash mismatch,
archive policy violations and unsupported schemas cannot be overridden by Full
Access because they are package-integrity failures, not runtime permissions.

## Compatibility, migrations and audit

| Method and path | Purpose | Success |
|---|---|---|
| `GET /api/v1/harness/compatibility` | Current app/OpenClaw/Harness ABI and quarantined counts | `200` summary |
| `POST /api/v1/harness/revisions/{id}/revalidate` | Run compatibility and verification against current runtime | `202` job |
| `GET /api/v1/harness/migrations` | Redacted migration/backup status | `200` history |
| `GET /api/v1/harness/audit-events` | Filter by resource/action/time/correlation/cursor | `200` redacted events |

There is no API to run an arbitrary migration, edit a schema version, delete an
audit event or select a backup path. Startup owns migrations.

## WebSocket messages

All events include `schema_version`, `event_id`, `correlation_id`, `occurred_at`
and `payload`. Client commands include `request_id`; the server acknowledges or
returns the common error envelope.

| Event | Direction | Purpose |
|---|---|---|
| `harness.project.changed` | server→HUD | Project/head revision state |
| `harness.job.progress` | server→HUD | Step, percent and bounded activity text |
| `harness.job.waiting_owner` | server→HUD | Exact non-authorizing prompt to open native sheet |
| `harness.job.completed` | server→HUD | Evidence/revision/package/install references |
| `harness.job.failed` | server→HUD | Error code and safe recovery actions |
| `harness.permission.preview` | server→HUD/native | Normalized scope and hashes |
| `harness.permission.decided` | native→server, server→HUD | Decision acknowledgement, never raw token |
| `harness.installation.changed` | server→HUD | Installed/enabled/quarantined/health state |
| `harness.runtime.changed` | server→HUD | Gateway generation and worker health |
| `harness.import.inspected` | server→HUD | Package safety/compatibility summary |
| `harness.migration.changed` | server→HUD | Startup migration/recovery status |

## Model-facing OpenClaw tools

The model receives a strictly smaller surface than the owner UI:

| Tool | Allowed effect |
|---|---|
| `jarvis_harness_project_create` | Create sandboxed draft from the current owner request |
| `jarvis_harness_project_inspect` | Read selected project/revision/evidence summaries |
| `jarvis_harness_author` | Start bounded source-generation job |
| `jarvis_harness_verify` | Build/test/preview exact draft/revision |
| `jarvis_harness_job_status` | Read/cancel current job tied to the request |
| `jarvis_harness_request_activation` | Produce owner-visible permission sheet only |
| `jarvis_harness_repair_revision` | Create a new child revision; never mutate active source |

There is deliberately no model tool for approval, Full Access, install commit,
permanent delete, signing-key access, migration, Safe Mode exit or audit deletion.

## Status and authorization errors

| Status | Meaning |
|---:|---|
| `400` | Schema/limit validation failed |
| `401` | Loopback session missing/expired |
| `403` | Owner assertion/capability absent or scope denied |
| `404` | Resource absent or not owned |
| `409` | Revision, lifecycle generation, job lease or public ID conflict |
| `410` | Download ticket/package intake expired |
| `413` | Compressed/expanded/file-count limit exceeded |
| `415` | Unsupported package/content type |
| `422` | Valid syntax but incompatible/unsafe package or plugin |
| `423` | Project, registry, Gateway restart or migration lock held |
| `429` | Job/runtime/rate budget exceeded |
| `503` | Gateway, sandbox, vault or migration recovery unavailable |
