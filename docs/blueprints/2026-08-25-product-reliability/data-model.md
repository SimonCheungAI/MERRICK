# Data Model

## InstallationRecord

**Storage:** `~/Library/Application Support/JarvisStark/install-state.json`, native-written, mode 0600.

| Field | Type | Rule |
|---|---|---|
| schemaVersion | integer | required |
| installedBundlePath | absolute path | must equal `/Applications/MERRICK.app` for product install |
| version | string | from bundle Info.plist |
| installedAt | UTC ISO-8601 | required |
| lastLaunchAt | UTC ISO-8601 | optional |

## LifecycleDiagnosticEvent

| Field | Type | Rule |
|---|---|---|
| timestamp | UTC ISO-8601 | required |
| stage | enum | `launching`, `local_core`, `interface`, `model`, `ready` |
| code | stable string | required on failure |
| detail | redacted string | max 240 chars |

No credential, memory, conversation or workspace schema changes are required.
