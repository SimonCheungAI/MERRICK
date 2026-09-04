# Development roadmap

Each milestone is a deployable vertical slice with tests, a safe default and a
documented rollback. Incomplete native behavior is controlled by
`JARVIS_OPENCLAW_NATIVE`, initially off.

## Milestone 1 — Runtime 2026.8.1 (Day 1)

Goal: the existing MERRICK behavior runs unchanged on the new pinned
OpenClaw/Codex runtime.

- [ ] Upgrade `openclaw`, `@openclaw/codex` and matching lockfile entries.
- [ ] Back up a copied test state and run `doctor --fix` route migration.
- [ ] Update version/config markers and bundled plugin layout checks.
- [ ] Set external-supervisor environment and verify clean shutdown.
- [ ] Run config validation, provider probes, 431+ tests, plugin tests, build
  and clean-install release verification.

Deliverable: packaged app on `2026.8.1` with legacy dispatch still active.

Rollback: restore the previous dependency/lock/config commit and verified app.

## Milestone 2 — Official Gateway client and dashboard (Days 2-3)

Goal: MERRICK can connect as a paired operator client, observe sessions
and safely open Control UI without changing command routing.

- [ ] Add exact Gateway client/protocol dependencies and bridge process.
- [ ] Implement device identity, pairing, reconnect, session subscriptions,
  approval/question backfill and typed Python facade.
- [ ] Add OpenClaw Workspace button and bilingual dashboard command.
- [ ] Add lifecycle, protocol mismatch, dashboard secret-redaction and E2E
  process cleanup tests.

Deliverable: read-only OpenClaw session/progress view plus safe Control UI open.

Rollback: disable `JARVIS_OPENCLAW_NATIVE`; legacy behavior is unchanged.

## Milestone 3 — Native session dispatch (Days 4-5)

Goal: an opted-in voice/text turn is executed entirely by OpenClaw with its
complete resolved capability surface.

- [ ] Bind MERRICK conversations to OpenClaw sessions.
- [ ] Dispatch all opted-in turns through `chat.send` with request idempotency.
- [ ] Project progress and one terminal answer to HUD/TTS.
- [ ] Mirror OpenClaw session permission mode; default to `auto`.
- [ ] Remove the local action-planner/allowlist from the native code path.
- [ ] Add conversation, coding, browser, filesystem, cancellation and duplicate
  effect integration tests.

Deliverable: native mode supports conversation and real OpenClaw work behind a
user-visible beta switch.

Rollback: switch native mode off; do not retry ambiguous effectful runs.

## Milestone 4 — MERRICK OpenClaw plugin (Days 6-7)

Goal: MERRICK appears as an OpenClaw-native companion rather than an
external opaque client.

- [ ] Create manifest and `jarvis-companion` Plugin SDK package.
- [ ] Register session extension, scoped commands, UI tab descriptor, tool/run
  metadata and lifecycle cleanup with supported grouped APIs.
- [ ] Surface questions and approvals as accessible schema-driven cards.
- [ ] Preserve OpenClaw plugin consent and never auto-enable community code.

Deliverable: Control UI displays MERRICK session state and companion
controls; MERRICK displays OpenClaw interactions.

Rollback: disable the bundled plugin; Gateway client integration still works.

## Milestone 5 — Coding and multi-agent workspace (Days 8-9)

Goal: coding sessions, tasks, subagents and stable multi-session work are
usable through voice and Control UI.

- [ ] Add “work in repository” session creation/linking.
- [ ] Render durable progress, changed-file summaries, questions and results.
- [ ] Support stable task/session/subagent surfaces and an explicit opt-in for
  experimental Swarm only if release validation passes.
- [ ] Verify workspace modes, cancellation and concurrent session limits.

Deliverable: the user can ask MERRICK to code, watch OpenClaw work and
continue the same session in Control UI.

Rollback: hide coding workspace controls without disabling basic native chat.

## Milestone 6 — Promotion and legacy retirement (Days 10-12)

Goal: OpenClaw-native mode becomes the default with no duplicate MERRICK
execution gate.

- [ ] Complete clean install, upgrade, OAuth, provider failure, offline,
  dashboard, plugin, browser, code, multi-agent, quit and uninstall matrix.
- [ ] Make native mode default after parity metrics pass.
- [ ] Remove unreachable legacy planner branches and obsolete allowlist UI.
- [ ] Keep only MERRICK-specific OpenClaw tools that add native value.
- [ ] Remove the feature flag after two verified releases.

Deliverable: one OpenClaw execution authority and one MERRICK companion
experience.

Rollback: revert the cleanup commit and disable native mode.
