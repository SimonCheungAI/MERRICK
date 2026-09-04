# Data Model

All records are local under `~/Library/Application Support/JarvisStark/` with owner-only permissions. Secrets remain in Keychain, never here.

## ProviderProfile

Existing `provider-profile.json` gains no secret fields.

| Field | Type | Constraints |
|---|---|---|
| provider | string | supported provider identifier |
| model | string | printable, max 120 |
| baseURL | URL? | HTTPS only |
| authMode | enum | `api`, `jarvis-oauth`, `cli` |
| updatedAt | UTC ISO-8601 | required |
| verifiedAt | UTC ISO-8601? | updated only after connector verification |

## AccessRoot

**Table/file:** `access-policy.json`, schema version 1.

| Field | Type | Constraints |
|---|---|---|
| id | UUID | stable root identifier |
| displayName | string | max 120; user-facing only |
| path | string | canonical absolute directory, native-written |
| read | boolean | defaults false |
| write | boolean | defaults false; implies read |
| addedAt / updatedAt | UTC ISO-8601 | required |

Policy also records `directAutomationEnabled`, `allowGeneralGUI`, and schema version. Protected MERRICK state, Keychain, hidden credential roots and system roots are hard-denied even if an ancestor was chosen.

## AuditOperation

**Table:** `file_audit_operations`.

| Field | Type | Constraints |
|---|---|---|
| id | UUID | primary key |
| started_at / completed_at | UTC ISO-8601 | indexed by completed time |
| turn_id | string | no transcript content |
| request_digest | SHA-256 | correlation only |
| root_id | UUID | indexed; must reference policy root at execution |
| operation | enum | create, update, patch, rename, quarantine_delete, restore |
| source_path / target_path | string | root-relative, max 2048 |
| status | enum | pending, completed, failed, rolled_back |
| error_code | string? | stable public code, no secrets |
| before_hash / after_hash | SHA-256? | content identity |
| before_bytes / after_bytes | integer? | non-negative |
| reversible_until | UTC ISO-8601? | snapshot retention expiry |

Indexes: `(completed_at DESC)`, `(root_id, completed_at DESC)`, `(source_path, completed_at DESC)`.

## FileRevision

**Table:** `file_audit_revisions` plus private snapshot blobs.

| Field | Type | Constraints |
|---|---|---|
| id | UUID | primary key |
| operation_id | UUID | foreign key AuditOperation |
| direction | enum | before, after |
| storage_kind | enum | text_diff, snapshot, hash_only |
| blob_path | string? | private relative path only |
| sha256 | SHA-256 | required |
| bytes | integer | required |

Text snapshots are retained up to 2 MiB; binary snapshots up to 16 MiB; larger files get hash-only audit with a visible non-reversible label. Quarantined deletes retain the original object until expiry.
