# Lifecycle Bridge Contract

Native callbacks delivered only after bridge authentication:

```json
{
  "type": "lifecycle",
  "stage": "local_core",
  "state": "starting",
  "code": null,
  "message": "Starting local core…"
}
```

Stages: `launching`, `local_core`, `interface`, `model`, `ready`, `failed`.

Failure callback adds a stable code such as `RUNTIME_MISSING`, `PORT_OCCUPIED`, `UI_BRIDGE_TIMEOUT`, `MODEL_CONNECTION_FAILED`, or `DUPLICATE_INSTANCE_REDIRECTED`. The UI renders one recovery action: Retry, Open Settings, or Focus MERRICK.

Provider requests remain: `getProviderSetupState`, `saveProviderAPIKey`, `connectProviderCLI`, `cancelProviderConnection`, and `disconnectProvider`. No terminal request exists in the user-facing protocol.
