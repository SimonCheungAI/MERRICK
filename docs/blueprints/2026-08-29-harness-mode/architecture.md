# Architecture

## Pattern and decision

Extend the existing local **modular monolith** with a durable Harness workflow,
a host-owned plugin policy kernel, a persistent user plugin vault and an
out-of-process plugin runtime. OpenClaw remains the conversational planner and
tool orchestrator. It is not the authority that approves or installs the code
it generated.

A microservice architecture is rejected because MERRICK is a single-owner
desktop product. Loading arbitrary generated code directly into the production
OpenClaw Gateway is also rejected as the default: an in-process Node plugin can
bypass a per-tool permission manifest before the host can mediate it.

## Component map and trust boundaries

```text
Verified owner
 voice request ─────────────── trusted native click / biometric assertion
      │                                      │
      ▼                                      ▼
Native macOS host + Web HUD ───── authenticated loopback bridge ─────┐
  Harness workspace · diff · evidence · permission sheet             │
                                                                     ▼
                    MERRICK modular monolith (FastAPI)
  ┌────────────────────────────────────────────────────────────────────┐
  │ Harness Orchestrator                                               │
  │  durable jobs · revisions · build/test pipeline · cancellation     │
  │                                                                    │
  │ Policy & Approval Kernel       Package/Compatibility Service       │
  │  normalized grants             archive inspection · hashes · SBOM  │
  │  owner assertion               schema migration · quarantine       │
  │                                                                    │
  │ Plugin Registry (SQLite)       Gateway Config Projector            │
  │  lifecycle · grants · audit     staged config · restart · rollback │
  └──────────────────────────────┬─────────────────────────────────────┘
                                 │ exact broker capabilities
        ┌────────────────────────┴────────────────────────┐
        ▼                                                 ▼
Harness Lab                                        Production Runtime
 separate state/home                              jarvis-harness-bridge
 test Gateway + fixtures                OpenClaw tool registration/proxy
 no user secrets                                       │ typed local RPC
 deny-by-default egress                                ▼
        │                                      Plugin Worker Supervisor
        ▼                                   one revision/process boundary
Plugin Worker Sandbox                           scoped fs/net/app/process
generated/imported code                         audit · timeout · revocation

Persistent user data (outside signed app bundle)
~/Library/Application Support/JarvisStark/PluginVault/
  registry.sqlite · projects/ · revisions/ · artifacts/ · packages/
  evidence/ · backups/ · trash/ · runtime/
```

The signed application ships the orchestration, bridge and migration code. It
never owns mutable user-plugin source. The vault belongs to the OS user and is
preserved across normal application replacement, update and reinstall.

## Responsibility boundaries

| Component | Owns | Must not own |
|---|---|---|
| OpenClaw/Codex agent | Requirement interpretation, source generation, test proposals, repair suggestions | Approval, persistent grants, production config, signing keys |
| Harness Orchestrator | Durable phase machine, workspace leases, tool budgets, evidence collection | Trusting generated manifests without host validation |
| Policy Kernel | Permission normalization, risk computation, owner assertions, grants and revocation | Executing plugin code or taking model claims as evidence |
| Package Service | Safe archive inspection, canonical hashing, signing, import/export, compatibility checks | Loading imported code while inspecting it |
| Plugin Registry | Stable identity, immutable revisions, active-set and last-known-good snapshots | Secret values or mutable source blobs inside JSON columns |
| Config Projector | Build staged OpenClaw config from committed registry state, restart and rollback | Accepting arbitrary config fragments from a plugin |
| Harness Bridge | Register stable OpenClaw proxy tools and route exact calls to workers | Evaluating plugin JavaScript in the Gateway process |
| Worker Supervisor | OS process isolation, RPC, budgets, health and termination | Granting access that is absent from the host grant |
| Native host | Trusted approval surface, Keychain, macOS permission prompts | Treating voice/model/WebView fields as authorization |

## Plugin execution profiles

### Sandboxed Harness plugin — default

