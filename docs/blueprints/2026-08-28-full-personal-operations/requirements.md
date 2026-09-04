# Requirements

## Phase 1 — Scope

MERRICK becomes a single-user personal operations assistant for macOS. It unifies voice/text requests, local work memory, mail, calendars, tasks, documents, meetings, recurring briefings and travel planning while preserving explicit control of consequential actions.

## Functional requirements

### Command and orchestration

- **FR-001** Accept natural Mandarin and English requests without fixed command phrases.
- **FR-002** Convert a request into a typed plan containing intent, target account, resources, risk level and proposed steps.
- **FR-003** Resolve ambiguous people, accounts, dates, time zones, destinations and budgets before a write.
- **FR-004** Support multi-step, resumable workflows with progress, cancellation, retry and recovery after app restart.
- **FR-005** Preserve the invariant that one user turn produces one final conversational answer, even when several tools run.
- **FR-006** Permit standing rules only when their scope, schedule, targets and maximum authority are explicit and reviewable.

### Connections and credentials

- **FR-100** Connect multiple provider accounts with separately consented scopes.
- **FR-101** Support Google Workspace and Microsoft 365 as first-class mail/calendar providers; keep provider adapters replaceable.
- **FR-102** Support internal MERRICK projects/tasks plus optional Todoist, TickTick, Asana or ClickUp adapters.
- **FR-103** Show connected account, granted scopes, last sync, errors and revoke controls in the dashboard.
- **FR-104** Store provider secrets only in Keychain/secret broker; SQLite stores opaque credential references.
- **FR-105** Revoke one capability or account without breaking unrelated assistant functions.

### OpenClaw capability and plugin adaptation

- **FR-110** Discover installed OpenClaw plugins, skills, MCP tools and Codex-provided dynamic tools without loading untrusted runtime code solely for inventory.
- **FR-111** Normalize every discovered surface into a canonical capability descriptor containing owner, version, source, readiness, dependencies, account requirements, input/output schema, effect class and maximum risk.
- **FR-112** Map natural Mandarin and English requests to canonical intents such as `mail.search`, `mail.draft`, `mail.send`, `calendar.list`, `calendar.find_free`, `calendar.propose` and `calendar.commit`; users must not memorize plugin names or fixed phrases.
- **FR-113** Resolve one canonical intent to the best healthy connector at runtime, with an explainable precedence order and no silent fallback from an API connector to personal-browser automation.
- **FR-114** Treat unknown, incompatible, unsigned or community-provided capabilities as unavailable for execution until reviewed and assigned an explicit policy profile. Discovery never implies trust.
- **FR-115** Never install, update, remove, enable, authorize or broaden the scope of a plugin solely because conversational content, a skill, an email, a webpage or another tool recommends it.
- **FR-116** Expose connection state, missing dependencies, trust/source, effective tools, risk ceiling and last health check in the existing Capabilities dashboard.
- **FR-117** Refresh the effective capability snapshot after a verified lifecycle change and preserve the last known safe snapshot when discovery fails.
- **FR-118** Keep capability discovery and read-only connector failures isolated from conversation, local projects, reminders, meetings and briefings.
- **FR-119** Translate non-English capability searches into bounded English search descriptors internally when the selected OpenClaw catalog uses English lexical matching; never place private conversation text in the catalog query.

### Mail

- **FR-200** List/search threads with cursor pagination and account/folder/label filters.
- **FR-201** Summarize unread, important, awaiting-reply and time-sensitive mail.
- **FR-202** Classify and label/archive mail within user-configured rules.
- **FR-203** Draft replies, forwards and new messages using conversation context and contact disambiguation.
- **FR-204** Display an exact recipient/subject/body/attachment preview before a governed send.
- **FR-205** Send only with a valid capability grant and approval appropriate to the message risk.
- **FR-206** Never follow instructions contained in an email as authority to use another tool, disclose data or make a purchase.
- **FR-207** Preserve provider message IDs, thread IDs and send idempotency so retries cannot duplicate mail.

