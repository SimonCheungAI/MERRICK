# Native Lifecycle Contract

This slice introduces no backend or web API. The native host owns the lifecycle.

| Event | Producer | Meaning |
|---|---|---|
| `app.duplicate_launch_redirected` | Native host | A second bundle copy focused the active instance and exited before backend startup. |
| `app.reopen_focused` | Native host | A Dock/Finder reopen made the HUD frontmost. |
| `backend.port_unavailable` | Native host | Backend did not start because the loopback listener is unavailable; visible recovery state is shown. |

Failure UI contract: every startup failure must have (1) a short user-facing category, (2) one recovery action, and (3) a local support-log location. It must not depend on a loaded web view.
