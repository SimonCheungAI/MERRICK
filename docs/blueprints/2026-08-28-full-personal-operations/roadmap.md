# Development Roadmap

## Delivery rules

- Each milestone ends in demonstrable working software behind a capability flag.
- Default flags are off until migration, tests and rollback checks pass.
- No milestone broadens OpenClaw host permission to compensate for a missing connector.
- Commits remain small and reversible; database migrations have down/read-compatibility plans.

## Capability-adapter vertical slices (next delivery track)

These slices refine Milestones 0–3 for OpenClaw/plugin compatibility. Each is
independently demonstrable and keeps the previous path available.

### Slice CA-1 — Normalized read-only catalog (1–2 days)

Goal: the current Capabilities view distinguishes discovered, enabled, ready,
connected, reviewed and authorized states without executing any new tool.

- [x] Add pure normalization for plugin/skill inventory and canonical effect/risk
  metadata; unknown operations remain `unreviewed` and non-executable.
- [x] Cache a versioned last-known-safe snapshot off the voice response path.
- [x] Extend existing inventory tests with malformed IDs, bounded metadata,
  dependency/auth readiness and schema-drift fixtures.
- [x] Flag: `capability_adapter_v1`, default off until UI and regression tests pass.

Deliverable: the dashboard accurately explains why `gog` and `himalaya` are
discovered but unavailable, while conversation and local organizer remain live.

Rollback: disable the flag; the current plugin/skill inventory projection is
unchanged. Revert the slice commit; no database migration is required.

Status (2026-08-29): complete and packaged. Eleven catalog/HUD tests pass; the
installed app explicitly enables the flag after verification while the code
default remains off.

### Slice CA-2 — Reviewed resolver with synthetic mail/calendar (2–3 days)

Goal: natural Chinese/English paraphrases resolve to canonical intents and a
mock connector, never directly to arbitrary plugin tools.

- Add a reviewed binding registry, deterministic connector precedence and
  schema-hash validation using in-memory fixtures first.
- Add bilingual intent/paraphrase tests and bounded English catalog-query
  generation with no private text.
- Run synthetic `mail.search`, `mail.draft`, `calendar.list` and
  `calendar.propose` through the existing R0–R2 policy/preview boundary.
- Flag: `capability_resolver_v1`, dependent on CA-1.

Deliverable: voice/text requests produce a typed synthetic result or exact
preview; no external account is connected and no write can leave the app.

Rollback: disable resolver flag; local organizer routing continues.

### Slice CA-3 — Google mail/calendar read-only connection (4–7 days)

Goal: one explicitly connected Google account supports inbox search/read and
calendar list/free-busy through canonical tools with read-only scopes.

- Use the app-owned OAuth/Keychain adapter as the reference connector.
- Add a reviewed OpenClaw `gog` compatibility pack only after binary version,
  credential boundary and contract tests pass; it is not an automatic fallback.
- Add account/scope/health UI, cursor pagination, hostile-content isolation and
  cached offline projections.
- Flags: `google_workspace_read_v1` and, separately,
  `openclaw_gog_compat_v1`, both default off.

Deliverable: “总结今天的重要邮件和会议” returns sourced read-only results;
the same request still works locally when the connector is offline.

Rollback: revoke read scopes, disable flags and purge bounded cache; provider
data is untouched.

### Slice CA-4 — Governed drafts and external commits (5–8 days)

Goal: mail drafts and event proposals are editable locally; send/invite/update
uses exact preview, one-time approval, idempotency and provider reconciliation.

- Request write scopes incrementally only when the owner enables the feature.
- Bind approval to connector, account, recipients/attendees, content/time,
  schema hash and revision.
- Add timeout/unknown-outcome and duplicate-effect tests before live writes.
- Flags: `mail_write_v1`, `calendar_write_v1`, default off independently.

Deliverable: one approved test message and event execute exactly once and leave
redacted receipts. No standing send/invite rule ships in this slice.

Rollback: disable write grants/flags; read mode and exportable drafts remain.

### Slice CA-5 — Reviewed plugin compatibility packs (ongoing, 1–3 days each)

Goal: add other OpenClaw plugins without changing the conversational contract.

