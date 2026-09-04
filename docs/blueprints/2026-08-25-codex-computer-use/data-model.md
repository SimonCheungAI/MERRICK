# Data Model

No database is added. One private JSON record may be written under `OpenClaw/native-home/.codex/jarvis-computer-use-state.json`.

## ComputerUseInstallState

| Field | Type | Constraint | Purpose |
|---|---|---|---|
| `schemaVersion` | integer | `1` | Parsing compatibility |
| `assetVersion` | string | manifest version only | Determines whether reseeding is needed |
| `installedAt` | UTC ISO-8601 | required on success | Local support chronology |
| `lastStatus` | enum | `ready`, `unavailable`, `failed` | Last known capability state |
| `lastErrorCode` | allowlisted string/null | no raw exception | Actionable recovery category |

The record must never contain a token, username, model prompt, screenshot, document path, transcript, raw TCC state, or operating-system command.
