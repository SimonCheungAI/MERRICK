# Requirements

## Feasibility

Complexity: Complex. The work crosses native macOS permissions, Keychain/OAuth, OpenClaw policy, model tooling, local persistence and the settings UI. Estimated effort: 3–5 independently shippable slices. Verdict: proceed.

## Functional requirements

- FR-01: A user can select a provider and connect from MERRICK Settings without manually opening a terminal.
- FR-02: API-key providers store the key only in macOS Keychain; Settings never redisplays it.
- FR-03: Codex and Claude subscription flows run as an app-owned child process. MERRICK displays progress, device code and a browser-open action, then detects completion and restarts only its own model layer.
- FR-04: A user can inspect the active provider, model, connection type and last verified time, reconnect, or disconnect it from Settings.
- FR-05: A user can enable Direct Automation once, choose read roots and write roots with native directory pickers, and later revoke any root.
- FR-06: Read access may cover user-selected folders; write/create/edit/rename/delete operations may occur only inside user-authorized write roots. macOS-protected locations still require macOS permission.
- FR-07: The assistant can perform ordinary GUI operations beyond a fixed application alias list when Accessibility has been granted and the request is tied to the active turn.
- FR-08: Every file mutation is recorded before completion: operation, request/turn identifier, timestamp, root, paths, before/after hashes, byte counts, result and recoverability.
- FR-09: Text-file mutations retain bounded before/after revisions; delete is implemented as recoverable quarantine inside MERRICK private state. A user can inspect and restore a revision from Settings.
- FR-10: The existing workspace-only library remains available as a safe fallback while the broader access feature is disabled or fails.

## Non-functional requirements

- NFR-01: No API key, OAuth token, document content or credential appears in the HUD, audit row, trace log, Workspace or Git repository.
- NFR-02: Policy lookup and audit append add under 50 ms on the local path; they never wait for a cloud model.
- NFR-03: A failed new access path preserves the current workspace-only behaviour and produces an actionable local error.
- NFR-04: All persisted timestamps are UTC ISO-8601. Paths are stored relative to an access-root identifier where possible.
- NFR-05: Unit tests use a temporary policy and audit store; they never start the live Gateway.

## Constraints and assumptions

- C-01: This is a native macOS first implementation. Portability is maintained through host ports, not claimed as shipped for Windows/Linux.
- C-02: OAuth account consent cannot be embedded or bypassed; the browser is the account authority. The terminal is not part of the user-facing flow.
- C-03: Direct Automation means no repeated per-action confirmation inside authorized roots, not unrestricted access to secrets, passwords, payment, account-consent or system-security interfaces.
- C-04: A selected write root is the authority boundary for a file turn. Content of files/web pages cannot expand it.
- C-05: Large/binary files are hashed and recorded; only bounded revision snapshots are retained.

## Resolved questions

- OQ-01: Should broad access be on by default? No. It is explicitly enabled once in Settings, then remains direct within selected roots.
- OQ-02: Can MERRICK silently delete? Yes only inside a write root and only through recoverable quarantine; permanent purge stays an explicit settings action.
- OQ-03: Does audit content leave the Mac? No. It is local application state and excluded from normal Workspace/Git backup.
