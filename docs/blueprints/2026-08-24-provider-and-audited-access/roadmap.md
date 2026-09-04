# Delivery Roadmap

## M1 — Native connection without Terminal (MVP, 1 slice)

Goal: a user can complete provider connection from Settings while MERRICK displays progress and browser launch itself.

- Characterize existing API-key and profile behaviour.
- Replace Terminal launch with an app-owned connector/output parser and cancel path.
- Add connection state/verified time and UI error/loading states.
- Test fake connector output, cancellation, prior-profile preservation and native build.

Rollback: revert the slice; existing API-key path remains untouched. Feature flag: `inAppProviderConnection` defaults off until native test pass.

## M2 — Policy UI and read-only catalog (MVP, 1 slice)

Goal: user can enable automation, choose roots and see exactly what is authorized; no broad file writes yet.

- Native access profile with 0600 permissions and directory-picker bridge.
- Automation & Files settings panel in both languages.
- Python policy resolver with protected-path denials and tests.

Rollback: flag off; workspace-only library remains default.

## M3 — Audited mutations and recovery (V1, 1–2 slices)

Goal: authorized direct write/edit/rename/delete operations are durable, auditable and reversible when snapshots exist.

- SQLite audit/revision implementation with atomic pre-image requirement.
- Narrow OpenClaw file adapter and turn binding.
- Audit list/detail/restore UI; test against temporary roots and database.

Rollback: flag off stops new broad operations; completed files remain, audit supports recovery.

## M4 — General GUI portability (V1, 1 slice)

Goal: direct visible GUI requests are not blocked by a small installed-app alias list.

- Resolve installed apps dynamically; retain current-turn binding and Accessibility gate.
- Expand GUI planner only for visible non-secret controls.
- Test installed-app resolver and forbidden UI cases.

Rollback: use existing alias path through a compatibility flag.
