# Architecture

```text
Finder / Dock / Spotlight
          │
          ▼
/Applications/MERRICK.app
          │ native owner instance + visible lifecycle state
          ├── Contents/Resources/runtime/
          │   ├── Python backend (Uvicorn)
          │   ├── Node runtime
          │   └── bundled OpenClaw code/plugins
          │
          ├── macOS Keychain (provider secrets only)
          └── ~/Library/Application Support/JarvisStark/
              ├── provider profile, OpenClaw mutable state
              ├── diagnostics
              └── memory / workspace / voice identity
```

## Launch flow

1. Native process enters a `launching` state, checks for an existing same-bundle process and focuses it if present.
2. The owner validates its embedded runtime before launching the loopback backend.
3. Backend authenticated health succeeds; the native host loads the HUD.
4. The renderer authenticates its bridge (`interface_ready`).
5. The backend prewarms the selected local model connection; the renderer changes from `connecting_model` to `ready` or receives an actionable connection error.

The current generic `booting` label is compatibility-only. New status mapping must distinguish backend, UI bridge and model connection so users never need terminal logs to decide what failed.

## Authority boundaries

- Bundle resources are read-only post-signing.
- Native host owns lifecycle, Keychain access, provider child processes, folder selection and macOS permissions.
- Python owns local sessions and OpenClaw child lifecycle.
- Renderer may request status and configuration only through the authenticated native bridge.
- OpenClaw receives provider configuration at launch, never API keys via prompt/UI storage.
