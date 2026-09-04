# Bridge Contract

| Event | Producer | Meaning |
|---|---|---|
| `computer_use.seed.ready` | backend bootstrapper | Private resources are present and version-compatible. |
| `computer_use.setup.ready` | OpenClaw/Codex integration | Plugin and MCP server advertised usable tools. |
| `computer_use.setup.unavailable` | backend bootstrapper | No compatible bundled client/source; chat remains available. |
| `computer_use.setup.failed` | backend bootstrapper | Setup failed; error category is redacted and component is disabled for this gateway lifetime. |
| `computer_use.permission_required` | MCP error adapter | macOS permission is required; app presents recovery guidance. |

`ComputerUseStatus` is a local capability state only. It is not an authorization grant, does not expose user TCC details, and never converts a failed action into a successful model claim.