- Each pack declares canonical intents, exact supported versions/schema hashes,
  risk ceiling, scopes, fixtures, health probe, redaction and compensation.
- Official or bundled sources are preferred; community packages require source
  review and a pinned artifact. There is no bulk-enable or generic call path.
- Contract, injection, permission-denial, timeout and rollback tests are
  mandatory before enabling one pack.

Deliverable: each newly reviewed plugin appears as another connector behind an
existing canonical intent, or introduces a separately reviewed canonical
domain when necessary.

Rollback: quarantine/disable only that binding and revert its atomic commit.

## Milestone 0 — Authority baseline and typed contracts (MVP, days 1–5)

Goal: the existing assistant continues working, but every future office action has a typed contract and the current broad runtime authority is no longer the execution boundary.

Tasks:

- Add versioned operation/approval/WebSocket schemas and generated fixtures for Python, JS and Swift.
- Introduce connector, policy, secret-store, audit and workflow ports with no provider implementation.
- Add a compatibility adapter around the existing organizer.
- Move the main assistant away from direct unrestricted effect tools; retain a separately controlled developer mode only for local development.
- Add feature flags and a migration/rollback harness.

Deliverable: MERRICK can plan and preview a synthetic mail/calendar operation, deny it by default and record a redacted audit event.

Testing: schema compatibility, policy deny matrix, prompt-injection corpus, no-secret logging, existing voice/organizer regression suite.

Rollback: disable `personal_operations_v1`; old read-only/local organizer flows remain available.

## Milestone 1 — Connections, Keychain, workflow and approval kernel (MVP, days 6–12)

Goal: connect/revoke a test account and run a durable synthetic workflow through approval without exposing credentials.

Tasks:

- Add database migrations for connections, grants, workflows, steps, operations, approvals, attempts, outbox and audit.
- Implement Keychain secret references and OAuth PKCE broker.
- Implement native approval card, expiry, exact preview hashing and optional biometric confirmation.
- Implement restart recovery, idempotency and mock-provider reconciliation.
- Add Connections, Approvals and Activity dashboard foundations.

Deliverable: a mock provider operation survives restart, requests approval, executes once and produces a receipt.

Testing: migration copy/verify, OAuth state/PKCE attack tests, idempotency, crash-at-every-step recovery, audit hash chain.

Rollback: revoke mock connection, disable workflow worker, keep migrated tables unused.

## Milestone 2 — Google mail/calendar read assistant (MVP, days 13–22)

Goal: MERRICK can safely summarize a connected Gmail inbox and Google Calendar without write scopes.

Tasks:

- Implement incremental Gmail metadata/body-on-demand adapter with read-only/metadata scopes.
- Implement Google Calendar events/free-busy adapter with read-only scopes.
- Build cursor sync, rate-limit handling, minimal cache and configurable retention.
- Add Inbox and Agenda dashboard views with cursor pagination.
- Feed bounded, labelled-untrusted content into read-only OpenClaw workflows.
- Merge inbox/agenda into morning briefing and daily focus plan.

Deliverable: “今天有什么要处理的邮件和会议？” returns a sourced summary and dashboard cards; no provider write capability exists.

Testing: Google adapter contract tests against recorded redacted fixtures, pagination, time zones/DST, hostile-email prompt injection, offline mode.

Rollback: revoke Google read scopes and purge bounded cache without touching provider data.

## Milestone 3 — Governed mail and calendar writes (MVP, days 23–32)

Goal: draft/send mail and create/update events through exact preview and approval.

Tasks:

- Add incremental Gmail send/modify and Calendar event scopes only when enabled.
- Implement encrypted drafts, attachment staging and recipient/contact disambiguation.
- Implement calendar proposals, conflict analysis, invitation previews and provider etag handling.
- Add R1/R2 policy rules, approval UX and receipts.
- Add duplicate-send/update reconciliation and safe compensation paths.

Deliverable: MERRICK drafts a reply and meeting invitation, shows exact effects, sends/commits once after approval and records provider IDs.

Testing: recipient confusion, BCC disclosure, attachment substitution, preview mutation, stale etag, duplicate network response, approval expiry.

Rollback: disable mail/calendar write grants; drafts remain exportable, read mode continues.

