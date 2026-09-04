# Data Model

No database or new persisted business entity is required.

## LifecycleDiagnosticEvent

**Storage:** append-only local text log under `/tmp/jarvis-native.log` today; future migration may copy only the most recent redacted events to `~/Library/Application Support/JarvisStark/Diagnostics/lifecycle.log`.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| timestamp | UTC ISO-8601 | required | Existing native trace format |
| event | string | allowlisted lifecycle category | e.g. `app.duplicate_launch_redirected` |
| pid | integer | optional, same-user only | Never command line or path |
| detail | string | redacted, max 240 chars | No secrets/transcripts |

No user preference, provider, memory or voiceprint schema changes are required.
