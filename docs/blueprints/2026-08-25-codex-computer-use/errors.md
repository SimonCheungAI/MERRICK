# Error Handling

| Category | User-facing state | Recovery |
|---|---|---|
| `COMPUTER_USE_ASSET_MISSING` | “Computer control is not installed in this MERRICK copy.” | Reinstall/update MERRICK; chat remains available. |
| `COMPUTER_USE_INSTALL_FAILED` | “Computer control could not finish setting up.” | Restart MERRICK; consult the local diagnostic log if repeated. |
| `COMPUTER_USE_MCP_UNAVAILABLE` | “Computer control is installed but not ready.” | Restart MERRICK; re-enable from Settings when provided. |
| `COMPUTER_USE_PERMISSION_REQUIRED` | “macOS needs Accessibility or Screen Recording permission for Computer Use.” | Open the relevant macOS Privacy & Security setting and approve. |
| `COMPUTER_USE_CLIENT_EXITED` | “Computer control stopped unexpectedly.” | The current action ends; conversation remains available and a fresh gateway retry is permitted. |

Errors are surfaced as a capability status, not silently converted into standby. They are rate-limited to one visible notification per turn.
