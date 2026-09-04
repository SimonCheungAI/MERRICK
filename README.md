# MERRICK

[Website](https://getmerrick.com/) · [MIT License](LICENSE) · macOS / Apple silicon

A transparent macOS voice assistant with a floating point-cloud interface,
streamed English speech, OpenClaw system tools, and ChatGPT/Codex subscription
authentication. No OpenAI API key is required.

This repository is the public source distribution. It deliberately excludes
developer credentials, notarization records, personal memory, voiceprints,
local workspaces, generated applications, and dependency/model caches. Signed
release downloads will be published separately after Apple notarization.

MERRICK addresses its verified owner as “sir” when an address is useful.
It does not retain or volunteer a personal name as part of its persona.

## Architecture

```text
macOS speech recognition → local FastAPI/WebSocket → OpenClaw loopback Gateway
                                              ├─ Codex app-server (the brain)
                                              ├─ official Gateway protocol client (v4)
                                              ├─ full OpenClaw main session and tool router
                                              ├─ OpenClaw Control UI one-time handoff
                                              ├─ coding, sessions, skills and subagents
                                              ├─ signed native macOS companion bridge
                                              ├─ explicit one-window screen vision
                                              ├─ scoped transcript + wiki memory
                                              └─ structured personal operations
```

The desktop app streams partial recognition immediately. After a short stable
pause, the durable OpenClaw main session receives the request and decides
whether its enabled tools are needed. MERRICK does not use a second action
vocabulary or capability allowlist in front of OpenClaw. Text is sent to the HUD and TTS queue as model
deltas arrive, so speech can start before the full answer is ready. A transcript
that grows during the initial action-prefix probe cancels and replaces that
speculative request before any stale text or audio can escape.

Voice language can be changed in **SETUP → Voice Language**. English and
Mandarin both use the local Merrick identity: English is anchored by its
approved English accent-calibration reference, while Mandarin keeps the
original selected Merrick reference. Edge voices remain fallback-only.
Switching also updates recognition and clears any in-flight reply so
old-language audio cannot leak into the new conversation.

## Install and authorize OpenClaw

```sh
git clone https://github.com/SimonCheungAI/MERRICK.git
cd MERRICK
uv sync
./scripts/setup-openclaw.sh
./scripts/login-openclaw.sh
```

The second command displays a one-time OpenAI device code. It signs OpenClaw in
with the existing ChatGPT/Codex subscription; it does not create or store an API
key in this repository.

OpenClaw is pinned to `2026.8.1`. Runtime config, OAuth credentials, sessions,
transcript summaries, and the gateway token stay outside the repo under:

```text
~/Library/Application Support/JarvisStark/OpenClaw/
```

Completed owner conversations are also kept locally as readable daily notes:

```text
~/Library/Application Support/JarvisStark/OpenClaw/memory/daily/YYYY-MM-DD.md
```

Each entry contains the local time, your utterance, and MERRICK's final
answer. SQLite/FTS remains the fast retrieval index, while these notes are the
date-organised record. On exit, a source-checkout install publishes that same
private memory snapshot to its configured private Git repository; a packaged
install stores the snapshot only under Application Support until a repository
is configured.

## Build and run the desktop app

The source checkout requires macOS on Apple silicon, Xcode command-line tools,
Python 3.12 or newer through `uv`, and `pnpm`. The selected local Steadfast
voice runtime uses Qwen3-TTS model files stored outside Git; when those files
are unavailable, the development runtime uses its bounded Edge TTS fallback.
The self-contained release builder also expects the official Codex Computer
Use assets installed by Codex on the build Mac.

```sh
./scripts/build-macos-app.sh
open dist/MERRICK.app
```

For a distributable Apple-silicon installer, use:

```sh
./scripts/package-macos-app.sh
```

This generates `dist/MERRICK-macOS-arm64.dmg`. The recipient drags
MERRICK into Applications; no project checkout, Python, Node, Homebrew,
or Codex installation is needed. With no release credentials the script
produces an explicitly labelled, ad-hoc-signed **internal QA image** only.

For an external release, first store App Store Connect notarization credentials
with `notarytool`, then run:

```sh
JARVIS_PUBLIC_RELEASE=1 \
JARVIS_CODESIGN_IDENTITY="Developer ID Application: Your Company (TEAMID)" \
JARVIS_NOTARY_PROFILE="MERRICK_NOTARY" \
./scripts/package-macos-app.sh
```

Public mode fails closed unless the Developer ID identity and notary profile
are present. It signs with the hardened runtime and trusted timestamp, submits
the DMG to Apple, staples and validates the ticket, and runs Gatekeeper's
distribution assessment before reporting success.

The Developer ID path signs native Python/Node dependencies individually,
removes development-only debugging entitlements, and retains valid vendor
signatures (including Computer Use). Private-key signing is serial to avoid
stacked Keychain authorization prompts. The build writes
`dist/MERRICK-signing-report.json`; notarization writes the submission result
and Apple log to `dist/MERRICK-notarization*.json`. An `Accepted` result is
required before stapling or presenting the image as notarized.

To sign a separately staged, already-built app without replacing the installed
app or rebuilding the internal QA image:

```sh
.venv/bin/python scripts/macos_release_signing.py /path/to/staging/MERRICK.app \
  --identity "Developer ID Application: Your Company (TEAMID)" \
  --report /path/to/staging/signing-report.json
```

Add `--dry-run` for a read-only inventory. Store notarization credentials using
the interactive `notarytool store-credentials` prompt; do not put passwords or
signing private keys in source files, shell history, or the application bundle.

The app starts its Python backend; the backend starts the loopback OpenClaw
Gateway when needed. First launch requires macOS Microphone and Speech
Recognition permission. Screen Recording permission is optional and requested
only when the user directly asks to inspect the current visible window.

Closing the MERRICK window quits the application rather than hiding it.
The native host gives the backend a bounded graceful-shutdown window, then
terminates its owned process group so the local API, OpenClaw Gateway, TTS, and
audio workers cannot remain behind. A later launch also reclaims a verified
orphan left by a hard crash before starting a new backend.

To remove MERRICK without leaving local state behind, open **Settings →
Uninstall → Uninstall and erase local data**. After an explicit confirmation,
the bundled uninstaller removes the app-owned processes, Application Support
data, Workspace, preferences, Keychain provider credentials, notifications,
and bundle-specific privacy grants before deleting the application. Export any
memory or Workspace files you want to keep first.

## First-run model connection

On first launch, MERRICK presents a native setup screen. It can reuse a
local Codex/ChatGPT login or a local Claude Code login, or connect an API key
for OpenAI, Anthropic, Gemini, Kimi (Moonshot), DeepSeek, or a custom
OpenAI-compatible endpoint. The selected provider and model are stored in a
local, permission-restricted profile at:

```text
~/Library/Application Support/JarvisStark/provider-profile.json
```

API keys never enter that profile, the OpenClaw config, workspace, logs, or
GitHub backup. They are held in macOS Keychain and passed only to MERRICK's
local backend and its gateway child at launch. Reopen **SETUP → Manage model
connection** to switch providers later.

## Permission boundary

OpenClaw is the execution and authorization boundary. The durable `main`
session uses the full configured OpenClaw profile: browser, computer, files,
exec, coding, skills, sessions, subagents, automations, and installed
integrations. A method accepted by OpenClaw is not rejected by a second
MERRICK capability or verb allowlist.

Removing that duplicate gate does not bypass OpenClaw security. Gateway roles,
operator scopes, device pairing, protocol validation, and action-time user
approvals remain authoritative. MERRICK keeps provider credentials in
Keychain and passes them only to its owned local runtime. The native companion
bridge validates the calls that cross into macOS APIs, but it does not filter
OpenClaw's own capability surface.

Open **SETUP → OpenClaw Workspace → Open OpenClaw Control UI** to use the full
OpenClaw interface. MERRICK requests an official short-lived browser
handoff for the exact app-owned loopback Gateway; the pairing URL never enters
the web HUD or logs.

Pure conversation still carries an instruction not to use tools unnecessarily.
Requested work is interpreted by OpenClaw itself rather than by fixed phrases.
The companion may retain specialised user-facing flows such as structured
personal operations, visible public research, notifications, and one-window
screen capture. Those are presentation integrations, not restrictions on the
OpenClaw main session.

## Unified workspace documents

MERRICK reads documents and writes its requested notes or summaries in one
dedicated folder, created on first use:

```text
~/Library/Application Support/JarvisStark/Workspace/Documents/
```

Put PDFs, Word (`.docx`), Markdown, text, CSV, or JSON files there and ask, for
example, “Read the attention paper” or “What were this paper's experimental
results?” Ask it to create or revise a note there when you want it to write.
MERRICK resolves only files below that folder, rejects symlinks that leave
it, and cannot list or open any other location. Its reader automatically hides
the small internal MERRICK configuration files in that folder, so it will
not mistake them for your documents.

Text extraction and the persistent extraction cache run locally. The cache is
stored in `~/Library/Application Support/JarvisStark/DocumentCache/` and is used
only to avoid extracting an unchanged document again. For an answer, the local
host ranks the document chunks and sends at most about 11,000 relevant characters
to the authenticated model; it never sends the entire library or grants the
model a path-reading tool. As with screen vision, those selected excerpts are
processed through the configured Codex/OpenAI session and are not stored in the
MERRICK conversation-memory archive. Scanned or protected PDFs without an
embedded text layer cannot be read yet.

## Codex workspace control

For creating or revising working notes, MERRICK uses Codex in this same
dedicated workspace:

```text
~/Library/Application Support/JarvisStark/Workspace/Documents/
```

Say, for example, “Create a note in the Merrick workspace with today’s project
decisions,” “List the workspace files,” or “Update the draft in the workspace.”
Codex can read, create, and edit only inside that folder. It cannot read another
folder, delete, move, rename, chmod, run shell commands, alter app settings, or
perform generic computer control. `AGENTS.md` in the workspace records the same
boundary for every Codex turn.

The companion personal Codex plugin `jarvis-codex-bridge` can list and read
user documents from that same folder in the Codex desktop app. It exposes no
generic filesystem or desktop-control tool.

The Gateway exposes no model-callable generic filesystem or shell tool. Codex
enforces its own `workspace-write` sandbox for the dedicated workspace. This
avoids a macOS nested-sandbox limitation while preserving the practical write
boundary: the conversational model has no path or shell interface, and Codex
cannot write beyond that single workspace.

The Gateway listens only on a fresh random loopback port and uses a random
256-bit bearer token. Before sending that token, MERRICK verifies the
listener PID, user, runtime binary, project directory, and private config file;
it refuses to attach to an unmanaged Gateway.
The MERRICK WebSocket separately fails closed unless both its exact local
HTTP origin and a random per-launch desktop bridge token match. Every native
WebKit message carries the same token, must come from the main local frame, and
the privileged HUD is prevented from navigating away from its local origin.
Both the health check and main HUD document must return an HMAC proof, so a
different process cannot impersonate the backend by pre-empting its local port.

DuckDuckGo provides key-free search. It is an experimental HTML integration, so
search may occasionally encounter a challenge page. The non-conversational
research executor is the only component allowed to expose `web_search`;
model-callable `web_fetch` is disabled.

## Memory

OpenClaw keeps the stable MERRICK session in its own state store. Completed
voice conversations are also sent in bounded chunks to OpenClaw's scoped
`transcripts` tool through a separate `memory-writer` agent, which writes an
append-only transcript and deterministic summary under its state directory.
The conversational `main` agent cannot call that writer and receives no generic
path, transcript-import, wiki-write, or file-writing tool.

## Verification

```sh
./scripts/openclaw-audit.sh
pnpm --filter openclaw-plugin-jarvis-safe-tools test
~/.local/bin/uv run python -m py_compile server/main.py server/openclaw_client.py
~/.local/bin/uv run python -m unittest discover -s tests -v
```

The audit validates the active config, inspects the runtime plugin, and runs
OpenClaw's deep security audit. Secrets and runtime state are ignored by Git.
Security issues should be reported privately through GitHub Security
Advisories rather than a public issue.

## Main files

- `server/main.py` — voice session, streaming, interruption, and TTS flow
- `server/openclaw_client.py` — authenticated loopback OpenClaw client
- `server/openclaw_gateway_rpc.py` — supervisor for the official Gateway v4 client
- `openclaw/gateway-client-bridge/` — typed OpenClaw protocol bridge
- `openclaw/openclaw.template.json5` — full-capability template with user-resolved action approvals
- `openclaw/action-planner-workspace/` — dormant legacy native-action fallback
- `openclaw/plugins/jarvis-safe-tools/` — native companion bridge (stable legacy id)
- `desktop/MerrickApp.swift` — transparent desktop window and native speech input
- `web/` — point-cloud HUD
