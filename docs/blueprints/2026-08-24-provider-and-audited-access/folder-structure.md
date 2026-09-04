# Target Folder Structure

```text
desktop/
  MerrickApp.swift                 # Native bridge, Keychain, OAuth and root picker adapters
server/
  contracts/
    automation.py                 # Typed event and port contracts
  application/
    provider_connection.py        # Connection workflow
    file_operations.py            # Turn-bound file workflow
  adapters/
    access_policy.py              # Native-written policy reader
    file_audit_sqlite.py          # Transactional audit/revision store
    openclaw_file_tools.py        # Narrow OpenClaw adapter
  main.py                         # Compatibility delegation only
web/
  app.js                          # Settings rendering/event handling only
  index.html                      # Connection and Automation & Files panels
  style.css                       # Existing visual system tokens
tests/
  test_access_policy.py
  test_file_audit.py
  test_provider_connection.py
  test_session_action_execution.py
```

Existing `server/library.py` stays the workspace document reader during migration. Existing `server/openclaw_client.py` remains a gateway facade; it must not gain SQLite/file mutation implementation details.
