# Architecture

## Phase 2 — Architecture

Pattern: extend the existing modular monolith with one **app-owned native capability bootstrap**. The signed app bundle is immutable; its resources seed a private runtime once. OpenClaw continues to own agent routing and Codex continues to own the MCP calls.

```text
Signed MERRICK app bundle
  runtime/codex-computer-use/        official client + local marketplace asset
              │ read-only seed
              ▼
Application Support/JarvisStark/OpenClaw/native-home/.codex/
  ├─ computer-use/                   native client copied once
  ├─ marketplaces/jarvis-bundled/    local plugin marketplace
  └─ plugins/                        Codex-owned installed plugin state
              │ CODEX_HOME
              ▼
MERRICK-owned OpenClaw Gateway
  ├─ Codex harness ── setup/probe ──► official computer-use MCP server
  └─ normal model stream ◄──────────► MERRICK local backend / HUD
```

## Key flows

### First compatible startup

1. The native app starts the backend as usual.
2. Before launching the gateway, the backend calls the bootstrapper. It verifies immutable bundle assets using an allowlisted layout, then copies them into the private Codex home atomically if the recorded version differs.
3. It supplies that private `CODEX_HOME` to the gateway, whose Computer Use configuration points to the private marketplace JSON and enables `autoInstall`.
4. OpenClaw/Codex enables plugins, installs `computer-use`, reloads MCP servers, and probes its tool inventory before the first Computer Use turn.
5. On success, the agent can invoke native Computer Use tools. On any failure, the component becomes unavailable but ordinary conversation stays online.

### Subsequent startup/update

1. The bootstrapper compares the immutable manifest version with a redacted local installation record.
2. Equal versions: no copy and no marketplace install attempt; warm gateway path is unchanged.
3. New version: stage a new private resource directory, validate required executables/manifests, then atomically replace the prior seed. The Codex-managed plugin is re-enabled/reloaded.
4. If staging fails, retain the last known-good private resource state and launch without Computer Use.

## Security and performance

- The only trust boundary crossed is signed/bundled resources to a same-user 0700 private directory. No downloaded/unverified bundle path is accepted.
- macOS TCC remains authoritative. MERRICK can guide but cannot grant Accessibility/Screen Recording access.
- Plugin capability discovery happens during gateway warm-up; normal no-tool turns do not wait on an installer. A circuit breaker disables Computer Use after a setup failure until the next explicit restart/retry.
- Current OpenClaw, browser and app-specific tools retain their existing contracts; Computer Use is additive.
