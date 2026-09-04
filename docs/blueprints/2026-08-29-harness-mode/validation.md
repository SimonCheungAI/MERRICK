# Architecture Validation

## Result

**PASS WITH WARNINGS — implementation may begin at Milestone 0 only.**

The design passes all 25 architecture checks. The warnings are implementation
gates, not unresolved architecture conflicts: the current broad OpenClaw host
authority must be narrowed before production activation; the sandbox must fail
closed on every supported macOS build; and packaged update preservation must be
proven before V1 release.

## 25-point quality check

### Scalability

- [x] **S1 — Indexed hot columns:** project/job status, revision identity,
  installation compatibility/health, grants, packages, audit resource/time and
  active-set membership have explicit indexes or uniqueness constraints.
- [x] **S2 — No N+1 design:** library screens use one joined bulk projection;
  revision/grant/health summaries are not queried per card.
- [x] **S3 — Caching:** redacted library projection caches by active generation;
  source, artifacts and dependencies use content-addressed caches.
- [x] **S4 — Durable/externalized state:** SQLite and PluginVault own jobs,
  revisions, grants and active sets. Memory holds reconstructable leases,
  sockets and caches only.
- [x] **S5 — Scaling path:** the local app is intentionally single-instance;
  a future multi-host version can substitute PostgreSQL and leased host worker
  supervisors without changing domain or API contracts.
- [x] **S6 — Async long work:** author/build/test/import/export/activation and
  migration are durable jobs and do not block HTTP/WebSocket request threads.

### Security

- [x] **SEC1 — Authentication:** every endpoint requires the authenticated
  loopback owner session; there are no public Harness endpoints.
- [x] **SEC2 — Authorization:** owner checks apply per resource; persistent/FULL
  grants and lifecycle commits require exact native owner assertions. The model
  has no approval/activation API.
- [x] **SEC3 — Input validation:** versioned schemas, body/upload limits,
  normalized permissions and hardened archive inspection are defined.
- [x] **SEC4 — Sensitive data:** Keychain stores secrets; the vault is private;
  exports, audit and evidence exclude secrets/PII; backups retain private file
  permissions and rely on OS disk encryption for source at rest.
- [x] **SEC5 — Secret management:** workers receive opaque handles and an empty
  environment, never raw Keychain, Gateway, signing or bridge secrets.
- [x] **SEC6 — Auth throttling:** owner-assertion verification/upload is limited
  to five requests/minute with progressive local backoff and security audit;
  other read/mutation/job limits are explicit.

### Maintainability

- [x] **M1 — Folder convention:** domain/application/adapters/contracts and
  separate signed bridge/SDK/UI/test folders follow the existing modular-monolith
  convention.
- [x] **M2 — Separation of concerns:** agent, policy, package, registry, config,
  bridge, worker and native-host responsibilities are explicit.
- [x] **M3 — No circular dependencies:** adapters point inward to application
  ports and pure domain rules; plugin code is never imported into the app/Gateway.
- [x] **M4 — External configuration:** grants, active sets, compatibility ranges,
  manifests and product limits are versioned state/configuration, not generated
  source conditionals.
- [x] **M5 — Logging:** correlation IDs, append-only redacted audit events,
  tamper-evident hashes and bounded evidence retention are defined.
- [x] **M6 — Actionable errors:** stable phase-specific taxonomy, retry matrix,
  recovery actions, Safe Mode and snapshot restore are specified.

### Performance

- [x] **P1 — Latency targets:** library reads target 300 ms at 500 plugins,
  policy decisions 100 ms excluding owner input and progress start 500 ms;
  long operations are visibly asynchronous.
- [x] **P2 — DB connections:** one serialized SQLite writer and bounded read pool;
  no DB lease spans model/build/Gateway work.
- [x] **P3 — Pagination:** every project/job/library/evidence/grant/import-file,
  active-set and audit list uses bounded cursor pagination.
- [x] **P4 — Static assets:** signed, versioned, loopback-served assets with CSP,
  no third-party runtime resources or plugin-provided HTML.

### Consistency

- [x] **C1 — Naming:** plural REST resources, `snake_case` JSON, prefixed opaque
  IDs and consistent job semantics.
- [x] **C2 — Errors:** every endpoint uses the same code/message/retryable/
  correlation/recovery envelope.
- [x] **C3 — Time:** all stored/API timestamps are ISO-8601 UTC; local display
  conversion is presentation-only.

## Requirements coverage

| Requirement cluster | Architecture/spec evidence | Delivery |
|---|---|---|
| Natural-language authoring and iteration | Harness Orchestrator, model tool subset, project/revision/job models | M1, M5 |
| Explicit authorization and Full Access | Host Policy Kernel, native assertion, revision-bound grants | M3–M4 |
| Real OpenClaw production tools | Signed Harness Bridge, worker RPC, active-set transaction | M4 |
| Export/upload | Deterministic package, safe intake and import/export APIs | M2 |
| Upgrade survival | Application Support vault, migrations, compatibility quarantine | M0, M6 |
| Rollback/recovery | Immutable revisions, last-known-good generation, Safe Mode | M4, M6 |
| Native ecosystem compatibility | Explicit `native_full_trust` profile | M7 |

## Warnings and assigned resolutions

1. **Current broad OpenClaw authority:** the existing main-agent configuration
   can bypass a future lifecycle UI unless production config/vault mutation is
   technically removed from the model's direct surface. **Resolution: M0,
   release blocker for M4.**
2. **macOS sandbox support:** the exact enforceable profile and child-process
   behavior must be verified on every supported macOS release; unavailable or
   weakened isolation must not fall back to unrestricted execution. **Resolution:
   M3, release blocker for preview and production sandbox plugins.**
3. **Upgrade ownership:** the current repository has an Application Support
   convention, but the new PluginVault preservation contract is not yet tested
   through signed bundle replacement/uninstall. **Resolution: M0 creates the
   location; M6 is the V1 release gate.**
4. **Native OpenClaw plugins:** fine-grained plugin permissions are not
   enforceable for in-process native code. **Resolution: keep disabled through
   V1; M7 requires separate Full Trust approval and recovery qualification.**

## Final gate

Architecture is internally consistent and ready for thin-slice implementation.
Implementation may begin with **Milestone 0 — Authority and persistent-vault
baseline**. Generated/imported production activation must remain disabled until
Milestones 0–4 and their release-blocking tests pass.
