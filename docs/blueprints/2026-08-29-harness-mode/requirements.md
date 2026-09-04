# Requirements

## Scope and assumptions

MERRICK Harness Mode lets the verified local owner ask MERRICK to
create, test, preview, install and manage new OpenClaw plugins. Generated and
imported plugins are user-owned data, live outside the signed application
bundle, can be exported or imported as portable packages, and survive normal
MERRICK upgrades.

The first release is local-first and single-owner. A remote marketplace,
publisher payments, organization administration and unattended cross-device
sync are outside V1. “Full Access” means a revocable, host-enforced permission
profile; it never means bypassing macOS, secret-storage or package-integrity
boundaries.

## Functional requirements

### Creation and iteration

- **FR-01**: The verified owner can request a capability in natural language
  and enter Harness Mode explicitly.
- **FR-02**: MERRICK must create a versioned plugin project in an isolated
  lab, never directly in the active plugin store.
- **FR-03**: Each project must include an OpenClaw manifest, source, lockfile,
  permission manifest, generated provenance, tests and human-readable README.
- **FR-04**: MERRICK can inspect, edit, build, type-check, validate and test
  only the selected draft during a Harness session.
- **FR-05**: The owner can inspect a live activity stream, stop generation or
  testing, resume a draft, discard it, or create a new immutable revision.
- **FR-06**: A draft may be previewed in an ephemeral test Gateway whose state
  and credentials are separate from the production Gateway.
- **FR-07**: Harness Mode must produce an evidence bundle containing build,
  validation, test, security-scan and preview results before activation.

### Permission and activation

- **FR-08**: Every plugin declares normalized capabilities: filesystem roots
  and access mode, network destinations, processes/commands, applications,
  secrets, OpenClaw services, user-data classes and destructive effects.
- **FR-09**: The host policy engine, not the model or plugin, computes the
  requested risk tier and activation requirements.
- **FR-10**: Default activation uses least privilege. The owner may grant once,
  grant while enabled, grant persistently, deny, or edit the requested scope.
- **FR-11**: Full Access requires a separate, explicit owner action with a clear
  summary of its consequences. It is plugin-scoped, revocable and auditable.
- **FR-12**: Imported plugins never inherit Full Access or prior grants from
  their publisher, export package or previous device.
- **FR-13**: Installation must be transactional: stage, verify, register,
  restart the Gateway, health-check, then commit; otherwise restore the prior
  active set automatically.
- **FR-14**: The owner can disable, re-enable, roll back, quarantine or uninstall
  a non-core plugin without affecting its exported packages or retained drafts.
- **FR-15**: Core MERRICK plugins remain immutable through Harness Mode.

### Plugin library, export and import

- **FR-16**: The capability library lists core, bundled, generated and imported
  plugins separately with status, source, version, permissions, health and
  available rollback revisions.
- **FR-17**: Lists support search, source/status filters and cursor pagination;
  the initial local implementation may return one bounded page when fewer than
  100 plugins exist.
- **FR-18**: The owner can export a selected immutable plugin revision as a
  `.jarvis-plugin` archive without credentials, tokens, local absolute paths,
  logs, caches, node modules or private test fixtures.
- **FR-19**: Export packages include canonical metadata, content hashes,
  dependency lock data, compatibility constraints and an optional local
  publisher signature.
- **FR-20**: The owner can upload/import a `.jarvis-plugin` file, inspect it
  before installation, and reject or quarantine malformed, incompatible,
  unsigned or unexpectedly privileged packages.
- **FR-21**: Import uses archive traversal, symlink, decompression-bomb, filename,
  file-count and size defenses and never executes package lifecycle scripts
  during inspection.
- **FR-22**: The owner can export or import one plugin in V1; deterministic batch
  backup/restore may follow in V2.

### Upgrade survival and compatibility

- **FR-23**: Mutable plugin projects, artifacts, grants, audit records and the
  registry must live below the app-owned Application Support directory, never
  inside the signed `.app` or source checkout.
- **FR-24**: Application upgrades must preserve user plugin data and run
  forward-only, versioned schema migrations under a pre-migration backup.
- **FR-25**: On first launch after upgrade, MERRICK must revalidate enabled
  plugins against the new OpenClaw/MERRICK compatibility contract before
  loading them.
- **FR-26**: Compatible plugins remain enabled. Incompatible or unhealthy
  plugins are retained but quarantined with an explanation and repair/export
  options; they are never silently deleted.
- **FR-27**: Built-in plugin updates must not overwrite a user-owned plugin,
  even when IDs collide. Stable origin-qualified identities must prevent
  namespace collisions.
- **FR-28**: An uninstall must ask separately whether to retain or remove the
  user plugin vault; normal upgrade and reinstall retain it by default.

### Audit, recovery and UX

- **FR-29**: Every generation, test, permission, import, export, activation,
  restart, rollback, quarantine and migration transition produces a redacted,
  append-only audit event.
- **FR-30**: Plugin deletion is soft by default through a recoverable trash;
  permanent deletion is a separate owner-confirmed operation.
