# Delivery Roadmap

## M1 — Isolated installer and safe fallback (MVP)

- Bundle/seed a verified Computer Use resource layout into MERRICK's private Codex home.
- Make `CODEX_HOME` private and configure the local marketplace path.
- Keep Computer Use disabled unless bootstrap/preflight confirms compatible assets.
- Add source-contract tests for private state, configuration, and fallback.

Deliverable: MERRICK can start and chat even when assets are missing; it never trips all turns into standby.

Rollback: disable the `computerUse` configuration and restart the gateway (L2), or revert the single slice (L1).

## M2 — Official MCP installation/probe (V1)

- Enable Codex plugins and remove only the two app-server flags that suppress plugin discovery.
- Install/re-enable `computer-use` from the MERRICK-private marketplace, reload MCP, and probe tool status.
- Validate a harmless `list_apps`/capability operation after granting macOS permissions.

Deliverable: a live MERRICK turn exposes the Computer Use MCP surface without using global Codex state.

Rollback: persist `lastStatus=failed`, skip setup for the gateway lifetime, and retain normal chat.

## M3 — Distribution/legal gate (V2)

- Confirm redistribution terms for the proprietary Computer Use app/resources.
- If bundling is not authorized, replace resource copying with an explicit official dependency installer while retaining the same private home contract.
- Add Settings status/retry UI and clean-install test on a Mac with no global Codex installation.
