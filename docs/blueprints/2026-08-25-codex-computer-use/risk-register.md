# Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---:|---:|---|
| A proprietary asset cannot be redistributed in a public build | Medium | High | Keep M3 as a release gate; use only authorized local assets during development. |
| Enabling a missing plugin blocks every model turn | High without bootstrap | High | Install/probe before enabling; capability failure falls back to chat. |
| Global Codex state leaks into MERRICK | Medium | High | Set private `HOME` and `CODEX_HOME`; no global-path fallback. |
| macOS TCC permission is denied | High | Medium | Present guidance; retain conversation and non-Computer-Use tools. |
| Native client update breaks plugin protocol | Medium | Medium | Versioned seed, atomic stage, last-known-good private resources. |
| Extra setup slows ordinary dialogue | Medium | Medium | Prewarm once; skip installer after a ready record; hard circuit breaker on failure. |
