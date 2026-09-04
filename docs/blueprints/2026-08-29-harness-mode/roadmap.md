# Development Roadmap

## Delivery rules

- Each milestone is a thin, demonstrable vertical slice behind a feature flag.
- No generated/imported code enters the production Gateway before Milestone 4.
- Each slice has a rollback that leaves the vault readable and prior MERRICK
  conversation/organizer behaviour intact.
- Schema, package and Harness ABI versions are explicit from the first slice;
  migrations include historical fixtures before the next release ships.
- Commits remain small and reversible. Security controls are product behaviour,
  not a final hardening phase.

## Milestone 0 — Authority and persistent-vault baseline (MVP, 3–5 days)

Goal: MERRICK can discover a private user plugin vault and display a
read-only lifecycle snapshot, while the agent is technically unable to mutate
production plugin config or grants directly.

Tasks:

- Add `harness_mode_v1` and `user_plugin_runtime_v1` flags, default off.
- Define versioned contracts, permission algebra and state machines as pure code.
- Create private `PluginVault` root validation, SQLite migration runner, audit
  chain and application-start health projection.
- Add Config Projector and active-set interfaces with a no-user-plugin generation.
- Constrain the main OpenClaw/Codex agent away from direct production config,
  vault-registry and grant mutations; retain a clearly separate developer mode.
- Add the signed/bundled `jarvis-harness-bridge` skeleton with no generated tools.

Deliverable: the Capabilities view shows “Harness unavailable/ready,” vault
schema, active generation and Safe Mode status; app restart preserves a sample
registry record, but no user code can execute.

Testing: permission deny matrix; exact owner/resource checks; SQLite crash and
integrity fixtures; symlink/private-mode vault checks; configuration conformance;
existing conversation, voice and capability-catalog regressions.

Rollback: disable flags and load the existing core-only OpenClaw config. The new
empty/read-only vault remains untouched.

## Milestone 1 — Isolated authoring and verification lab (MVP, 6–9 days)

Goal: a user request creates a real TypeScript plugin project that MERRICK
can edit, build and test in an isolated lab, without production activation.

Tasks:

- Implement project, immutable revision, job/step and evidence repositories.
- Create the versioned Harness TypeScript SDK, plugin template, permissions
  manifest and deterministic source-tree hashing.
- Expose model tools for project creation, bounded authoring, verification,
  status and cancellation only.
- Build with bundled Node/pnpm, frozen lockfile, disabled lifecycle scripts and
  an app-controlled dependency cache.
- Add type-check, unit-test, static scan, OpenClaw/Harness schema validation and
  disposable test-Gateway smoke stages.
- Implement leases, restart recovery, budgets and activity events.

Deliverable: “make a read-only plugin that summarizes selected Markdown notes”
produces source, tests and evidence; it can be inspected and revised but cannot
touch production or personal files.

Testing: malicious instructions/source comments, budget exhaustion, cancellation,
process-tree cleanup, lockfile tampering, install-script blocking, deterministic
hashes, interrupted job recovery and synthetic plugin golden path.

Rollback: stop Lab workers and disable authoring tools; retain/export project
source as ordinary files.

## Milestone 2 — Portable import/export (MVP, 4–6 days)

Goal: an immutable revision can move safely between two clean MERRICK
profiles without carrying authority or disappearing from the source profile.

Tasks:

- Implement deterministic `.jarvis-plugin` writer, manifest, permission schema,
  compatibility ranges, hashes, SBOM and optional local Ed25519 signature.
- Implement streamed intake and archive traversal/link/bomb/duplicate-path limits.
- Add pre-accept inspection, file inventory, signature state and compatibility UI.
- Enforce fixed export include/exclude schemas and secret/absolute-path scanner.
- Add import collision handling and origin-qualified identities.
- Add local file panels, download tickets and package audit events.

Deliverable: export the Markdown plugin from profile A, import it into profile B,
compare identical source/artifact hashes, and observe that profile B has no grant
or active installation.

Testing: ZIP Slip, symlink/hardlink/special-file corpus, Unicode/case collisions,
compressed and expanded limits, corrupt hashes, invalid signatures, secret
canaries, reproducible archive bytes and cross-profile round trip.

Rollback: disable upload/export UI and delete only unaccepted intake files;
accepted immutable revisions stay in the vault.

## Milestone 3 — Sandboxed preview and permission broker (MVP, 7–10 days)

Goal: the owner can run a plugin against synthetic or explicitly selected data
while every host interaction is denied or mediated by a revocable grant.

Tasks:

- Implement worker supervisor, authenticated local RPC and versioned worker ABI.
- Generate macOS sandbox profiles with private home, closed descriptors, process,
  filesystem and network boundaries; fail closed when isolation is unavailable.
- Implement broker ports for filesystem, network, apps, processes, data and
  opaque secret handles with policy checks on every call.
- Build declared/static/observed permission reconciliation and exact previews.
- Implement native permission sheet for once/session/while-enabled/persistent and
  Full Access requests; voice/model may open but cannot decide it.
- Implement immediate revocation, worker termination, limits and circuit breakers.

Deliverable: the sample plugin previews with a selected notes folder, is denied
outside it, requests a new permission when expanded, and loses access immediately
when the user revokes the grant.

Testing: path/symlink race, DNS rebinding/private-network SSRF, process escape,
environment/FD leakage, revoked-session replay, owner-assertion tampering, voice
approval rejection, Full Access exclusion boundaries and hostile plugin corpus.

Rollback: terminate all preview workers and disable the broker; projects and
evidence remain readable/exportable.

