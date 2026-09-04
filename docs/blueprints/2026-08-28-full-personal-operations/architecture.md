# Architecture

## Phase 2 — Pattern

Extend the current local **modular monolith** with a durable workflow kernel, a host-owned policy engine and a typed connector gateway. OpenClaw remains the planner and workflow orchestrator; it never receives provider credentials and never becomes the final authorization source.

Microservices are rejected: this is a single-owner local product, and network boundaries would increase failure and deployment complexity without a scaling benefit. Browser-only automation is also rejected as the primary architecture because mail, calendar and booking effects need stable identifiers, idempotency and reconciliation.

## Component map

```text
Voice / text / scheduled trigger
              │
              ▼
Native macOS host + Web HUD
  permissions · biometric handoff · notifications · visible approval
              │ authenticated typed bridge
              ▼
Personal Operations Application (FastAPI modular monolith)
  ├─ Command intake + entity resolution
  ├─ Workflow kernel + transactional outbox
  ├─ Host-owned policy / approval engine
  ├─ Organizer / meetings / briefing domain
  ├─ Connection broker + Keychain references
  ├─ Audit / receipts / reconciliation
  └─ Connector registry
       ├─ Mail: Gmail API / Microsoft Graph / IMAP read-only fallback
       ├─ Calendar: Google Calendar / Microsoft Graph / EventKit adapter
       ├─ Work: local organizer / Todoist / TickTick / Asana / ClickUp
       ├─ Artifacts: local Workspace / provider document APIs
       ├─ Travel: approved API adapter / isolated browser adapter
       └─ Notifications: macOS / optional channel adapter
              ▲                          ▲
              │ typed tool contracts     │ isolated, bounded capabilities
              │                          │
OpenClaw Gateway + Codex harness ────────┘
  planner · skills · TaskFlow · automations · memory · isolated browser
```

## Responsibility boundaries

| Module | Owns | Must not own |
|---|---|---|
| OpenClaw orchestration | Natural-language planning, tool selection, workflow sequencing, summaries | Credentials, final approval, payment data, provider retries with side effects |
| Policy engine | Risk classification, grants, approval tickets, data-disclosure checks | Natural-language generation |
| Workflow kernel | Durable state, retries, idempotency, compensation, reconciliation | Provider-specific payload construction |
| Connector adapters | OAuth refresh, provider schemas, cursors, rate limits, effect verification | Cross-domain policy decisions |
| Native host | Keychain, biometrics, macOS permissions, notifications, handoff UI | Model planning |
| Web HUD | Presentation and explicit owner decisions | Trusting client-supplied authorization fields |

## OpenClaw capability adaptation

MERRICK adds a host-owned **Capability Adapter** between OpenClaw's
inventories and the Personal Operations application. It consumes declarative
plugin manifests, skill eligibility, effective tool policy, MCP descriptors and
Codex dynamic-tool descriptors. It does not execute a plugin while building the
catalog and never treats `installed`, `enabled`, `eligible`, `connected` and
`authorized` as synonyms.

```text
OpenClaw manifests / skill cards / effective tools / MCP / Codex dynamic tools
                                  │
                                  ▼
                     Capability discovery adapters
                                  │ bounded, redacted observations
                                  ▼
                 Canonical Capability Registry snapshot
         source · trust · health · dependencies · auth · schema · risk
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
          Dashboard projection          Intent/connector resolver
                                                │
                           host policy → preview/approval → connector
```

### Canonical descriptor

Every executable surface is projected into an app-owned descriptor with a
stable canonical intent, source-specific operation ID, schema hash, effect
class, maximum risk, required account/scopes, readiness, health and trust
profile. Provider-specific names never become the conversation contract.
`gmail_search_messages`, a future Microsoft Graph tool and a reviewed IMAP
adapter may all implement `mail.search`; only an exact connector operation is
bound when a plan is validated.

### Resolution order

1. Resolve a Mandarin or English utterance to a canonical intent and typed
   entities without selecting a provider tool.
2. Resolve the requested account and capability grant.
3. Select the highest-precedence healthy connector: first-party API, reviewed
   official OpenClaw plugin, reviewed local adapter, then an explicitly chosen
   browser handoff. Community plugins and personal-browser automation are never
   silent fallbacks.
4. Validate the connector schema hash and classify the exact effect as R0–R3.
5. Execute R0 reads, create R1 drafts, or produce an immutable preview and
   approval request for R2/R3. The model never receives a reusable capability.
6. Reconcile provider IDs and publish one user-facing result; connector work
   remains below the immediate voice acknowledgement path.

OpenClaw Tool Search may compact a large eligible catalog for embedded
OpenClaw agents. The current Codex harness instead uses its stable dynamic-tool
surface. Both are discovery mechanisms only: the same host policy, approval,
audit and connector contracts apply after selection. Because OpenClaw's lexical
catalog search is English-oriented, MERRICK maps Chinese intent labels to
bounded English capability terms without forwarding private utterance text.