- **FR-31**: Long-running generation/build/test/import operations expose states,
  progress and cancellation and recover safely after app restart.
- **FR-32**: Errors identify the failed phase and offer a safe next action
  without leaking prompts, secrets or host paths.
- **FR-33**: Desktop UI and spoken interaction support the workflow, but voice
  alone cannot grant persistent permissions or Full Access.
- **FR-34**: Harness Mode provides no email notifications, mobile UI or admin
  panel in V1; completion remains visible in the local activity center.

## Non-functional requirements

- **NFR-01 Security**: Draft and imported code is untrusted until committed.
  Preview execution uses OS-level isolation where available, a separate home,
  a separate Gateway port, no inherited credentials and deny-by-default egress.
- **NFR-02 Authorization**: Activation and grants require a fresh verified-owner
  session; Full Access also requires a click in trusted host UI.
- **NFR-03 Integrity**: Stored revisions and exports use canonical SHA-256
  content hashes; package verification occurs before extraction into the vault.
- **NFR-04 Durability**: Registry mutations, activation changes and migrations
  are atomic and crash-safe. A failure cannot leave half-installed code active.
- **NFR-05 Recovery**: The last known-good active-set snapshot is retained, and
  Gateway boot can bypass all user plugins in Safe Mode.
- **NFR-06 Performance**: Library reads complete within 300 ms at 500 plugins;
  permission decisions within 100 ms excluding user interaction; progress
  begins within 500 ms for long operations.
- **NFR-07 Limits**: Default import cap is 50 MiB compressed, 200 MiB expanded,
  5,000 files and nesting depth 20. Overrides require a future policy change,
  not a request embedded in a package.
- **NFR-08 Compatibility**: Every revision declares MERRICK, OpenClaw,
  Node and plugin-API ranges; migrations never mutate immutable source
  revisions in place.
- **NFR-09 Privacy**: Exports exclude secrets and personal data by construction;
  generated code receives opaque secret handles rather than secret values.
- **NFR-10 Accessibility**: All authorization and lifecycle controls are fully
  keyboard accessible, screen-reader labelled and do not rely on color alone.
- **NFR-11 Observability**: Logs use correlation IDs and structured redaction;
  source code and command output are retained only inside the selected project
  and evidence bundle according to local retention settings.
- **NFR-12 Testability**: Policy decisions, package verification, migrations and
  activation transactions are deterministic and testable without an LLM.

## Implicit requirements review

| Area | Decision |
|---|---|
| Pagination | Cursor pagination in plugin library and audit history |
| Error states | Phase-specific errors, resumable jobs, safe-mode recovery |
| Email notifications | Not required for a local desktop V1 |
| Mobile | Not required; responsive layout remains desirable |
| Admin panel | Not required for the single-owner release |
| File uploads | `.jarvis-plugin` only, strict bounded validation |
| Audit logs | Required and append-only |
| Soft delete | Required for projects and installed user plugins |

## Constraints

- Existing Python backend, WebSocket HUD, native macOS host and pinned OpenClaw
  runtime remain the primary stack.
- OpenClaw currently requires a Gateway restart for plugin code/config changes.
- The signed application bundle is immutable and may be replaced during update.
- User code must never gain authority merely because an LLM generated it.
- Web pages, plugin README files, source comments and package metadata are
  untrusted content and cannot approve permissions or expand scope.
- Existing unrelated worktree changes must remain untouched.

## Dependencies

- Pinned OpenClaw plugin SDK and `plugins init/build/validate/install` CLI.
- macOS Application Support storage and Keychain-backed secret broker.
- Existing Gateway ownership/restart logic and capability inventory.
- A local SQLite registry and migration runner.
- A sandbox runner: macOS Seatbelt/sandbox profile where available, with a
  separately scoped process/container runner as the portability fallback.
- Archive, hashing, signature and static-analysis libraries bundled and pinned
  by MERRICK

## Conflicts resolved

- **Maximum productivity vs safety**: Full Access exists, but only as explicit,
  plugin-scoped owner authorization enforced outside the model.
- **Generated plugins vs upgrade replacement**: all mutable plugins live in a
  persistent user vault; the application only ships immutable core plugins.
- **Easy sharing vs trusted execution**: export/import preserves code and
  metadata, never authority. The receiving owner grants permissions anew.
- **Self-improvement vs reproducibility**: the model may create new immutable
  revisions but cannot mutate the currently active revision in place.

## Open questions and assumed answers

- **Cloud marketplace?** Deferred. Portable file exchange is sufficient for V1.
- **Multiple local macOS accounts?** Each OS account receives an isolated vault.
- **Developer signing requirement?** Optional local signature in V1; integrity
  hashes are mandatory. Trusted publisher identities are a later marketplace
  concern.
- **Automatic activation?** No. Automated authoring and preview are allowed;
  first activation and every permission expansion require owner approval.
- **Can Full Access be global?** A user may set a standing preference that
  preselects Full Access for newly requested work, but each plugin still stores
  its own revocable grant and the trusted UI shows the effective scope before
  first activation.