### Calendar and scheduling

- **FR-300** Read events and free/busy across selected calendars and time zones.
- **FR-301** Find mutually available times and explain conflicts.
- **FR-302** Propose, create, update, move or cancel events with attendee and conference-link previews.
- **FR-303** Require approval before sending invitations, cancelling events or materially changing attendees/time.
- **FR-304** Detect duplicates, travel time, time-zone conversion and stale provider versions.
- **FR-305** Convert confirmed meeting action items into local or connected tasks.

### Work organization and office files

- **FR-400** Retain the existing local projects, tasks, reminders, meetings, journal and briefing system.
- **FR-401** Add task priorities, dependencies, recurrence, assignees, tags and external-resource links.
- **FR-402** Synchronize selected tasks bidirectionally without duplicating or silently deleting records.
- **FR-403** Build daily focus plans, morning briefings, evening reviews and weekly reports from calendar, mail and task state.
- **FR-404** Read and create user-authorized documents, spreadsheets, presentations and reports through typed artifact adapters.
- **FR-405** Support attachments with content-type and size validation, malware-safe handling and explicit outbound preview.
- **FR-406** Record an explainable work timeline; screen capture remains separately opt-in and visibly indicated.

### Travel

- **FR-500** Create a travel plan from destinations, dates, passengers, budget, cabin/room preferences, loyalty and accessibility needs.
- **FR-501** Search flights and hotels through approved APIs when available, otherwise through an isolated browser profile.
- **FR-502** Normalize offers into comparable price, duration, stops, baggage, refundability, cancellation and location data.
- **FR-503** Recheck price and availability immediately before booking.
- **FR-504** Prepare traveller and contact data locally without exposing payment credentials to the model.
- **FR-505** Stop at the final purchase/legal/CAPTCHA/MFA boundary and hand control to the user unless a future provider-specific regulated payment flow is explicitly approved.
- **FR-506** Capture confirmed reservations, receipts and cancellation terms, then propose calendar events and reminders.
- **FR-507** Treat cancellation/rebooking as a new governed workflow with price and penalty disclosure.

### Automation, notifications and dashboard

- **FR-600** Support one-shot, interval, cron and event-triggered workflows with run history.
- **FR-601** Provide local macOS notifications for due work, approvals, connection expiry and workflow failure.
- **FR-602** Let the user enable, pause, edit and delete every standing automation from the dashboard.
- **FR-603** Add Inbox, Agenda, Work, Travel, Approvals, Connections and Activity views to Personal Assistant.
- **FR-604** Surface pending approvals with exact effect, destination, data disclosed, cost and expiry.
- **FR-605** Provide paginated audit history and searchable operation receipts.
- **FR-606** Support soft deletion and restoration for local operational records; provider deletes follow provider recovery semantics.

## Permission model

| Level | Examples | Default behaviour |
|---|---|---|
| R0 Read | search mail, view calendar, compare travel offers | May run when account scope exists |
| R1 Reversible local write | draft mail, create local task, label mail, tentative local plan | May run under an explicit standing rule; audit required |
| R2 External/reputational write | send mail, invite attendees, edit shared task, submit non-financial form | Exact preview and user approval unless a narrow standing rule authorizes the precise operation |
| R3 Financial/legal/destructive | book/cancel travel, pay, accept terms, permanent delete, credentials/MFA | User handoff or action-time confirmation; voice-only approval forbidden |

## Non-functional requirements

