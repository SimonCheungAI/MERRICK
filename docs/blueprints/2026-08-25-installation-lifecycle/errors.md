# Error Handling

| Code/category | User-facing message | Recovery |
|---|---|---|
| `DUPLICATE_INSTANCE_REDIRECTED` | “MERRICK is already open. Its window has been brought forward.” | No action needed. |
| `BACKEND_PORT_IN_USE` | “Another local process is using MERRICK’s local service. Quit MERRICK and reopen it.” | Visible quit/reopen instructions; do not silently start a second service. |
| `BACKEND_START_FAILED` | “MERRICK could not start its local core.” | Keep error window visible; link/prompt to diagnostics. |
| `BACKEND_HEALTH_TIMEOUT` | “MERRICK’s local core took too long to become ready.” | Quit/reopen; report diagnostics if repeated. |
| `BUNDLE_RUNTIME_MISSING` | “This copy is incomplete. Move MERRICK to Applications and reinstall from the DMG.” | Never fall back to a random source path in a packaged build. |

Errors use local native text only until the web UI is authenticated and loaded.
