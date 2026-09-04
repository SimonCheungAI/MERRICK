# Risk Register

| ID | Risk | Likelihood | Impact | Mitigation | Owner / milestone |
|---|---|---:|---:|---|---|
| R-01 | Current template exposes `exec: full`, elevated mode, destructive actions and `approvalPolicy: never` to the main agent | High | Critical | Milestone 0 makes typed host policy the only production effect path; add configuration conformance tests and fail closed outside explicit developer mode | Architecture / M0 |
| R-02 | Prompt injection in mail, event descriptions, attachments or webpages requests data/tool use | High | Critical | Tag untrusted content, read-only agent isolation, opaque host IDs, cross-domain disclosure check, injection test corpus | Security / M0–M3 |
| R-03 | OAuth tokens or PII leak into prompts/logs/SQLite/backups | Medium | Critical | Keychain refs, encrypted fields, schema allowlists, redaction tests, backup exclusions, retention controls | Security / M1 |
| R-04 | Duplicate email, invitation or booking after timeout/retry | Medium | Critical | Idempotency keys, provider IDs/etags, execution-attempt ledger, unknown-outcome reconciliation, never blindly retry R3 | Workflow / M1–M5 |
| R-05 | Voice/ASR mishears recipient, date, traveller or amount | High | High | Typed entity resolution, exact previews, text/native confirmation for R2/R3, voice-only R3 forbidden | Product / M3–M5 |
| R-06 | Browser automation changes or clicks a destructive submit | High | High | API-first, isolated profile, domain/site adapters, submit boundary blocked, selector refresh once, visible handoff | Browser / M5 |
| R-07 | Personal browser/session is exposed to agent | Medium | Critical | Dedicated OpenClaw profile by default; explicit per-session opt-in for personal browser; no password manager/sync in agent profile | Security / M0, M5 |
| R-08 | Travel API access, prices or inventory are incomplete | High | Medium | Provider abstraction, source disclosure, live price refresh, browser supplement, never imply exhaustive market coverage | Travel / M5 |
| R-09 | Travel provider onboarding, commercial terms or regional regulation delays release | High | High | Build test-mode handoff first, separate search from transaction, treat commercial launch as external gate | Product/legal / M5–M7 |
| R-10 | Google restricted scopes or Microsoft tenant policies block connection | Medium | High | Incremental least-privilege scopes, developer/test mode, verification workstream, clear reauth diagnostics | Connections / M2, M7 |
| R-11 | Local DB migration corrupts existing tasks/meetings/briefings | Low | High | Copy-verify-swap, timestamped recoverable backup, migration fixtures from every historical schema | Data / M1, M4 |
| R-12 | Provider and local edits create sync loops or overwrite newer work | Medium | High | External link table, etag/revision checks, tombstones, conflict UI, no last-write-wins for meaningful fields | Work / M4 |
| R-13 | Scheduled workflow runs twice or after being disabled | Medium | High | Gateway job id + local idempotency, generation ownership, pause barrier and audit verification | Automation / M6 |
| R-14 | Long-running OpenClaw/browser step blocks conversation | Medium | Medium | Detached workflow worker, per-step timeout/cancellation, circuit breaker, progress separate from final answer | Runtime / M1, M5 |
| R-15 | Model ranking hides fees, refundability or uncertainty | Medium | High | Deterministic normalized fields, source/refresh timestamp, total-cost computation outside model, terms shown before selection | Travel / M5 |
| R-16 | User assumes “full assistant” includes unsupported sites or guaranteed bookings | High | Medium | Capability inventory, per-provider status, explicit handoff language, never claim completion without receipt | UX / all |
| R-17 | Audit log itself becomes a privacy liability | Medium | Medium | Redacted metadata, body hashes not content, retention/export/delete controls, encrypted backup | Security / M1, M7 |
| R-18 | Third-party plugin or skill supply-chain compromise | Medium | Critical | Pin versions/checksums, allowlisted manifests, signed/bundled assets, no automatic unreviewed installs, security audit before enable | Runtime / M0, M7 |
| R-19 | Connector outage blocks core assistant | Medium | Medium | Per-connector circuit breaker, cached dashboard, local organizer independent, visible degraded state | Reliability / M2+ |
| R-20 | Approval fatigue leads to unsafe broad standing rules | Medium | High | Batched low-risk previews, narrowly templated rules, R3 excluded, periodic permission review and expiry | Product/security / M3, M6 |
| R-21 | OpenClaw/plugin upgrade changes a tool schema while an old mapping remains enabled | Medium | Critical | Persist schema hashes and compatible versions; quarantine drift before execution; contract fixtures per supported version | Runtime / M0 |
| R-22 | A plugin name/description or MCP descriptor tricks the planner into selecting a higher-authority operation | Medium | Critical | Treat catalog metadata as untrusted, map only reviewed operations to canonical intents, host-side risk and account resolution | Security / M0–M1 |
| R-23 | Chinese tool discovery fails because OpenClaw lexical Tool Search expects English | High | Medium | Canonical bilingual intent map and bounded private-data-free English catalog queries; test Chinese paraphrase corpus | Product/runtime / M0–M2 |
| R-24 | Capability refresh or Gateway reload blocks the first voice response | Medium | High | Background snapshots, last-known-safe cache, no discovery/reload on the acknowledgement path, latency regression tests | Runtime / M0 |
| R-25 | Marketplace availability is mistaken for installation, connection or permission | High | High | Separate source/install/enable/readiness/connection/grant states in storage and UI; never auto-install or auto-authorize | Product/security / M0–M2 |

## Immediate pre-implementation warning

The current OpenClaw template's broad execution settings must not be interpreted as completion of this project. They increase capability visibility but do not provide domain authorization, idempotency, provider reconciliation or safe handling of external content. Milestone 0 is therefore a release-blocking prerequisite, not optional hardening.
