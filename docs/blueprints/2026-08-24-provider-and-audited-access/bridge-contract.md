# Local Bridge and Service Contract

The renderer communicates only through the authenticated native bridge. Names are camelCase; all responses include `ok` and optional stable `code`/`message`.

## Provider messages

| Request | Body | Result |
|---|---|---|
| `getProviderSetupState` | none | configured provider/model/auth mode/verified time/reconnect requirement |
| `saveProviderAPIKey` | provider, model, baseUrl?, apiKey | Keychain save, profile update, backend restart result |
| `connectProviderCLI` | provider, model | starts app-owned OAuth/CLI connector; legacy name retained during migration |
| `cancelProviderConnection` | none | terminates only the MERRICK-owned connector |
| `disconnectProvider` | provider | removes MERRICK profile and its Keychain item after native device-owner authentication |

Progress callback: `merrickNativeProviderSetupProgress({ phase, deviceCode?, verificationURL?, message })`. The UI must mask any accidental secret-like text and render the URL as a native `openExternalURL` action, never as raw HTML.

## Access messages

| Request | Body | Result |
|---|---|---|
| `getAutomationAccessState` | none | policy summary, native permission status, audit count |
| `chooseAutomationAccessRoot` | mode `read` or `write` | native directory picker result, never a client supplied path |
| `saveAutomationAccessPolicy` | directAutomationEnabled, allowGeneralGUI, rootIds/modes | validated policy and gateway reload result |
| `getFileAuditPage` | cursor?, limit 1–100, rootId? | paginated metadata only |
| `getFileAuditDetail` | operationId | metadata and safe diff/snapshot availability |
| `restoreFileAuditRevision` | operationId | new audited restore operation result |

## Python ports

```python
class AccessPolicyPort(Protocol):
    def resolve(self, operation: str, path: Path) -> AuthorizedPath: ...

class AuditFileTransactionPort(Protocol):
    def write_atomic(self, path: AuthorizedPath, content: bytes, turn_id: str) -> AuditOperation: ...
    def patch(self, path: AuthorizedPath, patch: TextPatch, turn_id: str) -> AuditOperation: ...
    def move(self, source: AuthorizedPath, target: AuthorizedPath, turn_id: str) -> AuditOperation: ...
    def quarantine_delete(self, path: AuthorizedPath, turn_id: str) -> AuditOperation: ...
    def restore(self, operation_id: str, turn_id: str) -> AuditOperation: ...
```

OpenClaw's adapter gets only these operations, with the current turn ID and selected root binding. It does not receive direct `group:fs`, runtime, shell, node or gateway authority.
