# Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Generic intent routing intercepts orchestration text | High | High | dedicated controller bypasses local document/action routing |
| Coroutine returns after a spoken error | High | High | typed result object; terminal state requires OpenClaw evidence |
| Duplicate click launches duplicate children | Medium | High | one active run per plan and stable launch replay keys |
| Gateway restart loses in-memory board | Medium | Medium | reconcile from task ledger using stored OpenClaw ids |
| One child hangs indefinitely | Medium | High | per-child timeout and bounded waits |
| Child completion starts competing spoken replies | Medium | Medium | visible children stay in their session; MERRICK speaks only parent synthesis |
| Result text injects markup | Low | High | bounded strings rendered with `textContent` |
| Too many agents exhaust resources/cost | Medium | High | UI/runtime cap eight, OpenClaw concurrency cap four |
| Dirty worktree overlap | High | Medium | narrow modules, inspect diffs, no unrelated formatting |
| Feature incomplete at release | Low | Medium | off switch and independent sequential fallback |
| Per-child close targets a replacement | Low | Critical | match session key plus observed durable sessionId generation |
| Agent appended during finalization is omitted | Medium | High | accept only starting/running and recompute live wait set |
| Manual task leaks through board persistence | Low | High | instruction excluded from `to_dict` and persisted snapshot |
| Forged/remote terminal URL crosses native boundary | Low | Critical | accept only exact receipt URL on loopback HTTP(S) origin |
| Archive click hides a still-running agent | Low | High | hide only after OpenClaw archive commit; otherwise preserve card and error |