## Milestone 4 — Work hub, documents and meeting follow-through (V1, days 33–42)

Goal: one operational view joins mail, calendar, local projects/tasks, documents and meeting action items.

Tasks:

- Extend organizer schema for recurrence, dependencies, tags, assignees, revisions and external links.
- Add one external task adapter selected by the owner.
- Implement conflict-aware bidirectional sync and soft-delete/tombstone handling.
- Add typed document/report jobs using the bounded Workspace Library.
- Link confirmed meeting action items and email follow-ups to tasks.
- Upgrade Overview/Journal/Meetings with source and sync status.

Deliverable: a meeting decision creates approved tasks, links the source event/email and appears in daily/weekly reports.

Testing: sync loops, concurrent edit conflicts, soft-delete restore, recurrence, document type/size validation, accessibility regression.

Rollback: disconnect task provider; preserve local task copies and links as inactive metadata.

## Milestone 5 — Travel research and booking handoff (V1, days 43–57)

Goal: search, compare and prepare flights/hotels, then stop safely at the final purchase boundary.

Tasks:

- Implement travel plan/option/reservation models and comparison UI.
- Integrate one approved flight/hotel API in test mode; normalize price and terms.
- Add OpenClaw isolated-browser fallback for supported public search/preparation flows.
- Implement price refresh, expiry, itinerary ranking explanations and currency handling.
- Add local traveller-profile secret references; never expose payment/passport data to the model.
- Implement native checkout handoff, outcome reconciliation and receipt/calendar proposals.

Deliverable: MERRICK produces a comparable shortlist, fills a test booking to checkout, hands control to the owner and records a simulated confirmation.

Testing: stale offers, tax/currency totals, non-refundable terms, CAPTCHA/MFA handoff, unknown 202 booking outcome, no-double-book invariant, browser selector drift.

Rollback: disable travel connectors and browser adapter; retain read-only plan history.

## Milestone 6 — Standing workflows and operational dashboard (V1, days 58–67)

Goal: daily personal operations run reliably without becoming silent autonomous authority.

Tasks:

- Map standing rules to OpenClaw automations/TaskFlow with local policy constraints.
- Add configurable inbox triage, agenda prep, follow-up reminders, morning/evening/weekly reports.
- Add macOS notifications for approval, failure and expiring connections.
- Finish Workflows, Rules and Activity views with pause/edit/delete and run receipts.
- Add per-rule tool budgets, circuit breakers and quiet hours.

Deliverable: a user-configured morning workflow reads permitted sources, produces a newspaper-style briefing and queues—not sends—recommended follow-ups.

Testing: DST/clock changes, missed runs, duplicate wakeups, pause/resume, notification denial, tool-budget exhaustion, concurrent conversation.

Rollback: pause all standing rules with one local switch; manual assistant remains functional.

## Milestone 7 — Provider breadth and release hardening (V2, days 68–82)

Goal: add the second productivity ecosystem and prepare a supportable distributable release.

Tasks:

- Implement Microsoft Graph mail/calendar adapter with delegated least-privilege scopes.
- Add additional task/provider adapters according to owner demand.
- Complete Google/Microsoft OAuth verification and travel-provider commercial onboarding as applicable.
- Add encrypted backup/export, retention controls, dependency/security scanning and incident procedures.
- Run long-duration soak, accessibility, localization and packaged-app upgrade tests.
- Publish capability documentation explaining exactly what is automatic, approved and handoff-only.

Deliverable: signed/notarized candidate supports Google and Microsoft accounts with consistent policy, audit and recovery semantics.

Testing: cross-provider contract suite, migration from every prior milestone, credential rotation/revocation, 7-day soak, packaged clean-machine E2E.

## Effort and sequencing

| Scope | Milestones | Estimate for one experienced engineer |
|---|---|---:|
| Useful read assistant | 0–2 | 3–4.5 weeks |
| Mail/calendar action MVP | 0–3 | 4.5–6.5 weeks |
| Full V1 personal operations | 0–6 | 11–14 weeks |
| Provider breadth/release readiness | 0–7 | 14–18 weeks plus external verification/onboarding |

Provider approvals can run in parallel but are not controlled by engineering estimates.
