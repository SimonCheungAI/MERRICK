# MERRICK Harness Mode Blueprint

Status: validated with release-blocking implementation warnings on 2026-08-30.
Implementation may begin at Milestone 0; generated/imported production plugins
remain disabled until the M0–M4 gates pass.

Implementation progress (2026-08-30): Milestone 0 slice 0 is complete. The
packaged host explicitly enables a read-only Harness readiness surface; a
private, versioned, core-only PluginVault registry is created in Application
Support and projected into the existing OpenClaw capability panel. Symlinked or
unavailable vault state fails closed without taking the ordinary capability
inventory offline. Production user-plugin execution remains hard-disabled. The
next M0 slice is the host-only lifecycle/config authority boundary and signed
empty Harness Bridge.

| Attribute | Decision |
|---|---|
| Project | MERRICK Harness Mode and User Plugin Vault |
| Complexity | Complex |
| Verdict | PROCEED |
| Architecture | Local modular monolith + host policy kernel + persistent vault + sandboxed plugin workers |
| Safe Harness MVP | 5–7.5 engineering weeks |
| Product-complete V1 | 7–11 engineering weeks |
| Native OpenClaw compatibility | V2, explicit Full Trust only |

## Outcome

The owner may instruct MERRICK to create, test and preview a plugin. The
plugin becomes a production OpenClaw tool only after a trusted native approval
binds exact permissions—or an explicit plugin-scoped Full Access grant—to one
immutable revision. Default plugins execute out of process through a signed
OpenClaw bridge; imported native in-process OpenClaw plugins are treated as
separate Full Trust code.

Generated and imported plugins are user-owned data under macOS Application
Support. They can be exported/uploaded as deterministic `.jarvis-plugin`
packages, never carry grants or secrets, survive ordinary app upgrades and are
retained—but quarantined rather than deleted—when a new runtime is incompatible.

## Blueprint package

| Document | Phase and purpose |
|---|---|
| [requirements.md](requirements.md) | Phase 0–1: feasibility, explicit/implicit requirements, constraints and resolved conflicts |
| [architecture.md](architecture.md) | Phase 2: components, trust boundaries, execution profiles, flows, stack and scale |
| [data-model.md](data-model.md) | Phase 3: registry entities, immutable revisions, grants, jobs, active sets and retention |
| [api-contracts.md](api-contracts.md) | Phase 3: REST/WebSocket/model tool contracts and authorization boundaries |
| [errors.md](errors.md) | Phase 3: error taxonomy, retries, cancellation, restart and rollback recovery |
| [risk-register.md](risk-register.md) | Phase 3: security, lifecycle, supply-chain and product risks |
| [roadmap.md](roadmap.md) | Phase 4: working vertical slices, tests, estimates and rollback |
| [validation.md](validation.md) | Phase 5: 25-point quality gate and implementation permission |

## Non-negotiable decisions

1. The model may author and test, but cannot approve permissions or commit a
   production active set.
2. Sandboxed Harness plugins are the default. Generated code does not execute in
   the production Gateway process.
3. Full Access is explicit, plugin-scoped, revision-bound, revocable and audited;
   it does not bypass OS consent, Keychain or package/migration integrity.
4. Exported/imported packages contain code and evidence, never credentials,
   grants, absolute paths, private logs or personal fixtures.
5. The signed app bundle and core bridge are immutable to Harness Mode. User
   plugins live in `~/Library/Application Support/JarvisStark/PluginVault`.
6. Upgrades revalidate compatibility. Failure quarantines and retains a plugin;
   it never silently removes it.
7. Activation is staged and health-checked. Failure returns to the previous
   active generation or core-only Safe Mode.

## Immediate implementation target

Milestone 0 establishes the vault, schema, host-only lifecycle authority,
core-only active-set generation and configuration conformance tests. This is the
prerequisite that safely unlocks the existing OpenClaw production capability.
