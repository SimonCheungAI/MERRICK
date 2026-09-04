# Errors and Recovery

| Code | User-facing recovery |
|---|---|
| `DUPLICATE_INSTANCE_REDIRECTED` | “MERRICK is already open; its window was brought forward.” |
| `RUNTIME_MISSING` | “This install is incomplete. Reinstall MERRICK into Applications from its DMG.” |
| `PORT_OCCUPIED` | “Another local MERRICK core is running. Quit MERRICK, then reopen it.” |
| `UI_BRIDGE_TIMEOUT` | “The interface did not finish loading. Restart MERRICK; diagnostics are available in Settings.” |
| `MODEL_CONNECTION_FAILED` | “Your local core is ready, but the selected model connection needs attention.” Open Settings → Model connection. |
| `KEYCHAIN_SAVE_FAILED` | “macOS Keychain rejected the credential; the previous connection is unchanged.” |

All errors are native/local and avoid secrets or user content.
