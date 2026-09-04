# Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---:|---:|---|
| Two bundle copies race at launch | Medium | High | Query/redirect before backend startup; port remains owned by one host. |
| HUD is off-screen/invisible | Low | High | Reopen explicitly orders front and activates; existing constrained position restore remains. |
| Dock behavior breaks transparent HUD | Low | Medium | Keep borderless/floating window; change only application activation policy. |
| Gatekeeper blocks externally shared DMG | Medium | High | Document and add Developer ID/notarization release gate; no security bypass. |
| Startup errors appear after WebKit failure | Medium | Medium | Keep native error label independent from HUD loading. |
| Stale port from a crash | Medium | Medium | Existing orphan reclaim stays; health proof rejects foreign listeners; error is visible. |
