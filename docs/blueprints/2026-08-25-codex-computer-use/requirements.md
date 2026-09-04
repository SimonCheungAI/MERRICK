# Requirements

## Phase 0 — Feasibility

Complexity: **Moderate**. The feature crosses the signed macOS bundle, a proprietary Codex-native client, isolated OpenClaw/Codex runtime state, model tool discovery, and macOS TCC permissions. Estimated effort: two small vertical slices. Verdict: **PROCEED WITH DISTRIBUTION WARNING**.

Evidence: this Mac has the official `computer-use` plugin in the OpenAI bundled marketplace and an installed 69 MB `Codex Computer Use.app`. The plugin launcher resolves its native client from `CODEX_HOME/computer-use`; the current MERRICK gateway deliberately uses a private `HOME`, so it cannot discover that client or marketplace. Enabling the OpenClaw flag without an app-owned source causes every Codex turn to fail before streaming.

## Functional requirements

- FR-01: A MERRICK installation with the bundled Computer Use assets can install and enable the official `computer-use` MCP server in MERRICK's private Codex home.
- FR-02: Normal voice conversation remains available when Computer Use assets are absent, uninstalled, disabled, or denied by macOS.
- FR-03: MERRICK never reads, writes, registers plugins in, or uses credentials from the user's `~/.codex` or a separately installed OpenClaw instance.
- FR-04: The gateway exposes computer tools only after the plugin reports an available MCP server; it must not start a turn that will fail solely because setup is missing.
- FR-05: The app surfaces one concise local status/recovery message for unavailable client, failed installation, unavailable MCP server, and denied macOS permissions.
- FR-06: Installation state and diagnostics contain no screenshots, documents, transcripts, provider credentials, or model prompts.

## Non-functional requirements

- NFR-01: Existing plain conversation p95 first-token latency must not regress by more than 250 ms after the one-time setup completes.
- NFR-02: First-time native installation may take up to 60 seconds, must report progress, and must never block the microphone/UI thread.
- NFR-03: All mutable plugin/config/auth state remains under `~/Library/Application Support/JarvisStark/OpenClaw/native-home/` with mode 0700.
- NFR-04: A failure is reversible by disabling one configuration flag/restarting the gateway; no user data migration is required.

## Constraints and non-goals

- macOS only; Computer Use depends on Accessibility and Screen Recording permissions that the OS user must explicitly approve.
- The official plugin manifest is proprietary. A publicly distributed MERRICK build may include it only when its distribution terms permit; otherwise onboarding must obtain it through an official installer/source. This implementation validates the app-owned integration on the current authorized Mac.
- This slice enables the official Computer Use transport; it does not remove the existing MERRICK action audit/receipt system or promise arbitrary unattended file mutation.
- No global Codex marketplace, global plugin cache, account profile, or API key becomes a dependency.
