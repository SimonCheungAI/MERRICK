# Requirements

## Feasibility

Complexity: **Moderate**. This changes one macOS product's install/lifecycle behavior and its local runtime observability; it does not introduce a cloud service. Estimate: 2–3 reversible slices. Verdict: **PROCEED**.

## Functional requirements

- FR-01: There is exactly one user-facing MERRICK application copy in `/Applications`; staging copies are not treated as a runnable install.
- FR-02: Finder, Dock, Spotlight and `open -a` launch the same application and reveal an active window.
- FR-03: One native host owns the loopback backend, audio pipeline and OpenClaw Gateway; a second launch focuses the owner without starting another runtime.
- FR-04: Startup presents explicit native phases: starting local core, loading interface, connecting model, ready, or actionable failure. `booting` may not persist without a diagnostic category.
- FR-05: OpenClaw, Node and Python remain inside the application bundle. MERRICK creates its mutable per-user OpenClaw state only in Application Support.
- FR-06: Provider binding and reconnection happen in the MERRICK settings UI. API keys use Keychain; subscription sign-in opens a browser device flow from MERRICK, never Terminal.
- FR-07: Removing duplicate app copies never deletes `~/Library/Application Support/JarvisStark`, Keychain items, memory, voiceprints or workspace documents.

## Non-functional requirements

- NFR-01: Duplicate launch handling is local and completes before backend spawn.
- NFR-02: Startup stage changes are delivered within 250 ms of the native transition; backend readiness has a bounded timeout.
- NFR-03: Diagnostic records are redacted, local, and contain no API key, OAuth code, transcript, document or memory content.
- NFR-04: The packaged app remains code-signed and self-contained; a clean Mac needs no Homebrew, Python, Node, OpenClaw, Codex CLI or Terminal setup.

## Resolved choices

- The formal installation target is `/Applications/MERRICK.app`; `dist/` is developer output only.
- “Internalize OpenClaw” means bundle its runtime and manage its state/config through MERRICK. It does not mean storing secrets inside the bundle or exposing raw OpenClaw configuration to users.
- A failed setup must remain recoverable from MERRICK Settings; the interface must not silently funnel users into a terminal.