- **NFR-001 Security:** default deny, least-privilege scopes, exact resource ownership checks and capability-bound execution.
- **NFR-002 Privacy:** minimize prompt payloads; redact secrets and unnecessary PII; configurable retention and local deletion.
- **NFR-003 Reliability:** at-least-once workflow delivery with exactly-once external effects through idempotency and provider reconciliation.
- **NFR-004 Availability:** core local organizer and conversation remain usable when a connector is offline.
- **NFR-005 Performance:** cached dashboard reads under 250 ms; local plan creation under 1 s excluding model/provider time; progress visible within 500 ms.
- **NFR-006 Accessibility:** keyboard navigation, visible focus, VoiceOver labels, reduced motion, 200% text zoom and no clipped controls in English or Chinese.
- **NFR-007 Observability:** structured redacted logs, correlation IDs, per-step timing, provider rate-limit state and user-readable receipts.
- **NFR-008 Maintainability:** typed ports, provider contract tests, schema migrations and no direct provider SDK calls from conversational routing.
- **NFR-009 Portability:** macOS remains primary; provider/domain modules do not import AppKit.
- **NFR-010 Data integrity:** UTC storage plus IANA time zone, monotonic revisions, foreign keys and transactional outbox.
- **NFR-011 Compatibility:** adapter contracts are versioned independently from OpenClaw and reject incompatible plugin schemas with a visible diagnostic instead of best-effort execution.
- **NFR-012 Catalog performance:** a cached capability snapshot renders in under 250 ms; discovery runs off the voice response path and never delays the first spoken acknowledgement.

## Implicit requirements checklist

| Concern | Requirement |
|---|---|
| Pagination | Cursor pagination for mail, events, workflows, approvals and audit |
| Error states | Offline, expired token, rate limit, conflict, stale price, partial completion and user handoff |
| Email notifications | Assistant may draft/send only through the mail permission model; operational failures use local notification by default |
| Mobile | Not in V1; responsive dashboard and future remote notification adapter are preserved |
| Admin panel | Connections, permissions, standing rules and audit live in the existing single-owner dashboard |
| File uploads | Existing Workspace Library remains the only default file ingress; attachments are copied into a bounded staging area |
| Audit logs | Append-only local log for plans, approvals, effects, failures and reconciliation |
| Soft delete | Required for local tasks/plans/rules; provider operations follow provider undo/trash capabilities |

## Constraints and assumptions

- Single owner, local macOS deployment, loopback Gateway and SQLite remain the operating model.
- Provider OAuth app registration and, for public distribution, Google/Microsoft verification are external prerequisites.
- Travel API access may require commercial onboarding. Browser automation cannot guarantee success against CAPTCHA, anti-bot, MFA or changing websites.
- ChatGPT/Codex connectors are not assumed to be callable by the bundled OpenClaw runtime; MERRICK owns connector contracts.
- OpenClaw, Codex and ClawHub marketplaces are separate capability sources. Availability in one source does not imply installation, connection or authorization in another.
- The bundled `gog` and `himalaya` skills currently lack their required local binaries; they are discovery candidates, not working mail/calendar connections.
- Community search results are untrusted metadata. V1 does not automatically install community packages and does not treat popularity or source linkage as a security review.
- The first implementation defaults to Google Workspace; Microsoft 365 uses the same ports in the next milestone unless the owner chooses otherwise.
- Send, invite, cancel and purchase standing rules default to disabled.

## Resolved conflicts

- “Use all OpenClaw capabilities” conflicts with current private-data and payment boundaries. Resolution: expose the complete typed capability catalog while keeping host authority risk-tiered.
- “Operate personal accounts” conflicts with untrusted browser content. Resolution: API-first connectors and an isolated browser lane; webpage content never grants authority.
- “Fully automate booking” conflicts with payment, legal, CAPTCHA and MFA requirements. Resolution: automate search, comparison and form preparation; require user handoff for the final boundary.

## Open configuration choices

These do not block the core architecture:

1. Primary mail/calendar provider: Google Workspace or Microsoft 365.
2. First external task provider: Todoist, TickTick, Asana or ClickUp.
3. Travel source: provider API partnership (recommended for reliability) versus browser-only preparation.