### Plugin lifecycle

- Inventory and diagnostics are read-only and may refresh in the background.
- Installation, update, removal, enablement and account connection are separate
  owner-visible operations. Marketplace search results are untrusted metadata.
- A newly discovered tool is `unreviewed` and non-executable until a policy
  profile assigns canonical intents, effect classes, schema bounds and scopes.
- Version or schema-hash changes quarantine the affected executable mapping
  until contract tests or a signed compatibility rule pass; the last safe
  catalog remains visible.
- Revoking one connector invalidates its grants and pending approvals but does
  not disable local organizer or unrelated providers.

### Initial canonical surface

| Domain | Canonical intents | Execution boundary |
|---|---|---|
| Mail | `mail.search`, `mail.read`, `mail.classify`, `mail.draft`, `mail.send` | Search/read R0; draft R1; exact recipient/body send R2 |
| Calendar | `calendar.list`, `calendar.freebusy`, `calendar.propose`, `calendar.commit`, `calendar.cancel` | Read R0; proposal R1; invite/change R2; destructive cancellation up to R3 |
| Tasks | `task.list`, `task.create`, `task.update`, `task.complete` | Local work R0/R1; shared-provider effects up to R2 |
| Documents | `artifact.read`, `artifact.create`, `artifact.update`, `artifact.share` | Bounded local work R0/R1; external disclosure R2 |
| Travel | `travel.search`, `travel.compare`, `travel.prepare`, `travel.handoff` | Research R0; local preparation R1; payment/legal boundary remains user-owned R3 |

## Technology decisions

| Layer | Choice | Rationale |
|---|---|---|
| Runtime | Existing Python/FastAPI process | Preserves voice/WebSocket lifecycle and domain code |
| Orchestration | Pinned OpenClaw Gateway + TaskFlow/automations | Durable scheduled and multi-step agent work |
| Storage | SQLite with foreign keys, WAL, migrations, outbox | Correct scale for one local owner; transactional writes |
| Secrets | macOS Keychain + opaque `secret_ref` | No refresh token or payment secret in DB/prompt/log |
| Contracts | Pydantic/JSON Schema + versioned WebSocket events | One validated schema across Python, JS, Swift and OpenClaw tools |
| Provider HTTP | `httpx` adapters with OAuth and explicit timeouts | Existing stack, testable transport injection |
| Browser fallback | OpenClaw-managed isolated Chromium profile | Deterministic tabs without touching personal Chrome |
| Native calendar fallback | EventKit adapter behind the same calendar port | Useful local capability without leaking AppKit into domain logic |

## Key flow A — inbox triage and governed reply

1. A scheduled sync uses the mail adapter's cursor to fetch changed metadata and requested bodies; secrets remain inside the adapter.
2. The application stores minimal cache records, emits `mail.changed`, and invokes a read-only OpenClaw workflow with bounded content.
3. OpenClaw proposes labels, priority, follow-up tasks and an optional reply draft. The host validates every referenced message ID and recipient.
4. R0 summaries are displayed automatically. R1 labels/tasks execute only under configured rules.
5. A send creates an R2 `operation_request` and exact preview hash. The HUD shows recipients, subject, body, attachments and disclosed data.
6. Approval creates a short-lived capability bound to that immutable preview. The mail adapter sends once using an idempotency key, then reconciles the provider message ID.
7. Audit records contain hashes and redacted metadata; the full body remains in provider storage or bounded local cache according to retention policy.

## Key flow B — travel search, preparation and booking handoff

1. MERRICK gathers missing dates, travellers, airports, room constraints, budget and refundability requirements into a local `travel_plan`.
2. API adapters search in parallel; an isolated browser adapter may supplement results. Raw webpages are untrusted evidence only.
3. Normalization produces comparable `travel_options`; OpenClaw ranks and explains options but cannot select itself.
4. The owner selects an option. MERRICK refreshes price/availability and displays total cost, currency, baggage, cancellation and supplier.
5. Traveller data is injected by the host adapter from the local vault; payment data is never provided to the model.
6. The workflow stops in `awaiting_user_handoff` on the final supplier checkout. The user handles payment, terms, CAPTCHA and MFA.
7. The connector or receipt parser reconciles the outcome. A confirmed reservation creates a receipt, proposed calendar events and reminders; an unknown outcome is never blindly retried.

## Scalability and concurrency

