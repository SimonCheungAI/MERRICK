# Roadmap

## M1 — One formal installation (MVP)

- Install current verified bundle to Applications.
- Remove only the redundant DMG staging app.
- Register/launch the Applications app and verify one backend listener.

## M2 — Diagnosable startup (MVP)

- Add lifecycle stages and a bounded UI-bridge readiness watchdog.
- Render actionable failure/retry state instead of indefinite `booting`.
- Add tests for runtime missing, duplicate focus, and bridge timeout.

## M3 — In-app connection integrity (V1)

- Retain the existing Keychain/API/device-flow provider UI as the sole user onboarding path.
- Add a connection-health summary and retry action without gateway restart during an active turn.
- Verify all bundled dependencies and provider UI contracts in release packaging.