## Milestone 4 — Transactional production activation (MVP, 6–9 days)

Goal: an approved sandboxed plugin becomes a real OpenClaw tool, survives
Gateway restart and can be disabled or rolled back without destabilizing MERRICK

Tasks:

- Complete the core Harness Bridge tool registration/proxy and worker handshake.
- Implement installations, runtime instances, active sets and Config Projector.
- Stage/validate/swap/restart/health-check/commit activation transaction.
- Add public plugin-ID collision rules, reserved core IDs and exact hash handshakes.
- Implement disable, enable, rollback, quarantine and core-only Safe Mode.
- Require current evidence and revision-bound grant before candidate creation.

Deliverable: approve and activate the Markdown plugin, call it from an ordinary
MERRICK conversation, restart the app, revoke/disable it, and roll back to
its previous revision. A deliberately broken revision rolls back automatically.

Testing: crash at every activation boundary, concurrent generation conflict,
Gateway timeout, bridge generation/hash mismatch, worker crash, revocation while
calling, ID collision, core-ID shadow attempt and packaged-app E2E.

Rollback: disable `user_plugin_runtime_v1`; core-only config starts and all user
revisions/grants/active-set history remain retained.

## Milestone 5 — Complete Harness and Plugin Library experience (V1, 5–8 days)

Goal: users can operate the entire lifecycle through natural conversation and a
clear visual workspace without needing CLI or filesystem knowledge.

Tasks:

- Add Harness project view with activity, source diff, evidence and preview.
- Extend Capabilities into a searchable/paginated Plugin Library with origin,
  health, permissions, versions, rollback, export/import and quarantine views.
- Add conversational repair flow that always creates a child revision.
- Add progress/cancellation/restart states, accessible controls and concise
  English/Chinese product copy; spoken replies remain short.
- Add permission review center, grant expiry/revocation and periodic Full Access
  reminders without approval fatigue.
- Add redacted audit/activity view and diagnostics export.

Deliverable: a non-developer can request, watch, test, authorize, activate,
export, import, update, roll back and disable a plugin from the product UI.

Testing: keyboard/screen-reader navigation, mobile-width layout, long names and
errors, localization, pagination, rapid cancel/resume, stale previews, UI/model
attempts to bypass native approval, usability acceptance flow.

Rollback: hide V1 UI and model entry points; installations continue under the
Milestone 4 lifecycle controls.

## Milestone 6 — Upgrade preservation and recovery qualification (V1, 5–7 days)

Goal: replacing the signed app and upgrading OpenClaw/Harness ABI never silently
removes user plugins and cannot trap the core assistant offline.

Tasks:

- Add expand-migrate-contract registry migrations and pre-migration snapshots.
- Add startup compatibility scan, per-plugin quarantine and repair guidance.
- Make packaging/update/uninstall scripts explicitly preserve `PluginVault`;
  add a separate owner-confirmed vault-removal workflow.
- Add disk preflight, read-only recovery, snapshot restore and Safe Mode launch.
- Build upgrade fixtures for every released schema, Harness ABI and supported
  OpenClaw version; verify compatible plugins remain enabled.
- Document the user-data contract and support diagnostics.

Deliverable: upgrade a packaged older build with enabled compatible and
incompatible plugins: compatible code remains live; incompatible code is
retained/quarantined/exportable; a migration fault starts recovery without data
loss.

Testing: signed bundle replacement, reinstall, app-only uninstall, explicit data
removal, low disk, corrupt DB, interrupted migration, incompatible ABI, last-good
and core-only boot, snapshot restore and hashes before/after upgrade.

Rollback: restore the pre-migration snapshot and previous app version; keep the
newer vault mounted read-only until migration can safely resume.

## Milestone 7 — Native OpenClaw compatibility and sharing hardening (V2, 5–8 days)

Goal: advanced owners can import an ecosystem plugin that requires in-process
OpenClaw APIs with an honest Full Trust boundary and robust recovery.

Tasks:

- Detect native-only APIs and require `native_full_trust` profile.
- Add source/SBOM/vulnerability review, exact artifact pinning and signed package
  preference; never convert manifest claims into fine-grained enforcement.
- Add separate native warning/approval, Gateway restart and Safe Mode watchdog.
- Add publisher-key management and signature verification without inheriting
  permissions or treating a signature as safety certification.
- Add deterministic batch backup/restore and optional offline plugin collection.
- Prepare a future marketplace protocol without implementing remote discovery,
  payment or automatic updates.

Deliverable: import, explicitly trust and run one pinned native OpenClaw sample;
a crashing sample triggers core-only recovery and remains exportable/disabled.

Testing: malicious native sample, dependency CVEs, signature/key rotation,
Gateway crash loop, core shadowing, safe-mode startup and backup/restore round trip.

Rollback: disable native compatibility globally; sandboxed Harness plugins and
the retained native package library continue to work/be exportable respectively.

## Effort and gates

| Scope | Milestones | Estimate, one experienced engineer | Release gate |
|---|---|---:|---|
| Safe authoring + portable packages | 0–2 | 2.5–4 weeks | No production execution |
| Useful sandboxed Harness MVP | 0–4 | 5–7.5 weeks | M0–M4 release blockers pass |
| Product-complete V1 + upgrade survival | 0–6 | 7–11 weeks | Packaged upgrade/recovery qualification |
| Native OpenClaw compatibility V2 | 0–7 | 8–13 weeks | Explicit Full Trust security review |

Milestones 1 and 2 can overlap after M0 contracts freeze. Milestones 3 and 4 are
security-sequential: production activation cannot begin before broker isolation,
revocation and native approval tests pass.