Generated plugins target a small, versioned Harness Plugin ABI. The production
Gateway loads one reviewed core plugin, `jarvis-harness-bridge`, which publishes
the generated plugin's tools and forwards calls over authenticated local RPC to
one worker process per active revision. Host services such as filesystem,
network, apps, subprocesses and secrets are capability calls; each is checked
against the current grant and audit policy.

This profile supports least privilege, immediate revocation, per-plugin crash
containment and most activation without loading generated JavaScript into the
Gateway. Tool-catalog changes may still require a controlled Gateway refresh
until the pinned OpenClaw version supports reliable dynamic registration.

### Native OpenClaw compatibility plugin — exceptional

An imported package that requires OpenClaw's unrestricted in-process plugin SDK
cannot be honestly constrained by the Harness permission broker. It is labelled
`native_full_trust`, requires a separate trusted-host warning and owner click,
is never auto-enabled, and always triggers a Gateway restart. Its effective
authority is the Gateway process authority, regardless of manifest claims.

The initial product may export such packages but should not generate them by
default. This profile exists for OpenClaw ecosystem compatibility, not as a
shortcut around the sandbox.

## Permission architecture

Permissions are host-normalized structured values, not free-form strings:

- filesystem: exact roots, read/write/create/delete and symlink policy;
- network: scheme, host, port and HTTP methods, with private-network denial;
- process: exact executable identity, argument pattern and working roots;
- applications: bundle ID and bounded operations;
- data: conversation, memory, contacts, mail and calendar classes;
- secrets: opaque named handles, never plaintext delivery by default;
- effects: read, local write, external write, destructive and financial;
- runtime: CPU, memory, wall time, concurrency and output limits.

The effective grant is the intersection of the plugin declaration, user choice,
OS permission and product maximum. It can be `once`, `session`, `while_enabled`
or `persistent`. `full_access` expands the product maximum for that plugin, but
remains revocable and cannot bypass OS consent, Keychain isolation, package
integrity or the prohibition on self-approving new permissions.

A global owner preference may reduce repeated prompts, but first activation of
a new plugin and every permission expansion still presents the exact effective
scope in the trusted native surface. Voice can request the sheet; it cannot
press the approval control.

## Key flow A — instruction to production capability

1. The verified owner says or types, for example, “build a plugin that turns my
   meeting notes into follow-up tasks.” MERRICK creates a Harness project
   and an immutable draft revision; it does not touch the active plugin set.
2. The agent receives a bounded workspace and approved authoring tools. It
   writes source, tests and a declared permission manifest through the Harness
   file API. Web/document content inside the project remains untrusted.
3. The orchestrator resolves dependencies from a pinned allowlisted registry,
   builds with lifecycle scripts disabled, runs type checks, OpenClaw/Harness
   validation, static analysis, unit tests and package-content checks.
4. A preview starts a disposable Gateway and worker under a separate home with
   synthetic fixtures and no credentials. The owner can exercise the new tool;
   every attempted capability is displayed as evidence.
5. The policy kernel compares declared, observed and requested capabilities and
   produces a permission diff. Any undeclared access fails the preview.
6. The native host displays source provenance, tests, compatibility, requested
   permissions and the difference between sandboxed and Full Access modes.
7. Approval creates a signed, revision-bound grant. The installer stages the
   immutable revision, projects a candidate active set, restarts or refreshes
   OpenClaw, runs health checks, then commits the active-set generation.
8. Failure terminates the worker, restores the previous config/active set,
   restarts the last-known-good Gateway and retains the failed revision for
   repair or export.

## Key flow B — import and upgrade survival

1. The owner selects a `.jarvis-plugin` file. The backend copies it to a
   non-executable intake directory with a randomized name and enforces compressed
   size limits before parsing anything from the archive.
2. The package service rejects traversal paths, links, special files, duplicate
   canonical paths, oversized expansion, excessive nesting and unsupported
   schemas. It verifies canonical hashes and an optional publisher signature.
3. Metadata, source diff, compatibility and requested permissions are shown
   before extraction into an immutable vault revision. Exported grants and
   secret references are ignored by schema.
