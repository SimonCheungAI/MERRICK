# Architecture

## Pattern

Use the ADR-0001 modular monolith: native host owns credentials, macOS grants and directory selection; Python application workflows own policy checks and transactional audit; OpenClaw receives a narrow, current-turn-bound file/GUI capability through adapters. No additional daemon, service or cloud database is introduced.

## Components

```text
Settings UI (web/app.js)
  │ trusted bridge messages
  ▼
Native Host (desktop/MerrickApp.swift)
  ├─ ProviderConnectionPort → Keychain + app-owned OAuth child process
  └─ AccessPolicyPort → NSOpenPanel + protected access-policy.json
                                      │ environment / local bridge
                                      ▼
Application workflows (server/)
  ├─ Provider status adapter
  ├─ AccessPolicy service
  ├─ AuditedFileTransaction service ──► revisions + audit SQLite
  └─ DesktopAction workflow ──────────► native bridge
                                      ▲
                         turn-bound adapter capability
                                      │
                              OpenClaw main agent
```

## Key flows

### In-app provider connection

1. Settings requests provider state from the native host.
2. For an API key, native validation writes it to Keychain and writes a non-secret provider profile with mode `api`.
3. For subscription OAuth, native starts the app-owned connector with captured output. The UI receives a code/URL/status and opens the browser from a button; it never invokes Terminal.
4. Native detects the isolated MERRICK auth profile, persists non-secret metadata, and restarts only the MERRICK backend/Gateway.

### Audited file mutation

1. The current utterance routes to a file workflow only when it is a direct request and access policy enables the target operation.
2. The workflow resolves the path under an authorized root and rejects traversal, protected state, and out-of-root paths.
3. It creates an audit operation and captures a bounded pre-image/hash before writing.
4. The OpenClaw-facing adapter applies the requested atomic write/patch/move/quarantine-delete.
5. The workflow captures the result, stores a bounded revision, completes the audit record, and emits a concise completed/failed event.
6. Restore uses the audit record's pre-image and is itself an audited mutation.

## Authority boundaries

- The model proposes work but never receives Keychain secrets, an unrestricted shell, a raw system path, or a capability token.
- Native directory selection is the only way to widen file roots. The UI cannot forge a root or write profile files directly.
- The audit service is the sole mutation path for broad file access. Existing workspace library writes remain compatibility fallback until migrated.
- Browser/page/file contents are untrusted data and cannot widen access, trigger a provider switch, or purge an audit record.
- Desktop actions still require current-turn intent binding and macOS Accessibility; broad GUI support removes fixed app aliases, not account/password/security UI exclusions.

## Latency and scale

Policy and audit use local SQLite with WAL mode and indexed time/root/path queries. Revision capture is asynchronous only after the pre-image is safely retained; small text writes remain synchronous and atomic. Audit history is paginated and snapshots have retention/size caps.
