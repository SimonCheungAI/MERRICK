---
status: accepted
date: 2026-08-24
decision-makers: Project owner
consulted: Codex
informed: Future MERRICK maintainers and coding agents
---

# ADR-0002: Adopt App-Owned Provider Connection and Audited Direct Access

## Context

MERRICK already stores API keys in macOS Keychain and offers a Settings panel, but its isolated Codex subscription connection opens `scripts/login-openclaw.sh` in Terminal. Separately, the Gateway template confines filesystem work to one workspace and the action planner/natural GUI flow rejects file writes and many general desktop requests. This makes the assistant feel blocked even when the user wants it to perform ordinary work.

The product needs a direct assistant mode without losing attribution or the ability to inspect and reverse its changes. Granting OpenClaw a raw unrestricted shell/filesystem would bypass the native bridge and makes reliable auditing impossible.

## Decision

Use an app-owned provider connection flow and a policy-governed, audited direct-access workflow.

- The native macOS host owns Keychain credentials, account-authorization presentation, connection state and directory selection.
- OAuth browser consent remains external to the app account, but MERRICK shows progress/device-code state and launches the browser itself; Terminal is not part of the user workflow.
- A user enables Direct Automation once in Settings and chooses read/write roots. Direct actions do not require repeated confirmation inside those roots.
- Broad file mutation occurs only through an audited transaction port. It captures a pre-image before mutation, persists an append-only operation record, retains bounded revisions, and treats deletion as recoverable quarantine.
- OpenClaw receives narrow, current-turn-bound file/GUI capabilities; it does not receive arbitrary shell, credentials, raw all-path filesystem or audit-purge access.
- Existing workspace-only library and fixed action bridge remain compatibility fallbacks until corresponding slices are verified.

## Consequences

- Good: provider connection is discoverable and avoids exposing a Terminal workflow to normal users.
- Good: users can directly authorise productive file/desktop work and later inspect every mutation.
- Good: audit/recovery stays reliable because there is one mutation path.
- Bad: access configuration, audit retention and native permission failures add local-state complexity.
- Bad: the app cannot bypass OAuth browser consent or macOS TCC permission prompts.
- Neutral: no provider credential is added to source, Workspace, logs, memory or Git.

## Alternatives Considered

- Keep Terminal/device-code onboarding and workspace-only access: low engineering cost, but fails the requested usability goal.
- Enable OpenClaw `group:fs` and runtime globally: broad capability, but no dependable audit or recovery boundary.
- Require per-action confirmations: safer by interaction, but repeats the latency/blocking experience the user rejected.
- App-owned provider connection plus audited roots: selected because it provides direct operation after one explicit configuration while preserving traceability and rollback.

## Implementation and Verification

Follow the validated package at `docs/blueprints/2026-08-24-provider-and-audited-access/` in order. Each slice must be feature-flagged until verified, maintain the old path as fallback, and be revertible with `git revert`.

- Test provider success, cancellation, timeout and prior-profile preservation without live OAuth.
- Test policy traversal/protected-path rejection and audit pre-image-before-write using temporary roots.
- Test that all mutations include an audit operation and restore produces a new audit record.
- Test bridge payload validation and build the macOS application after every native slice.

Revisit this decision if a supported platform offers a platform-native scoped-file entitlement that replaces the current root policy, or if audit requirements expand to enterprise/compliance retention.
