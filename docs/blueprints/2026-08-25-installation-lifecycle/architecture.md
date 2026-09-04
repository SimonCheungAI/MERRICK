# Architecture

## Pattern

Keep the existing macOS native host plus modular-monolith backend. Add an **early single-instance lifecycle gate** in the native host; no new daemon, IPC server or cloud service is needed.

```text
Finder / Dock / Spotlight / open
              │
              ▼
      macOS Launch Services
              │
              ▼
 Native MERRICK host (MerrickApp.swift)
   ├─ Single-instance gate ─── existing host → activate its windows → terminate newcomer
   ├─ Normal activation ────── visible Dock/Command-Tab app + floating HUD
   ├─ Backend owner ────────── one Uvicorn listener on 127.0.0.1:8765
   └─ Diagnostics ──────────── local lifecycle log + visible recovery state
              │
              ▼
 bundled Python + OpenClaw runtime
```

## Key flows

### First launch

1. Native host starts with regular activation policy.
2. It queries running apps for the MERRICK bundle identifier, excluding its own PID.
3. No existing app: build the HUD, spawn the one local backend, poll its authenticated health endpoint, then load the HUD.
4. Any failure keeps the native window visible and writes a redacted lifecycle error to the local diagnostic log.

### Launch from another copy

1. A user double-clicks the DMG/staging copy while the Applications copy is active.
2. The new host finds the active same-bundle process before any service startup. It does not use `LSMultipleInstancesProhibited`, because that system-level rejection can occur before the host has an opportunity to make the existing window visible.
3. It brings all windows of that process forward, activates it, writes `app.duplicate_launch_redirected`, and terminates itself.
4. The active instance continues uninterrupted. No port conflict, provider reconnect, duplicate microphone prompt or second backend occurs.

### Reopen a hidden/inactive instance

`applicationShouldHandleReopen` and `applicationDidBecomeActive` make the existing HUD key, frontmost and visible. Window close remains a true quit; no invisible agent state is retained.

## Security and failure boundaries

- Only a same-user `NSRunningApplication` whose bundle identifier exactly matches MERRICK can receive activation.
- Duplicate handling never reads another app's documents, provider state or process command line.
- The backend continues to authenticate its bridge. A foreign process on port 8765 is never treated as healthy.
- Lifecycle logs use event/category/PID only; no secrets or conversation data.

## Performance

The duplicate gate is one local Launch Services query. It happens before all expensive startup work. Backend startup retains the current 30-second cap; human-visible feedback is immediate.