- Optimize for one owner and several connected accounts, not multi-tenant scale.
- Serialize writes per provider account and per external object; allow bounded parallel reads/searches.
- Keep durable state in SQLite/Keychain rather than process memory. A future multi-host edition can replace the storage ports with PostgreSQL and claim workflow steps through leases without changing domain contracts.
- Use cursor sync and provider webhooks where supported; fall back to jittered polling.
- Keep mail bodies and attachments out of long-lived cache unless explicitly retained.
- Cap workflow step count, browser actions, model tokens, concurrent connector calls and retry duration.
- Use transactional outbox delivery so a local commit and an emitted event cannot diverge.
- Use one serialized SQLite writer and a bounded read-connection pool; provider HTTP adapters reuse bounded `httpx` connection pools.
- Batch related mail/event/task lookups by ID and join dashboard projections; provider adapters expose bulk reads where the provider supports them, avoiding per-row N+1 calls.

## Target folder ownership

```text
server/
  domain/personal_operations/       pure entities, risk and state rules
  application/personal_operations/  workflows, policies and ports
  adapters/
    connections/                    OAuth + Keychain broker
    mail/ calendar/ tasks/ travel/  provider implementations
    storage/                         SQLite repositories, migrations, outbox
    openclaw/                        typed tool adapter
  contracts/v1/                     Pydantic + JSON Schema events/APIs
desktop/
  approvals/ notifications/         native confirmation and delivery
web/
  personal-operations/              dashboard views and accessible components
tests/
  contract/ integration/ e2e/       provider fixtures and cross-surface tests
```

Dependencies point inward: adapters → application → domain. Provider SDKs, FastAPI, AppKit and WebSocket types cannot be imported by the domain package. Runtime/provider configuration stays in validated config files and the connection/grant database, not hard-coded conditionals.

## Delivery and static assets

The HUD remains bundled, versioned static HTML/CSS/JS served only by the loopback backend with strict CSP and no third-party runtime assets. Packaged releases cache immutable assets by build version; development disables cache. Provider logos or remote media are downloaded only through bounded asset adapters and never execute in the HUD origin.

## Security architecture

### Authentication and authorization

- The desktop/WebSocket bridge uses the existing per-launch cryptographic token and loopback binding.
- OAuth uses Authorization Code + PKCE with exact loopback redirect URIs and incremental scopes.
- Every object access checks `owner_id` and `connection_id`; client-provided account ownership is never trusted.
- The policy engine defaults to deny and issues exact, expiring, single-use capability tickets.
- R3 actions require native visual confirmation or user handoff. Voice identity may unlock private read access but cannot approve R3.

### Data protection

- TLS for every provider request; strict SSRF allowlists for webhook and browser fetch surfaces.
- Keychain holds refresh tokens, API keys and traveller secrets. Payment credentials remain with browser/provider wallet whenever possible.
- Structured logs redact message bodies, recipients, traveller PII, tokens and URLs containing secrets.
- Encrypted local backup is opt-in and excludes Keychain material.

### Prompt-injection boundary

- Email, documents, webpages, event descriptions and attachments are tagged as untrusted content.
- Untrusted content is processed by read-only agents with no send/write/purchase tools.
- Tool arguments must reference host-issued opaque IDs; content cannot inject a new account, URL, recipient or scope.
- Cross-domain data disclosure is evaluated before planning and again before execution.

### Provider scope strategy

- Request read scopes first; request send/write scopes only when the user enables that capability.
- Use separate grants for Gmail read/modify/send and Calendar read/events rather than broad all-service access.
- Microsoft Graph mail read/write and `Mail.Send` remain distinct grants.
- Public distribution must complete provider verification for sensitive/restricted scopes.

## Failure containment

- A broken connector opens its circuit but leaves conversation, organizer and other connectors online.
- Unknown booking/send outcomes enter reconciliation; they are not retried as new effects.
- Expired approval returns to preview rather than silently reauthorizing.
- Browser selectors failing mid-flow produce a resumable handoff, not blind clicking.
- Gateway or app restart resumes persisted workflows only after revalidating grants, price/version and user intent freshness.
- Capability discovery timeout, malformed manifests and marketplace outages use the last known safe snapshot; they cannot block the current voice turn.
- An unknown or changed plugin schema is quarantined rather than coerced. Only that mapping becomes unavailable.
- Provider reads may retry within bounded budgets; ambiguous external writes enter reconciliation and are never repeated through a different connector.

## Sources informing the design

- OpenClaw tools and plugins: https://docs.openclaw.ai/tools and https://docs.openclaw.ai/plugins
- OpenClaw isolated browser and security: https://docs.openclaw.ai/tools/browser and https://docs.openclaw.ai/security
- OpenClaw automation: https://docs.openclaw.ai/automation
- OpenClaw Tool Search: https://docs.openclaw.ai/tools/tool-search
- OpenClaw plugin permission requests: https://docs.openclaw.ai/plugins/plugin-permission-requests
- Google Gmail/Calendar scopes: https://developers.google.com/workspace/gmail/api/auth/scopes and https://developers.google.com/workspace/calendar/api/auth
- Microsoft Graph permissions: https://learn.microsoft.com/en-us/graph/permissions-reference
- Duffel flights/stays workflow: https://duffel.com/docs