4. The imported revision follows the same build, preview and owner-approval path
   as generated code. An ID collision creates a distinct origin-qualified
   identity; only one conflicting public OpenClaw ID may be active.
5. During a later MERRICK update, the signed app bundle is replaced but
   `PluginVault` remains untouched. Startup takes an atomic pre-migration backup,
   migrates registry metadata and revalidates enabled revisions against the new
   Harness ABI/OpenClaw ranges.
6. Compatible revisions are loaded into the candidate active set. Incompatible
   revisions stay in the vault and become `quarantined`; the previous package,
   source and evidence remain available for repair or export.
7. The Gateway starts Safe Mode if the candidate set fails globally, then lets
   the owner restore the last-known-good generation or diagnose plugins one by
   one.

## Storage and package layout

```text
PluginVault/
  registry.sqlite
  registry.sqlite-wal / registry.sqlite-shm
  projects/<project_uuid>/worktree/          mutable owner draft
  revisions/<origin_uuid>/<plugin_uuid>/<sha256>/
    source/                                  immutable normalized source
    dist/                                    immutable build output
    manifest.json
    permissions.json
    sbom.cdx.json
  evidence/<revision_uuid>/<run_uuid>/       bounded immutable test evidence
  packages/<export_uuid>.jarvis-plugin       optional retained exports
  runtime/<instance_uuid>/                   sockets and non-durable temp data
  backups/<schema_version>/<timestamp>/      atomic migration snapshots
  trash/<tombstone_uuid>/                    recoverable removals
```

Archives use a deterministic ZIP container with normalized UTF-8 paths,
timestamps and permissions. `package.json` lifecycle scripts are stripped or
disabled in sandboxed builds. Dependencies are locked and mirrored into an
app-controlled content-addressed cache; `node_modules` is never exported.

## Active-set transaction and upgrade strategy

The registry owns monotonically increasing active-set generations. The Config
Projector reads only a committed generation and writes a complete candidate
OpenClaw config to a private temporary file. It validates the file with the
pinned CLI, atomically swaps it into place, restarts the Gateway and waits for
the exact generation/bridge health response. Only then does it mark the
generation active. The previous config, registry generation and runtime health
receipt remain a rollback unit.

Application updates use expand-migrate-contract schema changes. They first
verify available disk space, checkpoint SQLite, create a private snapshot and
record the app/runtime/plugin-API versions. Migrations are forward-only. A
failed migration leaves the old vault untouched and starts the application in
read-only recovery mode. No application installer or upgrade script recursively
deletes `PluginVault`.

## Technology choices

| Layer | Choice | Rationale |
|---|---|---|
| Application | Existing Python/FastAPI modular monolith | Reuses authenticated WebSocket, Gateway ownership and lifecycle code |
| Durable state | SQLite, WAL, foreign keys, numbered migrations | Correct local scale; transactions cover registry, jobs, grants and audit |
| Agent/runtime | Pinned OpenClaw + Codex authoring tools | Existing production orchestration and plugin SDK |
| Plugin ABI | TypeScript SDK + JSON Schema messages | Natural OpenClaw ecosystem fit with host-verifiable contracts |
| Isolation | Separate worker processes + macOS sandbox profile + RPC broker | Enforceable process boundary with per-plugin revocation |
| Build | Bundled Node/pnpm, frozen lockfile, lifecycle scripts disabled | Reproducibility and no dependency install hooks |
| Packaging | Deterministic ZIP, SHA-256, CycloneDX SBOM, optional Ed25519 signature | Portable, inspectable and versionable artifacts |
| Secrets | macOS Keychain and opaque secret handles | Secrets never enter package, database, prompts or logs |
| UI transport | Existing versioned WebSocket plus bounded local HTTP upload/download | Streams jobs while handling files without base64 expansion |
| Testing | Python unit/integration, Vitest for SDK/plugins, disposable Gateway E2E | Tests policy independently and verifies real OpenClaw registration |

## Scalability and concurrency

