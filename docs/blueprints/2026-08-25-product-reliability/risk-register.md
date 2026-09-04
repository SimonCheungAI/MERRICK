# Risks

| Risk | Mitigation |
|---|---|
| Removing an app copy removes private data | Never store user state in app bundle; delete staging copy only after verifying Application Support separation. |
| New install leaves old process holding port | Shutdown/focus old same-bundle instance before first formal launch; native singleton remains guard. |
| Gatekeeper blocks externally shared app | Developer ID signing/notarization is a release gate; no bypass is automated. |
| Provider sign-in fails | Preserve existing profile, show in-app reconnect/device-flow progress, never use Terminal. |
| Startup silently stalls | Stage watchdog produces a native actionable error and redacted diagnostic record. |
