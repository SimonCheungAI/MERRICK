# Error and Recovery Contract

## Error principles

- Every failure names the lifecycle phase, preserves the last known-good active
  set and returns a stable code plus safe recovery actions.
- Errors never include stack traces, prompts, secrets, environment variables,
  raw command output, personal file paths or imported README/source text.
- Retrying a job is idempotent or creates a new immutable revision. The system
  never resumes by mutating an already active artifact.
- Full Access can resolve a denied runtime capability; it cannot override
  corrupt archives, invalid hashes, incompatible ABI, failed owner identity,
  core immutability or migration integrity.

## Taxonomy

| Family | Example codes | HTTP | Behaviour |
|---|---|---:|---|
| Request | `INVALID_INPUT`, `LIMIT_OUT_OF_RANGE`, `UNSUPPORTED_JOB_KIND` | 400 | Reject before state change |
| Authentication | `BRIDGE_SESSION_EXPIRED`, `OWNER_VERIFICATION_REQUIRED` | 401/428 | Preserve job and open trusted verification |
| Authorization | `OWNER_ASSERTION_REQUIRED`, `CAPABILITY_DENIED`, `FULL_ACCESS_REQUIRED`, `PERMISSION_EXPANSION_REQUIRES_APPROVAL` | 403/409 | Never auto-broaden; request exact native sheet |
| Ownership | `RESOURCE_NOT_OWNED`, `PROJECT_SCOPE_MISMATCH` | 403 | Fail closed and security-audit |
| Project | `PROJECT_BUSY`, `REVISION_CONFLICT`, `WORKTREE_INVALID`, `PROJECT_TRASHED` | 409/423 | Wait, refresh revision or restore |
| Authoring | `AUTHOR_BUDGET_EXCEEDED`, `AUTHOR_INTERRUPTED`, `UNSAFE_INSTRUCTION_BLOCKED` | 409/429 | Preserve draft and evidence; explicit resume/repair |
| Dependency/build | `LOCKFILE_REQUIRED`, `DEPENDENCY_NOT_ALLOWED`, `INSTALL_SCRIPT_BLOCKED`, `BUILD_FAILED`, `TYPECHECK_FAILED` | 409/422 | No production staging; show bounded diagnostics |
| Verification | `TEST_FAILED`, `STATIC_SCAN_FAILED`, `OPENCLAW_VALIDATE_FAILED`, `PREVIEW_HEALTH_FAILED`, `UNDECLARED_CAPABILITY_OBSERVED` | 422 | Keep revision non-activatable; create repair revision |
| Sandbox | `SANDBOX_UNAVAILABLE`, `SANDBOX_POLICY_REJECTED`, `WORKER_LIMIT_EXCEEDED`, `WORKER_CRASHED` | 409/503 | Terminate worker; do not fall back to unsandboxed mode |
| Package | `PACKAGE_TOO_LARGE`, `PACKAGE_BOMB_BLOCKED`, `ARCHIVE_PATH_INVALID`, `ARCHIVE_LINK_BLOCKED`, `CONTENT_HASH_MISMATCH`, `SIGNATURE_INVALID`, `PACKAGE_SCHEMA_UNSUPPORTED` | 413/415/422 | Quarantine/delete intake; cannot override with Full Access |
| Compatibility | `HARNESS_API_INCOMPATIBLE`, `OPENCLAW_INCOMPATIBLE`, `NODE_INCOMPATIBLE`, `TOOL_SCHEMA_DRIFT`, `PLUGIN_ID_CONFLICT` | 409/422 | Retain and quarantine; repair or choose active lineage |
| Grant | `GRANT_EXPIRED`, `GRANT_REVOKED`, `GRANT_HASH_MISMATCH`, `OS_PERMISSION_MISSING`, `SECRET_HANDLE_MISSING` | 403/409 | Stop exact call/worker; re-preview or connect in host UI |
| Activation | `ACTIVE_SET_CONFLICT`, `CONFIG_VALIDATION_FAILED`, `GATEWAY_RESTART_FAILED`, `BRIDGE_GENERATION_MISMATCH`, `ACTIVATION_HEALTH_FAILED`, `ROLLBACK_FAILED` | 409/503 | Roll back candidate; Safe Mode if last-good fails |
| Migration/storage | `VAULT_UNAVAILABLE`, `DISK_SPACE_LOW`, `DATABASE_BUSY`, `INTEGRITY_CHECK_FAILED`, `BACKUP_FAILED`, `MIGRATION_FAILED` | 423/507/503 | No mutation; read-only recovery or restore snapshot |
| Runtime | `PLUGIN_TIMEOUT`, `PLUGIN_RATE_LIMITED`, `BROKER_PROTOCOL_ERROR`, `PLUGIN_UNHEALTHY`, `PLUGIN_QUARANTINED` | 409/429/503 | Kill/restart bounded worker; circuit-breaker/quarantine |
| Export/download | `EXPORT_NOT_READY`, `EXPORT_POLICY_VIOLATION`, `DOWNLOAD_TICKET_EXPIRED`, `DOWNLOAD_ALREADY_USED` | 409/410/422 | Regenerate from immutable revision |
| Internal | `INTERNAL_ERROR` | 500 | Correlation ID only; no automatic activation retry |