- Optimize for one owner, up to 500 installed revisions, 50 enabled plugins and
  four concurrent Lab jobs; these are configurable product limits, not trust
  decisions.
- Serve library and installation screens from one bulk registry projection with
  joined revision/grant/health summaries; never issue one query per plugin card.
  Cache this redacted projection by active-set generation and invalidate it on a
  registry commit. Content-addressed source, build and dependency objects are
  cached independently by hash.
- Serialize registry migrations, active-set commits and Gateway restarts.
- Use one serialized SQLite writer and a small bounded read-connection pool.
  Requests enqueue long-running work and never hold a database connection while
  a model, build, worker or Gateway restart is running.
- Lease one project revision to one authoring job; concurrent jobs create new
  revisions rather than editing the same source tree.
- Run workers separately with per-instance CPU, memory, wall-time, output and
  request-rate budgets. A crashing plugin cannot crash the application process.
- Use content-addressed build/dependency caches and deduplicate identical
  immutable revisions. Never deduplicate grants, audit or private evidence.
- Cursor-paginate audit and library projections and retain a bounded structured
  event stream; no external broker is needed for local V1.
- Durable jobs, revisions, grants and active sets are externalized to SQLite and
  the vault; process memory holds only reconstructable leases, sockets and
  caches. A future multi-host edition can replace SQLite with PostgreSQL, claim
  jobs through leases and assign plugin workers to host-specific supervisors
  without changing domain/API contracts. The local desktop remains intentionally
  single-instance rather than pretending to be horizontally scalable itself.

## Security architecture

- The loopback API requires the existing per-launch bridge secret and strict
  origin checks. Upload and download use short-lived, single-purpose tickets.
- Only the native host can submit a valid owner assertion for persistent or
  Full Access decisions; WebView fields are untrusted presentation data.
- The model cannot call activation, grant, signing-key or migration APIs.
  Model-facing tools can create/edit/test drafts and request an approval sheet.
- Package metadata, README, source comments, tests and tool descriptions are
  untrusted. Their instructions cannot alter policies or invoke unrelated tools.
- Sandboxed workers begin with an empty environment, private temporary home,
  closed inherited file descriptors and no Keychain/Gateway token. Network and
  host actions cross authenticated broker RPC with exact capability checks.
- Full Access is visually distinct, records the requested and effective scope,
  expires/revokes immediately at the broker and never grants permission to edit
  the policy kernel, registry, core bridge, MERRICK app bundle or another
  plugin's vault content.
- Native full-trust imports are an explicit exception: the UI must state that
  fine-grained enforcement is unavailable and provide Safe Mode/rollback.
- Exports are generated from an allowlist of immutable revision files; packages
  can never select arbitrary filesystem paths for inclusion.
- Audit records contain hashes, identities, decisions and stable error codes,
  not source prompts, secrets, personal documents or raw command output.

## Folder ownership

```text
server/harness/                  domain and application services
  domain/                        entities, permission algebra, state machines
  application/                   jobs, installer, migration and recovery
  adapters/                      sqlite, archive, build, sandbox, OpenClaw
server/contracts/harness/v1/     Pydantic and emitted JSON Schemas
openclaw/plugins/
  jarvis-harness-bridge/         signed core proxy plugin only
openclaw/harness-sdk/            versioned TypeScript authoring SDK
desktop/harness/                 trusted approval and file panels
web/harness/                     project, evidence and library presentation
tests/harness/                   unit, contract, integration, E2E and fixtures
```

Dependencies point inward: adapters depend on application ports, which depend
on pure domain rules. Generated/imported plugin code is never imported by a
Python application module or the production OpenClaw Gateway.

## UI and static-asset delivery

Harness views remain versioned HTML/CSS/JavaScript assets inside the signed app
and are served only by the authenticated loopback backend with the existing
strict CSP. V1 loads no third-party runtime script, font or plugin-provided HTML.
Source, README and evidence are rendered as escaped text. Development may disable
asset caching; packaged releases cache immutable assets by application build.
