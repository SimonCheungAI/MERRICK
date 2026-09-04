# Risk register

| ID | Risk | Likelihood | Impact | Mitigation | Owner milestone |
|---|---|---:|---:|---|---|
| R-001 | `2026.8.1` route migration disconnects the Codex account | Medium | High | Copy state, run doctor in staging, profile-specific provider probe, atomic rollback | M1 |
| R-002 | Gateway wire protocol changes independently of the bridge | Low | High | Pin Gateway client/protocol to exact release; startup version gate | M2 |
| R-003 | Removing the local allowlist causes accidental tool use in ordinary chat | Medium | High | OpenClaw `auto` default, clear agent guidance, visible tool progress, per-session mode control | M3 |
| R-004 | Two execution paths create duplicate external effects | Medium | Critical | Feature flag selects exactly one dispatcher; client request idempotency; no fallback after ambiguous effect | M3 |
| R-005 | Dashboard handoff leaks the shared Gateway token | Low | Critical | Use `openclaw dashboard --json`; consume URL only in Swift; redact output and never pass URL to HUD | M2 |
| R-006 | Approval event arrives before MERRICK subscribes | Medium | High | Subscribe immediately after hello; backfill pending approvals/questions; merge by ID | M2 |
| R-007 | App quit leaves Gateway or bridge alive | Medium | High | External supervisor mode, PID fingerprints, bounded shutdown E2E test | M1/M2 |
| R-008 | Plugin SDK changes break `jarvis-companion` | Medium | Medium | Exact pin, manifest contract tests, supported grouped APIs only | M4 |
| R-009 | Experimental multi-agent/Swarm is unstable | Medium | Medium | Expose stable sessions/subagents first; keep experimental Swarm opt-in | M5 |
| R-010 | MERRICK UI cannot render complex questions/approvals | Medium | Medium | Generic schema-driven cards plus “Open in Control UI” escape hatch | M4 |
| R-011 | Full transcripts/tool output are duplicated into companion storage | Low | High | Store only bounded projections/cursors; OpenClaw remains system of record | M2 |
| R-012 | Legacy `jarvis-safe-tools` removal breaks public research UX | Medium | Medium | Retain plugin during parity; remove gating before removing helpers | M3/M6 |
| R-013 | Installed community plugin is malicious | Medium | Critical | Preserve OpenClaw trust/capability consent and device/exec approvals; no auto-install from Merrick | M4 |
| R-014 | Media/config additions exceed packaged app expectations | Low | Medium | Release manifest verification and clean-install/uninstall lifecycle test | M6 |

## Rollback levels

- M1 dependency migration: restore package lock, copied configuration and state
  backup; rebuild the previous verified app.
- M2-M5 features: set `JARVIS_OPENCLAW_NATIVE=0` and restart the app.
- M6 cleanup: `git revert` legacy-removal commit; no schema data is destroyed.

No milestone deletes legacy state or OpenClaw-owned session data.