## Retry matrix

| Operation | Automatic retry | Limit | Rule |
|---|---|---:|---|
| SQLite read / busy transaction | Yes | 3 with jitter | No retry during migration lock |
| Agent author step | Only safe transport failure | 1 | Resume same bounded job; never duplicate revision commit |
| Dependency cache download | Yes | 2 | Exact pinned hash and allowlisted registry only |
| Build/type-check/unit test | No blind retry | 0 | Same input should be deterministic; request repair |
| Preview worker start | Yes | 1 | Fresh runtime directory and no extra permissions |
| Plugin runtime read call | Yes if tool declares idempotent | 1 | Same call ID and grant |
| Plugin write/external effect | No generic retry | 0 | Plugin contract must provide domain idempotency/reconciliation |
| Gateway restart | Yes | 1 | Then restore previous generation |
| Activation health check | No | 0 | Roll back candidate immediately |
| Import inspection | No | 0 | Identical archive hash reuses prior inspection |
| Export build | Yes | 1 | Deterministic immutable input |
| Schema migration | No in same boot | 0 | Restore/check snapshot, enter recovery mode |

## Circuit breakers

- One plugin worker: open after three crashes or timeouts in ten minutes;
  installation becomes `unhealthy`, then `quarantined` if restart also fails.
- Harness authoring: stop after configured iteration, token, wall-time, output or
  file-count budget; preserve the current worktree without activating it.
- Gateway activation: one failed candidate health check opens the activation
  breaker until rollback completes. No other plugin mutations run concurrently.
- Package intake: three policy failures for the same archive hash suppress
  repeated inspection until the owner chooses a different file.
- Dependency source: checksum or signature mismatch disables that source for the
  session; no fallback to an unpinned registry.
- Vault/migration: integrity or backup failure switches Harness to read-only;
  ordinary MERRICK conversation continues without user plugins when safe.

## Cancellation semantics

- Queued jobs cancel immediately. Author/build/test jobs request cooperative
  cancellation, then terminate the process tree after a bounded grace period.
- Preview cancellation always kills the disposable Gateway and worker and
  removes only runtime temporary data.
- Activation cancellation is allowed before config swap. After swap it becomes
  a rollback request and does not terminate the Gateway mid-write.
- Import cancellation removes only the randomized intake file after all readers
  close. Export cancellation never deletes the underlying revision.
- Migration cannot be user-cancelled after the transaction begins; the native
  host shows recovery progress and relies on crash-safe rollback.

## Startup and crash recovery

1. Acquire the single registry/migration lock and verify the vault root is an
   owned, private directory—not a symlink.
2. Run SQLite quick/integrity checks. If they fail, keep user plugins disabled
   and offer snapshot restore; never initialize an empty registry over damage.
3. Mark expired job leases `interrupted`; requeue only read-only inspection and
   deterministic export jobs. Authoring waits for owner resume.
4. If a candidate active set lacks a matching health receipt, restore its
   `previous_generation` before starting the production Gateway.
5. Remove stale runtime sockets/directories only after matching registry
   instances are stopped; never delete revision or evidence directories.
6. Start the bridge in Safe Mode, then load the committed active generation and
   require exact artifact/tool/grant hashes from each worker.
7. Quarantine only the incompatible/unhealthy member. If bridge or Gateway
   health fails globally, keep all user plugins disabled and retain the vault.

## Rollback failure

Rollback first restores the previous projected config and active-set generation,
then restarts the Gateway. If this fails, MERRICK starts the signed core
Gateway with no user plugin members. The HUD remains available with a recovery
receipt, export access to all retained revisions, and controls to retry one
plugin at a time. It never deletes the alleged failing plugin automatically.
