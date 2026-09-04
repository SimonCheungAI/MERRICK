# Error Handling

| Code | User-facing meaning | Recovery |
|---|---|---|
| `PROVIDER_CONNECTOR_UNAVAILABLE` | The bundled connector cannot start. | Keep current provider; reinstall/diagnose without losing profile. |
| `PROVIDER_AUTH_TIMEOUT` | Browser sign-in was not completed in time. | Retry connection; no credentials are saved. |
| `PROVIDER_AUTH_CANCELLED` | The in-app connection was cancelled. | Keep prior active connection. |
| `KEYCHAIN_SAVE_FAILED` | macOS Keychain rejected the credential. | Preserve prior profile and show macOS status. |
| `ACCESS_DISABLED` | Direct Automation is not enabled. | Open Settings → Automation & Files. |
| `ACCESS_ROOT_REQUIRED` | No authorized folder covers this path. | Choose a read/write folder in Settings. |
| `ACCESS_PROTECTED_PATH` | The path is private MERRICK/system/credential state. | Never allow override from conversation. |
| `ACCESS_MACOS_DENIED` | macOS denied folder/Accessibility access. | Direct user to the relevant System Settings permission. |
| `AUDIT_PREIMAGE_FAILED` | MERRICK could not retain the original safely. | Do not mutate; leave source intact. |
| `AUDIT_NOT_REVERSIBLE` | The record has no retained pre-image. | Show hash record; no restore action. |
| `AUDIT_RESTORE_CONFLICT` | Target changed after MERRICK's operation. | Offer restore-as-copy instead of overwrite. |

Errors are structured in trace logs with operation IDs only. The backend never converts a failed mutation into a success sentence.
